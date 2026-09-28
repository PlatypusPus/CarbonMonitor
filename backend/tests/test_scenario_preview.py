from datetime import datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from database import Base
from models.activity_record import ActivityRecord
from models.calculated_emission import CalculatedEmission
from models.emission_factor import EmissionFactor
from models.facility import Facility
from models.scenario import Scenario
from routers.scenarios import preview_scenario
from schemas.scenario import ScenarioPreview


def test_preview_uses_record_factor_and_never_changes_ledger():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        facility = Facility(name="College")
        factor = EmissionFactor(activity_type="electricity", factor_value=0.82,
                                unit="kg CO2e / kWh", valid_from=datetime(2020, 1, 1))
        newer = EmissionFactor(activity_type="electricity", factor_value=0.5,
                               unit="kg CO2e / kWh", valid_from=datetime(2025, 1, 1))
        db.add_all([facility, factor, newer])
        db.flush()
        record = ActivityRecord(facility_id=facility.id, activity_type="electricity",
                                quantity=100, unit="kWh", source="excel", confirmed_by_user=True,
                                period_start=datetime(2026, 1, 1), period_end=datetime(2026, 1, 31))
        db.add(record)
        db.flush()
        emission = CalculatedEmission(activity_record_id=record.id, scope=2, co2e_kg=82,
                                      emission_factor_id=factor.id)
        db.add(emission)
        db.commit()
        user = SimpleNamespace(role=SimpleNamespace(name="admin"))
        for quantity, expected, savings in [(80, 65.6, 20), (0, 0, 100), (120, 98.4, -20)]:
            result = preview_scenario(ScenarioPreview(activity_record_id=record.id, quantity=quantity), db, user)
            assert result.projected_co2e_kg == pytest.approx(expected)
            assert result.savings_percent == pytest.approx(savings)
            assert result.factor_value == 0.82
        assert record.quantity == 100 and emission.co2e_kg == 82
        assert db.query(ActivityRecord).count() == db.query(CalculatedEmission).count() == 1
        assert db.query(Scenario).count() == 0
        outsider = SimpleNamespace(role=SimpleNamespace(name="facility_manager"), facility_id=uuid4())
        with pytest.raises(HTTPException) as error:
            preview_scenario(ScenarioPreview(activity_record_id=record.id, quantity=80), db, outsider)
        assert error.value.status_code == 403
        record.quantity = emission.co2e_kg = 0
        db.flush()
        assert preview_scenario(ScenarioPreview(activity_record_id=record.id, quantity=10), db, user).savings_percent is None
        record.confirmed_by_user = False
        db.flush()
        with pytest.raises(HTTPException) as error:
            preview_scenario(ScenarioPreview(activity_record_id=record.id, quantity=80), db, user)
        assert error.value.status_code == 400
    engine.dispose()


@pytest.mark.parametrize("quantity", [-1, float("nan"), float("inf")])
def test_invalid_scenario_quantity(quantity):
    with pytest.raises(ValueError):
        ScenarioPreview(activity_record_id=uuid4(), quantity=quantity)
