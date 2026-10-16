/** Browser port of src/meshmind/agent.py: tabular Q-learning with the same update rule. */
import { Rng } from './rng'
import type { State } from './environment'

export interface AgentConfig {
  alpha: number
  gamma: number
  epsilonStart: number
  epsilonEnd: number
  epsilonDecay: number
}

export const DEFAULT_AGENT_CONFIG: AgentConfig = {
  alpha: 0.1,
  gamma: 0.95,
  epsilonStart: 1,
  epsilonEnd: 0.05,
  epsilonDecay: 0.998,
}

const key = (state: State, action: number) => `${state[0]},${state[1]},${state[2]}|${action}`

export class QLearningAgent {
  readonly config: AgentConfig
  epsilon: number
  evalMode = false
  readonly qTable = new Map<string, number>()
  private readonly rng: Rng

  constructor(config: AgentConfig = DEFAULT_AGENT_CONFIG, seed = 0) {
    this.config = config
    this.epsilon = config.epsilonStart
    this.rng = new Rng(seed)
  }

  getQ(state: State, action: number): number {
    return this.qTable.get(key(state, action)) ?? 0
  }

  hasSeen(state: State, actions: readonly number[]): boolean {
    return actions.some((a) => this.qTable.has(key(state, a)))
  }

  maxQ(state: State, actions: readonly number[]): number {
    if (actions.length === 0) return 0
    return Math.max(...actions.map((a) => this.getQ(state, a)))
  }

  /** Highest-Q valid action; ties go to the lowest node id. */
  greedyAction(state: State, actions: readonly number[]): number {
    if (actions.length === 0) throw new Error('no valid actions available')
    const sorted = [...actions].sort((x, y) => x - y)
    let best = sorted[0]!
    for (const a of sorted) if (this.getQ(state, a) > this.getQ(state, best)) best = a
    return best
  }

  selectAction(state: State, actions: readonly number[]): number {
    const epsilon = this.evalMode ? 0 : this.epsilon
    if (this.rng.next() < epsilon) return this.rng.choice(actions)
    return this.greedyAction(state, actions)
  }

  /** Q(s,a) <- Q(s,a) + alpha * [r + gamma * max Q(s',a') - Q(s,a)]; no bootstrap when done. */
  update(state: State, action: number, reward: number, next: State, nextActions: readonly number[], done: boolean): number {
    if (this.evalMode) throw new Error('Q-table updates are forbidden in evaluation mode')
    const future = done ? 0 : this.maxQ(next, nextActions)
    const current = this.getQ(state, action)
    const td = reward + this.config.gamma * future - current
    this.qTable.set(key(state, action), current + this.config.alpha * td)
    return td
  }

  decayEpsilon(): number {
    this.epsilon = Math.max(this.config.epsilonEnd, this.epsilon * this.config.epsilonDecay)
    return this.epsilon
  }
}
