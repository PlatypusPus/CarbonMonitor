export const formatNumber = (value) => typeof value === 'number' && Number.isFinite(value)
  ? value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '-';

// Sum monthly observations without inventing daily or hourly readings.
export function groupPeriods(rows, interval) {
  const buckets = new Map();
  for (const row of rows) {
    const date = new Date(row.timestamp);
    const year = date.getUTCFullYear();
    const month = date.getUTCMonth();
    const part = interval === 'year' ? 0 : interval === 'quarter' ? Math.floor(month / 3) : month;
    const key = year * 12 + part;
    const label = interval === 'year' ? String(year) : interval === 'quarter' ? `Q${part + 1}`
      : date.toLocaleDateString('en', { month: 'short', timeZone: 'UTC' });
    const bucket = buckets.get(key) ?? { key, year, label, value: 0, count: 0 };
    bucket.value += row.value ?? 0;
    bucket.count += row.count;
    buckets.set(key, bucket);
  }
  return [...buckets.values()].sort((a, b) => a.key - b.key);
}
