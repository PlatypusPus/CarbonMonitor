"""Pure calculation layer — no DB calls allowed here."""

from models.activity_record import ActivityRecord
from models.calculated_emission import CalculatedEmission
from models.emission_factor import EmissionFactor


def calculate_emissions(
    activity_record: ActivityRecord,
    emission_factor: EmissionFactor,
) -> CalculatedEmission:
    """
    TODO: Multiply activity_record.quantity by emission_factor.factor_value to produce co2e_kg.

    Rules:
    - scope must be derived from activity_type: electricity → scope 2, combustion fuels → scope 1.
      Define the mapping here once agreed.
    - This function MUST remain pure (no DB access). The scenario simulator calls it with
      hypothetical inputs that must never be persisted. Callers are responsible for saving
      the returned CalculatedEmission if needed.
    """
    raise NotImplementedError
