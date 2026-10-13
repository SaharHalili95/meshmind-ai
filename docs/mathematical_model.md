# Mathematical Model

## 1. Network

The network is a directed graph $G = (V, E)$. Each physical link becomes two directed
edges, one per direction. Each edge $e = (u, v)$ carries:

| Symbol | Attribute | Constraint |
|---|---|---|
| $C_e$ | `capacity` | $C_e > 0$ |
| $d_e$ | `base_latency` (ms) | $d_e \ge 0$ |
| $L_e$ | `load` | $L_e \ge 0$ (uncapped) |
| $\rho_e$ | `utilization` | $\rho_e = \min(L_e / C_e,\ \rho_{\max})$, with $\rho_{\max} = 1.5$ |
| $p_e$ | `congestion_penalty` | see below |

### Link utilization and load dynamics

When a flow $f$ with demand $\lambda_f$ traverses edge $e$, the edge's load becomes
$L_e \leftarrow L_e + \lambda_f$. Between consecutive flows every load decays
geometrically, which models earlier traffic finishing:

$$L_e \leftarrow \delta \cdot L_e, \qquad \delta = 0.85 .$$

If a link keeps receiving flows of average size $\bar\lambda$ at rate $q$ (the fraction of
flows that use it), its load settles at $L_e^* = q\bar\lambda / (1 - \delta)$. This is why
a few heavily shared links reach high utilization under the `high` profile while the rest of
the network stays lightly used.

### Congestion penalty and edge cost

$$
p_e =
\begin{cases}
d_e \left(\dfrac{\rho_e - 0.8}{0.2}\right)^2 & \rho_e > 0.8 \\[4pt]
0 & \text{otherwise}
\end{cases}
\qquad\qquad
\text{cost}_e = d_e + p_e .
$$

At $\rho = 0.9$ the penalty is $0.25\,d_e$, at $\rho = 1.0$ it equals $d_e$ (the link costs
twice its propagation delay), and at the cap $\rho = 1.5$ it is $12.25\,d_e$.

### M/M/1 queuing proxy (why a quadratic penalty)

For an M/M/1 queue with arrival rate $\lambda$ and service rate $\mu$, the mean time in the
system is

$$T = \frac{1}{\mu - \lambda} = \frac{1/\mu}{1 - \rho}, \qquad \rho = \lambda / \mu .$$

The queuing delay is close to zero at low load and explodes as $\rho \to 1$, and it is
undefined for $\rho \ge 1$. A simulator needs a cost that

