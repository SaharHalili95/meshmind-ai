"""Hop-by-hop routing environment with a Gym-style API.

An episode is an ordered batch of flows. Each flow is routed one hop at a time
by the policy; a flow terminates on delivery, an invalid action, a loop or the
step cap. Between flows, link loads decay to model traffic draining.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from meshmind.config import EnvironmentConfig
from meshmind.metrics import FlowResult
from meshmind.topology import NetworkTopology
from meshmind.traffic import Flow, TrafficGenerator

State = tuple[int, int, int]
"""(current_node, destination_node, utilization_bin)."""

UTILIZATION_BIN_EDGES: tuple[float, float] = (0.5, 0.85)


def utilization_bin(utilization: float) -> int:
    low, high = UTILIZATION_BIN_EDGES
    if utilization < low:
        return 0
    if utilization < high:
        return 1
    return 2


StepResult = tuple[State, float, bool, dict[str, Any]]


class NetworkEnvironment:
    def __init__(
        self,
        topology: NetworkTopology,
        traffic: TrafficGenerator,
        flows_per_episode: int = 25,
        config: EnvironmentConfig | None = None,
    ) -> None:
        if flows_per_episode < 1:
            raise ValueError("flows_per_episode must be >= 1")
        if set(traffic.nodes.tolist()) - set(topology.nodes):
            raise ValueError("traffic generator references nodes outside the topology")
        self.topology = topology
        self.traffic = traffic
        self.flows_per_episode = flows_per_episode
        self.config = config or EnvironmentConfig()
        self.flows: list[Flow] = []
        self.flow_index = 0
        self.episode_done = True
        self.completed_flows: list[FlowResult] = []

    @property
    def max_steps(self) -> int:
        return self.config.max_steps

    @property
    def current_flow(self) -> Flow:
        if self.episode_done:
            raise RuntimeError("episode is finished; call reset()")
        return self.flows[self.flow_index]

    def reset(self, seed: int | None = None, flows: Sequence[Flow] | None = None) -> State:
        """Clear link loads and start a new episode.

        ``flows`` replays an explicit scenario instead of sampling one from the
        traffic generator.
        """
        self.topology.reset_loads()
        if flows is not None:
            if not flows:
                raise ValueError("flows must not be empty")
            for flow in flows:
                if flow.source == flow.destination:
                    raise ValueError("flow source and destination must differ")
                if (
                    flow.source not in self.topology.graph
                    or flow.destination not in self.topology.graph
                ):
                    raise ValueError("flow references a node outside the topology")
            self.flows = list(flows)
        else:
            self.flows = self.traffic.generate(self.flows_per_episode, seed=seed)
        self.flow_index = 0
        self.episode_done = False
        self.completed_flows = []
        self._start_flow()
        return self.get_observation()

    def _start_flow(self) -> None:
        flow = self.flows[self.flow_index]
        self.current_node = flow.source
        self.path: list[int] = [flow.source]
        self.flow_steps = 0
        self.flow_latency = 0.0
        self.delivered_fraction = 1.0

    def get_observation(self) -> State:
        destination = self.flows[self.flow_index].destination
        util = self.topology.outgoing_utilization(self.current_node)
        return (self.current_node, destination, utilization_bin(util))

    def get_valid_actions(self, state: State | None = None) -> list[int]:
        """Outgoing neighbours, masking nodes the active flow already visited.

        The mask only applies to the active flow's current node. If every
        neighbour was visited (a dead end), all neighbours are returned so the
        flow can still act and terminate as a loop.
        """
        node = self.current_node if state is None else state[0]
        neighbors = self.topology.neighbors(node)
        if self.episode_done or node != self.current_node:
            return neighbors
        unvisited = [n for n in neighbors if n not in self.path]
        return unvisited or neighbors

    def _is_dead_end(self, node: int) -> bool:
        """True when every neighbour of ``node`` is already on the path (a loop is forced)."""
        return all(n in self.path for n in self.topology.neighbors(node))

    def step(self, action: int) -> StepResult:
        if self.episode_done:
            raise RuntimeError("episode is finished; call reset()")

        flow = self.current_flow
        state = self.get_observation()
        self.flow_steps += 1
        failure: str | None = None
        delivered = False
        hop_latency = 0.0

        if action not in self.topology.neighbors(self.current_node):
            reward = self.config.invalid_action_penalty
            failure = "invalid_action"
            next_state = state
        else:
            u, v = self.current_node, int(action)
            self.topology.add_load(u, v, flow.demand)
            hop_latency = self.topology.edge_cost(u, v)
            previous_fraction = self.delivered_fraction
            self.delivered_fraction *= self.topology.delivery_fraction(u, v)
            dropped = previous_fraction - self.delivered_fraction
            self.flow_latency += hop_latency
            reward = -self.config.latency_weight * hop_latency - self.config.drop_penalty * dropped

            revisited = v in self.path
            self.current_node = v
            self.path.append(v)
            next_state = self.get_observation()

            if v == flow.destination:
                delivered = True
                reward += self.config.delivery_reward
            elif revisited or self._is_dead_end(v):
                failure = "loop"
                reward += self.config.loop_penalty
            elif self.flow_steps >= self.config.max_steps:
                failure = "max_steps"
                reward += self.config.max_steps_penalty

        done = delivered or failure is not None
        info: dict[str, Any] = {
            "hop_latency": hop_latency,
            "flow_index": self.flow_index,
            "flow_steps": self.flow_steps,
            "flow_done": done,
            "episode_done": False,
        }
        if done:
            result = FlowResult(
                source=flow.source,
                destination=flow.destination,
                offered_demand=flow.demand,
                delivered_demand=flow.demand * self.delivered_fraction if delivered else 0.0,
                latency_ms=self.flow_latency,
                hops=len(self.path) - 1,
                success=delivered,
                failure_reason=failure,
                path=tuple(self.path),
            )
            self.completed_flows.append(result)
            info["flow_result"] = result
            info["avg_utilization"] = self.topology.average_utilization()
            self._advance_flow()
            info["episode_done"] = self.episode_done
        return next_state, float(reward), done, info

    def _advance_flow(self) -> None:
        if self.flow_index + 1 >= len(self.flows):
            self.episode_done = True
            return
        self.flow_index += 1
        self.topology.decay_loads(self.config.load_decay)
        self._start_flow()
