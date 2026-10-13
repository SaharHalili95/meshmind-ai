"""Tabular Q-learning agent implemented from first principles."""

from __future__ import annotations

import json
from collections.abc import Hashable, Sequence
from pathlib import Path

import numpy as np

from meshmind.config import AgentConfig


class QLearningAgent:
    """Off-policy TD(0) control with epsilon-greedy exploration.

    The Q-table is a plain ``dict`` keyed by ``(state, action)``; unseen pairs
    read as 0.0. Since per-hop rewards are negative, a zero initialisation is
    optimistic and pushes the agent to try untested next hops.
    """

    name = "q_learning"

    def __init__(self, config: AgentConfig | None = None, seed: int = 0) -> None:
        self.config = config or AgentConfig()
        self.alpha = self.config.alpha
        self.gamma = self.config.gamma
        self.epsilon = self.config.epsilon_start
        self.epsilon_end = self.config.epsilon_end
        self.epsilon_decay = self.config.epsilon_decay
        self.rng = np.random.default_rng(seed)
        self.q_table: dict[tuple[Hashable, int], float] = {}
        self.eval_mode = False

    def set_eval_mode(self, enabled: bool) -> None:
        self.eval_mode = enabled

    @property
    def effective_epsilon(self) -> float:
        return 0.0 if self.eval_mode else self.epsilon

    def get_q(self, state: Hashable, action: int) -> float:
        return self.q_table.get((state, action), 0.0)

    def max_q(self, state: Hashable, valid_actions: Sequence[int]) -> float:
        if not valid_actions:
            return 0.0
        return max(self.get_q(state, a) for a in valid_actions)

    def greedy_action(self, state: Hashable, valid_actions: Sequence[int]) -> int:
        """Highest-Q valid action; ties break toward the lowest node id for determinism."""
        if not valid_actions:
            raise ValueError("no valid actions available")
        return max(sorted(valid_actions), key=lambda a: self.get_q(state, a))

    def select_action(self, state: Hashable, valid_actions: Sequence[int]) -> int:
        if not valid_actions:
            raise ValueError("no valid actions available")
        if self.rng.random() < self.effective_epsilon:
            return int(self.rng.choice(list(valid_actions)))
        return self.greedy_action(state, valid_actions)

    def update(
        self,
        state: Hashable,
        action: int,
        reward: float,
        next_state: Hashable,
        next_valid_actions: Sequence[int],
        done: bool,
    ) -> float:
        """Apply Q(s,a) <- Q(s,a) + alpha * [r + gamma * max_a' Q(s',a') - Q(s,a)].

        Terminal transitions do not bootstrap. Returns the TD error.
        """
        if self.eval_mode:
            raise RuntimeError("Q-table updates are forbidden in evaluation mode")
        future = 0.0 if done else self.max_q(next_state, next_valid_actions)
        current = self.get_q(state, action)
        td_error = reward + self.gamma * future - current
        self.q_table[(state, action)] = current + self.alpha * td_error
        return td_error

    def decay_epsilon(self) -> float:
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)
        return self.epsilon

    def save(self, path: str | Path) -> None:
        entries = [
            {"state": list(state), "action": action, "q": value}
            for (state, action), value in sorted(self.q_table.items())
        ]
        payload = {"epsilon": self.epsilon, "config": vars(self.config), "q_table": entries}
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path, seed: int = 0) -> QLearningAgent:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        agent = cls(AgentConfig(**payload["config"]), seed=seed)
        agent.epsilon = float(payload["epsilon"])
        agent.q_table = {
            (tuple(entry["state"]), int(entry["action"])): float(entry["q"])
            for entry in payload["q_table"]
        }
        return agent
