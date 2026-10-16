import { describe, expect, it } from 'vitest'
import { QLearningAgent } from '@/sim/agent'
import { NetworkEnvironment, utilizationBin, type State } from '@/sim/environment'
import { agentPolicy, congestionAware, dijkstra, evaluate, shortestPath, trainEpisode } from '@/sim/policies'
import { ABILENE, congestionPenalty, NetworkTopology, SMALL_GRID, type TopologySpec } from '@/sim/topology'
import { generateFlows, TRAFFIC_PROFILES } from '@/sim/traffic'

const LINE: TopologySpec = {
  name: 'small_grid',
  viewBox: [100, 100],
  links: [[0, 1, 100, 1], [1, 2, 100, 1], [2, 3, 100, 1], [3, 4, 100, 1], [0, 4, 100, 50]],
  nodes: [0, 1, 2, 3, 4].map((id) => ({ id, label: String(id), short: String(id), x: 0, y: 0 })),
}
const lineEnv = () => new NetworkEnvironment(new NetworkTopology(LINE), 'moderate', 3)

describe('topology (same rules as topology.py)', () => {
  it('builds both directions of every link', () => {
    expect(new NetworkTopology(ABILENE).edges.size).toBe(30)
    expect(new NetworkTopology(SMALL_GRID).edges.size).toBe(14)
  })

  it.each([[0.5, 0], [0.8, 0], [0.9, 1], [1.0, 4], [1.2, 16]])('penalty at utilization %f', (u, expected) => {
    expect(congestionPenalty(4, u)).toBeCloseTo(expected)
  })

  it('caps utilization and computes proportional delivery', () => {
    const topo = new NetworkTopology(LINE)
    topo.addLoad(0, 1, 1000)
    expect(topo.edge(0, 1).utilization).toBeCloseTo(1.5)
    expect(topo.deliveryFraction(0, 1)).toBeCloseTo(0.1)
  })

  it('rejects zero capacity', () => {
    expect(() => new NetworkTopology({ ...LINE, links: [[0, 1, 0, 1]] })).toThrow()
  })
})

describe('traffic', () => {
  it('keeps demand in range and source != destination', () => {
    for (const profile of Object.keys(TRAFFIC_PROFILES) as (keyof typeof TRAFFIC_PROFILES)[]) {
      const [low, high] = TRAFFIC_PROFILES[profile]
      for (const f of generateFlows(ABILENE.nodes.map((n) => n.id), profile, 300, 7)) {
        expect(f.source).not.toBe(f.destination)
        expect(f.demand).toBeGreaterThanOrEqual(low)
        expect(f.demand).toBeLessThanOrEqual(high)
      }
    }
  })

  it('is reproducible from the seed', () => {
    const nodes = [0, 1, 2, 3]
    expect(generateFlows(nodes, 'dynamic', 20, 3)).toEqual(generateFlows(nodes, 'dynamic', 20, 3))
  })
})

describe('environment (same rules as environment.py)', () => {
  it.each([[0.49, 0], [0.5, 1], [0.84, 1], [0.85, 2]])('bin of %f is %i', (u, bin) => {
    expect(utilizationBin(u)).toBe(bin)
  })

  it('penalises an invalid action without touching load', () => {
    const env = lineEnv()
    env.reset(0, [{ source: 0, destination: 2, demand: 10 }])
    const { reward, done, info } = env.step(2)
    expect(reward).toBe(-100)
    expect(done).toBe(true)
    expect(info.flowResult?.failureReason).toBe('invalid_action')
    expect([...env.topology.edges.values()].every((e) => e.load === 0)).toBe(true)
  })

  it('masks visited neighbours and ends a revisit as a loop', () => {
    const env = lineEnv()
    env.reset(0, [{ source: 1, destination: 3, demand: 10 }])
    env.step(2)
    expect(env.validActions()).toEqual([3])
    const { reward, info } = env.step(1)
    expect(info.flowResult?.failureReason).toBe('loop')
    expect(reward).toBeCloseTo(-0.1 - 100)
  })

  it('rewards a delivery and accounts latency and load', () => {
    const env = lineEnv()
    env.reset(0, [{ source: 0, destination: 2, demand: 10 }, { source: 3, destination: 4, demand: 5 }])
    expect(env.step(1).reward).toBeCloseTo(-0.1)
    const { reward, info } = env.step(2)
    expect(reward).toBeCloseTo(-0.1 + 10)
    expect(info.flowResult?.path).toEqual([0, 1, 2])
    expect(info.flowResult?.latencyMs).toBeCloseTo(2)
    expect(env.topology.edge(0, 1).load).toBeCloseTo(10 * 0.85)
  })
})

