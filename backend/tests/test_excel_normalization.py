"""Tests for the Excel electricity ingestion + normalization layer.

Uses the real ``electricity.xlsx`` fixture at the repository root plus synthetic
workbooks for edge cases. Existing OCR behavior is covered by ``test_ocr.py``;
here we also assert the Excel layer does not change how OCR treats the same
workbook bytes.
"""

from datetime import date, datetime, time
from io import BytesIO
from pathlib import Path
from uuid import UUID

import pytest
from openpyxl import Workbook

from schemas.activity_record import ActivityRecordCreate
from services.excel.detector import detect_electricity_workbook, has_electricity_columns
from services.excel.normalizer import (
    normalize_workbook,
    normalize_row,
    select_activity_quantity,
)
from services.excel.parser import ParsedExcelRow, ParsedWorkbook, parse_workbook
from services.ocr import extract_activities_from_document

REPO_ROOT = Path(__file__).resolve().parents[2]
ELECTRICITY_XLSX = REPO_ROOT / "electricity.xlsx"

FIXTURE_FACILITY = UUID("11111111-1111-4111-8111-111111111111")


def _electricity_bytes() -> bytes:
    return ELECTRICITY_XLSX.read_bytes()


def _build_workbook(rows: list[list]) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    for row in rows:
        sheet.append(row)
    buffer = BytesIO()
    workbook.save(buffer)
    workbook.close()
    return buffer.getvalue()


DEFAULT_HEADERS = ["Month", "Mescom Units", "Sol Units", "Ex Units", "Net Units", "Unit used", "Net Bill"]


def _row(*, row_number: int, values: list) -> ParsedExcelRow:
    headers = tuple(str(h).strip().lower() for h in DEFAULT_HEADERS)
    return ParsedExcelRow(
        row_number=row_number,
        headers=headers,
        raw_headers=tuple(DEFAULT_HEADERS),
        values=tuple(values),
    )


# --- Parser / real fixture -------------------------------------------------


def test_real_fixture_exists() -> None:
    assert ELECTRICITY_XLSX.exists(), "repo-root electricity.xlsx fixture missing"


def test_real_fixture_parses_with_provenance() -> None:
    parsed = parse_workbook(_electricity_bytes(), filename="electricity.xlsx")

    assert parsed.sheet_name == "MescomBill "
    assert "month" in parsed.headers
    assert "mescom units" in parsed.headers
    assert "Mescom Units" in parsed.raw_headers
    # Header row is row 1, so data rows must start at their original row 2.
    assert [row.row_number for row in parsed.rows] == list(range(2, 2 + len(parsed.rows)))
    assert parsed.rows, "expected data rows"


def test_real_fixture_normalizes_rows() -> None:
    records = normalize_workbook(parse_workbook(_electricity_bytes(), filename="electricity.xlsx"))

    assert len(records) == 14
    first = records[0]
    assert first.period_start == date(2025, 6, 1)
    assert first.period_end == date(2025, 6, 30)
    assert first.source_filename == "electricity.xlsx"
    assert first.source_row == 2
    assert first.grid_import_kwh == pytest.approx(69099.99999999968)

    last = records[-1]
    assert last.period_start == date(2026, 7, 1)
    assert last.period_end == date(2026, 7, 31)
    assert last.source_row == 15

    # Cross-field consistency on a row with solar + export: net = solar - export.
    assert first.net_grid_kwh == pytest.approx(first.solar_generation_kwh - first.grid_export_kwh)


def test_real_fixture_preserves_source_columns_and_raw_values() -> None:
    first = normalize_workbook(parse_workbook(_electricity_bytes(), filename="electricity.xlsx"))[0]

    assert first.source_columns["mescom units"] == "grid_import_kwh"
    assert first.source_columns["net bill"] == "bill_amount"
    assert "Mescom Units" in first.raw_values
    assert "Month" in first.raw_values


# --- Detector ---------------------------------------------------------------


def test_detector_recognizes_electricity_workbook() -> None:
    parsed = parse_workbook(_electricity_bytes(), filename="electricity.xlsx")
    assert detect_electricity_workbook(parsed)


