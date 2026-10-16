/** Browser port of src/meshmind/topology.py: same links, same congestion penalty, same load rules. */

export const CONGESTION_THRESHOLD = 0.8

/** [source, target, capacity, base latency in ms] */
export type LinkSpec = readonly [number, number, number, number]

export interface EdgeState {
  u: number
  v: number
  capacity: number
  baseLatency: number
  load: number
  utilization: number
  congestionPenalty: number
}

export interface NodeInfo {
  id: number
  label: string
  short: string
  x: number
  y: number
}

export interface TopologySpec {
  name: TopologyName
  links: readonly LinkSpec[]
  nodes: readonly NodeInfo[]
  viewBox: readonly [number, number]
}

export type TopologyName = 'abilene' | 'small_grid'

export const ABILENE: TopologySpec = {
  name: 'abilene',
  viewBox: [1000, 470],
  links: [
    [0, 1, 100, 6.5], [0, 3, 100, 8.2], [1, 2, 100, 2.9], [1, 3, 100, 7.8], [2, 5, 100, 11.0],
    [3, 4, 100, 4.6], [4, 5, 100, 5.9], [4, 6, 100, 4.8], [5, 7, 100, 6.0], [6, 8, 80, 1.4],
    [6, 7, 100, 3.8], [8, 9, 100, 5.7], [9, 10, 80, 1.7], [10, 7, 100, 4.9], [7, 11, 150, 0.2],
  ],
  // Positions follow the real cities' longitude/latitude.
  nodes: [
    { id: 0, label: 'Seattle', short: 'SEA', x: 90, y: 60 },
    { id: 1, label: 'Sunnyvale', short: 'SNV', x: 80, y: 250 },
    { id: 2, label: 'Los Angeles', short: 'LAX', x: 165, y: 330 },
    { id: 3, label: 'Denver', short: 'DEN', x: 375, y: 200 },
    { id: 4, label: 'Kansas City', short: 'KC', x: 545, y: 215 },
    { id: 5, label: 'Houston', short: 'HOU', x: 535, y: 400 },
    { id: 6, label: 'Indianapolis', short: 'IND', x: 705, y: 215 },
    { id: 7, label: 'Atlanta', short: 'ATL', x: 735, y: 325 },
    { id: 8, label: 'Chicago', short: 'CHI', x: 670, y: 120 },
    { id: 9, label: 'New York', short: 'NYC', x: 915, y: 150 },
    { id: 10, label: 'Washington', short: 'WAS', x: 870, y: 235 },
    { id: 11, label: 'Atlanta-M5', short: 'M5', x: 790, y: 415 },
  ],
}

export const SMALL_GRID: TopologySpec = {
  name: 'small_grid',
  viewBox: [1000, 470],
  links: [
    [0, 1, 100, 2.0], [1, 2, 100, 2.0], [3, 4, 100, 3.0], [4, 5, 100, 3.0],
    [0, 3, 100, 1.0], [1, 4, 60, 1.0], [2, 5, 100, 1.0],
  ],
  nodes: [
    { id: 0, label: 'Node 0', short: '0', x: 220, y: 110 },
    { id: 1, label: 'Node 1', short: '1', x: 500, y: 110 },
    { id: 2, label: 'Node 2', short: '2', x: 780, y: 110 },
    { id: 3, label: 'Node 3', short: '3', x: 220, y: 360 },
    { id: 4, label: 'Node 4', short: '4', x: 500, y: 360 },
    { id: 5, label: 'Node 5', short: '5', x: 780, y: 360 },
  ],
}

export const TOPOLOGIES: Record<TopologyName, TopologySpec> = { abilene: ABILENE, small_grid: SMALL_GRID }

export function congestionPenalty(baseLatency: number, utilization: number): number {
  if (utilization <= CONGESTION_THRESHOLD) return 0
  const excess = (utilization - CONGESTION_THRESHOLD) / (1 - CONGESTION_THRESHOLD)
  return baseLatency * excess ** 2
}

export const edgeKey = (u: number, v: number) => `${u}-${v}`

export class NetworkTopology {
  readonly spec: TopologySpec
  readonly maxUtilization: number
  readonly edges = new Map<string, EdgeState>()
  private readonly adjacency = new Map<number, number[]>()

  constructor(spec: TopologySpec, maxUtilization = 1.5) {
    this.spec = spec
    this.maxUtilization = maxUtilization
    for (const node of spec.nodes) this.adjacency.set(node.id, [])
    for (const [a, b, capacity, latency] of spec.links) {
      if (a === b) throw new Error(`self-loop on node ${a}`)
      if (capacity <= 0) throw new Error(`link ${a}->${b} must have capacity > 0`)
      if (latency < 0) throw new Error(`link ${a}->${b} must have latency >= 0`)
      for (const [u, v] of [[a, b], [b, a]] as const) {
        this.edges.set(edgeKey(u, v), { u, v, capacity, baseLatency: latency, load: 0, utilization: 0, congestionPenalty: 0 })
        this.adjacency.get(u)!.push(v)
      }
    }
    for (const list of this.adjacency.values()) list.sort((x, y) => x - y)
  }

  get nodes(): number[] {
    return this.spec.nodes.map((n) => n.id)
  }

  neighbors(node: number): number[] {
    const list = this.adjacency.get(node)
    if (!list) throw new Error(`unknown node ${node}`)
    return list
  }

  edge(u: number, v: number): EdgeState {
    const edge = this.edges.get(edgeKey(u, v))
    if (!edge) throw new Error(`no link ${u}->${v}`)
    return edge
  }

  hasEdge(u: number, v: number): boolean {
    return this.edges.has(edgeKey(u, v))
  }

  edgeCost(u: number, v: number): number {
    const e = this.edge(u, v)
    return e.baseLatency + e.congestionPenalty
  }

  /** Share of a flow the link can carry under proportional sharing. */
  deliveryFraction(u: number, v: number): number {
    const e = this.edge(u, v)
    return e.load <= e.capacity ? 1 : e.capacity / e.load
  }

  private refresh(e: EdgeState): void {
    e.utilization = Math.min(e.load / e.capacity, this.maxUtilization)
    e.congestionPenalty = congestionPenalty(e.baseLatency, e.utilization)
  }

  addLoad(u: number, v: number, amount: number): void {
    if (amount < 0) throw new Error('load amount must be non-negative')
    const e = this.edge(u, v)
    e.load += amount
    this.refresh(e)
  }

  setLoad(u: number, v: number, load: number): void {
    const e = this.edge(u, v)
    e.load = load
    this.refresh(e)
  }

  decayLoads(factor: number): void {
    for (const e of this.edges.values()) {
      e.load *= factor
      this.refresh(e)
    }
  }

  resetLoads(): void {
    for (const e of this.edges.values()) {
      e.load = 0
      this.refresh(e)
    }
  }

  averageUtilization(): number {
    let sum = 0
    for (const e of this.edges.values()) sum += e.utilization
    return sum / this.edges.size
  }

  outgoingUtilization(node: number): number {
    const out = this.neighbors(node)
    if (out.length === 0) return 0
    return out.reduce((acc, v) => acc + this.edge(node, v).utilization, 0) / out.length
  }
}
