"""Small isolated regressions for calculation and intake correctness."""

from datetime import datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from database import Base
from models.activity_record import ActivityRecord
from models.calculated_emission import CalculatedEmission
from models.emission_factor import EmissionFactor
from models.facility import Facility
from models.period import Period
from routers.calculations import calculate_record
from routers.scenarios import run_scenario_endpoint
from schemas.activity_record import ActivityRecordCreate
from schemas.scenario import ScenarioCreate
from services.scenario import run_scenario
from services.uploads import parse_emissions_csv


def test_calculation_retry_regional_factor_and_scenario():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        start, end = datetime(2026, 1, 1), datetime(2026, 2, 1)
        facility = Facility(name="Regression", region_code="TEST")
        period = Period(name="Test month", start_date=start, end_date=end)
        db.add_all([facility, period])
        db.flush()
        for region, value, valid_from in [(None, 0.82, start), ("TEST", 0.1, start),
                                           ("TEST", 0.2, datetime(2026, 3, 1))]:
            db.add(EmissionFactor(activity_type="electricity", region=region,
                                  factor_value=value, unit="kg CO2e / kWh", valid_from=valid_from))
        record = ActivityRecord(facility_id=facility.id, activity_type="electricity",
                                quantity=100, unit="kWh", source="manual",
                                period_start=start, period_end=end, confirmed_by_user=True)
        db.add(record)
        db.commit()
        user = SimpleNamespace(id=uuid4(), role=SimpleNamespace(name="admin"))

        first = calculate_record(record.id, db, user)
        second = calculate_record(record.id, db, user)
        assert first.id == second.id
        assert db.scalars(select(CalculatedEmission)).all() == [first]
        assert first.co2e_kg == 10
        scenario = run_scenario_endpoint(ScenarioCreate(
            facility_id=facility.id, baseline_period_id=period.id,
            modified_inputs={"quantity": 50}), db, user)
        assert scenario.result_co2e_kg == 5
        assert str(record.id) in scenario.modified_inputs
        assert db.scalars(select(CalculatedEmission)).all() == [first]
        with pytest.raises(ValueError):
            run_scenario(db, {"activity_type": "electricity", "quantity": 1, "unit": "kWh"},
                         {"unit": "MWh"}, "TEST", end)
        record.confirmed_by_user = False
        db.commit()
        with pytest.raises(HTTPException) as exc:
            calculate_record(record.id, db, user)
        assert exc.value.status_code == 400
    engine.dispose()


@pytest.mark.parametrize("value,unit", [("-10", "kWh"), ("NaN", "kWh"),
                                       ("Infinity", "kWh"), ("1", "MWh")])
def test_invalid_csv_cannot_be_staged(value, unit):
    with pytest.raises(ValueError):
        parse_emissions_csv(f"timestamp,metric,value,unit\n2026-01-01,electricity,{value},{unit}\n".encode())


def test_fuel_defaults_and_manual_validation():
    rows = parse_emissions_csv(b" timestamp , metric , value \n2026-01-01,diesel,10\n2026-01-01,lpg,2\n")
    assert [row["unit"] for row in rows] == ["litre", "kg"]
    data = dict(facility_id=uuid4(), period_start="2026-01-01", period_end="2026-02-01",
                activity_type="electricity", quantity=100, unit="kWh", source="manual")
    assert ActivityRecordCreate(**data).quantity == 100
    for invalid in [{"quantity": -1}, {"quantity": float("nan")}, {"unit": "MWh"},
                    {"period_end": "2025-12-01"}, {"period_end": "2026-01-01"}]:
        with pytest.raises(ValueError):
            ActivityRecordCreate(**(data | invalid))
