export function fixed(value: number, digits = 1): string {
  return value.toFixed(digits);
}

export function pct(value: number): string {
  return `${Math.round(value)}%`;
}

export function cny(value: number): string {
  return `¥${value.toFixed(2)}`;
}
