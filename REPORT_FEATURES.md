# CarbonTrace — Features and Capabilities

This is the source of truth for the final report, "Automated Carbon Emission Monitoring and ESG Reporting System".

## Instructions for the editor (Prism)

1. Use this document as the authoritative description of the system. Where the report differs from it (pages, routes, roles, technologies, data sources, features), rewrite the report to match.
2. Add Section B as a chapter called "Features and Capabilities" after the Implementation chapter, or merge it into the Backend and Frontend Implementation sections.
3. Use Section C for System Testing and Results and Discussion.
4. This is the final report. Remove any "Future Work", "Future Enhancements" or "planned" content. Describe only what the system does. The conclusion should summarise what was built and achieved.
5. Describe the system only in its final form. Don't mention earlier versions, earlier designs, removed features, or other repositories or reports.
6. Only describe the technologies listed in Section A.3 as part of the system. Technologies discussed in the Literature Survey (IoT, MQTT, ELK, digital twins) stay there as background research only.
7. Anything marked **[FILL IN]** needs the team's input. Leave a visible placeholder. Don't invent numbers.
8. Use formal academic English in the first person plural ("we") throughout. Name the system "CarbonTrace".

---

## Section A — System overview

### A.1 Summary

CarbonTrace is a multi-tenant web application. Organizations use it to:

- import electricity and fuel activity data from spreadsheets, CSV files, PDFs and images;
- review every value before it is accepted;
- calculate Scope 1 and Scope 2 emissions with traceable emission factors;
- analyse trends;
- flag anomalies;
- run what-if reduction scenarios;
- export an ESG emissions report as a PDF.

### A.2 Architecture

| Layer | Implementation |
|---|---|
| Presentation | React 18 single-page app (Vite, React Router, TanStack Query, Axios, Tailwind CSS, Recharts, Lucide icons) |
| Application | FastAPI REST API under `/api`, organised as routers (HTTP), services (business logic) and schemas (Pydantic validation) |
| Data | PostgreSQL 16 through SQLAlchemy 2.0 |
| Infrastructure | Docker Compose: PostgreSQL, backend, Mailpit (email), and an optional packaged frontend behind an Nginx reverse proxy |

Data flow: **file → preview and validation → draft → human confirmation → activity record → calculated emission → dashboard, trends, anomalies and PDF report**

### A.3 Technology stack

| Area | Technologies |
|---|---|
| Backend | Python 3, FastAPI, Uvicorn, Pydantic v2, pydantic-settings, SQLAlchemy 2.0, psycopg 3 |
| Authentication | JWT (python-jose), Passlib with bcrypt, HTTP-only refresh-token cookies |
| Data intake | openpyxl (Excel), pytesseract with Tesseract OCR, PyMuPDF and pypdf (PDF) |
| Analytics | scikit-learn (Isolation Forest), NumPy |
| Reporting | ReportLab (PDF generation) |
| Email | Python SMTP client; Mailpit for local capture; any SMTP provider (STARTTLS or SSL) in production |
| Frontend | React 18, Vite 5, React Router 6, TanStack Query 5, Axios, Tailwind CSS, Recharts, Lucide |
| Database | PostgreSQL 16 |
| Tooling | uv (Python packages), npm, Ruff (lint), pytest, Node test runner, Git, GitHub Actions CI |
| Deployment | Docker, Docker Compose, Nginx |

### A.4 Data model (12 entities)

| Entity | Purpose |
|---|---|
| Organization | Tenant boundary. Every user and facility belongs to one organization. |
| EmailToken | Single-use email-verification and invitation tokens with expiry. |
| User | Account: name, email, hashed password, role, organization, assigned facility. |
| Role | admin, facility_manager, auditor. |
| UserSession | Refresh-token sessions, stored as hashes and revocable. |
| Facility | Site: name, location, region code, coordinates, facility type. |
| Upload | Uploaded file metadata: who uploaded it, when, for which facility, status, row count. |
| OCRDraft | A staged value from any intake source, waiting for review. Keeps the source file, row and column, and has a unique key to block duplicates. |
| ActivityRecord | Confirmed activity: facility, type (electricity, diesel, petrol, LPG), quantity, unit, period, source. |
| EmissionFactor | Factor by activity type, region, unit and validity period. |
| CalculatedEmission | kg CO2e and scope, linked to its activity record and to the exact factor used. |
| Anomaly | An Isolation Forest flag with score and expected value, linked to a calculated emission. |

