from datetime import datetime
from io import BytesIO

from pypdf import PdfReader
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from database import Base
from models.activity_record import ActivityRecord
from models.calculated_emission import CalculatedEmission
from models.emission_factor import EmissionFactor
from models.facility import Facility
from services.report import generate_esg_pdf


def test_report_totals_exclusions_and_safe_text():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        empty = PdfReader(BytesIO(generate_esg_pdf(db)))
        assert "No confirmed, calculated records" in empty.pages[0].extract_text()
        facility = Facility(name="Demo Facility 1 <North> & West\u2014wing")
        factor = EmissionFactor(activity_type="electricity", factor_value=0.82,
                                unit="kg CO2e / kWh", valid_from=datetime(2020, 1, 1))
        db.add_all([facility, factor])
        db.flush()
        for quantity, confirmed, calculated in [(100, True, True), (500, False, True), (80, True, False)]:
            record = ActivityRecord(facility_id=facility.id, activity_type="electricity",
                                    quantity=quantity, unit="kWh", source="excel",
                                    period_start=datetime(2025, 6, 1),
                                    period_end=datetime(2025, 6, 30), confirmed_by_user=confirmed)
            db.add(record)
            db.flush()
            if calculated:
                db.add(CalculatedEmission(activity_record_id=record.id, scope=2,
                                         co2e_kg=quantity*0.82, emission_factor_id=factor.id))
        db.commit()
        pdf = PdfReader(BytesIO(generate_esg_pdf(db)))
        text = "\n".join(page.extract_text() for page in pdf.pages)
        assert "82.00 kg CO2e (0.082 t CO2e)" in text
        assert "1 records across 1 facilities" in text
        assert "1 confirmed records without calculations" in text
        assert "<North> & West, wing" in text
        assert "independent physical sites" in text
        assert "\u2014" not in text
    engine.dispose()
