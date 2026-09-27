"""Deterministic detection of electricity spreadsheets.

No ML/LLM is used: detection is a simple keyword pass over the normalized
column headers (and, as a secondary signal, the filename). It only needs to
be good enough to say "this looks like an electricity workbook" before the
mapping layer decides which columns are meaningful.
"""

from __future__ import annotations

from services.excel.parser import ParsedWorkbook

# Strong, electricity-specific signals found verbatim in the current MESCOM-style sheet.
ELECTRICITY_SIGNAL_HEADERS: frozenset[str] = frozenset(
    {
        "month",
        "mescom units",
        "sol op",
        "sol clg",
        "sol units",
        "ex op",
        "ex clg",
        "ex units",
        "power chages",
        "fac charges",
        "load rate",
    }
)

# Weaker signals that are common in energy registers; combined they confirm electricity.
ELECTRICITY_HINT_HEADERS: frozenset[str] = frozenset(
    {
        "opening",
        "closing",
        "diff",
        "units",
        "net units",
        "total units",
        "unit used",
        "reading",
        "kwh",
    }
)

ELECTRICITY_FILENAME_HINTS: tuple[str, ...] = ("electric", "mescom", "kseb", "energy")


def has_electricity_columns(headers: set[str]) -> bool:
    """Return whether a header set looks like an electricity register.

    - A single strong signal is enough (e.g. ``month`` + ``mescom units``).
    - Otherwise at least two weak signals are required so bare ``units`` is
      never enough on its own.
    """
    strong = headers & ELECTRICITY_SIGNAL_HEADERS
    if strong:
        return True
    return len(headers & ELECTRICITY_HINT_HEADERS) >= 2


def detect_electricity_workbook(parsed: ParsedWorkbook) -> bool:
    """Detect whether a parsed workbook is electricity data."""
    headers = {header for header in parsed.headers if header}
    if has_electricity_columns(headers):
        return True

    lower_name = parsed.filename.lower()
    return any(hint in lower_name for hint in ELECTRICITY_FILENAME_HINTS)