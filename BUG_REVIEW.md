# Integration and bug review — 28 September 2026

Pulled `origin/main` through `935f555`, restored local work from a recovery stash, and resolved four frontend conflicts on `main`.

## Selected implementation

- Retained upstream's CSV/Excel/OCR intake, draft review, confirmation gate, shared factor lookup, and error boundary.
- Integrated the local landing page, onboarding, dashboard route, and mobile navigation. Preserved the local removal of Cross Verify.
- Replaced the unavailable manual-entry onboarding choice with an existing-data review option.

## Fixes verified

- Intake fetches `/activity/drafts`, handles Excel's array response correctly, and refreshes emissions after confirmation.
- Removed five identical duplicate backend function definitions and duplicate registered intake routes.
- Repeated calculation requests reuse an existing result and reject unconfirmed activities.
- Manual and scenario calculations use the same region/date factor resolver as draft confirmation.
- CSV/manual/scenario validation rejects negative/nonfinite quantities and incorrect units. Fuel CSV defaults use litres or kilograms. Manual records reject invalid date ranges.
- Scenario inputs serialize their baseline UUID correctly.
- Historical chart labels include dates, and latest readings are selected by activity time rather than calculation time.
- Query failures have explicit error states. Report copy describes the implemented summary rather than claiming BRSR readiness.
- Logout clears the refresh cookie, and account changes clear cached queries.
- Missing private Excel fixtures were replaced with a deterministic synthetic workbook.

## Checks

- Backend Ruff passed.
- 50 backend tests passed with no skips against a separate PostgreSQL database, including CSV/Excel/OCR lifecycle tests and all four time-bucket intervals.
- Frontend production build and onboarding test passed.
- Browser smoke test: sign-in, onboarding, draft listing, and confirmation into the overview worked with isolated synthetic data.
- Authenticated PDF export returned HTTP 200 with a valid PDF payload. Browser review also caught and fixed clipped chart axis labels.
- Runtime warnings: Vite's large-bundle advisory and the upstream Starlette/httpx deprecation warning.
- The original bug-reproduction script asserted broken behavior and referenced the superseded upload service. Its useful cases now live in `backend/tests/test_calculation_regressions.py`; `run_audit.ps1` runs the current checks.

Run `./run_audit.ps1 -TestDatabaseUrl 'postgresql+psycopg://USER:PASSWORD@HOST:PORT/carbontrace_e2e'` from PowerShell. Tests require an isolated database name ending in `_e2e`; the E2E suite deletes its own test data. If that database is unavailable, PostgreSQL tests are skipped, so a green unit-only run is not a full integration pass.

## Remaining presentation limits

- Default emission factors remain marked as placeholders; the Excel grid-import selection is explicitly a provisional business rule.
- Anomaly detection requires an explicit API trigger and at least 20 samples per metric/facility; a three-row seed cannot demonstrate it.
- The PDF remains an emissions summary rather than a complete compliance report.
- Authentication received basic checks only. Facility-wide reporting access was not redesigned.
- Tests used a fresh isolated database. Legacy database migration/backfill behavior and existing production data were not changed or certified.
- The deployment was not rebuilt or pushed. Use the integrated branch for the next deployment; an older Docker build can still show the old interface.

The original tracked and untracked work remains recoverable in the pre-integration stash. Generated Graphify data is preserved locally and ignored. The empty root npm lockfile was removed because the Node project and its real lockfile live under `frontend/`.
