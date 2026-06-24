"""Scenario simulator — what-if emission calculations that never touch real data tables."""


def run_scenario(baseline_activity: dict, modified_inputs: dict) -> dict:
    """
    TODO: Merge modified_inputs over baseline_activity to produce a hypothetical ActivityRecord,
    then call services.calculation.calculate_emissions() with it to get a projected co2e_kg.

    IMPORTANT constraints:
    - This function calls calculation.calculate_emissions() but MUST NOT persist anything to
      activity_records or calculated_emissions tables. Scenario results go only to scenarios table.
    - baseline_activity should be a dict representation of an ActivityRecord (not an ORM object)
      so this stays easy to unit-test without a DB.
    - modified_inputs keys must be a subset of ActivityRecord fields; reject unknown keys.
      TODO: decide which fields are overridable (quantity? activity_type? period?) and validate here.

    Returns a dict with at minimum: {"result_co2e_kg": float, "scope": int, "inputs_used": dict}
    """
    raise NotImplementedError
