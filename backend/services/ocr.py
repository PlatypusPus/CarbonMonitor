"""OCR extraction — parse activity data from uploaded documents."""

from __future__ import annotations

import csv
import re
from datetime import date, datetime
from io import BytesIO, StringIO
from typing import Iterable

UUID_PATTERN = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)
FLOAT_PATTERN = re.compile(r"[-+]?\d[\d,]*(?:\.\d+)?")
ACTIVITY_TYPES = ("electricity", "diesel", "petrol", "lpg")

HEADER_ALIASES: dict[str, tuple[str, ...]] = {
    "facility_id": ("facility id", "facility_id", "site id", "site_id", "facility"),
    "period_start": ("period start", "start date", "period_start", "start", "from"),
    "period_end": ("period end", "end date", "period_end", "end", "to"),
    "activity_type": ("activity type", "activity_type", "fuel type", "fuel", "metric", "activity"),
    "quantity": ("quantity", "amount", "usage", "value"),
    "unit": ("unit", "measurement", "uom"),
}
KNOWN_HEADERS = frozenset().union(*HEADER_ALIASES.values())
BINARY_EXTENSIONS = (".pdf", ".png", ".jpg", ".jpeg", ".webp", ".xlsx", ".xlsm", ".zip")


def _extract_pdf_text(file: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(BytesIO(file))
    text = "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    if text:
        return text

    try:
        import fitz
        import pytesseract
        from PIL import Image
    except Exception as exc:
        raise ValueError(
            "Scanned PDF OCR is unavailable: install pymupdf + pytesseract and ensure tesseract is installed"
        ) from exc

    doc = fitz.open(stream=file, filetype="pdf")
    parts: list[str] = []
    try:
        for page in doc:
            pix = page.get_pixmap(dpi=300, alpha=False)
            image = Image.open(BytesIO(pix.tobytes("png")))
            parts.append(pytesseract.image_to_string(image, config="--psm 6"))
    except Exception as exc:
        raise ValueError("Failed to OCR scanned PDF pages") from exc
    finally:
        doc.close()
    text = "\n".join(parts).strip()
    if not text:
        raise ValueError("PDF does not contain readable text")
    return text


def _extract_image_text(file: bytes) -> str:
    try:
        from PIL import Image
        import pytesseract
    except Exception as exc:
        raise ValueError("OCR image support is unavailable") from exc

    with Image.open(BytesIO(file)) as image:
        return pytesseract.image_to_string(image)


def _extract_text(file: bytes) -> str:
    if file.startswith(b"%PDF"):
        return _extract_pdf_text(file)

    try:
        return _extract_image_text(file)
    except Exception:
        return file.decode("utf-8", errors="ignore")


def _find_labeled_value(text: str, labels: Iterable[str]) -> str | None:
    for label in labels:
        pattern = rf"{label}\s*[:=]\s*(?P<value>.+)"
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            value = match.group("value").strip()
            if value:
                return value
    return None


def _parse_datetime(value: str) -> str:
    cleaned = value.strip()
    for candidate in (
        cleaned,
        cleaned.replace("Z", "+00:00"),
        cleaned.replace("/", "-"),
    ):
        try:
            return datetime.fromisoformat(candidate).isoformat()
        except ValueError:
            continue
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y %H:%M"):
        try:
            return datetime.strptime(cleaned, fmt).isoformat()
        except ValueError:
            continue
    raise ValueError(f"invalid datetime '{value}'")


def _parse_quantity(value: str) -> str:
    match = FLOAT_PATTERN.search(value.replace(",", ""))
    if match is None:
        raise ValueError(f"invalid quantity '{value}'")
    return match.group(0).replace(",", "")


def _pick_header(row: dict[str, str], aliases: tuple[str, ...]) -> str | None:
    for alias in aliases:
        value = row.get(alias)
        if value not in (None, ""):
            return value
    return None


def _extract_tabular(row: dict[str, str], facility_id: str | None = None) -> dict[str, str]:
    found_facility_id = _pick_header(row, HEADER_ALIASES["facility_id"])
    if found_facility_id is None:
        found_facility_id = facility_id
    if found_facility_id is None:
        raise ValueError("missing facility_id")

    period_start_raw = _pick_header(row, HEADER_ALIASES["period_start"])
    period_end_raw = _pick_header(row, HEADER_ALIASES["period_end"])
    if period_start_raw is None or period_end_raw is None:
        raise ValueError("missing period_start or period_end")

    activity_type = _pick_header(row, HEADER_ALIASES["activity_type"])
    if activity_type is None:
        raise ValueError("missing activity_type")
    activity_type = activity_type.strip().lower()
    if activity_type not in ACTIVITY_TYPES:
        raise ValueError(f"unsupported activity_type '{activity_type}'")

    quantity_raw = _pick_header(row, HEADER_ALIASES["quantity"])
    if quantity_raw is None:
        raise ValueError("missing quantity")
    quantity = _parse_quantity(quantity_raw)

    unit = _pick_header(row, HEADER_ALIASES["unit"])
    if unit is None:
        raise ValueError("missing unit")
    unit = unit.splitlines()[0].strip()

    return {
        "facility_id": found_facility_id,
        "period_start": _parse_datetime(period_start_raw),
        "period_end": _parse_datetime(period_end_raw),
        "activity_type": activity_type,
        "quantity": quantity,
        "unit": unit,
    }


def _build_records(rows: list[dict[str, str]], facility_id: str | None = None) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for index, row in enumerate(rows, start=2):
        try:
            records.append(_extract_tabular(row, facility_id))
        except ValueError as exc:
            raise ValueError(f"row {index}: {exc}") from exc
    return records


def _parse_csv_rows(text: str) -> list[dict[str, str]] | None:
    reader = csv.DictReader(StringIO(text))
    headers = {
        str(header).strip().lower()
        for header in (reader.fieldnames or [])
        if header is not None
    }
    if not headers or not headers & KNOWN_HEADERS:
        return None

    rows: list[dict[str, str]] = []
    for raw in reader:
        row = {
            str(key).strip().lower(): (value or "").strip()
            for key, value in raw.items()
        }
        if any(row.values()):
            rows.append(row)
    return rows or None


def _parse_excel_rows(file: bytes) -> list[dict[str, str]] | None:
    try:
        from openpyxl import load_workbook
    except ImportError as exc:
        raise ValueError("Excel support is unavailable: install openpyxl") from exc

    try:
        workbook = load_workbook(BytesIO(file), read_only=True, data_only=True)
        sheet = workbook.active
        raw_rows = [list(row) for row in sheet.iter_rows(values_only=True)]
        workbook.close()
    except Exception as exc:
        raise ValueError("Failed to read Excel workbook") from exc

    if not raw_rows:
        return None

    headers = [
        str(cell).strip().lower() if cell is not None else ""
        for cell in raw_rows[0]
    ]
    if not set(headers) & KNOWN_HEADERS:
        return None

    rows: list[dict[str, str]] = []
    for raw in raw_rows[1:]:
        row: dict[str, str] = {}
        for header, cell in zip(headers, raw):
            if cell is None or not header:
                continue
            if isinstance(cell, datetime):
                row[header] = cell.isoformat(sep="T")
            elif isinstance(cell, date):
                row[header] = cell.isoformat()
            else:
                row[header] = str(cell).strip()
        if any(row.values()):
            rows.append(row)
    return rows or None


def extract_activities_from_document(
    file: bytes,
    filename: str | None = None,
    facility_id: str | None = None,
) -> list[dict[str, str]]:
    """Extract one activity record per data row from an uploaded document.

    Supports tabular files (CSV/Excel — one record per data row) as well as the
    labelled-text bills parsed by :func:`extract_activity_from_document`.

    ``facility_id`` is the facility the caller selected in the UI: it is used
    for rows/documents that don't name one, so a bill without a facility label
    still stages instead of failing validation.
    """
    lower_name = (filename or "").lower()

    if lower_name.endswith((".xlsx", ".xlsm")) or file.startswith(b"PK\x03\x04"):
        rows = _parse_excel_rows(file)
        if rows is not None:
            return _build_records(rows, facility_id)

    if lower_name.endswith(".csv"):
        rows = _parse_csv_rows(file.decode("utf-8", errors="ignore"))
        if rows is not None:
            return _build_records(rows, facility_id)

    if not (file.startswith(b"%PDF") or lower_name.endswith(BINARY_EXTENSIONS)):
        rows = _parse_csv_rows(file.decode("utf-8", errors="ignore"))
        if rows is not None:
            return _build_records(rows, facility_id)

    return [_extract_single_from_document(file, facility_id)]


def _extract_single_from_document(
    file: bytes, facility_id: str | None = None
) -> dict[str, str]:
    text = _extract_text(file)
    normalised = "\n".join(line.strip() for line in text.splitlines() if line.strip())

    found_facility_id = _find_labeled_value(
        normalised, ("facility id", "facility_id", "site id", "site_id")
    )
    if found_facility_id is None:
        match = UUID_PATTERN.search(normalised)
        found_facility_id = match.group(0) if match else None
    if found_facility_id is None:
        found_facility_id = str(facility_id) if facility_id else None
    if found_facility_id is None:
        raise ValueError("missing facility_id")

    period_start_raw = _find_labeled_value(normalised, ("period start", "start date", "from"))
    period_end_raw = _find_labeled_value(normalised, ("period end", "end date", "to"))
    if period_start_raw is None or period_end_raw is None:
        raise ValueError("missing period_start or period_end")

    activity_type = _find_labeled_value(normalised, ("activity type", "fuel type", "metric"))
    if activity_type is None:
        for candidate in ACTIVITY_TYPES:
            if re.search(rf"\b{candidate}\b", normalised, flags=re.IGNORECASE):
                activity_type = candidate
                break
    if activity_type is None:
        raise ValueError("missing activity_type")
    activity_type = activity_type.strip().lower()
    if activity_type not in ACTIVITY_TYPES:
        raise ValueError(f"unsupported activity_type '{activity_type}'")

    quantity_raw = _find_labeled_value(normalised, ("quantity", "amount", "usage", "value"))
    if quantity_raw is None:
        raise ValueError("missing quantity")
    quantity = _parse_quantity(quantity_raw)

    unit = _find_labeled_value(normalised, ("unit", "measurement", "uom"))
    if unit is None:
        raise ValueError("missing unit")
    unit = unit.splitlines()[0].strip()

    return {
        "facility_id": found_facility_id,
        "period_start": _parse_datetime(period_start_raw),
        "period_end": _parse_datetime(period_end_raw),
        "activity_type": activity_type,
        "quantity": quantity,
        "unit": unit,
    }


def extract_activity_from_document(file: bytes) -> dict[str, str]:
    """Extract a single activity record (first record) from a document."""
    return extract_activities_from_document(file)[0]