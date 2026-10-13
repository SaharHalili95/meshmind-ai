"""Episode-based Q-learning training loop."""

from __future__ import annotations

from meshmind.agent import QLearningAgent
from meshmind.environment import NetworkEnvironment
from meshmind.metrics import MetricsTracker

TRAIN_SEED_STRIDE = 1


def train_seeds(base_seed: int, episodes: int) -> list[int]:
    return [base_seed + i * TRAIN_SEED_STRIDE for i in range(episodes)]


def train_agent(
    env: NetworkEnvironment,
    agent: QLearningAgent,
    episodes: int,
    base_seed: int = 0,
) -> list[dict[str, float]]:
    """Train ``agent`` for exactly ``episodes`` episodes and return per-episode history.

    Each history row holds the episode's total reward, mean absolute TD error
    (the "loss"), epsilon used, and delivery/latency statistics.
    """
    if episodes < 1:
        raise ValueError("episodes must be >= 1")
    agent.set_eval_mode(False)
    history: list[dict[str, float]] = []

    for episode, seed in enumerate(train_seeds(base_seed, episodes)):
        tracker = MetricsTracker()
        state = env.reset(seed=seed)
        total_reward = 0.0
        abs_td_sum = 0.0
        steps = 0
        epsilon_used = agent.epsilon

        while not env.episode_done:
            valid = env.get_valid_actions(state)
            action = agent.select_action(state, valid)
            next_state, reward, done, info = env.step(action)
            next_valid = [] if done else env.get_valid_actions(next_state)
            td_error = agent.update(state, action, reward, next_state, next_valid, done)
            total_reward += reward
            abs_td_sum += abs(td_error)
            steps += 1
            if done:
                tracker.record_flow(info["flow_result"])
                tracker.record_utilization(info["avg_utilization"])
                state = env.get_observation()
            else:
                state = next_state

        agent.decay_epsilon()
        history.append(
            {
                "episode": float(episode),
                "total_reward": total_reward,
                "mean_abs_td_error": abs_td_sum / steps,
                "epsilon": epsilon_used,
                "steps": float(steps),
                "pdr": tracker.pdr,
                "mean_latency_ms": tracker.mean_latency_ms,
                "routing_failures": float(tracker.routing_failures),
                "q_table_size": float(len(agent.q_table)),
            }
        )
    return history
