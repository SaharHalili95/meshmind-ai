/** Baselines (port of src/meshmind/baselines.py), plus metrics and the train/evaluate loops. */
import type { QLearningAgent } from './agent'
import type { FlowResult, NetworkEnvironment, State } from './environment'
import { Rng } from './rng'
import type { NetworkTopology } from './topology'

export type PolicyName = 'q_learning' | 'shortest_path' | 'congestion_aware' | 'random'
export const POLICY_ORDER: PolicyName[] = ['q_learning', 'shortest_path', 'congestion_aware', 'random']

export type ActionFn = (env: NetworkEnvironment, state: State, actions: number[]) => number

/** Dijkstra over the topology; `exclude` removes nodes (except the source) from the search. */
export function dijkstra(
  topology: NetworkTopology,
  source: number,
  target: number,
  weight: (u: number, v: number) => number,
  exclude: ReadonlySet<number> = new Set(),
): number[] | null {
  const dist = new Map<number, number>([[source, 0]])
  const prev = new Map<number, number>()
  const done = new Set<number>()
  while (true) {
    let u: number | undefined
    let best = Infinity
    for (const [node, d] of dist) {
      if (!done.has(node) && d < best) {
        best = d
        u = node
      }
    }
    if (u === undefined) return null
    if (u === target) break
    done.add(u)
    for (const v of topology.neighbors(u)) {
      if (exclude.has(v) || done.has(v)) continue
      const alt = best + weight(u, v)
      if (alt < (dist.get(v) ?? Infinity)) {
        dist.set(v, alt)
        prev.set(v, u)
      }
    }
  }
  const path = [target]
  while (path[0] !== source) path.unshift(prev.get(path[0]!)!)
  return path
}

export const shortestPath: ActionFn = (env, state) => {
  const path = dijkstra(env.topology, state[0], state[1], (u, v) => env.topology.edge(u, v).baseLatency)
  if (!path || path.length < 2) throw new Error('no route')
  return path[1]!
}

export const congestionAware: ActionFn = (env, state) => {
  const visited = new Set(env.path.filter((n) => n !== state[0]))
  const cost = (u: number, v: number) => env.topology.edgeCost(u, v)
  const path = dijkstra(env.topology, state[0], state[1], cost, visited) ?? dijkstra(env.topology, state[0], state[1], cost)
  if (!path || path.length < 2) throw new Error('no route')
  return path[1]!
}

export function randomPolicy(seed: number): ActionFn {
  const rng = new Rng(seed)
  return (_env, _state, actions) => rng.choice(actions)
}

export function agentPolicy(agent: QLearningAgent): ActionFn {
  return (_env, state, actions) => agent.greedyAction(state, actions)
}

export interface Metrics {
  pdr: number
  plr: number
  meanLatencyMs: number
  meanThroughput: number
  avgLinkUtilization: number
  routingFailures: number
  flows: number
}

export function summarize(flows: readonly FlowResult[], utilization: readonly number[]): Metrics {
  const offered = flows.reduce((s, f) => s + f.offeredDemand, 0)
  const delivered = flows.reduce((s, f) => s + f.deliveredDemand, 0)
  const ok = flows.filter((f) => f.success)
  const pdr = offered > 0 ? delivered / offered : 0
  return {
    pdr,
    plr: offered > 0 ? 1 - pdr : 0,
    meanLatencyMs: ok.length ? ok.reduce((s, f) => s + f.latencyMs, 0) / ok.length : 0,
    meanThroughput: flows.length ? delivered / flows.length : 0,
    avgLinkUtilization: utilization.length ? utilization.reduce((s, u) => s + u, 0) / utilization.length : 0,
    routingFailures: flows.length - ok.length,
    flows: flows.length,
  }
}

export const EVAL_SEED_OFFSET = 1_000_000

export function evaluate(env: NetworkEnvironment, act: ActionFn, baseSeed: number, episodes: number): Metrics {
  const flows: FlowResult[] = []
  const utilization: number[] = []
  for (let i = 0; i < episodes; i++) {
    let state = env.reset(baseSeed + EVAL_SEED_OFFSET + i)
    while (!env.episodeDone) {
      const result = env.step(act(env, state, env.validActions(state)))
      if (result.done) {
        flows.push(result.info.flowResult!)
        utilization.push(result.info.avgUtilization!)
        state = env.episodeDone ? result.state : env.observation()
      } else {
        state = result.state
      }
    }
  }
  return summarize(flows, utilization)
}

export interface EpisodeLog {
  episode: number
  totalReward: number
  epsilon: number
  pdr: number
  failures: number
}

/** One training episode: epsilon-greedy rollout with a Bellman update after every hop. */
export function trainEpisode(env: NetworkEnvironment, agent: QLearningAgent, seed: number, episode: number): EpisodeLog {
  agent.evalMode = false
  const flows: FlowResult[] = []
  let state = env.reset(seed)
  let total = 0
  const epsilon = agent.epsilon
  while (!env.episodeDone) {
    const actions = env.validActions(state)
    const action = agent.selectAction(state, actions)
    const { state: next, reward, done, info } = env.step(action)
    agent.update(state, action, reward, next, done ? [] : env.validActions(next), done)
    total += reward
    if (done) {
      flows.push(info.flowResult!)
      state = env.episodeDone ? next : env.observation()
    } else {
      state = next
    }
  }
  agent.decayEpsilon()
  const m = summarize(flows, [])
  return { episode, totalReward: total, epsilon, pdr: m.pdr, failures: m.routingFailures }
}
