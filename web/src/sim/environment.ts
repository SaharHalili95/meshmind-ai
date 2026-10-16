/** Browser port of src/meshmind/environment.py: identical state, masking, reward and termination rules. */
import type { NetworkTopology } from './topology'
import { generateFlows, type Flow, type TrafficProfile } from './traffic'

export type State = readonly [current: number, destination: number, bin: number]
export type FailureReason = 'invalid_action' | 'loop' | 'max_steps'

export interface EnvConfig {
  maxSteps: number
  loadDecay: number
  invalidActionPenalty: number
  loopPenalty: number
  maxStepsPenalty: number
  latencyWeight: number
  deliveryReward: number
  dropPenalty: number
}

export const DEFAULT_ENV_CONFIG: EnvConfig = {
  maxSteps: 20,
  loadDecay: 0.85,
  invalidActionPenalty: -100,
  loopPenalty: -100,
  maxStepsPenalty: -100,
  latencyWeight: 0.1,
  deliveryReward: 10,
  dropPenalty: 50,
}

export interface FlowResult {
  source: number
  destination: number
  offeredDemand: number
  deliveredDemand: number
  latencyMs: number
  hops: number
  success: boolean
  failureReason: FailureReason | null
  path: number[]
}

export interface StepInfo {
  hopLatency: number
  flowDone: boolean
  episodeDone: boolean
  flowResult?: FlowResult
  avgUtilization?: number
}

export interface StepResult {
  state: State
  reward: number
  done: boolean
  info: StepInfo
}

export function utilizationBin(utilization: number): number {
  if (utilization < 0.5) return 0
  if (utilization < 0.85) return 1
  return 2
}

export class NetworkEnvironment {
  readonly topology: NetworkTopology
  readonly profile: TrafficProfile
  readonly flowsPerEpisode: number
  readonly config: EnvConfig
  flows: Flow[] = []
  flowIndex = 0
  episodeDone = true
  currentNode = 0
  path: number[] = []
  flowSteps = 0
  flowLatency = 0
  deliveredFraction = 1

  constructor(topology: NetworkTopology, profile: TrafficProfile, flowsPerEpisode = 25, config: EnvConfig = DEFAULT_ENV_CONFIG) {
    this.topology = topology
    this.profile = profile
    this.flowsPerEpisode = flowsPerEpisode
    this.config = config
  }

  get currentFlow(): Flow {
    return this.flows[this.flowIndex]!
  }

  reset(seed: number, flows?: Flow[]): State {
    this.topology.resetLoads()
    this.flows = flows ?? generateFlows(this.topology.nodes, this.profile, this.flowsPerEpisode, seed)
    this.flowIndex = 0
    this.episodeDone = false
    this.startFlow()
    return this.observation()
  }

  private startFlow(): void {
    this.currentNode = this.currentFlow.source
    this.path = [this.currentNode]
    this.flowSteps = 0
    this.flowLatency = 0
    this.deliveredFraction = 1
  }

  observation(): State {
    const util = this.topology.outgoingUtilization(this.currentNode)
    return [this.currentNode, this.currentFlow.destination, utilizationBin(util)]
  }

  /** Outgoing neighbours the active flow has not visited; all neighbours at a dead end. */
  validActions(state?: State): number[] {
    const node = state ? state[0] : this.currentNode
    const neighbors = this.topology.neighbors(node)
    if (this.episodeDone || node !== this.currentNode) return neighbors
    const unvisited = neighbors.filter((n) => !this.path.includes(n))
    return unvisited.length > 0 ? unvisited : neighbors
  }

  private isDeadEnd(node: number): boolean {
    return this.topology.neighbors(node).every((n) => this.path.includes(n))
  }

  step(action: number): StepResult {
    if (this.episodeDone) throw new Error('episode is finished; call reset()')
    const flow = this.currentFlow
    const state = this.observation()
    this.flowSteps += 1
    let failure: FailureReason | null = null
    let delivered = false
    let hopLatency = 0
    let reward: number
    let nextState: State

    if (!this.topology.neighbors(this.currentNode).includes(action)) {
      reward = this.config.invalidActionPenalty
      failure = 'invalid_action'
      nextState = state
    } else {
      const u = this.currentNode
      const v = action
      this.topology.addLoad(u, v, flow.demand)
      hopLatency = this.topology.edgeCost(u, v)
      const previous = this.deliveredFraction
      this.deliveredFraction *= this.topology.deliveryFraction(u, v)
      const dropped = previous - this.deliveredFraction
      this.flowLatency += hopLatency
      reward = -this.config.latencyWeight * hopLatency - this.config.dropPenalty * dropped

      const revisited = this.path.includes(v)
      this.currentNode = v
      this.path.push(v)
      nextState = this.observation()

      if (v === flow.destination) {
        delivered = true
        reward += this.config.deliveryReward
      } else if (revisited || this.isDeadEnd(v)) {
        failure = 'loop'
        reward += this.config.loopPenalty
      } else if (this.flowSteps >= this.config.maxSteps) {
        failure = 'max_steps'
        reward += this.config.maxStepsPenalty
      }
    }

    const done = delivered || failure !== null
    const info: StepInfo = { hopLatency, flowDone: done, episodeDone: false }
    if (done) {
      info.flowResult = {
        source: flow.source,
        destination: flow.destination,
        offeredDemand: flow.demand,
        deliveredDemand: delivered ? flow.demand * this.deliveredFraction : 0,
        latencyMs: this.flowLatency,
        hops: this.path.length - 1,
        success: delivered,
        failureReason: failure,
        path: [...this.path],
      }
      info.avgUtilization = this.topology.averageUtilization()
      this.advanceFlow()
      info.episodeDone = this.episodeDone
    }
    return { state: nextState, reward, done, info }
  }

  private advanceFlow(): void {
    if (this.flowIndex + 1 >= this.flows.length) {
      this.episodeDone = true
      return
    }
    this.flowIndex += 1
    this.topology.decayLoads(this.config.loadDecay)
    this.startFlow()
  }
}