def test_detector_recognizes_header_sets() -> None:
    assert has_electricity_columns({"month", "mescom units"})
    assert has_electricity_columns({"month", "unit used"})
    # Bare weak signals are not enough on their own.
    assert not has_electricity_columns({"units"})


def test_detector_rejects_non_electricity_workbook() -> None:
    payload = _build_workbook([["Employee", "Salary"], ["Alice", 1000]])
    parsed = parse_workbook(payload, filename="payroll.xlsx")
    assert not detect_electricity_workbook(parsed)


# --- Period handling --------------------------------------------------------


def test_month_maps_to_period_start_and_end() -> None:
    payload = _build_workbook(
        [
            ["Month"],
            [datetime(2024, 2, 1)],
            [datetime(2025, 12, 1)],
            [datetime(2026, 7, 1)],
        ]
    )
    records = normalize_workbook(parse_workbook(payload, filename="months.xlsx"))

    assert records[0].period_start == date(2024, 2, 1)
    assert records[0].period_end == date(2024, 2, 29)  # leap-year aware
    assert records[1].period_end == date(2025, 12, 31)
    assert records[2].period_end == date(2026, 7, 31)


def test_month_string_formats_accepted() -> None:
    payload = _build_workbook(
        [["Month"], ["2025-06-01"], ["Jun 2025"], ["01/07/2026"]]
    )
    records = normalize_workbook(parse_workbook(payload, filename="months.xlsx"))

    assert records[0].period_start == date(2025, 6, 1)
    assert records[1].period_start == date(2025, 6, 1)
    assert records[2].period_start == date(2026, 7, 1)
    assert records[2].period_end == date(2026, 7, 31)


# --- Numeric normalization --------------------------------------------------


def test_numeric_values_normalized() -> None:
    record = normalize_row(
        _row(
            row_number=7,
            values=[
                datetime(2025, 6, 1),
                "69,100.00",
                "₹19,359",
                " 210 ",
                "19,149.0",
                "88,249",
                "1,34,050",
            ],
        ),
        filename="data.xlsx",
    )

    assert record.grid_import_kwh == pytest.approx(69100.0)
    assert record.solar_generation_kwh == pytest.approx(19359.0)
    assert record.grid_export_kwh == pytest.approx(210.0)
    assert record.net_grid_kwh == pytest.approx(19149.0)
    assert record.unit_used_kwh == pytest.approx(88249.0)
    assert record.bill_amount == pytest.approx(134050.0)  # Indian grouping


def test_empty_and_null_cells_are_left_none() -> None:
    record = normalize_row(
        _row(
            row_number=8,
            values=[datetime(2025, 6, 1), None, "", 210, None, None, None],
        ),
        filename="data.xlsx",
    )

    assert record.grid_import_kwh is None
    assert record.solar_generation_kwh is None
    assert record.grid_export_kwh == pytest.approx(210.0)
    assert record.total_consumption_kwh is None
    assert record.unit_used_kwh is None
    assert record.bill_amount is None


def test_empty_rows_are_skipped_safely() -> None:
    payload = _build_workbook(
        [
            ["Month", "Mescom Units"],
            [datetime(2025, 6, 1), 100],
            [None, None],
            ["", None],
            [datetime(2025, 7, 1), 200],
        ]
    )
    parsed = parse_workbook(payload, filename="sparse.xlsx")
    records = normalize_workbook(parsed)

    assert [row.row_number for row in parsed.rows] == [2, 5]  # empty rows 3 & 4 dropped
    assert [record.period_start for record in records] == [date(2025, 6, 1), date(2025, 7, 1)]


# --- Row-level errors -------------------------------------------------------