describe('Q-learning agent (same update as agent.py)', () => {
  const s: State = [0, 3, 1]
  const next: State = [1, 3, 0]

  it('applies the exact Bellman update', () => {
    const agent = new QLearningAgent({ alpha: 0.5, gamma: 0.9, epsilonStart: 1, epsilonEnd: 0.1, epsilonDecay: 0.5 })
    agent.qTable.set('0,3,1|1', 2)
    agent.qTable.set('1,3,0|2', 4)
    agent.qTable.set('1,3,0|3', -1)
    expect(agent.update(s, 1, -1, next, [2, 3], false)).toBeCloseTo(0.6)
    expect(agent.getQ(s, 1)).toBeCloseTo(2.3)
  })

  it('does not bootstrap on a terminal step', () => {
    const agent = new QLearningAgent({ alpha: 0.5, gamma: 0.9, epsilonStart: 1, epsilonEnd: 0.1, epsilonDecay: 0.5 })
    agent.qTable.set('1,3,0|2', 100)
    agent.update(s, 1, 10, next, [2], true)
    expect(agent.getQ(s, 1)).toBeCloseTo(5)
  })

  it('decays epsilon to its floor and refuses updates in eval mode', () => {
    const agent = new QLearningAgent({ alpha: 0.5, gamma: 0.9, epsilonStart: 1, epsilonEnd: 0.1, epsilonDecay: 0.5 })
    for (let i = 0; i < 6; i++) agent.decayEpsilon()
    expect(agent.epsilon).toBeCloseTo(0.1)
    agent.evalMode = true
    expect(() => agent.update(s, 1, 0, next, [2], false)).toThrow()
  })
})

describe('policies and training', () => {
  it('finds the min-latency path and avoids a hot link when congestion-aware', () => {
    const tri: TopologySpec = { ...LINE, links: [[0, 1, 100, 1], [1, 2, 100, 1], [0, 2, 100, 5]], nodes: LINE.nodes.slice(0, 3) }
    const env = new NetworkEnvironment(new NetworkTopology(tri), 'low', 1)
    const state = env.reset(0, [{ source: 0, destination: 2, demand: 5 }])
    expect(dijkstra(env.topology, 0, 2, (u, v) => env.topology.edge(u, v).baseLatency)).toEqual([0, 1, 2])
    env.topology.setLoad(0, 1, 150)
    expect(shortestPath(env, state, env.validActions())).toBe(1)
    expect(congestionAware(env, state, env.validActions())).toBe(2)
  })

  it('learns to route the small grid without failures', () => {
    const env = new NetworkEnvironment(new NetworkTopology(SMALL_GRID), 'high', 10)
    const agent = new QLearningAgent(undefined, 1)
    const logs = Array.from({ length: 600 }, (_, i) => trainEpisode(env, agent, 1 + i, i))
    const mean = (xs: number[]) => xs.reduce((a, b) => a + b, 0) / xs.length
    expect(mean(logs.slice(-60).map((l) => l.totalReward))).toBeGreaterThan(mean(logs.slice(0, 60).map((l) => l.totalReward)))
    const before = new Map(agent.qTable)
    expect(evaluate(env, agentPolicy(agent), 1, 10).routingFailures).toBe(0)
    expect(agent.qTable).toEqual(before)
  })
})
