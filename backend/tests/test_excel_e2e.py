"""End-to-end test of the complete Excel ingestion flow against the real API.

This test exercises the actual FastAPI endpoints against a real PostgreSQL
database (``carbontrace_e2e``) using the repo-root ``electricity.xlsx`` as the
uploaded file. It covers the full lifecycle:

    Excel file -> POST /api/activity/excel -> normalized records -> drafts
    -> POST /api/activity/ocr/{draft_id}/confirm -> ActivityRecord

and asserts that OCR ingestion + confirmation still work unchanged.

It is skipped automatically when the dedicated E2E database is unreachable.
Run it with the Postgres fixture present:

    createdb -O carbontrace carbontrace_e2e
    uv run pytest tests/test_excel_e2e.py -s
"""

from __future__ import annotations

import inspect
import os
from datetime import date, datetime, time
from pathlib import Path
from uuid import UUID

import pytest

TEST_DATABASE_URL = "postgresql+psycopg://carbontrace:carbontrace@localhost:5432/carbontrace_e2e"

REPO_ROOT = Path(__file__).resolve().parents[2]
ELECTRICITY_XLSX = REPO_ROOT / "electricity.xlsx"

ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "e2e-pass"


def _e2e_db_available() -> bool:
    try:
        import psycopg

        with psycopg.connect(
            host="localhost",
            port=5432,
            user="carbontrace",
            password="carbontrace",
            dbname="carbontrace_e2e",
        ) as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _e2e_db_available(),
    reason="carbontrace_e2e E2E Postgres database is not reachable",
)


# Point the app at the isolated E2E database BEFORE importing it. The SQLAlchemy
# engine is created from settings at import time, so this must come first.
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402

# The app is shared, but the E2E DB is reset by dropping/recreating it before
# this module runs; a session fixture keeps a single set of seeded roles.
from database import SessionLocal  # noqa: E402
from models.activity_record import ActivityRecord  # noqa: E402
from models.facility import Facility  # noqa: E402
from models.ocr_draft import OCRDraft  # noqa: E402
from models.role import Role  # noqa: E402
from models.session import UserSession  # noqa: E402
from models.upload import Upload  # noqa: E402
from models.user import User  # noqa: E402
from security import hash_password  # noqa: E402

FIRST_LINE_GRID_IMPORT = 69099.99999999968  # row 2 "Mescom Units"
FIRST_LINE_SOLAR = 19359.000000000015
FIRST_LINE_EXPORT = 210.00000000000796
FIRST_LINE_NET = 19149.000000000007
FIRST_LINE_TOTAL = 67970.49999999967
FIRST_LINE_USED = 88248.99999999968
FIRST_LINE_BILL = 722033.0


def _naive(value: str) -> datetime:
    """Parse an ISO datetime from JSON and strip the offset added by the DB."""
    return datetime.fromisoformat(value).replace(tzinfo=None)


@pytest.fixture(scope="session")
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


def _reset_test_data() -> None:
    """Wipe rows created by previous E2E runs so re-runs are deterministic.

    Deletion order respects foreign keys (children before parents). This relies
    on the session-scoped client fixture having already run init_db(), so all
    tables exist.
    """
    with SessionLocal() as db:
        db.query(OCRDraft).delete()
        db.query(ActivityRecord).delete()
        db.query(Upload).delete()
        db.query(UserSession).delete()
        user = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        if user is not None:
            db.delete(user)
        # SessionLocal has autoflush=False, so flush the pending user delete
        # before the bulk facility delete or Postgres sees a dangling FK.
        db.flush()
        db.query(Facility).filter(Facility.name == "E2E Facility").delete()
        db.commit()


