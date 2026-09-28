"""Synthetic electricity workbook; no private utility bill is needed for tests."""

from datetime import datetime
from io import BytesIO

from openpyxl import Workbook


def electricity_bytes() -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "MescomBill "
    # Keep Total Units in column T for the legacy upload adapter as well.
    sheet.append(["Month", "Mescom Units", "Sol Units", "Ex Units", "Net Units",
                  "Unit used", "Net Bill"] + [None] * 12 + ["Total Units"])
    for offset in range(14):
        year, month = divmod(2025 * 12 + 5 + offset, 12)
        sheet.append([datetime(year, month + 1, 1), 69100 + offset, 19359, 210,
                      19149, 88249 + offset, 722033] + [None] * 12 + [67970.5 + offset])
    buffer = BytesIO()
    workbook.save(buffer)
    workbook.close()
    return buffer.getvalue()
