"""Pure calculation layer — no DB calls allowed here."""

from models.activity_record import ActivityRecord
from models.calculated_emission import CalculatedEmission
from models.emission_factor import EmissionFactor

SCOPE_MAP = {"electricity": 2, "diesel": 1, "petrol": 1, "lpg": 1}


def calculate_emissions(
    activity_record: ActivityRecord,
    emission_factor: EmissionFactor,
) -> CalculatedEmission:
    """Multiply activity_record.quantity by emission_factor.factor_value to produce co2e_kg."""
    scope = SCOPE_MAP.get(activity_record.activity_type, 1)
    co2e_kg = activity_record.quantity * emission_factor.factor_value
    return CalculatedEmission(
        activity_record_id=activity_record.id,
        scope=scope,
        co2e_kg=co2e_kg,
        emission_factor_id=emission_factor.id,
    )
