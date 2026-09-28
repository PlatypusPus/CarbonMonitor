# College dataset

The active Docker presentation database contains the original `electricity.xlsx` supplied by the college. All 14 monthly records, June 2025 through July 2026, belong to one facility named College Campus. The former HQ and three demo facility partitions are no longer present as separate sites.

The original workbook remains unchanged. The importer reads saved numeric results from Mescom Units, totalling 1,116,257.5 units. The current application treats those units as kWh and applies the configured factor. This unit assumption and the seeded factor still require validation for external reporting.

## Import workflow

1. Select College Campus in Data Intake.
2. Choose the original workbook and review the preview.
3. Upload, then check the source filename, row, column, quantity, and period before confirmation.
4. Do not also import the three old split workbooks. That would count the same institute history twice.

The original data has already been imported. An identical re-upload to the same facility is skipped by the draft key.

## Scope 1

The college has not supplied fuel usage. The separate Scope 1 workbook is a clearly labelled synthetic example with the same monthly coverage and steady illustrative diesel consumption. Its quantities are not inferred from electricity and must not be reported as measured college activity. It is not imported into the college ledger.

The college report displays missing Scope 1 data as Not provided, not zero. Replace sample quantities with documented diesel, petrol, or LPG records before importing actual Scope 1 activity.

## Anomalies

No synthetic spikes or anomaly flags are included. Existing demo flags were removed. The detector has not been run against this import; no flags is not a certification that measurements are anomaly-free. The supplied values are preserved without smoothing.

Private workbooks and database backups remain outside Git.
