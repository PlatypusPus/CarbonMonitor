from datetime import date
from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from PIL import Image, ImageDraw, ImageFont

from services.ocr import extract_activities_from_document, extract_activity_from_document


def test_extract_activity_from_document_parses_labelled_text() -> None:
    payload = b"""
    Facility ID: 11111111-1111-4111-8111-111111111111
    Period Start: 2026-07-01
    Period End: 2026-07-31
    Activity Type: electricity
    Quantity: 1245.5
    Unit: kWh
    """

    result = extract_activity_from_document(payload)

    assert result == {
        "facility_id": "11111111-1111-4111-8111-111111111111",
        "period_start": "2026-07-01T00:00:00",
        "period_end": "2026-07-31T00:00:00",
        "activity_type": "electricity",
        "quantity": "1245.5",
        "unit": "kWh",
    }


def test_extract_activity_from_document_requires_known_fields() -> None:
    payload = b"Facility ID: 11111111-1111-4111-8111-111111111111"

    try:
        extract_activity_from_document(payload)
    except ValueError as exc:
        assert "missing" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_extract_activity_from_document_parses_pdf_text() -> None:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.drawString(72, 720, "Facility ID: 11111111-1111-4111-8111-111111111111")
    pdf.drawString(72, 700, "Period Start: 2026-07-01")
    pdf.drawString(72, 680, "Period End: 2026-07-31")
    pdf.drawString(72, 660, "Activity Type: electricity")
    pdf.drawString(72, 640, "Quantity: 1245.5")
    pdf.drawString(72, 620, "Unit: kWh")
    pdf.showPage()
    pdf.save()

    result = extract_activity_from_document(buffer.getvalue())

    assert result["facility_id"] == "11111111-1111-4111-8111-111111111111"
    assert result["activity_type"] == "electricity"
    assert result["unit"] == "kWh"


def test_extract_activity_from_document_ocrs_scanned_pdf() -> None:
    font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 48)
    image = Image.new("RGB", (2550, 3300), "white")
    draw = ImageDraw.Draw(image)
    lines = [
        "Facility ID: 11111111-1111-4111-8111-111111111111",
        "Period Start: 2026-07-01",
        "Period End: 2026-07-31",
        "Activity Type: electricity",
        "Quantity: 1245.5",
        "Unit: kWh",
    ]
    for i, line in enumerate(lines):
        draw.text((120, 120 + i * 360), line, fill="black", font=font)

    img_buffer = BytesIO()
    image.save(img_buffer, format="PNG")
    img_buffer.seek(0)

    pdf_buffer = BytesIO()
    pdf = canvas.Canvas(pdf_buffer, pagesize=letter)
    pdf.drawImage(
        ImageReader(Image.open(img_buffer)),
        0,
        0,
        width=612,
        height=792,
        preserveAspectRatio=True,
        mask="auto",
    )
    pdf.showPage()
    pdf.save()

    result = extract_activity_from_document(pdf_buffer.getvalue())

    assert result["facility_id"] == "11111111-1111-4111-8111-111111111111"
    assert result["period_end"] == "2026-07-31T00:00:00"
    assert result["activity_type"] == "electricity"
    assert result["unit"] == "kWh"


def test_extract_activities_from_csv_builds_one_draft_per_row() -> None:
    payload = (
        b"facility_id,period_start,period_end,activity_type,quantity,unit\n"
        b"11111111-1111-4111-8111-111111111111,2026-07-01,2026-07-31,electricity,1245.5,kWh\n"
        b"22222222-2222-4222-8222-222222222222,2026-08-01,2026-08-31,diesel,50,litres\n"
    )

    result = extract_activities_from_document(payload, "bills.csv")

    assert len(result) == 2
    assert result[0] == {
        "facility_id": "11111111-1111-4111-8111-111111111111",
        "period_start": "2026-07-01T00:00:00",
        "period_end": "2026-07-31T00:00:00",
        "activity_type": "electricity",
        "quantity": "1245.5",
        "unit": "kWh",
    }
    assert result[1]["facility_id"] == "22222222-2222-4222-8222-222222222222"
    assert result[1]["activity_type"] == "diesel"
    assert result[1]["quantity"] == "50"


def test_extract_activities_from_csv_uses_header_aliases() -> None:
    payload = (
        b"Facility ID,Start,End,Fuel,Usage,UOM\n"
        b"11111111-1111-4111-8111-111111111111,01/07/2026,31/07/2026,petrol,200,L\n"
    )

    result = extract_activities_from_document(payload, "data.csv")

    assert result[0]["facility_id"] == "11111111-1111-4111-8111-111111111111"
    assert result[0]["period_start"] == "2026-07-01T00:00:00"
    assert result[0]["activity_type"] == "petrol"
    assert result[0]["quantity"] == "200"


def test_extract_activities_from_csv_reports_bad_rows() -> None:
    payload = (
        b"facility_id,period_start,period_end,activity_type,quantity,unit\n"
        b"11111111-1111-4111-8111-111111111111,2026-07-01,2026-07-31,electricity,1245.5,kWh\n"
        b",2026-08-01,2026-08-31,diesel,50,litres\n"
    )

    try:
        extract_activities_from_document(payload, "bills.csv")
    except ValueError as exc:
        assert "row 3" in str(exc) and "facility_id" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_extract_activities_from_excel() -> None:
    from openpyxl import Workbook

    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["facility_id", "period_start", "period_end", "activity_type", "quantity", "unit"])
    sheet.append(
        [
            "11111111-1111-4111-8111-111111111111",
            date(2026, 7, 1),
            date(2026, 7, 31),
            "electricity",
            1245.5,
            "kWh",
        ]
    )
    buffer = BytesIO()
    workbook.save(buffer)

    result = extract_activities_from_document(buffer.getvalue(), "bills.xlsx")

    assert len(result) == 1
    assert result[0]["facility_id"] == "11111111-1111-4111-8111-111111111111"
    assert result[0]["period_start"] == "2026-07-01T00:00:00"
    assert result[0]["period_end"] == "2026-07-31T00:00:00"
    assert result[0]["activity_type"] == "electricity"
    assert result[0]["quantity"] == "1245.5"
    assert result[0]["unit"] == "kWh"
