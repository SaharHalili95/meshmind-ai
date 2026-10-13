from __future__ import annotations

import copy

from meshmind.agent import QLearningAgent
from meshmind.baselines import ShortestPathBaseline
from meshmind.environment import NetworkEnvironment
from meshmind.evaluation import EVAL_SEED_OFFSET, eval_seeds, evaluate_agent, evaluate_policy
from meshmind.metrics import METRIC_KEYS
from meshmind.training import train_agent, train_seeds


def trained_agent(env: NetworkEnvironment) -> QLearningAgent:
    agent = QLearningAgent(seed=0)
    train_agent(env, agent, 50, base_seed=0)
    return agent


def test_evaluation_does_not_modify_q_table(grid_env: NetworkEnvironment) -> None:
    agent = trained_agent(grid_env)
    q_before = copy.deepcopy(agent.q_table)
    epsilon_before = agent.epsilon
    evaluate_agent(grid_env, agent, episodes=10, base_seed=0)
    assert agent.q_table == q_before
    assert agent.epsilon == epsilon_before


def test_eval_mode_is_restored(grid_env: NetworkEnvironment) -> None:
    agent = trained_agent(grid_env)
    evaluate_agent(grid_env, agent, episodes=2, base_seed=0)
    assert agent.eval_mode is False


def test_evaluation_returns_structured_metrics(grid_env: NetworkEnvironment) -> None:
    metrics = evaluate_agent(grid_env, trained_agent(grid_env), episodes=5, base_seed=0)
    assert set(METRIC_KEYS) <= set(metrics)
    assert all(isinstance(v, float) for v in metrics.values())
    assert 0.0 <= metrics["pdr"] <= 1.0
    assert metrics["pdr"] + metrics["plr"] == 1.0 or metrics["flows"] == 0
    assert metrics["flows"] == 5 * grid_env.flows_per_episode


def test_evaluation_is_deterministic(grid_env: NetworkEnvironment) -> None:
    agent = trained_agent(grid_env)
    a = evaluate_agent(grid_env, agent, episodes=5, base_seed=3)
    b = evaluate_agent(grid_env, agent, episodes=5, base_seed=3)
    assert a == b


def test_eval_scenarios_are_held_out() -> None:
    train = set(train_seeds(42, 10_000))
    held_out = set(eval_seeds(42, 1_000))
    assert train.isdisjoint(held_out)
    assert min(held_out) == 42 + EVAL_SEED_OFFSET


def test_evaluate_policy_for_baseline(grid_env: NetworkEnvironment) -> None:
    metrics = evaluate_policy(grid_env, ShortestPathBaseline(), episodes=3, base_seed=1)
    assert metrics["routing_failures"] == 0.0
    assert metrics["flows"] == 3 * grid_env.flows_per_episode
