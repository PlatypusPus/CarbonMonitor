# Live data verification

Checked the Docker PostgreSQL ledger against the original `electricity.xlsx` workbook on 29 September 2026. No college records were changed during this audit.

| Check | Result |
| --- | --- |
| Facility | College Campus |
| Confirmed electricity records | 14, June 2025 through July 2026 |
| Workbook reconciliation | All 14 quantities match the saved Mescom Units column |
| Electricity total | 1,116,257.50 kWh |
| Scope 2 emissions | 915,331.15 kg CO2e |
| Calculation | Every record equals quantity multiplied by its linked factor, 0.82 kg CO2e/kWh |
| Duplicate facility/type/period/quantity records | None |
| Missing calculations | None |
| Pending upload drafts | None |
| Scope 1 records | None, including diesel, petrol and LPG |

The generated synthetic diesel files have not been imported. They are demonstration data, not fuel records provided by the college. An empty Scope 1 ledger means data is missing, not that the college has zero fuel emissions.

## Subsequent approved demonstration import

After the audit, 14 generated diesel records were imported and confirmed in the separate **Fuel Demo** facility, covering June 2025 through July 2026. The total is 20,490 litres and 54,913.20 kg CO2e in Scope 1 using the configured demonstration factor of 2.68 kg CO2e/litre. Monthly API results reconcile to these totals. The source filename preserves the generated-data provenance. College Campus records were compared before and after the import and are unchanged. Select College Campus for real electricity records, or Fuel Demo for the illustrative fuel records; the administrator's All facilities view includes both.

The numerical reconciliation is against the saved Mescom Units values. The workbook also contains solar and net-unit columns, which are not substituted for purchased electricity. The configured emission factors are demonstration placeholders, so the calculation is internally consistent but is not an independently verified emissions inventory. Confirm the meter unit basis and applicable reporting-year factor before external reporting.

## Dashboard behavior

The From and Through controls filter reporting-period start dates in UTC, including both selected dates. They are shared between Overview and Trends. Overview's chart and activity list use the same activity type and date filter. Summary cards cover the selected dates; flagged-record counts are explicitly labelled as all dates.

Trends groups the monthly records into months, calendar quarters, or years. Monthly and quarterly charts have separate year panels using the same vertical scale. Totals retain their full precision internally; displayed values use two decimal places. Partial quarters and years include only the selected records and are not annualized. Choosing an unpopulated Scope 1 activity shows an empty chart instead of switching to electricity.

Verified against live PostgreSQL: selecting June 2025 returns one electricity record and one monthly chart point, both 56,662.00 kg CO2e. The summary count is also one. Regression tests cover inclusive date boundaries, empty ranges, reversed ranges and facility isolation.
