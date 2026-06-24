"""Rule engine — evaluate recommendation rules for a facility and period."""

import uuid

from models.recommendation import Recommendation


def evaluate_rules(facility_id: uuid.UUID, period_id: uuid.UUID) -> list[Recommendation]:
    """
    TODO: Evaluate all active rules against the facility's calculated emissions for the period.

    Planned rules (implement in order — do NOT hard-code thresholds here until values are agreed):

    1. scope2_dominance
       Trigger: Scope 2 emissions exceed X% of total emissions for the period.
       Message should suggest investigating electricity procurement or renewable energy options.
       TODO: agree threshold % with the product team.

    2. month_over_month_spike
       Trigger: Total co2e_kg for this period is more than Y% higher than the previous period.
       Message should flag the spike and name the top contributing activity_type.
       TODO: agree spike % and lookback window.

    3. anomaly_coincidence
       Trigger: A CalculatedEmission for this period aligns (within Z hours) with an existing
       Anomaly record for the same facility.
       Message should cross-reference the anomaly and suggest verifying the source reading.
       TODO: agree the time-window for "coincidence" and which anomaly severities qualify.

    Return an empty list if no rules fire — do not raise.
    Persist returned Recommendations via the router/service layer, not inside this function.
    """
    raise NotImplementedError
