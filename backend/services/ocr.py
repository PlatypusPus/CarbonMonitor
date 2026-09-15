"""OCR extraction — parse activity data from uploaded documents."""

from __future__ import annotations

import re
from datetime import datetime
from io import BytesIO
from typing import Iterable

UUID_PATTERN = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)
FLOAT_PATTERN = re.compile(r"[-+]?\d[\d,]*(?:\.\d+)?")
ACTIVITY_TYPES = ("electricity", "diesel", "petrol", "lpg")


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


def extract_activity_from_document(file: bytes) -> dict[str, str]:
    text = _extract_text(file)
    normalised = "\n".join(line.strip() for line in text.splitlines() if line.strip())

    facility_id = _find_labeled_value(normalised, ("facility id", "facility_id", "site id", "site_id"))
    if facility_id is None:
        match = UUID_PATTERN.search(normalised)
        facility_id = match.group(0) if match else None
    if facility_id is None:
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
        "facility_id": facility_id,
        "period_start": _parse_datetime(period_start_raw),
        "period_end": _parse_datetime(period_end_raw),
        "activity_type": activity_type,
        "quantity": quantity,
        "unit": unit,
    }
