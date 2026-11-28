// Godot math primitives used by the sim, ported to plain TypeScript (read-only support).
//
// Vector2 / Vector3 are VALUE types in GDScript: assignment copies them. Here they
// are small classes whose methods always return new vectors; never mutate a vector
// you did not create (use `copy()` when you need an independent value).

export const CMP_EPSILON = 0.00001;

export function clampf(value: number, min: number, max: number): number {
  return value < min ? min : value > max ? max : value;
}

export function maxf(a: number, b: number): number {
  return a > b ? a : b;
}

export function minf(a: number, b: number): number {
  return a < b ? a : b;
}

export function maxi(a: number, b: number): number {
  return a > b ? a : b;
}

export function lerpf(from: number, to: number, weight: number): number {
  return from + (to - from) * weight;
}

export function snappedf(value: number, step: number): number {
  return step !== 0 ? Math.floor(value / step + 0.5) * step : value;
}

export function isZeroApprox(value: number): boolean {
  return Math.abs(value) < CMP_EPSILON;
}

export function isEqualApprox(a: number, b: number): boolean {
  if (a === b) return true;
  let tolerance = CMP_EPSILON * Math.abs(a);
  if (tolerance < CMP_EPSILON) tolerance = CMP_EPSILON;
  return Math.abs(a - b) < tolerance;
}

// Godot's wrapf(value, min, max).
export function wrapf(value: number, min: number, max: number): number {
  const range = max - min;
  if (isZeroApprox(range)) return min;
  const result = value - range * Math.floor((value - min) / range);
  if (isEqualApprox(result, max)) return min;
  return result;
}

export class Vector2 {
  x: number;
  y: number;

  constructor(x = 0, y = 0) {
    this.x = x;
    this.y = y;
  }

  static get ZERO(): Vector2 {
    return new Vector2(0, 0);
  }

  static get RIGHT(): Vector2 {
    return new Vector2(1, 0);
  }

  copy(): Vector2 {
    return new Vector2(this.x, this.y);
  }

  add(o: Vector2): Vector2 {
    return new Vector2(this.x + o.x, this.y + o.y);
  }

  sub(o: Vector2): Vector2 {
    return new Vector2(this.x - o.x, this.y - o.y);
  }

  mul(s: number): Vector2 {
    return new Vector2(this.x * s, this.y * s);
  }

  div(s: number): Vector2 {
    return new Vector2(this.x / s, this.y / s);
  }

  neg(): Vector2 {
    return new Vector2(-this.x, -this.y);
  }

  length(): number {
    return Math.sqrt(this.x * this.x + this.y * this.y);
  }

  lengthSquared(): number {
    return this.x * this.x + this.y * this.y;
  }

  normalized(): Vector2 {
    const l = this.lengthSquared();
    if (l === 0) return new Vector2(0, 0);
    const len = Math.sqrt(l);
    return new Vector2(this.x / len, this.y / len);
  }

  dot(o: Vector2): number {
    return this.x * o.x + this.y * o.y;
  }

  // 2D cross product (z component of the 3D cross product).
  cross(o: Vector2): number {
    return this.x * o.y - this.y * o.x;
  }

  distanceTo(o: Vector2): number {
    return Math.sqrt((this.x - o.x) ** 2 + (this.y - o.y) ** 2);
  }

  distanceSquaredTo(o: Vector2): number {
    return (this.x - o.x) ** 2 + (this.y - o.y) ** 2;
  }

  moveToward(to: Vector2, delta: number): Vector2 {
    const vd = to.sub(this);
    const len = vd.length();
    return len <= delta || len < CMP_EPSILON ? to.copy() : this.add(vd.div(len).mul(delta));
  }

  angle(): number {
    return Math.atan2(this.y, this.x);
  }

  rotated(angle: number): Vector2 {
    const sine = Math.sin(angle);
    const cosi = Math.cos(angle);
    return new Vector2(this.x * cosi - this.y * sine, this.x * sine + this.y * cosi);
  }

  equals(o: Vector2): boolean {
    return this.x === o.x && this.y === o.y;
  }

  isFinite(): boolean {
    return Number.isFinite(this.x) && Number.isFinite(this.y);
  }
}

export class Vector3 {
  x: number;
  y: number;
  z: number;

  constructor(x = 0, y = 0, z = 0) {
    this.x = x;
    this.y = y;
    this.z = z;
  }

  static get ZERO(): Vector3 {
    return new Vector3(0, 0, 0);
  }

  static get UP(): Vector3 {
    return new Vector3(0, 1, 0);
  }

  copy(): Vector3 {
    return new Vector3(this.x, this.y, this.z);
  }

  add(o: Vector3): Vector3 {
    return new Vector3(this.x + o.x, this.y + o.y, this.z + o.z);
  }

  sub(o: Vector3): Vector3 {
    return new Vector3(this.x - o.x, this.y - o.y, this.z - o.z);
  }

  mul(s: number): Vector3 {
    return new Vector3(this.x * s, this.y * s, this.z * s);
  }

  length(): number {
    return Math.sqrt(this.x * this.x + this.y * this.y + this.z * this.z);
  }

  normalized(): Vector3 {
    const l = this.x * this.x + this.y * this.y + this.z * this.z;
    if (l === 0) return new Vector3(0, 0, 0);
    const len = Math.sqrt(l);
    return new Vector3(this.x / len, this.y / len, this.z / len);
  }

  dot(o: Vector3): number {
    return this.x * o.x + this.y * o.y + this.z * o.z;
  }

  cross(o: Vector3): Vector3 {
    return new Vector3(
      this.y * o.z - this.z * o.y,
      this.z * o.x - this.x * o.z,
      this.x * o.y - this.y * o.x,
    );
  }

  equals(o: Vector3): boolean {
    return this.x === o.x && this.y === o.y && this.z === o.z;
  }

  isZero(): boolean {
    return this.x === 0 && this.y === 0 && this.z === 0;
  }

  isFinite(): boolean {
    return Number.isFinite(this.x) && Number.isFinite(this.y) && Number.isFinite(this.z);
  }
}
