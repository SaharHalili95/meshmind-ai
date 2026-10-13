"""Policy evaluation on held-out traffic scenarios. Never mutates a learning agent."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Protocol

from meshmind.agent import QLearningAgent
from meshmind.environment import NetworkEnvironment, State
from meshmind.metrics import MetricsTracker

ActionFn = Callable[[NetworkEnvironment, State, Sequence[int]], int]

EVAL_SEED_OFFSET = 1_000_000
"""Evaluation scenarios use seeds disjoint from the training range."""


class RoutingPolicy(Protocol):
    name: str

    def reset(self, seed: int | None = None) -> None: ...

    def select_action(
        self, env: NetworkEnvironment, state: State, valid_actions: Sequence[int]
    ) -> int: ...


def eval_seeds(base_seed: int, episodes: int) -> list[int]:
    return [base_seed + EVAL_SEED_OFFSET + i for i in range(episodes)]


def run_policy(
    env: NetworkEnvironment, action_fn: ActionFn, seeds: Sequence[int]
) -> MetricsTracker:
    """Roll out ``action_fn`` over one episode per seed and collect flow metrics."""
    tracker = MetricsTracker()
    for seed in seeds:
        state = env.reset(seed=seed)
        while not env.episode_done:
            valid = env.get_valid_actions(state)
            action = action_fn(env, state, valid)
            state, _, done, info = env.step(action)
            if done:
                tracker.record_flow(info["flow_result"])
                tracker.record_utilization(info["avg_utilization"])
                state = env.get_observation()
    return tracker


def evaluate_policy(
    env: NetworkEnvironment, policy: RoutingPolicy, episodes: int, base_seed: int
) -> dict[str, float]:
    policy.reset(base_seed)
    tracker = run_policy(env, policy.select_action, eval_seeds(base_seed, episodes))
    return tracker.summary()


def evaluate_agent(
    env: NetworkEnvironment, agent: QLearningAgent, episodes: int, base_seed: int
) -> dict[str, float]:
    """Greedy evaluation (epsilon = 0). The agent's Q-table is read-only here."""
    previous_mode = agent.eval_mode
    agent.set_eval_mode(True)
    try:

        def act(_: NetworkEnvironment, state: State, valid: Sequence[int]) -> int:
            return agent.greedy_action(state, valid)

        tracker = run_policy(env, act, eval_seeds(base_seed, episodes))
    finally:
        agent.set_eval_mode(previous_mode)
    return tracker.summary()
