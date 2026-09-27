"""Source-specific column mappings for electricity workbooks.

Only columns whose semantic meaning is established get mapped — the current
MESCOM-style sheet has 43 columns and most are tariff/rate internals that are
deliberately ignored. Where a meaning is plausible but not finalized, that is
recorded in the concept notes and the field stays optional.

No mapping here decides which quantity is used for carbon accounting. That
decision is confined to :func:`services.excel.normalizer.select_activity_quantity`.
"""

from __future__ import annotations

from typing import NamedTuple


class Concept(NamedTuple):
    """A mapped source column: target normalized field, unit, and meaning notes."""

    field: str
    unit: str | None
    notes: str


# Keys are NORMALIZED column headers (lowercased, collapsed whitespace) as
# produced by services.excel.parser._normalize_header.
ELECTRICITY_COLUMN_MAPPINGS: dict[str, Concept] = {
    "month": Concept(
        field="period",
        unit=None,
        notes="Month-start date. period_start = that date, period_end = last day of the month.",
    ),
    "mescom units": Concept(
        field="grid_import_kwh",
        unit="kWh",
        notes="Units supplied/billed from the MESCOM grid (the metered import). "
        "kWh vs kVAh unit basis NOT confirmed — do not treat as finalized.",
    ),
    "sol units": Concept(
        field="solar_generation_kwh",
        unit="kWh",
        notes="Solar generation figure; gross-vs-net basis not confirmed.",
    ),
    "ex units": Concept(
        field="grid_export_kwh",
        unit="kWh",
        notes="Units exported to the grid.",
    ),
    "net units": Concept(
        field="net_grid_kwh",
        unit="kWh",
        notes="Observed to equal solar minus export on the sample sheet; semantics not "
        "officially documented.",
    ),
    "lt 15a": Concept(
        field="lt_15a_kwh",
        unit="kWh",
        notes="LT 15A tariff-category units; meaning not finalized.",
    ),
    "total units": Concept(
        field="total_consumption_kwh",
        unit="kWh",
        notes="Headline total on the sheet; exact basis (which flows it sums) not finalized.",
    ),
    "unit used": Concept(
        field="unit_used_kwh",
        unit="kWh",
        notes="Final consumption figure in the sheet; its relationship to grid imports "
        "(incl. solar self-use?) not finalized.",
    ),
    "net bill": Concept(
        field="bill_amount",
        unit="INR",
        notes="Final monetary total on the sheet (after charges/rebates).",
    ),
}

# Original (raw) column headers that feed each normalized field, keyed by the
# normalized field name — used to record which source columns provided the value.
MAPPED_FIELD_TO_HEADER: dict[str, str] = {
    concept.field: header for header, concept in ELECTRICITY_COLUMN_MAPPINGS.items()
}


def concept_for_header(header: str) -> Concept | None:
    return ELECTRICITY_COLUMN_MAPPINGS.get(header.strip().lower())