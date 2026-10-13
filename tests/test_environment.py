from __future__ import annotations

import pytest

from meshmind.config import EnvironmentConfig
from meshmind.environment import NetworkEnvironment, utilization_bin
from meshmind.topology import NetworkTopology
from meshmind.traffic import Flow, TrafficGenerator


def test_reset_is_reproducible(grid_env: NetworkEnvironment) -> None:
    first_obs = grid_env.reset(seed=7)
    first_flows = list(grid_env.flows)
    grid_env.step(grid_env.get_valid_actions(first_obs)[0])
    second_obs = grid_env.reset(seed=7)
    assert second_obs == first_obs
    assert grid_env.flows == first_flows
    assert all(u == 0.0 for u in grid_env.topology.utilizations())


def test_observation_structure(grid_env: NetworkEnvironment) -> None:
    state = grid_env.reset(seed=1)
    assert isinstance(state, tuple) and len(state) == 3
    current, destination, bin_ = state
    flow = grid_env.flows[0]
    assert (current, destination) == (flow.source, flow.destination)
    assert bin_ in (0, 1, 2)
    assert all(isinstance(x, int) for x in state)


@pytest.mark.parametrize(
    ("util", "expected"), [(0.0, 0), (0.49, 0), (0.5, 1), (0.84, 1), (0.85, 2), (1.5, 2)]
)
def test_utilization_bins(util: float, expected: int) -> None:
    assert utilization_bin(util) == expected


def test_utilization_bin_reflects_outgoing_load(line_env: NetworkEnvironment) -> None:
    line_env.reset(flows=[Flow(1, 3, 10.0)])
    line_env.topology.set_load(1, 0, 90.0)
    line_env.topology.set_load(1, 2, 90.0)
    assert line_env.get_observation()[2] == 2


def test_valid_actions_are_outgoing_neighbors(line_env: NetworkEnvironment) -> None:
    state = line_env.reset(flows=[Flow(0, 2, 10.0)])
    assert line_env.get_valid_actions(state) == [1, 4]


def test_invalid_action_is_penalised_and_terminates(line_env: NetworkEnvironment) -> None:
    line_env.reset(flows=[Flow(0, 2, 10.0), Flow(1, 3, 10.0)])
    state, reward, done, info = line_env.step(2)
    assert reward == -100.0
    assert done
    result = info["flow_result"]
    assert not result.success
    assert result.failure_reason == "invalid_action"
    assert result.delivered_demand == 0.0
    assert all(u == 0.0 for u in line_env.topology.utilizations())
    assert state[0] == 0
    assert line_env.get_observation()[:2] == (1, 3)


def test_visited_nodes_are_masked(line_env: NetworkEnvironment) -> None:
    line_env.reset(flows=[Flow(1, 3, 10.0)])
    state, *_ = line_env.step(2)
    assert line_env.get_valid_actions(state) == [3]


def test_revisiting_a_node_terminates_as_loop(line_env: NetworkEnvironment) -> None:
    line_env.reset(flows=[Flow(1, 3, 10.0)])
    line_env.step(2)
    _, reward, done, info = line_env.step(1)
    assert done
    assert info["flow_result"].failure_reason == "loop"
    assert reward == pytest.approx(-0.1 * 1.0 - 100.0)
    assert info["episode_done"]


def test_entering_a_dead_end_terminates_as_loop() -> None:
    # 0 -- 1 -- 2, plus leaf 3 hanging off 1
    topo = NetworkTopology([(0, 1, 100.0, 1.0), (1, 2, 100.0, 1.0), (1, 3, 100.0, 1.0)])
    env = NetworkEnvironment(topo, TrafficGenerator(topo.nodes, "low", 0), 1)
    env.reset(flows=[Flow(0, 2, 5.0)])
    env.step(1)
    _, _, done, info = env.step(3)
    assert done
    assert info["flow_result"].failure_reason == "loop"


def test_max_steps_caps_flow_length(line_topology: NetworkTopology) -> None:
    env = NetworkEnvironment(
        line_topology,
        TrafficGenerator(line_topology.nodes, "low", 0),
        1,
        config=EnvironmentConfig(max_steps=2),
    )
    env.reset(flows=[Flow(0, 3, 5.0)])
    _, _, done, _ = env.step(1)
    assert not done
    _, reward, done, info = env.step(2)
    assert done
    assert info["flow_result"].failure_reason == "max_steps"
    assert info["flow_result"].hops == 2
    assert reward == pytest.approx(-0.1 * 1.0 - 100.0)


def test_successful_delivery_and_latency(line_env: NetworkEnvironment) -> None:
    line_env.reset(flows=[Flow(0, 2, 10.0)])
    _, r1, done1, _ = line_env.step(1)
    _, r2, done2, info = line_env.step(2)
    assert not done1 and done2
    result = info["flow_result"]
    assert result.success
    assert result.path == (0, 1, 2)
    assert result.latency_ms == pytest.approx(2.0)
    assert result.delivered_demand == pytest.approx(10.0)
    assert r1 == pytest.approx(-0.1)
    assert r2 == pytest.approx(-0.1 + 10.0)


def test_edge_load_accounting_and_decay(line_env: NetworkEnvironment) -> None:
    line_env.reset(flows=[Flow(0, 2, 30.0), Flow(3, 4, 10.0)])
    line_env.step(1)
    assert line_env.topology.edge_attributes(0, 1)["load"] == pytest.approx(30.0)
    line_env.step(2)
    decay = line_env.config.load_decay
    assert line_env.topology.edge_attributes(0, 1)["load"] == pytest.approx(30.0 * decay)
    assert line_env.topology.edge_attributes(1, 2)["load"] == pytest.approx(30.0 * decay)
    assert line_env.topology.edge_attributes(1, 0)["load"] == 0.0


def test_overloaded_link_drops_demand(line_topology: NetworkTopology) -> None:
    env = NetworkEnvironment(line_topology, TrafficGenerator(line_topology.nodes, "low", 0), 1)
    env.reset(flows=[Flow(0, 1, 200.0)])
    _, reward, done, info = env.step(1)
    assert done
    assert info["flow_result"].delivered_demand == pytest.approx(100.0)
    hop_cost = line_topology.edge_cost(0, 1)
    assert reward == pytest.approx(-0.1 * hop_cost - 50.0 * 0.5 + 10.0)


def test_episode_runs_all_flows_then_stops(grid_env: NetworkEnvironment) -> None:
    state = grid_env.reset(seed=3)
    finished = 0
    while not grid_env.episode_done:
        state, _, done, _ = grid_env.step(grid_env.get_valid_actions(state)[0])
        if done:
            finished += 1
            state = grid_env.get_observation()
    assert finished == grid_env.flows_per_episode
    with pytest.raises(RuntimeError):
        grid_env.step(0)


def test_reset_rejects_bad_flows(line_env: NetworkEnvironment) -> None:
    with pytest.raises(ValueError):
        line_env.reset(flows=[])
    with pytest.raises(ValueError):
        line_env.reset(flows=[Flow(0, 0, 1.0)])
    with pytest.raises(ValueError):
        line_env.reset(flows=[Flow(0, 99, 1.0)])