---

## Section B — Features and capabilities

### B.1 Accounts, organizations and access control

- **Sign-up with email verification.** Users enter name, email, organization name and a password of at least 10 characters. Sign-up creates a private organization with one empty facility. Verification links expire after 24 hours and work once. Verification email can be re-sent. If email delivery fails, the new account is rolled back so the user can try again.
- **Secure login.** A short-lived JWT access token is held in browser memory, not localStorage. A refresh token is set as an HTTP-only cookie and stored only as a hash. Refresh tokens rotate on every refresh. Logout revokes the session. When a request gets a 401 response, the frontend refreshes the token once and retries the request.
- **Multi-tenant isolation.** Organizations can't see each other's data. The backend enforces this for facilities, intake, dashboards, trends, scenarios, calculations, anomalies and reports.
- **Role-based access.**
  - Administrators manage facilities and users in their organization and can view all facilities or one at a time.
  - Facility managers upload, confirm drafts and view reports only for their assigned facility.
  - Several managers can share a facility.
- **Invitations.** An administrator invites a user by email to a specific facility. The invitation expires after 7 days and works once. It stops working if the issuing administrator leaves, is disabled, or loses admin rights. Accepting it moves the account into the inviting organization as a facility manager.
- **Account self-service.**
  - The account page shows name, organization, role, join date, last sign-in, upload count and active sessions.
  - Users can change their password, which revokes every session.
  - Users can delete their account. This requires the password and typing `DELETE`. The profile is anonymized and the organization keeps its records.
  - A sole administrator must hand over the admin role before leaving.
- **Safety rules.**
  - An administrator cannot disable or demote their own account.
  - Permission changes invalidate the affected user's sessions.
  - In production, startup refuses the default JWT secret and requires an HTTPS public URL and TLS mail delivery.
- **Administrator bootstrap.** A command-line script (`create_admin.py`) creates an administrator with an organization and an empty facility.

### B.2 Facility management

- Create, edit and delete facilities: name, location, region code, coordinates, facility type.
- Assign one or more facility managers to each facility.
- A facility that still has records can't be deleted. The API returns a clear conflict error (HTTP 409) and no data is lost.
- The workspace header has a facility selector. Administrators can choose "All facilities" or a single facility.

### B.3 Multi-source data intake with human review

Every source follows the same lifecycle. **Nothing affects totals until a person confirms it.**

| Source | How it works |
|---|---|
| Excel (.xlsx) electricity workbooks | Rule-based detection of utility (MESCOM-style) workbooks from their column headers: Month, Mescom Units, Sol Units, Ex Units, Net Units, Total Units and others. Each column maps to a normalized field with its unit and notes. The source row and column are kept for every value. |
| CSV and generic spreadsheets | Activity rows (timestamp, activity type, value, optional unit and facility) are parsed and validated. Generic .xlsx files are converted to CSV first. Default units are applied for fuels: litres for diesel and petrol, kg for LPG. |
| PDF bills and images (OCR) | Tesseract OCR for PNG, JPG and WEBP images; PDF text extraction and rendering. Header aliases are matched for facility, period start and end, activity type, quantity and unit. Limits: 10 MB per file, 5 PDF pages, about 4 megapixels, 30-second timeout. |
| API entry | Authorized users can create, update and delete activity records through the REST API. |

- **Validation.** Negative, NaN or infinite quantities and unsupported units are rejected. Each period must have consistent timezone information.
- **Preview before staging.** The preview endpoint shows parsed rows and validation errors before anything is saved.
- **Duplicate protection.** Every draft has a unique key, so uploading the same file again for the same facility is skipped instead of double-counted.
- **Draft review.** Each draft shows the source filename, row, column, quantity and period. A reviewer confirms it (it becomes an activity record and its emission is calculated) or discards it.
- **Provenance.** Every record keeps the upload, the uploader, the time, the source type and the facility.

### B.4 Emission calculation

- Formula: **CO2e (kg) = activity quantity × emission factor**. Values are shown in tonnes when large.
- **Scopes.** Purchased electricity is Scope 2. Fuel combustion (diesel, petrol, LPG) is Scope 1.
- **Factor resolution.** The factor is chosen by activity type and validity period, using the period end date. A regional factor matching the facility's region is preferred over a global one.
- **Traceability.** Every result stores links to its activity record and to the exact factor used, so any figure can be traced back to its source.
- **Idempotent.** Calculating a record again returns the existing result instead of creating a duplicate.
- **Configured factors:**

