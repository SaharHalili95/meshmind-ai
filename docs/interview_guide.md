# Interview Guide

Questions a reviewer or interviewer is likely to ask about MeshMind AI, with the answers
the design supports.

---

## 1. Why tabular Q-learning and not DQN / PPO / GNNs?

**Short answer:** the state space is small enough to enumerate. A table gives exact,
inspectable values and convergence guarantees, and it removes a whole class of
deep-RL failure modes. That makes it the right tool to *establish* whether learning
helps at all.

* Abilene has $12 \times 12 \times 3 = 432$ states and at most 4 actions each. Training
  visits only about 900 $(s,a)$ pairs. A neural network would add function-approximation
  error, replay buffers, target networks and hyperparameter sensitivity, and gain nothing
  at this scale.
* Tabular Q-learning converges to $Q^*$ under the usual Robbins-Monro conditions (every
  pair visited infinitely often, decaying step size) in a stationary MDP. Our constant
  $\alpha$ and non-stationary loads break those assumptions a little, and that is a good
  thing to say out loud.
* Every learned decision can be audited: `q_table_seed42.json` lists the value of each next
  hop (e.g. Kansas City -> Indianapolis vs. Kansas City -> Houston) for every
  destination and congestion bin.

**When to switch:** once the state includes per-link utilizations, demand size or queue
lengths, the table blows up ($3^{30}$ states for per-edge bins on Abilene). At that point
you need function approximation. GNN-based policies are the natural fit because they are
invariant to topology size and node ordering.

## 2. Q-learning trade-offs

| Property | Implication here |
|---|---|
| Off-policy | Learns the greedy policy while exploring with epsilon-greedy; evaluation uses pure greedy |
| TD(0) bootstrapping | Fast credit assignment along 2-5 hop paths, but biased early while Q is wrong |
| Max operator | Overestimation bias. Small here (few actions, near-deterministic rewards); Double Q-learning is the standard fix |
| Constant alpha | Tracks non-stationary congestion instead of freezing; never fully converges |
| Optimistic zero init | All rewards are negative, so untried actions look attractive and exploration happens for free |

## 3. State discretization choices

The state is `(current, destination, bin)`, where `bin` is the mean outgoing utilization of
the current router, split at 0.5 and 0.85.

* **Why local, not global?** A router realistically knows its own interface counters. Global
  link state needs a control-plane protocol with propagation delay. Local-only state is
  also why matching the global congestion-aware baseline is a meaningful result.
* **Why 0.85 as the upper edge?** The congestion penalty starts at 0.8, so bin 2 roughly
  means "my links are already being penalised". The 0.5 edge separates idle from busy.
* **Why only 3 bins?** Each extra bin multiplies the table size, and every state needs
  enough visits for its Q-values to settle. Three bins keep the Abilene table at 432 states,
  which 75k training flows per seed cover densely.
* **Known weakness: aggregation.** A *mean* over outgoing links hides *which* link is hot.
  A node with one saturated link and one idle link looks like "medium". A per-action
  feature (the utilization of the candidate link) would fix this at the cost of a larger
  table.
* **Missing: demand size.** The agent can't tell a 60 Mb/s flow from a 120 Mb/s one, yet the
  big one is the one that tips a link into loss.

## 4. Action space constraints

* Actions are next hops (outgoing neighbours), so a degree-4 router has at most 4 actions.
  Physically impossible moves are never offered. If a policy still emits one, the
  environment returns -100 and ends the flow without touching link state.
* **Loop masking.** Neighbours already on the flow's path are removed from the valid set.
  Without this, a Markov state that doesn't remember the path gets *aliased*: "from node B
  go to A" is good when the flow started at B and terrible when it just came from A.
* **Dead-end termination.** Entering a node whose every neighbour is already visited
  (e.g. the leaf Atlanta-M5 on a transit path) ends the flow immediately, so the penalty
  lands on the *decision that caused it*. In an earlier version the penalty came one step
  later, on the aliased leaf state. The agent then learned the detour was fine and
  failed about 6% of evaluation flows. Moving the termination one step earlier brought
  failures to zero.

## 5. Failure cases worth discussing

