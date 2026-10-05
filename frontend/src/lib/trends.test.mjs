import assert from 'node:assert/strict';
import { test } from 'node:test';
import { groupPeriods, formatNumber, formatEmissions, mergeMonthly } from './trends.js';

test('calendar groups preserve totals, count and year boundaries', () => {
  const rows = [
    { timestamp: '2026-01-01T00:00:00Z', value: 30.125, count: 1 },
    { timestamp: '2025-12-01T00:00:00Z', value: 20, count: 1 },
    { timestamp: '2025-10-01T00:00:00Z', value: 10, count: 2 },
  ];
  assert.deepEqual(groupPeriods(rows, 'quarter').map(({ year, label, value, count }) => ({ year, label, value, count })),
    [{year:2025,label:'Q4',value:30,count:3},{year:2026,label:'Q1',value:30.125,count:1}]);
  assert.equal(groupPeriods(rows, 'month').length, 3);
  assert.equal(groupPeriods(rows, 'year').reduce((sum, row) => sum + row.value, 0), 60.125);
  assert.deepEqual(groupPeriods([], 'month'), []);
  assert.equal(formatNumber(30.125), (30.125).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2}));
  assert.equal(formatNumber(null), '-');
});

test('emissions switch to tonnes and months merge across metrics', () => {
  assert.equal(formatEmissions(999).unit, 'kg CO₂e');
  assert.deepEqual(formatEmissions(2500), { value: formatNumber(2.5), unit: 't CO₂e' });
  assert.equal(formatEmissions(undefined).value, '-');
  const merged = mergeMonthly({
    scope2: [{ timestamp: '2026-02-01T00:00:00Z', value: 5 }, { timestamp: '2026-01-01T00:00:00Z', value: 3 }],
    scope1: [{ timestamp: '2026-01-01T00:00:00Z', value: 2 }, { timestamp: '2026-01-15T00:00:00Z', value: 1 }],
  });
  assert.deepEqual(merged.map(({ key, scope1, scope2 }) => [key, scope1, scope2]), [['2026-01', 3, 3], ['2026-02', undefined, 5]]);
});
