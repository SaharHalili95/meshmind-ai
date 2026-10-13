from __future__ import annotations

import itertools

import numpy as np
import pytest

from meshmind.agent import QLearningAgent
from meshmind.config import AgentConfig
from meshmind.environment import NetworkEnvironment
from meshmind.training import train_agent

EPISODES = 400


@pytest.fixture(scope="module")
def trained() -> tuple[QLearningAgent, list[dict[str, float]]]:
    from meshmind.topology import NetworkTopology
    from meshmind.traffic import TrafficGenerator

    topology = NetworkTopology.from_name("small_grid")
    env = NetworkEnvironment(topology, TrafficGenerator(topology.nodes, "high", 0), 10)
    agent = QLearningAgent(AgentConfig(epsilon_decay=0.99), seed=1)
    history = train_agent(env, agent, EPISODES, base_seed=1)
    return agent, history


def test_respects_episode_limit(trained: tuple) -> None:
    _, history = trained
    assert len(history) == EPISODES
    assert [row["episode"] for row in history] == list(range(EPISODES))


def test_history_rows_are_structured(trained: tuple) -> None:
    _, history = trained
    expected = {
        "episode",
        "total_reward",
        "mean_abs_td_error",
        "epsilon",
        "steps",
        "pdr",
        "mean_latency_ms",
        "routing_failures",
        "q_table_size",
    }
    assert all(set(row) == expected for row in history)
    assert all(np.isfinite(list(row.values())).all() for row in history)


def test_reward_increases(trained: tuple) -> None:
    _, history = trained
    rewards = [row["total_reward"] for row in history]
    window = EPISODES // 10
    assert np.mean(rewards[-window:]) > np.mean(rewards[:window])


def test_td_error_loss_decreases(trained: tuple) -> None:
    _, history = trained
    losses = [row["mean_abs_td_error"] for row in history]
    window = EPISODES // 10
    assert np.mean(losses[-window:]) < np.mean(losses[:window])


def test_routing_failures_drop(trained: tuple) -> None:
    _, history = trained
    window = EPISODES // 10
    early = np.mean([row["routing_failures"] for row in history[:window]])
    late = np.mean([row["routing_failures"] for row in history[-window:]])
    assert late < early


def test_epsilon_decays_monotonically(trained: tuple) -> None:
    agent, history = trained
    eps = [row["epsilon"] for row in history]
    assert eps[0] == 1.0
    assert all(b <= a for a, b in itertools.pairwise(eps))
    assert agent.epsilon == pytest.approx(max(0.05, 0.99**EPISODES))


def test_q_table_is_populated(trained: tuple) -> None:
    agent, _ = trained
    assert len(agent.q_table) > 50


def test_training_is_deterministic(grid_env: NetworkEnvironment) -> None:
    a = train_agent(grid_env, QLearningAgent(seed=3), 20, base_seed=9)
    b = train_agent(grid_env, QLearningAgent(seed=3), 20, base_seed=9)
    assert a == b


def test_invalid_episode_count(grid_env: NetworkEnvironment) -> None:
    with pytest.raises(ValueError):
        train_agent(grid_env, QLearningAgent(), 0)
