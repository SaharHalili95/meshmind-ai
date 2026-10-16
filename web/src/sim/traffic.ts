/** Browser port of src/meshmind/traffic.py. */
import { Rng } from './rng'

export type TrafficProfile = 'low' | 'moderate' | 'high' | 'dynamic'

export const TRAFFIC_PROFILES: Record<TrafficProfile, readonly [number, number]> = {
  low: [5, 15],
  moderate: [20, 50],
  high: [60, 120],
  dynamic: [10, 90],
}

export interface Flow {
  source: number
  destination: number
  demand: number
}

export function generateFlows(nodes: readonly number[], profile: TrafficProfile, count: number, seed: number): Flow[] {
  if (nodes.length < 2) throw new Error('traffic generation needs at least two nodes')
  const rng = new Rng(seed)
  const [low, high] = TRAFFIC_PROFILES[profile]

  const pairs = Array.from({ length: count }, () => {
    const source = rng.choice(nodes)
    const others = nodes.filter((n) => n !== source)
    return [source, rng.choice(others)] as const
  })

  let demands: number[]
  if (profile === 'dynamic') {
    // Demand drifts along a sinusoid across the episode, like daily traffic.
    const phase = rng.uniform(0, 2 * Math.PI)
    const mid = (low + high) / 2
    const amplitude = (high - low) / 3
    demands = pairs.map((_, i) => {
      const mean = mid + amplitude * Math.sin((2 * Math.PI * i) / count + phase)
      return Math.min(high, Math.max(low, rng.normal(mean, (high - low) / 8)))
    })
  } else {
    demands = pairs.map(() => rng.uniform(low, high))
  }

  return pairs.map(([source, destination], i) => ({ source, destination, demand: demands[i]! }))
}
