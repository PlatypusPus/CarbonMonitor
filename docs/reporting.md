# Calculations and reporting

Confirmed activity is converted using `quantity x emission factor`. Results are stored in kg CO2e; divide by 1,000 for tonnes. Fuel combustion is Scope 1 and purchased electricity is Scope 2. Scope 3 is not implemented.

The resolver prefers a valid regional factor over a global factor, using the activity period end. Seeded factors are demonstration placeholders. Electricity imports currently use cached `Mescom Units` as kWh; the meter unit basis needs confirmation before external use. Solar generation and exports are not deducted.

## PDF contents

- Reporting coverage and generation time.
- Total, Scope 1, and Scope 2 emissions.
- Facility totals, record counts, individual date ranges, and percentage shares.
- Activity quantities, applied factors, and calculated emissions.
- Pending draft counts, missing calculations, methodology, and demo-data disclosures.

Only confirmed records with calculations contribute to totals. Totals are summed before display rounding. The report uses all available periods and is a presentation summary, not a complete BRSR submission or independently verified disclosure.

Anomaly detection requires at least 20 readings in each facility and activity group and an explicit API trigger. The college dataset has 14 monthly records, so the absence of flags does not demonstrate normality.

## What-if scenarios

Open **What-if Scenarios**, select a confirmed monthly record, and enter a proposed consumption or choose a reduction preset. The comparison uses that record's applied emission factor and shows the projected emissions and change. Scenarios are hypothetical previews: they do not save activity, change the college data, or contribute to report totals.

Authentication supports login, refresh, and logout. Managers' PDFs include only their assigned facility; administrators can export all facilities or select one in the workspace header. See [facilities and user access](access.md).
