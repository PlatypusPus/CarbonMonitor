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

// kg below 1,000, tonnes above, so headline numbers stay readable.
export function formatEmissions(kg) {
  if (typeof kg !== 'number' || !Number.isFinite(kg)) return { value: '-', unit: 'kg CO₂e' };
  return Math.abs(kg) >= 1000
    ? { value: formatNumber(kg / 1000), unit: 't CO₂e' }
    : { value: formatNumber(kg), unit: 'kg CO₂e' };
}

export const compactNumber = (value) => new Intl.NumberFormat('en', { notation: 'compact', maximumFractionDigits: 1 }).format(value);

// Merge per-metric monthly series into rows of { key: 'YYYY-MM', label, [series]: kg }.
export function mergeMonthly(seriesByName) {
  const months = new Map();
  for (const [name, rows] of Object.entries(seriesByName)) {
    for (const row of rows ?? []) {
      const date = new Date(row.timestamp);
      const key = `${date.getUTCFullYear()}-${String(date.getUTCMonth() + 1).padStart(2, '0')}`;
      const month = months.get(key) ?? { key, label: date.toLocaleDateString('en', { month: 'short', year: '2-digit', timeZone: 'UTC' }) };
      month[name] = (month[name] ?? 0) + (row.value ?? 0);
      months.set(key, month);
    }
  }
  return [...months.values()].sort((a, b) => a.key.localeCompare(b.key));
}
