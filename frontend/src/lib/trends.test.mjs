import assert from 'node:assert/strict';
import { test } from 'node:test';
import { groupPeriods, formatNumber } from './trends.js';

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
