from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from PIL import Image, ImageDraw, ImageFont

from services.ocr import extract_activity_from_document


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
