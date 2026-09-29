"""Real HTTP authorization checks with an isolated in-memory ledger."""

from datetime import datetime
from io import BytesIO
from unittest.mock import patch

from fastapi.testclient import TestClient
from pypdf import PdfReader
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app
from models.activity_record import ActivityRecord
from models.calculated_emission import CalculatedEmission
from models.emission_factor import EmissionFactor
from models.facility import Facility
from models.ocr_draft import OCRDraft
from models.role import Role
from models.user import User
from security import create_access_token, hash_password


def test_facility_isolation_and_admin_user_lifecycle():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        admin_role, manager_role = Role(name="admin"), Role(name="facility_manager")
        alpha, beta = Facility(name="Alpha campus"), Facility(name="Private Beta campus")
        db.add_all([admin_role, manager_role, alpha, beta])
        db.flush()
        admin = User(email="admin@example.com", hashed_password=hash_password("test-password"), role=admin_role)
        manager = User(email="manager@example.com", hashed_password=hash_password("test-password"), role=manager_role, facility_id=alpha.id)
        unassigned = User(email="unassigned@example.com", hashed_password="unused", role=manager_role)
        db.add_all([admin, manager, unassigned])
        factor = EmissionFactor(activity_type="electricity", factor_value=0.82, unit="kg CO2e / kWh", valid_from=datetime(2020, 1, 1))
        db.add(factor)
        db.flush()
        records, drafts = [], []
        for facility, quantity in [(alpha, 100), (beta, 900)]:
            record = ActivityRecord(facility_id=facility.id, activity_type="electricity", quantity=quantity,
                unit="kWh", source="manual", confirmed_by_user=True,
                period_start=datetime(2026, 1, 1), period_end=datetime(2026, 2, 1))
            db.add(record)
            db.flush()
            db.add(CalculatedEmission(activity_record_id=record.id, scope=2, co2e_kg=quantity*0.82, emission_factor_id=factor.id))
            draft = OCRDraft(user_id=admin.id, facility_id=facility.id, source_filename="private.csv",
                source_type="upload", activity_type="electricity", quantity=10, unit="kWh",
                period_start=datetime(2026, 3, 1), period_end=datetime(2026, 4, 1))
            db.add(draft)
            records.append(record)
            drafts.append(draft)
        db.commit()
        # Restart seeding must never attach an unassigned account to old data.
        with patch("database.SessionLocal", lambda: Session(engine)):
            from database import _seed_defaults
            _seed_defaults()
        db.refresh(unassigned)
        assert unassigned.facility_id is None
        def session():
            yield db
        app.dependency_overrides[get_db] = session
        client = TestClient(app)
        def headers(user):
            return {"Authorization": "Bearer " + create_access_token(str(user.id), user.role.name)}
        ah, mh, uh = headers(admin), headers(manager), headers(unassigned)
        try:
            # Default account creation gets a fresh workspace, even with old records present.
            fresh = client.post("/api/users", headers=ah, json={
                "email": "fresh@example.com", "full_name": "Fresh manager", "password": "fresh-password",
            })
            assert fresh.status_code == 201, fresh.text
            assert fresh.json()["facility_id"] not in (str(alpha.id), str(beta.id), None)
            signed_in = client.post("/api/auth/login", json={"email": "fresh@example.com", "password": "fresh-password"})
            fresh_headers = {"Authorization": "Bearer " + signed_in.json()["access_token"]}
            for route in ["/api/activity", "/api/activity/drafts", "/api/emissions/summary", "/api/emissions/latest", "/api/anomalies"]:
                response = client.get(route, headers=fresh_headers)
                assert response.status_code == 200, response.text
                assert response.json() == [], (route, response.text)
            assert client.get("/api/users", headers=mh).status_code == 403
            assert client.post("/api/facilities", headers=mh, json={"name": "Escape"}).status_code == 403
            assert [r["id"] for r in client.get("/api/facilities", headers=mh).json()] == [str(alpha.id)]
            assert client.patch(f"/api/facilities/{beta.id}", headers=mh, json={"name": "Stolen"}).status_code == 403
            assert client.patch(f"/api/facilities/{alpha.id}", headers=mh, json={"location": "Campus road"}).status_code == 200
            assert len(client.get("/api/activity", headers=mh).json()) == 1
            assert len(client.get("/api/activity/drafts", headers=mh).json()) == 1
            assert client.post(f"/api/activity/ocr/{drafts[1].id}/confirm", headers=mh).status_code == 403
            assert client.delete(f"/api/activity/ocr/{drafts[1].id}", headers=mh).status_code == 403
            assert client.post("/api/scenarios/preview", headers=mh,
                json={"activity_record_id": str(records[1].id), "quantity": 10}).status_code == 403
            assert client.get(f"/api/activity/{records[1].id}", headers=mh).status_code == 403
            assert client.post(f"/api/calculations/{records[1].id}/calculate", headers=mh).status_code == 403
            csv = {"file": ("own.csv", b"timestamp,metric,value,unit\n2026-05-01,electricity,50,kWh\n", "text/csv")}
            assert client.post("/api/upload", headers=mh, data={"facility_id": str(beta.id)}, files=csv).status_code == 403
            assert client.get("/api/emissions/latest", headers=mh).json()[0]["value"] == 82
            assert client.get("/api/emissions/summary", headers=mh).json()[0]["count"] == 1
            for route in ["/api/emissions/latest", "/api/emissions/summary"]:
                included = client.get(route, headers=mh, params={"start_date": "2026-01-01", "end_date": "2026-01-01"})
                assert included.status_code == 200 and len(included.json()) == 1
                excluded = client.get(route, headers=mh, params={"start_date": "2026-01-02"})
                assert excluded.status_code == 200 and excluded.json() == []
                assert client.get(route, headers=mh, params={"start_date": "2026-02-01", "end_date": "2026-01-01"}).status_code == 422
            assert client.get("/api/emissions/timeseries", headers=mh, params={"metric": "electricity", "start_date": "2026-02-01", "end_date": "2026-01-01"}).status_code == 422
            for route in ["/api/emissions/summary", "/api/emissions/latest", "/api/anomalies", "/api/reports/esg", "/api/activity/drafts"]:
                assert client.get(route, params={"facility_id": str(beta.id)}, headers=mh).status_code == 403
                assert client.get(route, headers=uh).status_code == 403
            for route in ["/api/scenarios/", "/api/recommendations/"]:
                assert client.get(route, headers=uh).status_code == 403
            pdf = client.get("/api/reports/esg", headers=mh)
            text = "".join(page.extract_text() for page in PdfReader(BytesIO(pdf.content)).pages)
            assert "Alpha campus" in text and "Private Beta campus" not in text
            assert "1 pending drafts" in text
            assert client.post("/api/upload", headers=mh, files=csv).status_code == 201
            assert client.post(f"/api/activity/ocr/{drafts[0].id}/confirm", headers=mh).status_code == 201
            assert len(client.get("/api/activity", headers=ah).json()) == 3
            payload = {"email": "new@example.com", "full_name": "New manager", "password": "new-password", "facility_id": str(beta.id)}
            assert client.post("/api/users", headers=mh, json=payload).status_code == 403
            response = client.post("/api/users", headers=ah, json=payload)
            assert response.status_code == 201, response.text
            assert "password" not in response.text
            new_id = response.json()["id"]
            assert client.post("/api/users", headers=ah, json=payload).status_code == 409
            signed_in = client.post("/api/auth/login", json={"email": "NEW@example.com", "password": "new-password"})
            assert signed_in.status_code == 200
            nh = {"Authorization": "Bearer " + signed_in.json()["access_token"]}
            assert client.get("/api/activity", headers=nh).json()[0]["facility_id"] == str(beta.id)
            assert client.patch(f"/api/users/{new_id}", headers=ah, json={"facility_id": str(alpha.id)}).status_code == 200
            assert client.get("/api/activity", headers=nh).status_code == 401
            signed_in = client.post("/api/auth/login", json={"email": "new@example.com", "password": "new-password"})
            nh = {"Authorization": "Bearer " + signed_in.json()["access_token"]}
            assert client.get("/api/activity", headers=nh).json()[0]["facility_id"] == str(alpha.id)
            assert client.patch(f"/api/users/{new_id}", headers=ah, json={"is_active": False}).status_code == 200
            assert client.get("/api/activity", headers=nh).status_code == 401
            assert client.patch(f"/api/users/{admin.id}", headers=ah, json={"is_active": False}).status_code == 409
        finally:
            app.dependency_overrides.clear()
            client.close()
    engine.dispose()
