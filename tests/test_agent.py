from __future__ import annotations

from pathlib import Path

import pytest

from meshmind.agent import QLearningAgent
from meshmind.config import AgentConfig

S = (0, 3, 1)
S_NEXT = (1, 3, 0)


def make_agent(**overrides: float) -> QLearningAgent:
    params = {
        "alpha": 0.5,
        "gamma": 0.9,
        "epsilon_start": 1.0,
        "epsilon_end": 0.1,
        "epsilon_decay": 0.5,
    }
    params.update(overrides)
    return QLearningAgent(AgentConfig(**params), seed=0)


def test_unseen_pairs_default_to_zero() -> None:
    assert make_agent().get_q(S, 1) == 0.0


def test_exact_bellman_update() -> None:
    agent = make_agent()
    agent.q_table[(S, 1)] = 2.0
    agent.q_table[(S_NEXT, 2)] = 4.0
    agent.q_table[(S_NEXT, 3)] = -1.0
    td = agent.update(S, 1, reward=-1.0, next_state=S_NEXT, next_valid_actions=[2, 3], done=False)
    # target = -1 + 0.9 * 4 = 2.6 ; td = 0.6 ; Q = 2 + 0.5 * 0.6 = 2.3
    assert td == pytest.approx(0.6)
    assert agent.get_q(S, 1) == pytest.approx(2.3)


def test_terminal_transition_does_not_bootstrap() -> None:
    agent = make_agent()
    agent.q_table[(S, 1)] = 1.0
    agent.q_table[(S_NEXT, 2)] = 100.0
    agent.update(S, 1, reward=10.0, next_state=S_NEXT, next_valid_actions=[2], done=True)
    assert agent.get_q(S, 1) == pytest.approx(1.0 + 0.5 * (10.0 - 1.0))


def test_max_q_uses_only_valid_actions() -> None:
    agent = make_agent()
    agent.q_table[(S_NEXT, 2)] = -3.0
    agent.q_table[(S_NEXT, 9)] = 50.0
    assert agent.max_q(S_NEXT, [2]) == -3.0
    assert agent.max_q(S_NEXT, []) == 0.0
    agent.update(S, 1, reward=0.0, next_state=S_NEXT, next_valid_actions=[2], done=False)
    assert agent.get_q(S, 1) == pytest.approx(0.5 * 0.9 * -3.0)


def test_greedy_action_and_tie_breaking() -> None:
    agent = make_agent()
    assert agent.greedy_action(S, [4, 2, 7]) == 2
    agent.q_table[(S, 7)] = 1.0
    assert agent.greedy_action(S, [4, 2, 7]) == 7


def test_epsilon_decay_is_multiplicative_with_floor() -> None:
    agent = make_agent()
    assert agent.decay_epsilon() == pytest.approx(0.5)
    assert agent.decay_epsilon() == pytest.approx(0.25)
    assert agent.decay_epsilon() == pytest.approx(0.125)
    assert agent.decay_epsilon() == pytest.approx(0.1)
    assert agent.decay_epsilon() == pytest.approx(0.1)


def test_exploration_only_returns_valid_actions() -> None:
    agent = make_agent()
    choices = {agent.select_action(S, [3, 5]) for _ in range(200)}
    assert choices == {3, 5}


def test_eval_mode_is_greedy_and_read_only() -> None:
    agent = make_agent()
    agent.q_table[(S, 5)] = 1.0
    agent.set_eval_mode(True)
    assert agent.effective_epsilon == 0.0
    assert all(agent.select_action(S, [3, 5]) == 5 for _ in range(100))
    with pytest.raises(RuntimeError):
        agent.update(S, 3, 1.0, S_NEXT, [1], False)
    assert agent.epsilon == 1.0


def test_select_action_requires_actions() -> None:
    with pytest.raises(ValueError):
        make_agent().select_action(S, [])


def test_save_and_load_round_trip(tmp_path: Path) -> None:
    agent = make_agent()
    agent.q_table[(S, 1)] = -2.5
    agent.q_table[(S_NEXT, 3)] = 7.0
    agent.decay_epsilon()
    path = tmp_path / "q.json"
    agent.save(path)
    loaded = QLearningAgent.load(path)
    assert loaded.q_table == agent.q_table
    assert loaded.epsilon == agent.epsilon
    assert loaded.config == agent.config


@pytest.mark.parametrize(
    "overrides",
    [
        {"alpha": 0.0},
        {"gamma": 1.5},
        {"epsilon_end": 0.9, "epsilon_start": 0.5},
        {"epsilon_decay": 0.0},
    ],
)
def test_invalid_hyperparameters(overrides: dict) -> None:
    with pytest.raises(ValueError):
        make_agent(**overrides)
