"""Intermediate normalized electricity record.

This is the output of the Excel normalization layer and the shared "canonical
format" between OCR and Excel intake. It is NOT a database model and does NOT
replace ``ActivityRecordCreate`` — it is the structured intermediate that gets
mapped onto ``ActivityRecordCreate`` before the existing validation/draft flow.

Semantics
---------
Field meanings are only attached where they are established by the source
mapping in :mod:`services.excel.mappings`. Anything ambiguous is optional and
left ``None``. No field here is presumed to be the final carbon-accounting
quantity — see :func:`services.excel.normalizer.select_activity_quantity`.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict


class NormalizedElectricityRecord(BaseModel):
    """One normalized monthly electricity record from an Excel row.

    Provenance fields (``source_filename``, ``source_row``) are always present
    so every record can be traced back to its origin. ``source_columns`` maps
    original source column names to the normalized fields they fed;
    ``raw_values`` preserves the original cell values (display forms) keyed by
    original column name so no information is lost during normalization.
    """

    model_config = ConfigDict(extra="forbid")

    period_start: date
    period_end: date
    grid_import_kwh: float | None = None
    solar_generation_kwh: float | None = None
    grid_export_kwh: float | None = None
    net_grid_kwh: float | None = None
    lt_15a_kwh: float | None = None
    total_consumption_kwh: float | None = None
    unit_used_kwh: float | None = None
    bill_amount: float | None = None

    source_filename: str
    source_row: int
    source_columns: dict[str, str] = {}
    raw_values: dict[str, str] = {}