import raw from './results.json'
import type { PolicyName } from '@/sim/policies'

export type MetricKey = 'pdr' | 'plr' | 'mean_latency_ms' | 'mean_throughput' | 'avg_link_utilization' | 'routing_failures' | 'mean_hops'

export interface Stat {
  mean: number
  std: number
}

export interface PerSeedRow {
  seed: number
  policy: PolicyName
  pdr: number
  plr: number
  mean_latency_ms: number
  mean_throughput: number
  avg_link_utilization: number
  routing_failures: number
  mean_hops: number
}

export interface Comparison {
  metric: MetricKey
  baseline: PolicyName
  mean_diff: number
  ci_low: number
  ci_high: number
  p_value: number
  wins: number
  n: number
  higher_is_better: boolean
  significant: boolean
}

export interface SweepPoint {
  relative_load: number
  shortest_path: Comparison
  congestion_aware: Comparison
  pdr: Record<PolicyName, number>
}

export interface BenchmarkResults {
  config: {
    topology: { name: string }
    traffic: { profile: string; flows_per_episode: number }
    agent: { alpha: number; gamma: number; epsilon_start: number; epsilon_end: number; epsilon_decay: number }
    train_episodes: number
    eval_episodes: number
  }
  seeds: number[]
  policies: Record<PolicyName, Record<MetricKey, Stat>>
  perSeed: PerSeedRow[]
  comparisons: Comparison[]
  loadSweep: SweepPoint[]
  rewardCurve: { window: number; episode: number[]; mean: number[]; std: number[] }
}

/** Results of the Python benchmark (exported by scripts/export_web_data.py). */
export const results = raw as unknown as BenchmarkResults
