"""Read .xlsx workbooks into structured rows without altering original values.

The parser is deliberately low-level: it only reads cells and preserves
provenance (original row number, original column headers along with their
normalized forms). No electricity-specific interpretation happens here.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from io import BytesIO
from typing import Any

from openpyxl import load_workbook

_WS = re.compile(r"\s+")


def _normalize_header(value: Any) -> str:
    """Lowercase, strip, and collapse inner whitespace of a header cell."""
    if value is None:
        return ""
    return _WS.sub(" ", str(value).strip().lower())


@dataclass(frozen=True)
class ParsedExcelRow:
    """A single data row with its original row number and headers.

    ``headers`` are the normalized (lowercased, collapsed) column names used for
    lookups; ``raw_headers`` preserve the original header text for provenance.
    """

    row_number: int
    headers: tuple[str, ...]
    raw_headers: tuple[str, ...]
    values: tuple[Any, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            header: value
            for header, value in zip(self.headers, self.values)
            if header
        }

    @property
    def is_empty(self) -> bool:
        return all(
            value is None or (isinstance(value, str) and not value.strip())
            for value in self.values
        )


@dataclass(frozen=True)
class ParsedWorkbook:
    """A parsed workbook: normalized headers plus one row per data row."""

    filename: str
    sheet_name: str
    headers: tuple[str, ...]
    raw_headers: tuple[str, ...]
    rows: list[ParsedExcelRow]

    def __bool__(self) -> bool:
        return bool(self.rows)


def parse_workbook(
    file: bytes,
    *,
    filename: str,
    sheet_name: str | None = None,
) -> ParsedWorkbook:
    """Parse ``file`` (xlsx bytes) into :class:`ParsedWorkbook`.

    - The first non-empty sheet (or ``sheet_name`` if given) is read with
      ``data_only=True`` so formula results are used.
    - Row 1 is treated as the header row; data rows map back to their original
      (1-based) Excel row numbers.
    - Empty rows are skipped safely; values are never string-coerced here.
    """
    try:
        workbook = load_workbook(BytesIO(file), read_only=True, data_only=True)
    except Exception as exc:  # openpyxl raises a range of zipped/xml errors
        raise ValueError(f"{filename}: not a readable Excel workbook") from exc

    try:
        if sheet_name:
            sheet = workbook[sheet_name]
        else:
            # Find the first non-empty sheet (has at least one row with data)
            sheet = None
            for ws in workbook.worksheets:
                first_row = next(ws.iter_rows(values_only=True), None)
                if first_row and any(cell is not None and str(cell).strip() != "" for cell in first_row):
                    sheet = ws
                    break
            if sheet is None:
                # Fallback to active sheet if all sheets appear empty
                sheet = workbook.active
        raw_rows = [list(row) for row in sheet.iter_rows(values_only=True)]
        used_sheet = sheet
    except KeyError as exc:
        raise ValueError(f"{filename}: sheet '{sheet_name}' not found") from exc
    finally:
        workbook.close()

    if not raw_rows:
        raise ValueError(f"{filename}: workbook is empty")

    raw_headers = tuple(str(cell) if cell is not None else "" for cell in raw_rows[0])
    headers = tuple(_normalize_header(cell) for cell in raw_rows[0])

    rows: list[ParsedExcelRow] = []
    for index, cells in enumerate(raw_rows[1:], start=2):
        row = ParsedExcelRow(
            row_number=index,
            headers=headers,
            raw_headers=raw_headers,
            values=tuple(cells),
        )
        if not row.is_empty:
            rows.append(row)

    return ParsedWorkbook(
        filename=filename,
        sheet_name=used_sheet.title,
        headers=headers,
        raw_headers=raw_headers,
        rows=rows,
    )