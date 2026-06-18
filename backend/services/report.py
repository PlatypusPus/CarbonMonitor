"""Generate an ESG summary report as a PDF."""

from datetime import datetime, timezone
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from services.anomaly import query_anomalies
from services.emissions import query_summary

_BRAND = colors.HexColor("#2E9E6B")


def _fmt(value: object) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def _table(rows: list[list[str]]) -> Table:
    table = Table(rows, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), _BRAND),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F4F7F5")]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return table


def generate_esg_pdf() -> bytes:
    summary = query_summary()
    anomalies = query_anomalies(limit=50)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, title="CarbonTrace ESG Report")
    styles = getSampleStyleSheet()
    elements = [
        Paragraph("CarbonTrace ESG Report", styles["Title"]),
        Paragraph(f"Generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}", styles["Normal"]),
        Spacer(1, 0.6 * cm),
        Paragraph("Emission Summary", styles["Heading2"]),
    ]

    summary_rows = [["Metric", "Readings", "Average", "Latest", "Unit"]]
    for item in summary:
        summary_rows.append(
            [
                _fmt(item["metric"]),
                _fmt(item["count"]),
                _fmt(item["avg_value"]),
                _fmt(item["latest_value"]),
                _fmt(item.get("unit")),
            ]
        )
    if len(summary_rows) == 1:
        summary_rows.append(["No data available", "", "", "", ""])
    elements.append(_table(summary_rows))
    elements.append(Spacer(1, 0.6 * cm))

    elements.append(Paragraph(f"Detected Anomalies ({len(anomalies)})", styles["Heading2"]))
    if anomalies:
        rows = [["Timestamp", "Metric", "Facility", "Value", "Expected"]]
        for anomaly in anomalies[:25]:
            rows.append(
                [
                    _fmt(anomaly.get("timestamp")),
                    _fmt(anomaly.get("metric")),
                    _fmt(anomaly.get("facility_name")),
                    _fmt(anomaly.get("value")),
                    _fmt(anomaly.get("expected_value")),
                ]
            )
        elements.append(_table(rows))
    else:
        elements.append(Paragraph("No anomalies detected.", styles["Normal"]))

    doc.build(elements)
    return buffer.getvalue()