1. **Reward hacking.** With a loop penalty of -50, the agent under `high` load learned to
   loop flows on purpose, because dropping a flow was cheaper than delivering it through
   saturated links (drop penalty + congestion latency > 50). The fix was to make every
   failure strictly worse than the worst feasible delivery
   (see `docs/mathematical_model.md`). Lesson: the reward has to encode the operator's
   *ordering* of outcomes, not just their rough direction.
2. **Unseen states at evaluation.** A greedy agent in a never-visited state falls back to a
   tie-break (lowest node id), which is arbitrary. Loop masking keeps that from becoming a
   failure, but a production system would fall back to shortest path instead.
3. **Non-stationarity.** The traffic the agent routes changes the loads it observes.
   Different agents sharing links (multi-agent) would make this much worse.
4. **Leaf bottlenecks.** Traffic to or from a single-homed node has exactly one route. No
   routing policy can avoid its loss, which caps the achievable PDR.
5. **Distribution shift.** An agent trained on `high` will route sub-optimally under a
   different traffic matrix (e.g. a hotspot) because its Q-values encode where
   congestion *usually* is.

## 6. Scaling limits to real systems

| Concern | This project | Real network |
|---|---|---|
| Granularity | flow-level, one decision per hop per flow | per-packet forwarding at line rate (ns budget) |
| State size | 432 states | thousands of routers, per-prefix destinations |
| Control loop | instant, global clock | telemetry is delayed, sampled, lossy |
| Safety | failures cost reward | failures cost SLAs; you need guardrails and fallback to IGP routes |
| Training | simulator, millions of mistakes are free | online exploration on live traffic is unacceptable |

Realistic deployment paths:

* **Offline RL / policy distillation:** learn in a simulator calibrated on real telemetry,
  then compile the policy into weights for WCMP/ECMP or SR-TE segment lists. Don't make
  per-packet decisions with RL.
* **Hierarchical control:** RL at the traffic-engineering layer (minutes) chooses
  link weights or tunnel splits. The data plane keeps deterministic forwarding.
* **Function approximation over topology:** GNN policies that generalise across
  topologies and survive link failures without retraining.
* **Guardrails:** always keep a shortest-path fallback, rate-limit policy changes, and
  verify loop-freedom before installing routes.

## 7. "How do you know the improvement is real?"

* The comparison is paired: all policies are evaluated on identical held-out flow sequences,
  so the unit of analysis is the per-seed difference.
* 10 seeds and an **exact sign-flip permutation test**: under H0 each paired difference is
  equally likely to be positive or negative, so the 2¹⁰ = 1,024 sign patterns give the exact
  null distribution. No normality assumption, no SciPy. The PDR gain over shortest path
  (+1.79 pts, 95% bootstrap CI [+1.53, +2.08]) has p = 0.002, the smallest value 10 pairs
  can produce, and is positive on 10/10 seeds.
* **Why 3 seeds were not enough:** with n = 3 the smallest attainable p-value is 2/2³ = 0.25,
  so no 3-seed result can ever be significant, however consistent it looks. Moving to 10
  seeds is what turned "level with congestion-aware" into a significant win
  (+0.32 pts PDR, p = 0.006).
* Not everything is significant, and that is reported too: latency vs shortest path
  (+0.51 ms, p = 0.17) is a tie.
* Evaluation can't leak training data: the scenario seed ranges are disjoint, and the
  Q-table is provably frozen (a test asserts it is unchanged).
* The load sweep repeats everything at five capacity levels. Against shortest path the gain
  is positive at every load; against congestion-aware there is a **crossover near load
  0.9**: below it live global state wins (−0.6 pts), above it the learned policy wins by up
  to +2.5 pts. Reporting where the method loses is as important as where it wins.
  What I would add next: a link-failure scenario and topology generalisation.

## 8. Engineering decisions to highlight

* The agent has **zero knowledge of the environment class**. It works on hashable states
  and integer actions, so it can be reused or replaced.
* All randomness flows from explicit seeds through `np.random.default_rng`. There is no
  global RNG state, so every result in the README regenerates exactly.
* Configuration is typed (frozen dataclasses), validated on construction, and loaded
  strictly: unknown YAML keys raise instead of being silently ignored.
* 130 tests run in about 4 s, including exact Bellman-update arithmetic, zero
  bootstrapping on terminal transitions, and an end-to-end pipeline + plotting test.