1. is exactly zero in the normal operating region (so it doesn't distort routing on an idle network),
2. grows faster than linearly near saturation, like $1/(1-\rho)$, and
3. stays **finite and bounded** past saturation, where the M/M/1 formula breaks down.

The thresholded quadratic $p_e$ with the cap $\rho_{\max}$ meets all three. It is a
bounded surrogate for the M/M/1 knee, scaled by $d_e$ so that long links pay
proportionally more when congested. The capped value also keeps rewards bounded, which
helps tabular TD learning stay stable.

### Loss model (proportional sharing)

An overloaded link ($L_e > C_e$) cannot carry all of its traffic. MeshMind uses
proportional sharing, so the flow that pushes the link over capacity keeps only

$$\phi_e = \min\!\left(1, \frac{C_e}{L_e}\right)$$

of its demand. Along a path $P = (e_1, \dots, e_k)$ the delivered demand is

$$\lambda_f^{\text{deliv}} = \lambda_f \prod_{i=1}^{k} \phi_{e_i}$$

if the flow reaches its destination, and $0$ if it fails (invalid action, loop, or step
cap).

### End-to-end latency

$$\text{latency}_f = \sum_{e \in P} \left(d_e + p_e\right),$$

where each $p_e$ is evaluated right after the flow's own load is added, so a flow "feels"
the congestion it creates.

## 2. Performance metrics

Over the set of evaluated flows $\mathcal{F}$, with $\mathcal{F}^{+} \subseteq \mathcal{F}$
the successfully delivered ones:

$$
\text{PDR} = \frac{\sum_{f \in \mathcal{F}} \lambda_f^{\text{deliv}}}{\sum_{f \in \mathcal{F}} \lambda_f},
\qquad
\text{PLR} = 1 - \text{PDR}
$$

$$
\overline{\text{latency}} = \frac{1}{|\mathcal{F}^{+}|}\sum_{f \in \mathcal{F}^{+}} \text{latency}_f,
\qquad
\overline{\text{throughput}} = \frac{1}{|\mathcal{F}|}\sum_{f \in \mathcal{F}} \lambda_f^{\text{deliv}}
$$

Average link utilization is $\frac{1}{|E|}\sum_e \rho_e$, sampled at the end of every flow
and averaged. Every ratio returns `0.0` when its denominator is zero (no offered traffic,
no successful flows), so a degenerate run never raises `ZeroDivisionError`.

PDR is **demand-weighted**: losing a 110 Mb/s flow costs more than losing a 65 Mb/s one.
This matches how operators measure loss in bytes, not in flow counts.

## 3. Markov decision process

| Element | Definition |
|---|---|
| State $s$ | $(v, t, b)$: current node, destination, and the utilization bin of $v$'s outgoing links |
| Bin $b$ | $\bar\rho_v = \text{mean}_{(v,w) \in E}\,\rho_{vw}$; $b = 0$ if $\bar\rho_v < 0.5$, $1$ if $0.5 \le \bar\rho_v < 0.85$, $2$ otherwise |
| Actions $\mathcal{A}(s)$ | outgoing neighbours of $v$ that the flow has not visited (all neighbours if none remain) |
| Transition | add $\lambda_f$ to $(v, a)$, move to $a$, recompute the bin |
| Episode boundary | the flow ends: delivered, invalid action, loop/dead end, or $k = 20$ hops |

The state space has size $|V|^2 \cdot 3$: 108 for `small_grid` and 432 for `abilene`.
In practice only about 800-1,000 $(s, a)$ pairs are ever visited on Abilene.

### Reward

Per hop $(v \to a)$, with $\Delta\phi$ the fraction of the flow's demand dropped on that
hop:

$$
r = -\,w_{\text{lat}} \cdot \text{cost}_{(v,a)} \;-\; w_{\text{drop}} \cdot \Delta\phi
\;+\;
\begin{cases}
+R_{\text{deliv}} & a = t \\
R_{\text{loop}} & \text{revisit or dead end} \\
R_{\text{steps}} & k = k_{\max} \\
0 & \text{otherwise}
\end{cases}
$$

with defaults $w_{\text{lat}} = 0.1$ per ms, $w_{\text{drop}} = 50$, $R_{\text{deliv}} = 10$,
$R_{\text{loop}} = R_{\text{steps}} = -100$. An action that is not an outgoing edge at all
returns $r = -100$ and ends the flow without changing any load.

The magnitudes are chosen so that **any failure is worse than any delivery**. The worst
realistic delivery costs about $-(0.1 \cdot 360) - 50 + 10 = -76$, which is above $-100$.
An earlier version used $R_{\text{loop}} = -50$. Under heavy load the agent learned to
deliberately loop flows because that was cheaper than delivering them through congested
links. This is a textbook reward-hacking failure.

## 4. Tabular Q-learning

The action-value table $Q : \mathcal{S} \times \mathcal{A} \to \mathbb{R}$ is a Python
`dict`, initialised lazily to $0$. Since every hop reward is negative, a zero start is
**optimistic**: untried actions look better than tried ones, which drives exploration on
its own.

### Bellman update

After observing $(s, a, r, s', \text{done})$:

$$
Q(s,a) \leftarrow Q(s,a) + \alpha \Big[\, r + \gamma \,(1 - \text{done}) \max_{a' \in \mathcal{A}(s')} Q(s', a') - Q(s,a) \Big]
$$

* The bracket is the TD error $\delta$. Training logs $\overline{|\delta|}$ per episode as
  the "loss".
* When `done` is true the bootstrap term is exactly $0$, because there is no future after a
  terminal transition.
* The $\max$ ranges only over the **valid** actions of $s'$, so values of masked or
  non-existent edges never leak into the target.

### Exploration schedule

$$
a =
\begin{cases}
\text{uniform}(\mathcal{A}(s)) & \text{with probability } \epsilon \\
\arg\max_{a \in \mathcal{A}(s)} Q(s,a) & \text{otherwise (ties go to the lowest node id)}
\end{cases}
\qquad
\epsilon \leftarrow \max(\epsilon_{\text{end}},\ \epsilon \cdot \epsilon_{\text{decay}})
$$

$\epsilon$ decays once per episode: $1.0 \to 0.05$ with decay $0.998$, reaching the floor
after about 1,500 of the 3,000 training episodes. In evaluation mode $\epsilon$ is forced to
$0$ and updates are forbidden.

Defaults: $\alpha = 0.1$, $\gamma = 0.95$. With at most about 5 hops per flow, the
discount barely shrinks the delivery bonus ($0.95^5 \approx 0.77$), so the agent still
values reaching the destination.
