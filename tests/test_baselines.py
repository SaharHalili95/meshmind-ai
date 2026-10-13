from __future__ import annotations

from meshmind.baselines import (
    CongestionAwareBaseline,
    RandomRoutingBaseline,
    ShortestPathBaseline,
    shortest_path,
)
from meshmind.environment import NetworkEnvironment
from meshmind.evaluation import evaluate_policy
from meshmind.topology import NetworkTopology
from meshmind.traffic import Flow, TrafficGenerator

# Triangle: direct 0->2 costs 5ms, detour 0->1->2 costs 2ms.
TRIANGLE = [(0, 1, 100.0, 1.0), (1, 2, 100.0, 1.0), (0, 2, 100.0, 5.0)]


def make_env(links: list) -> NetworkEnvironment:
    topo = NetworkTopology(links)
    return NetworkEnvironment(topo, TrafficGenerator(topo.nodes, "low", 0), 5)


def test_shortest_path_on_known_weights() -> None:
    topo = NetworkTopology(TRIANGLE)
    assert shortest_path(topo, 0, 2) == [0, 1, 2]
    assert topo.path_latency([0, 1, 2]) == 2.0


def test_shortest_path_baseline_follows_min_latency_route() -> None:
    env = make_env(TRIANGLE)
    state = env.reset(flows=[Flow(0, 2, 5.0)])
    policy = ShortestPathBaseline()
    action = policy.select_action(env, state, env.get_valid_actions(state))
    assert action == 1


def test_congestion_aware_avoids_hot_link() -> None:
    env = make_env(TRIANGLE)
    state = env.reset(flows=[Flow(0, 2, 5.0)])
    env.topology.set_load(0, 1, 150.0)  # utilization 1.5 -> penalty 12.25ms
    valid = env.get_valid_actions(state)
    assert CongestionAwareBaseline().select_action(env, state, valid) == 2
    assert ShortestPathBaseline().select_action(env, state, valid) == 1


def test_congestion_aware_matches_shortest_path_when_idle() -> None:
    env = make_env(TRIANGLE)
    state = env.reset(flows=[Flow(0, 2, 5.0)])
    valid = env.get_valid_actions(state)
    assert CongestionAwareBaseline().select_action(env, state, valid) == 1


def test_baselines_deliver_every_flow_on_grid(grid_env: NetworkEnvironment) -> None:
    for policy in (ShortestPathBaseline(), CongestionAwareBaseline()):
        metrics = evaluate_policy(grid_env, policy, episodes=5, base_seed=0)
        assert metrics["routing_failures"] == 0.0


def test_random_routing_is_seed_reproducible(grid_env: NetworkEnvironment) -> None:
    def rollout(seed: int) -> list[int]:
        policy = RandomRoutingBaseline(seed)
        state = grid_env.reset(seed=0)
        actions = []
        for _ in range(30):
            if grid_env.episode_done:
                break
            valid = grid_env.get_valid_actions(state)
            action = policy.select_action(grid_env, state, valid)
            assert action in valid
            actions.append(action)
            state, _, done, _ = grid_env.step(action)
            if done:
                state = grid_env.get_observation()
        return actions

    assert rollout(5) == rollout(5)
    assert rollout(5) != rollout(6)


def test_random_reset_restores_sequence() -> None:
    policy = RandomRoutingBaseline(3)
    env = make_env(TRIANGLE)
    state = env.reset(flows=[Flow(0, 2, 5.0)])
    valid = env.get_valid_actions(state)
    first = [policy.select_action(env, state, valid) for _ in range(20)]
    policy.reset()
    assert [policy.select_action(env, state, valid) for _ in range(20)] == first
