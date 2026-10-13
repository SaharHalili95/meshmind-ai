# Experiment Methodology

## Research question

Can a tabular Q-learning agent that only sees *local* congestion (a 3-level utilization bin
at the current router) match or beat routing policies that need global, real-time link
state, while delivering more traffic than static shortest-path routing?

## Setup (defaults in `configs/default.yaml`)

| Parameter | Value |
|---|---|
| Topology | Abilene (12 PoPs, 15 bidirectional links, 30 directed edges) |
| Traffic profile | `high`: demand ~ U(60, 120) Mb/s, uniform random src != dst |
| Flows per episode | 25, routed sequentially; load decay 0.85 between flows |
| Hop cap | 20 |
| Training | 3,000 episodes (75,000 flows) per seed |
| Evaluation | 100 held-out episodes (2,500 flows) per seed and policy |
| Seeds | 42, 100, 2026 |
| Agent | alpha = 0.1, gamma = 0.95, epsilon 1.0 -> 0.05, decay 0.998/episode |

## Multi-seed protocol

For each seed $s \in \{42, 100, 2026\}$, independently:

1. Build a fresh topology (all loads zero), traffic generator and environment.
2. Create a fresh `QLearningAgent(seed=s)`. Its exploration RNG is seeded by $s$.
3. **Train** for 3,000 episodes. Episode $i$ uses traffic seed $s + i$.
4. **Evaluate** the frozen greedy agent on 100 episodes with traffic seeds
   $s + 10^6 + j$, $j = 0..99$.
5. Evaluate `ShortestPathBaseline`, `CongestionAwareBaseline` and
   `RandomRoutingBaseline(seed=s)` on **the same 100 held-out episodes**.

The seed controls every source of randomness: traffic, exploration, and random routing.
Re-running the pipeline reproduces `per_seed_results.csv` bit for bit. The test suite
checks this property for both training and evaluation.

## Train/evaluation split

* **Disjoint scenarios:** training seeds are $[s, s + 3000)$ and evaluation seeds
  are $[s + 10^6, s + 10^6 + 100)$. These ranges never overlap for any seed in the study
  (`test_eval_scenarios_are_held_out`), so the agent is never scored on a traffic matrix it
  trained on.
* **Frozen policy:** `evaluate_agent` turns on `eval_mode`, which forces $\epsilon = 0$
  and makes `QLearningAgent.update` raise `RuntimeError`. A test deep-copies the Q-table
  before evaluation and asserts it is unchanged afterwards.
* **Paired comparison:** all four policies are scored on identical flow sequences, so
  differences between them come from routing decisions, not from luckier traffic.

## Metrics and aggregation

Per `(seed, policy)` one `MetricsTracker` collects all 2,500 evaluated flows and reports:

* **PDR / PLR**: demand-weighted delivery and loss ratios
* **Mean latency (ms)**: over delivered flows, including congestion penalties
* **Mean throughput**: delivered Mb/s per offered flow
* **Average link utilization**: mean over all 30 edges, sampled at the end of every flow
* **Routing failures**: flows ending in an invalid action, a loop/dead end, or the hop cap

Across seeds, `aggregate_metrics` reports the **mean and sample standard deviation**
(`ddof=1`). With only $n = 3$ seeds the std is a rough dispersion indicator, not a
confidence interval. The paired per-seed rows in `per_seed_results.csv` are the more
informative comparison.

## Results (3 seeds, mean ± std)

| Policy | PDR | PLR | Latency (ms) | Throughput | Link util | Failures |
|---|---|---|---|---|---|---|
| **Q-learning** | **0.607 ± 0.008** | **0.393 ± 0.008** | 79.50 ± 0.27 | **54.53 ± 0.53** | 0.382 ± 0.002 | 0 |
| Shortest path | 0.592 ± 0.007 | 0.408 ± 0.007 | **78.30 ± 0.71** | 53.16 ± 0.45 | 0.381 ± 0.001 | 0 |
| Congestion-aware | 0.607 ± 0.009 | 0.394 ± 0.009 | 80.62 ± 1.43 | 54.49 ± 0.54 | 0.417 ± 0.001 | 0 |
| Random | 0.212 ± 0.004 | 0.788 ± 0.004 | 182.67 ± 2.99 | 19.09 ± 0.40 | 0.662 ± 0.004 | 1019 ± 33 |

Paired by seed (`per_seed_results.csv`):

* Q-learning beats shortest path on PDR on **all 3 seeds** (+1.57, +1.58, +1.42 points).
  The gap is about 2x the cross-seed std, and the paired gaps are very consistent.
* Q-learning is level with the congestion-aware baseline on PDR (+0.02, +0.06, +0.07
  points). It uses **2.5 vs 2.7 mean hops** and **8.5% less network-wide utilization**
  (0.382 vs 0.417), and has lower latency on every seed. The congestion-aware baseline
  reaches the same delivery by taking longer detours, which use more capacity.
* Q-learning pays about 1.2 ms (1.5%) of latency compared with shortest path in exchange
  for its higher delivery ratio.
* Random routing is a sanity floor. Even with loop masking, about 41% of its flows end in a
  dead end.

### Honest scope

* Under `moderate` and `dynamic` load (single-seed probes during development), all three
  non-random policies are within about 1-2 PDR points of each other. Little congestion
  means little room to improve. The learned policy's value shows up under load.
* The congestion-aware baseline here is strong: it recomputes Dijkstra with live global
  link state at **every hop**. Q-learning matching it from a 3-bin local signal is the
  interesting result. Beating it by a wide margin was never expected.
* These results are from a flow-level simulator, not packet-level emulation. See the
  interview guide for the limits.

## Reproducing

```bash
make install
make experiments          # ~20 s on a laptop: trains, evaluates, writes results/ and figures
make test                 # 116 tests
```

You can override any parameter by copying `configs/default.yaml` and passing
`--config path/to/your.yaml` to `python -m meshmind.cli experiments`.
