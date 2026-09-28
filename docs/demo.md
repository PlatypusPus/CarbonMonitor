# Three-facility presentation

The three supplied workbooks contain real monthly data from one institute, divided into consecutive date ranges. For the presentation they are assigned to three demo facilities. This demonstrates facility separation, not three independent physical meter histories.

| Workbook | Facility | Coverage | Rows |
|---|---|---|---|
| electricity_facility_1 (1).xlsx | Demo Facility 1 | June to October 2025 | 5 |
| electricity_facility_2 (1).xlsx | Demo Facility 2 | November 2025 to March 2026 | 5 |
| electricity_facility_3 (1).xlsx | Demo Facility 3 | April to July 2026 | 4 |

## Import

1. Create the three facilities in Data Intake.
2. Select all three files. Choose a file in the queue and explicitly select its facility.
3. Check Month and Mescom Units in the preview. These are the date and quantity used for electricity calculations.
4. Upload the selected file. Review its drafts, including the source filename, row, column, and facility, then confirm each row.
5. Choose the next queued file and assign its facility. Repeat until all 14 rows are confirmed.

An identical re-upload to the same facility is skipped by the draft key. Assigning a file to another facility creates distinct records, so do not upload the original combined workbook as well.

## Formula preservation

The split workbooks contain cached numeric results and broken formula expressions, including bare `=` cells. The importer reads the saved values and does not run Excel formulas. Keep the original files unchanged. For future splits, export each partition as values-only from the original calculated workbook, or repair references in Excel before recalculating and saving. Do not replace missing values with zero.

The three facilities have different time coverage. Use the date ranges in the PDF when explaining totals. No inference about relative facility efficiency is supported by this split.

Private workbooks stay outside Git.