| Activity | Factor |
|---|---|
| Electricity | 0.82 kg CO2e/kWh |
| Diesel | 2.68 kg CO2e/litre |
| Petrol | 2.31 kg CO2e/litre |
| LPG | 2.94 kg CO2e/kg |

### B.5 Overview dashboard

- Summary cards for the selected date range: total, Scope 1 and Scope 2 emissions, and record counts.
- A monthly emissions-by-scope chart.
- A list of recent confirmed records.
- "From" and "Through" date filters: inclusive, in UTC, and shared with the Trends page.
- An activity-type filter that applies to both the chart and the record list.
- Data refreshes periodically, so new confirmations appear without reloading the page.

### B.6 Trends and analytics

- Group monthly records by month, calendar quarter or year.
- Monthly and quarterly views are split into one panel per year, all on the same vertical scale, so years can be compared directly.
- Totals keep full precision internally and display with two decimal places. Units switch to tonnes for large values.
- Partial quarters and years show only the selected records and are not annualized.
- Activity types with no data show an empty chart.

### B.7 Anomaly detection

- An Isolation Forest (scikit-learn) model is trained separately for each facility and activity type. Each group needs at least 20 readings. Contamination is 6% and the random seed is fixed, so results are reproducible.
- Only confirmed records are analysed.
- Flags are stored with an anomaly score and an expected value. A record is never flagged twice.
- Detection is started through the API (`POST /api/anomalies/run`) by administrators or facility managers.
- The Anomaly review page lists the flags: date, activity, facility, value, expected value and score.

### B.8 What-if scenarios

- Select a confirmed record and enter a proposed consumption, or choose a reduction preset (for example 10%, 20% or 30% less).
- The page shows baseline emissions, projected emissions, the absolute change and the percentage change, using the record's own emission factor and scope.
- Scenarios are previews only. They never change activity records, calculated emissions or report totals.

### B.9 ESG PDF report

Generated with ReportLab and downloaded from the Emissions report page (`GET /api/reports/esg`). Administrators can export all facilities or one. Facility managers get only their own facility.

The report contains:

- reporting coverage and generation time;
- total, Scope 1 and Scope 2 emissions;
- facility totals, record counts, date ranges and percentage shares;
- activity quantities, applied emission factors and calculated emissions;
- data-quality notes: pending draft counts and missing calculations;
- methodology and data disclosures. Missing Scope 1 data is shown as "Not provided", not zero.

Totals are summed before rounding. If there is no data, the report is still a valid PDF with an empty-state message.

### B.10 User interface

| Page | Route | Purpose |
|---|---|---|
| Landing | `/` | Product overview and FAQ |
| Sign in / Create account | `/login`, `/signup` | Authentication |
| Email verification / Join organization | `/verify-email`, `/join-organization` | Account links from email |
| Onboarding | `/onboarding` | First-run setup for each user |
| Overview | `/dashboard` | Summary cards, scope chart, recent records |
| Data intake | `/upload` | Upload, preview, review and confirm drafts |
| Trends & analytics | `/trends` | Month, quarter and year trends |
| What-if scenarios | `/scenarios` | Reduction previews |
| Anomaly review | `/anomalies` | Flagged records |
| Emissions report | `/esg-report` | PDF download |
| Your account | `/profile` | Profile, password, sessions, invitations, deletion |
| Facilities & users / My facility | `/administration` | Facility and user management (admin); facility details (manager) |

Other interface features:

- Protected routes send signed-out users to the login page.
- The layout is responsive: on mobile, the sidebar becomes a horizontal tab bar.
- Every data page has loading, empty and error states, and an error boundary catches failures.
- The typeface is Public Sans, with a text wordmark.

### B.11 Deployment and operations

- **Docker Compose services:**
  - `postgres` (16-alpine, with a `pg_isready` health check and a persistent volume);
  - `backend` (FastAPI on Uvicorn, with Tesseract and Poppler installed; starts once PostgreSQL is healthy);
  - `mailpit` (local email capture on port 8025);
  - `frontend` and `nginx` (optional `web` profile: the static build behind a reverse proxy on port 80).
