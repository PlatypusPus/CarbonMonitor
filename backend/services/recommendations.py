"""Rule engine — evaluate recommendation rules for a facility and period."""

import uuid
import json
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from models.recommendation import Recommendation
from models.calculated_emission import CalculatedEmission
from models.activity_record import ActivityRecord
from models.anomaly import Anomaly
from models.period import Period
from models.facility import Facility


def evaluate_rules(db: Session, facility_id: uuid.UUID, period_id: uuid.UUID) -> list[Recommendation]:
    period = db.get(Period, period_id)
    if not period:
        return []
        
    stmt = (
        select(CalculatedEmission, ActivityRecord)
        .join(ActivityRecord, CalculatedEmission.activity_record_id == ActivityRecord.id)
        .where(
            ActivityRecord.facility_id == facility_id,
            ActivityRecord.period_start >= period.start_date,
            ActivityRecord.period_end <= period.end_date
        )
    )
    current_emissions = db.execute(stmt).all()
    if not current_emissions:
        return []

    recs = []
    
    total_co2e = sum(calc.co2e_kg for calc, _ in current_emissions)
    scope2_co2e = sum(calc.co2e_kg for calc, _ in current_emissions if calc.scope == 2)
    if total_co2e > 0 and (scope2_co2e / total_co2e) > 0.5:
        recs.append(Recommendation(
            facility_id=facility_id,
            period_id=period_id,
            rule_id="TopEmitters",
            message="Scope 2 emissions exceed 50% of total emissions. Investigate electricity procurement or renewable energy options.",
            supporting_numbers=json.dumps({"total_co2e_kg": total_co2e, "scope2_co2e_kg": scope2_co2e})
        ))

    prev_stmt = select(Period).where(Period.end_date <= period.start_date).order_by(Period.end_date.desc()).limit(1)
    prev_period = db.execute(prev_stmt).scalar_one_or_none()
    if prev_period:
        prev_emissions_stmt = (
            select(func.sum(CalculatedEmission.co2e_kg))
            .join(ActivityRecord)
            .where(
                ActivityRecord.facility_id == facility_id,
                ActivityRecord.period_start >= prev_period.start_date,
                ActivityRecord.period_end <= prev_period.end_date
            )
        )
        prev_total = db.execute(prev_emissions_stmt).scalar() or 0.0
        if prev_total > 0 and ((total_co2e - prev_total) / prev_total) > 0.2:
            recs.append(Recommendation(
                facility_id=facility_id,
                period_id=period_id,
                rule_id="SpikeDetect",
                message=f"Total emissions spiked by over 20% compared to the previous period ({prev_period.name}).",
                supporting_numbers=json.dumps({"current_total": total_co2e, "previous_total": prev_total})
            ))
            
    fac = db.get(Facility, facility_id)
    if fac:
        anomalies_stmt = select(Anomaly).where(
            Anomaly.facility_name == fac.name,
            Anomaly.timestamp >= period.start_date,
            Anomaly.timestamp <= period.end_date
        )
        anomalies = db.execute(anomalies_stmt).scalars().all()
        if anomalies:
            recs.append(Recommendation(
                facility_id=facility_id,
                period_id=period_id,
                rule_id="AnomalyCoincidence",
                message=f"Found {len(anomalies)} anomalies during this period. Verify the source readings.",
                supporting_numbers=json.dumps({"anomaly_count": len(anomalies)})
            ))

    return recs
