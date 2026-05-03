export function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

export function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

export function easeInOutCubic(t: number): number {
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
}

export function randomBetween(min: number, max: number): number {
  return min + Math.random() * (max - min);
}

export function pushBounded<T>(arr: T[], value: T, maxLength: number): T[] {
  const next = [...arr, value];
  while (next.length > maxLength) next.shift();
  return next;
}