- **Configuration** comes from environment variables (`.env`) through Pydantic settings: database, JWT, CORS, public URL and SMTP.
- **Database initialization at startup:**
  - creates the tables;
  - applies idempotent schema updates;
  - seeds roles and emission factors;
  - holds a PostgreSQL advisory lock so that several workers never initialize at the same time.
- A `/health` endpoint for container checks.
- `run_backfill.py`: an idempotent maintenance script that fills in missing calculations and upload metadata.

### B.12 REST API summary

| Group | Endpoints |
|---|---|
| `/api/auth` | login, refresh, logout, me |
| `/api/account` | signup, resend-verification, verify-email, profile (get, update, delete), password, invitations, invitations/preview, join |
| `/api/users` | list, create, update (admin) |
| `/api/facilities` | list, get, create, update, delete |
| `/api/upload` | preview, upload (CSV/XLSX → drafts) |
| `/api/activity` | list, get, create, update, delete, drafts, ocr, excel, confirm draft, discard draft |
| `/api/calculations` | calculate one record, list |
| `/api/emissions` | latest, timeseries, summary |
| `/api/anomalies` | list, run |
| `/api/scenarios` | preview |
| `/api/reports` | esg (PDF) |

### B.13 Methodology and reporting boundary

State these in the methodology or results discussion. They describe the boundary of the final system.

- Scope 1 (fuel combustion) and Scope 2 (purchased electricity) are covered. Scope 3 is outside the scope of the project.
- The emission factors in B.4 are the values configured for this project. Organizations replace them with their approved factors (for example, the CEA grid emission factor) before external disclosure.
- Electricity quantities from utility workbooks use the billed "Mescom Units" column as kWh. Solar generation and grid exports are recorded but not deducted from purchased electricity.
- The PDF is an internal ESG emissions summary. It is not a regulatory filing (such as BRSR) or an independently assured disclosure.

---

## Section C — Testing and results

### C.1 Automated testing

| Suite | Count | Coverage |
|---|---|---|
| Backend (pytest) | 60 tests, all passing | Account verification, invitations, organization isolation, session revocation, account deletion, expired links, mail-failure rollback; facility isolation and admin user lifecycle; calculation regressions (idempotent calculation, regional factor selection, input validation); Excel detection and normalization; end-to-end Excel import; OCR parsing of text, images and PDFs; the full upload → draft → confirm → dashboard flow; PDF report contents; scenario previews |
| Frontend (Node test runner) | 3 tests, all passing | Onboarding state storage; trend grouping, totals across year boundaries, tonne conversion |
| Static checks | — | Ruff lint, backend import check, Vite production build |

Test environment:

- 16 backend tests run against a dedicated PostgreSQL test database. Its name must end in `_e2e`, so tests can never touch real data. The rest run on in-memory SQLite.
- Synthetic workbooks and bills are generated in memory, so no private data is needed.
- GitHub Actions runs lint, the import check, the backend tests and the frontend build on every push and pull request.

**[FILL IN: a manual test-case table (ID, description, steps, expected result, actual result, pass/fail), if the report template requires one.]**

### C.2 Data verification results

Audit of the deployed PostgreSQL ledger against the college's electricity workbook (29 September 2026):

| Check | Result |
|---|---|
| Facility | College Campus |
| Confirmed electricity records | 14 (June 2025 – July 2026) |
| Workbook reconciliation | All 14 quantities match the "Mescom Units" column |
| Electricity total | 1,116,257.50 kWh |
| Scope 2 emissions | 915,331.15 kg CO2e (0.82 kg CO2e/kWh) |
| Calculation check | Every record equals quantity × its linked factor |
| Duplicates, missing calculations, pending drafts | None |

To demonstrate Scope 1, a separate "Fuel Demo" facility holds 14 synthetic diesel records for the same months: 20,490 litres and 54,913.20 kg CO2e. Label it as illustrative data, not measured college activity.

Dashboard check: selecting June 2025 returns one electricity record and one chart point, both 56,662.00 kg CO2e.

**[FILL IN: screenshots of the Landing, Overview, Data intake (draft review), Trends, What-if scenarios, Anomaly review, Administration pages and a page of the generated PDF.]**

**[FILL IN: measured response times for the dashboard endpoints and PDF generation, if the report states performance figures.]**
