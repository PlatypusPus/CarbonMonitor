"""Natural-language scenarios: the AI proposes quantities, the app does the maths."""
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from database import Base
from models.activity_record import ActivityRecord
from models.calculated_emission import CalculatedEmission
from models.emission_factor import EmissionFactor
from models.facility import Facility
from routers.scenarios import ask_scenario
from schemas.scenario import ProposedChange, ScenarioAsk, ScenarioPlan
from services.scenario_ai import plan_scenario


def test_ask_calculates_ai_proposals_with_record_factor():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        facility = Facility(name="College")
        factor = EmissionFactor(activity_type="electricity", factor_value=0.82,
                                unit="kg CO2e / kWh", valid_from=datetime(2020, 1, 1))
        db.add_all([facility, factor])
        db.flush()
        record = ActivityRecord(facility_id=facility.id, activity_type="electricity", quantity=100, unit="kWh",
                                source="excel", confirmed_by_user=True,
                                period_start=datetime(2026, 1, 1), period_end=datetime(2026, 1, 31))
        db.add(record)
        db.flush()
        db.add(CalculatedEmission(activity_record_id=record.id, scope=2, co2e_kg=82, emission_factor_id=factor.id))
        db.commit()
        user = SimpleNamespace(role=SimpleNamespace(name="admin"))
        plan = ScenarioPlan(explanation="Cut electricity by 20%.", changes=[
            ProposedChange(record="r1", proposed_quantity=80, reason="20% less"),
            ProposedChange(record="r99", proposed_quantity=5, reason="made up"),
            ProposedChange(record="r1", proposed_quantity=-3, reason="negative")])
        with patch("routers.scenarios.list_activity_records", return_value=[record]), \
             patch("routers.scenarios.plan_scenario", return_value=plan) as ai:
            answer = ask_scenario(ScenarioAsk(prompt="what if we use 20% less power"), db, user)
        assert list(ai.call_args.args[1]) == ["r1"]
        assert len(answer.changes) == 1 and len(answer.skipped) == 2
        assert answer.projected_co2e_kg == pytest.approx(65.6)
        assert answer.savings_co2e_kg == pytest.approx(16.4)
        assert record.quantity == 100
    engine.dispose()


def test_plan_needs_api_key():
    with patch("services.scenario_ai.get_settings", return_value=SimpleNamespace(gemini_api_key="")):
        with pytest.raises(HTTPException) as error:
            plan_scenario("anything", {}, None)
    assert error.value.status_code == 503
