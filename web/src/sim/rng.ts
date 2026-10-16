/** Small seeded PRNG (mulberry32) so every browser run is reproducible from its seed. */
export class Rng {
  private state: number

  constructor(seed: number) {
    this.state = seed >>> 0
  }

  next(): number {
    this.state = (this.state + 0x6d2b79f5) >>> 0
    let t = this.state
    t = Math.imul(t ^ (t >>> 15), t | 1)
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }

  uniform(low: number, high: number): number {
    return low + (high - low) * this.next()
  }

  int(n: number): number {
    return Math.floor(this.next() * n)
  }

  choice<T>(items: readonly T[]): T {
    if (items.length === 0) throw new Error('cannot choose from an empty list')
    return items[this.int(items.length)]!
  }

  normal(mean: number, std: number): number {
    const u = 1 - this.next()
    const v = this.next()
    return mean + std * Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v)
  }
}