def test_malformed_rows_raise_useful_row_errors() -> None:
    payload = _build_workbook(
        [
            ["Month", "Mescom Units"],
            [datetime(2025, 6, 1), 100],  # ok
            ["not-a-date", 100],  # bad Month
            [datetime(2025, 8, 1), "NaN"],  # bad numeric
        ]
    )
    parsed = parse_workbook(payload, filename="bad.xlsx")

    with pytest.raises(ValueError) as exc_info:
        normalize_workbook(parsed)
    message = str(exc_info.value)
    assert "row 3" in message and "invalid Month" in message
    assert "row 4" in message and "invalid numeric value" in message


def test_missing_month_is_a_row_error() -> None:
    payload = _build_workbook([["Mescom Units"], [100]])
    parsed = parse_workbook(payload, filename="nomonth.xlsx")
    with pytest.raises(ValueError) as exc_info:
        normalize_workbook(parsed)
    assert "row 2" in str(exc_info.value) and "missing Month" in str(exc_info.value)


# --- Quantity selection boundary --------------------------------------------


def test_select_activity_quantity_is_the_explicit_boundary() -> None:
    record = normalize_row(
        _row(
            row_number=9,
            values=[datetime(2025, 6, 1), 69100.0, 19359.0, 210.0, 19149.0, 88249.0, 722033.0],
        ),
        filename="data.xlsx",
    )

    quantity, unit, source_column = select_activity_quantity(record)

    # The boundary is provisional and documented; for now grid import wins and
    # every other quantity remains represented separately on the record.
    assert quantity == pytest.approx(69100.0)
    assert unit == "kWh"
    assert source_column == "mescom units"


def test_select_activity_quantity_without_grid_import_returns_none() -> None:
    record = normalize_row(
        _row(
            row_number=10,
            values=[datetime(2025, 6, 1), None, 19359.0, None, None, None, None],
        ),
        filename="data.xlsx",
    )
    quantity, _, _ = select_activity_quantity(record)
    assert quantity is None


# --- ActivityRecordCreate contract ------------------------------------------


def test_excel_payload_maps_to_activity_record_create() -> None:
    record = normalize_workbook(parse_workbook(_electricity_bytes(), filename="electricity.xlsx"))[0]
    quantity, unit, _ = select_activity_quantity(record)

    payload = ActivityRecordCreate.model_validate(
        {
            "facility_id": FIXTURE_FACILITY,
            "period_start": datetime.combine(record.period_start, time.min),
            "period_end": datetime.combine(record.period_end, time.min),
            "activity_type": "electricity",
            "quantity": quantity,
            "unit": unit,
            "source": "excel",
            "confirmed_by_user": False,
        }
    )

    assert payload.facility_id == FIXTURE_FACILITY  # supplied externally
    assert payload.activity_type == "electricity"
    assert payload.source == "excel"
    assert payload.quantity == pytest.approx(69099.99999999968)
    assert payload.confirmed_by_user is False  # drafts are never auto-confirmed


def test_excel_payload_still_enforces_validation() -> None:
    with pytest.raises(Exception) as exc_info:
        ActivityRecordCreate.model_validate(
            {
                "facility_id": FIXTURE_FACILITY,
                "period_start": datetime(2025, 6, 1, tzinfo=None),
                "period_end": datetime(2025, 6, 30),
                "activity_type": "coal",  # not a valid activity type
                "quantity": 100,
                "unit": "kWh",
                "source": "excel",
                "confirmed_by_user": False,
            }
        )
    assert "activity_type" in str(exc_info.value)


# --- OCR isolation ----------------------------------------------------------


def test_ocr_treatment_of_excel_bytes_is_unchanged() -> None:
    # The Excel layer must not leak into OCR: feeding the workbook to the OCR
    # extractor must still take the legacy path (no recognized tabular headers
    # -> single-document extraction -> missing facility_id).
    with pytest.raises(ValueError) as exc_info:
        extract_activities_from_document(_electricity_bytes(), "electricity.xlsx")
    assert "facility_id" in str(exc_info.value)


def test_parsed_workbook_repr() -> None:
    parsed = ParsedWorkbook(
        filename="x.xlsx",
        sheet_name="Sheet1",
        headers=("month",),
        raw_headers=("Month",),
        rows=[],
    )
    assert not parsed  # bool honours empty rows