@pytest.fixture(scope="session")
def e2e_setup(client: TestClient) -> tuple[str, UUID]:
    """Seed an admin user + facility and return (auth header, facility UUID)."""
    _reset_test_data()
    with SessionLocal() as db:
        role = db.query(Role).filter(Role.name == "admin").one()
        user = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        if user is None:
            facility = Facility(name="E2E Facility", location="Mangaluru", region_code="KA")
            db.add(facility)
            db.flush()
            db.add(
                User(
                    email=ADMIN_EMAIL,
                    hashed_password=hash_password(ADMIN_PASSWORD),
                    full_name="E2E Admin",
                    role_id=role.id,
                    facility_id=facility.id,
                )
            )
            facility_id = facility.id
        else:
            facility_id = user.facility_id
        db.commit()

    login = client.post(
        "/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, facility_id


def test_excel_ingestion_end_to_end(client: TestClient, e2e_setup: tuple[str, UUID]) -> None:
    headers, facility_id = e2e_setup
    xlsx_bytes = ELECTRICITY_XLSX.read_bytes()

    # --- 1. Accept the real electricity.xlsx with an externally supplied facility ---
    response = client.post(
        "/api/activity/excel",
        headers=headers,
        data={"facility_id": str(facility_id)},
        files={
            "file": (
                "electricity.xlsx",
                xlsx_bytes,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert response.status_code == 201, response.text
    drafts = response.json()
    assert len(drafts) == 14  # every valid monthly row becomes a draft

    # Re-uploading the same file must NOT create duplicate drafts.
    repeat = client.post(
        "/api/activity/excel",
        headers=headers,
        data={"facility_id": str(facility_id)},
        files={
            "file": (
                "electricity.xlsx",
                xlsx_bytes,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert repeat.status_code == 201, repeat.text
    assert repeat.json() == []  # no new drafts: rows already ingested

    # Non-electricity workbooks are rejected by the detector.
    from services.excel.parser import parse_workbook
    from services.excel.detector import detect_electricity_workbook

    parsed = parse_workbook(xlsx_bytes, filename="electricity.xlsx")
    assert detect_electricity_workbook(parsed)  # detected as electricity data

    # --- 2. The first row is the actual June 2025 record (Excel row 2) ---
    draft = drafts[0]
    assert draft["source_type"] == "excel"  # source="excel"
    assert draft["source_filename"] == "electricity.xlsx"  # provenance
    assert draft["source_row"] == 2  # provenance: original Excel row
    assert draft["source_column"] == "Mescom Units"  # provenance: original column
    assert draft["facility_id"] == str(facility_id)  # facility supplied externally
    assert draft["activity_type"] == "electricity"
    assert draft["quantity"] == pytest.approx(FIRST_LINE_GRID_IMPORT)  # provisional, see below
    assert draft["unit"] == "kWh"
    assert draft["status"] == "draft"  # not auto-confirmed
    assert draft["activity_record_id"] is None

    # Month -> period_start / period_end (June has 30 days).
    assert _naive(draft["period_start"]) == datetime.combine(date(2025, 6, 1), time.min)
    assert _naive(draft["period_end"]) == datetime.combine(date(2025, 6, 30), time.min)

    # All rows normalized: periods + provenance for every one.
    for index, d in enumerate(drafts, start=2):
        assert d["source_row"] == index
        assert d["source_type"] == "excel"
        _naive(d["period_start"]).day == 1

    # --- 3. All normalized electricity quantities remain available on the record ---
    from services.excel.normalizer import normalize_workbook

    normalized = normalize_workbook(parsed)
    assert len(normalized) == 14
    first = normalized[0]
    assert first.period_start == date(2025, 6, 1)
    assert first.period_end == date(2025, 6, 30)
    assert first.source_filename == "electricity.xlsx"
    assert first.source_row == 2
    assert first.grid_import_kwh == pytest.approx(FIRST_LINE_GRID_IMPORT)
    assert first.solar_generation_kwh == pytest.approx(FIRST_LINE_SOLAR)
    assert first.grid_export_kwh == pytest.approx(FIRST_LINE_EXPORT)
    assert first.net_grid_kwh == pytest.approx(FIRST_LINE_NET)
    assert first.total_consumption_kwh == pytest.approx(FIRST_LINE_TOTAL)
    assert first.unit_used_kwh == pytest.approx(FIRST_LINE_USED)
    assert first.bill_amount == pytest.approx(FIRST_LINE_BILL)
    # Solar/export/net cross-check.
    assert first.net_grid_kwh == pytest.approx(first.solar_generation_kwh - first.grid_export_kwh)

    # --- 4. Draft retrievable from storage (already fetched via the API above) ---
    from models.ocr_draft import OCRDraft
    from uuid import UUID as _UUID

    with SessionLocal() as db:
        stored = db.get(OCRDraft, _UUID(draft["id"]))
        assert stored is not None
        assert stored.source_type == "excel"
        assert stored.source_row == 2
        assert stored.source_column == "Mescom Units"
        stored_count = db.query(OCRDraft).count()

    assert stored_count == 14

    # The list endpoint reloads the persisted drafts (create + confirm flow).
    list_response = client.get("/api/activity", headers=headers)
    assert list_response.status_code == 200
    listed_ids = {draft["id"] for draft in list_response.json()}
    assert draft["id"] in listed_ids

    # --- 5. Confirm the draft through the existing confirmation flow ---
    confirm = client.post(f"/api/activity/ocr/{draft['id']}/confirm", headers=headers)
    assert confirm.status_code == 201, confirm.text
    record = confirm.json()
    assert record["source"] == "excel"
    assert record["facility_id"] == str(facility_id)
    assert record["activity_type"] == "electricity"
    assert record["quantity"] == pytest.approx(FIRST_LINE_GRID_IMPORT)
    assert record["unit"] == "kWh"
    assert record["confirmed_by_user"] is True
    assert _naive(record["period_start"]) == datetime.combine(date(2025, 6, 1), time.min)
    assert _naive(record["period_end"]) == datetime.combine(date(2025, 6, 30), time.min)
    record_id = record["id"]

    with SessionLocal() as db:
        confirmed = db.get(OCRDraft, _UUID(draft["id"]))
        assert confirmed.status == "confirmed"
        assert confirmed.confirmed_at is not None
        assert confirmed.activity_record_id == _UUID(record_id)

    # --- 6. Print one complete chain for a real Excel row (row 2) ---
    print("\n===== COMPLETE EXCEL INGESTION CHAIN (row 2) =====")
    print("EXCEL ROW:")
    for key, value in first.raw_values.items():
        print(f"  {key}: {value}")
    print("NORMALIZED RECORD:")
    print(f"  period_start={first.period_start.isoformat()}")
    print(f"  period_end={first.period_end.isoformat()}")
    print(f"  grid_import_kwh={first.grid_import_kwh}")
    print(f"  solar_generation_kwh={first.solar_generation_kwh}")
    print(f"  grid_export_kwh={first.grid_export_kwh}")
    print(f"  net_grid_kwh={first.net_grid_kwh}")
    print(f"  total_consumption_kwh={first.total_consumption_kwh}")
    print(f"  unit_used_kwh={first.unit_used_kwh}")
    print(f"  bill_amount={first.bill_amount}")
    print(f"  source_filename={first.source_filename} / source_row={first.source_row}")
    print("DRAFT:")
    for key in (
        "id",
        "source_type",
        "source_filename",
        "source_row",
        "source_column",
        "facility_id",
        "period_start",
        "period_end",
        "activity_type",
        "quantity",
        "unit",
        "status",
    ):
        print(f"  {key}={draft[key]}")
    print("CONFIRMED ACTIVITY RECORD:")
    for key in ("id", "facility_id", "period_start", "period_end", "activity_type", "quantity", "unit", "source", "confirmed_by_user"):
        print(f"  {key}={record[key]}")
    print("==================================================")


def test_ocr_ingestion_and_confirmation_unchanged(
    client: TestClient, e2e_setup: tuple[str, UUID]
) -> None:
    headers, facility_id = e2e_setup

    payload = (
        f"Facility ID: {facility_id}\n"
        "Period Start: 2026-07-01\n"
        "Period End: 2026-07-31\n"
        "Activity Type: electricity\n"
        "Quantity: 1245.5\n"
        "Unit: kWh\n"
    ).encode()

    ocr_response = client.post(
        "/api/activity/ocr",
        headers=headers,
        files={"file": ("bill.txt", payload, "text/plain")},
    )
    assert ocr_response.status_code == 201, ocr_response.text
    ocr_drafts = ocr_response.json()
    assert len(ocr_drafts) == 1
    ocr_draft = ocr_drafts[0]
    assert ocr_draft["source_type"] == "ocr"
    assert ocr_draft["source_row"] is None
    assert ocr_draft["source_column"] is None
    assert ocr_draft["status"] == "draft"

    confirm = client.post(f"/api/activity/ocr/{ocr_draft['id']}/confirm", headers=headers)
    assert confirm.status_code == 201, confirm.text
    record = confirm.json()
    assert record["source"] == "ocr"
    assert record["confirmed_by_user"] is True
    assert record["activity_type"] == "electricity"
    assert record["quantity"] == pytest.approx(1245.5)
    assert record["unit"] == "kWh"


def test_facilities_api_create_and_list(client: TestClient, e2e_setup: tuple[str, UUID]) -> None:
    """POST /api/facilities + GET /api/facilities back the intake page picker."""
    headers, _ = e2e_setup

    created = client.post(
        "/api/facilities",
        headers=headers,
        json={"name": "E2E Test Plant", "location": "Bantwal"},
    )
    assert created.status_code == 201, created.text
    facility = created.json()
    assert facility["name"] == "E2E Test Plant"
    assert facility["location"] == "Bantwal"
    assert facility["id"]

    listed = client.get("/api/facilities", headers=headers)
    assert listed.status_code == 200, listed.text
    assert any(item["id"] == facility["id"] for item in listed.json())


def test_quantity_selection_remains_provisional_marker() -> None:
    """The business-rule boundary must still exist and be marked as temporary."""
    from services.excel.normalizer import select_activity_quantity

    source = inspect.getsource(select_activity_quantity)
    assert "BUSINESS RULE" in source
    assert any(marker in source.upper() for marker in ("TEMPORARY", "PROVISIONAL", "TODO"))
    assert "NOT THE FINAL" in source.upper()

    from schemas.normalized_electricity import NormalizedElectricityRecord

    record = NormalizedElectricityRecord(
        period_start=date(2025, 6, 1),
        period_end=date(2025, 6, 30),
        grid_import_kwh=100.0,
        solar_generation_kwh=50.0,
        source_filename="x.xlsx",
        source_row=2,
    )
    quantity, unit, column = select_activity_quantity(record)
    assert quantity == pytest.approx(100.0)
    assert unit == "kWh"
    assert column == "mescom units"