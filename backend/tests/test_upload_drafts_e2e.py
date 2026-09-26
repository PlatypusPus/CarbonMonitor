"""End-to-end test of the CSV/XLSX upload review lifecycle.

Uploads used to write straight into ``activity_records`` and
``calculated_emissions``, so unreviewed data moved dashboards and re-uploading a
file double-counted it. This test pins the replacement behaviour:

    CSV/XLSX -> POST /api/upload -> drafts (ledger untouched)
             -> POST /api/activity/ocr/{id}/confirm -> ActivityRecord + emission
             -> DELETE /api/activity/ocr/{id}           -> discarded

It also asserts the ``confirmed_by_user`` gate on the reporting queries, and
that a draft linked to a pre-existing unconfirmed record adopts it on confirm
rather than duplicating it.

Each test stages its own uniquely-named file so the assertions don't depend on
execution order.

Skipped automatically when the dedicated E2E database is unreachable:

    createdb -O carbontrace carbontrace_e2e
    uv run pytest tests/test_upload_drafts_e2e.py -s
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from uuid import UUID

import pytest

TEST_DATABASE_URL = "postgresql+psycopg://carbontrace:carbontrace@localhost:5432/carbontrace_e2e"

_TEST_DIR = Path(__file__).resolve().parent
ELECTRICITY_XLSX = _TEST_DIR / "fixtures" / "electricity.xlsx"

ADMIN_EMAIL = "upload-e2e@example.com"
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


os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402
from database import SessionLocal  # noqa: E402
from models.activity_record import ActivityRecord  # noqa: E402
from models.calculated_emission import CalculatedEmission  # noqa: E402
from models.facility import Facility  # noqa: E402
from models.ocr_draft import OCRDraft  # noqa: E402
from models.role import Role  # noqa: E402
from models.session import UserSession  # noqa: E402
from models.upload import Upload  # noqa: E402
from models.user import User  # noqa: E402
from security import hash_password  # noqa: E402
from services.emissions import query_summary  # noqa: E402


@pytest.fixture(scope="session")
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


def _reset_test_data() -> None:
    with SessionLocal() as db:
        db.query(CalculatedEmission).delete()
        db.query(OCRDraft).delete()
        db.query(ActivityRecord).delete()
        db.query(Upload).delete()
        db.query(UserSession).delete()
        user = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        if user is not None:
            db.delete(user)
        db.flush()
        db.query(Facility).filter(Facility.name == "Upload E2E Facility").delete()
        db.commit()


@pytest.fixture(scope="session")
def e2e_setup(client: TestClient) -> tuple[dict[str, str], UUID]:
    _reset_test_data()
    with SessionLocal() as db:
        role = db.query(Role).filter(Role.name == "admin").one()
        user = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        if user is None:
            facility = Facility(name="Upload E2E Facility", region_code="KA")
            db.add(facility)
            db.flush()
            db.add(
                User(
                    email=ADMIN_EMAIL,
                    hashed_password=hash_password(ADMIN_PASSWORD),
                    full_name="Upload E2E Admin",
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


def _csv(rows: list[tuple[str, float]]) -> str:
    lines = ["timestamp,metric,value,unit,facility_name"]
    lines += [f"{ts},electricity,{value},kWh,HQ" for ts, value in rows]
    return "\n".join(lines) + "\n"


def _upload_csv(client: TestClient, headers: dict[str, str], filename: str, body: str):
    return client.post(
        "/api/upload",
        headers=headers,
        files={"file": (filename, body.encode(), "text/csv")},
    )


def _drafts_for(filename: str) -> list[OCRDraft]:
    with SessionLocal() as db:
        return (
            db.query(OCRDraft)
            .filter(OCRDraft.source_filename == filename)
            .order_by(OCRDraft.quantity)
            .all()
        )


def _record_count() -> int:
    with SessionLocal() as db:
        return db.query(ActivityRecord).count()


def _electricity_count_in_reports() -> int:
    with SessionLocal() as db:
        return {r["metric"]: r["count"] for r in query_summary(db)}.get("electricity", 0)


def test_upload_stages_drafts_without_touching_the_ledger(
    client: TestClient, e2e_setup: tuple[dict[str, str], UUID]
) -> None:
    """An upload must not create ActivityRecords or emissions before review."""
    headers, _ = e2e_setup
    before_records = _record_count()

    response = _upload_csv(
        client, headers, "staged.csv", _csv([("2024-01-01T00:00:00", 100.0)])
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "pending_review"
    assert body["row_count"] == 1

    with SessionLocal() as db:
        assert db.query(ActivityRecord).count() == before_records, "upload wrote to the ledger"
        assert db.query(CalculatedEmission).count() == 0

    drafts = _drafts_for("staged.csv")
    assert len(drafts) == 1
    assert drafts[0].status == "draft"
    assert drafts[0].source_type == "upload"
    assert drafts[0].quantity == 100.0
    assert drafts[0].activity_record_id is None


def test_reuploading_the_same_file_is_deduped(
    client: TestClient, e2e_setup: tuple[dict[str, str], UUID]
) -> None:
    """Re-uploading must stage nothing new instead of double counting."""
    headers, _ = e2e_setup
    body = _csv([("2024-02-01T00:00:00", 200.0)])

    first = _upload_csv(client, headers, "dedup.csv", body)
    assert first.status_code == 201, first.text
    assert first.json()["row_count"] == 1

    second = _upload_csv(client, headers, "dedup.csv", body)
    assert second.status_code == 201, second.text
    assert second.json()["row_count"] == 0, "duplicate rows were staged again"

    assert len(_drafts_for("dedup.csv")) == 1


def test_upload_targets_the_selected_facility(
    client: TestClient, e2e_setup: tuple[dict[str, str], UUID]
) -> None:
    """An explicit facility_id (the intake dropdown) overrides the account's."""
    headers, account_facility = e2e_setup
    with SessionLocal() as db:
        other = Facility(name="Upload E2E Facility B", region_code="KA")
        db.add(other)
        db.commit()
        other_id = other.id

    try:
        response = client.post(
            "/api/upload",
            headers=headers,
            data={"facility_id": str(other_id)},
            files={
                "file": (
                    "picked-facility.csv",
                    _csv([("2024-09-01T00:00:00", 111.0)]).encode(),
                    "text/csv",
                )
            },
        )
        assert response.status_code == 201, response.text

        drafts = _drafts_for("picked-facility.csv")
        assert len(drafts) == 1
        assert drafts[0].facility_id == other_id, "draft ignored the selected facility"
        assert drafts[0].facility_id != account_facility
    finally:
        with SessionLocal() as db:
            db.query(OCRDraft).filter(
                OCRDraft.source_filename == "picked-facility.csv"
            ).delete()
            db.query(Upload).filter(Upload.filename == "picked-facility.csv").delete()
            db.query(Facility).filter(Facility.name == "Upload E2E Facility B").delete()
            db.commit()


def test_confirming_a_draft_credits_the_emissions_ledger(
    client: TestClient, e2e_setup: tuple[dict[str, str], UUID]
) -> None:
    """Confirm is the only path that writes a record AND its emission."""
    headers, _ = e2e_setup
    _upload_csv(client, headers, "confirm.csv", _csv([("2024-03-01T00:00:00", 100.0)]))
    draft = _drafts_for("confirm.csv")[0]

    response = client.post(f"/api/activity/ocr/{draft.id}/confirm", headers=headers)
    assert response.status_code == 201, response.text
    record = response.json()
    assert record["confirmed_by_user"] is True
    assert record["source"] == "csv", "upload drafts are recorded as csv in the ledger"

    with SessionLocal() as db:
        emissions = (
            db.query(CalculatedEmission)
            .join(
                ActivityRecord,
                CalculatedEmission.activity_record_id == ActivityRecord.id,
            )
            .filter(ActivityRecord.id == record["id"])
            .all()
        )
        assert len(emissions) == 1, "confirm did not create a CalculatedEmission"
        # 100 kWh * the seeded global electricity factor (0.82)
        assert emissions[0].co2e_kg == pytest.approx(82.0)
        assert emissions[0].scope == 2

    # Confirming twice is a conflict, not a second emission.
    again = client.post(f"/api/activity/ocr/{draft.id}/confirm", headers=headers)
    assert again.status_code == 409, again.text

    with SessionLocal() as db:
        emissions = (
            db.query(CalculatedEmission)
            .filter(CalculatedEmission.activity_record_id == record["id"])
            .all()
        )
        assert len(emissions) == 1, "double confirm created a second emission"


def test_unconfirmed_rows_are_excluded_from_reporting(
    client: TestClient, e2e_setup: tuple[dict[str, str], UUID]
) -> None:
    """A staged row must not move a dashboard until it is confirmed."""
    headers, _ = e2e_setup
    baseline = _electricity_count_in_reports()

    _upload_csv(
        client,
        headers,
        "gated.csv",
        _csv([("2024-04-01T00:00:00", 100.0), ("2024-05-01T00:00:00", 200.0)]),
    )
    drafts = _drafts_for("gated.csv")
    assert len(drafts) == 2

    # Both staged, neither confirmed -> reporting is unmoved.
    assert _electricity_count_in_reports() == baseline

    client.post(f"/api/activity/ocr/{drafts[0].id}/confirm", headers=headers)
    assert _electricity_count_in_reports() == baseline + 1

    client.post(f"/api/activity/ocr/{drafts[1].id}/confirm", headers=headers)
    assert _electricity_count_in_reports() == baseline + 2


def test_discard_removes_a_staged_draft(
    client: TestClient, e2e_setup: tuple[dict[str, str], UUID]
) -> None:
    headers, _ = e2e_setup
    before_records = _record_count()

    _upload_csv(client, headers, "discard.csv", _csv([("2024-06-01T00:00:00", 300.0)]))
    draft = _drafts_for("discard.csv")[0]

    response = client.delete(f"/api/activity/ocr/{draft.id}", headers=headers)
    assert response.status_code == 204, response.text

    assert _drafts_for("discard.csv") == []
    assert _record_count() == before_records


def test_confirmed_drafts_cannot_be_discarded(
    client: TestClient, e2e_setup: tuple[dict[str, str], UUID]
) -> None:
    """The ledger is append-only for audit: confirm is a one-way door."""
    headers, _ = e2e_setup
    _upload_csv(client, headers, "final.csv", _csv([("2024-07-01T00:00:00", 400.0)]))
    draft = _drafts_for("final.csv")[0]

    assert client.post(f"/api/activity/ocr/{draft.id}/confirm", headers=headers).status_code == 201

    response = client.delete(f"/api/activity/ocr/{draft.id}", headers=headers)
    assert response.status_code == 409, response.text

    with SessionLocal() as db:
        assert db.get(OCRDraft, draft.id) is not None


def test_confirm_adopts_a_legacy_unconfirmed_record(
    client: TestClient, e2e_setup: tuple[dict[str, str], UUID]
) -> None:
    """A backfilled draft must adopt its linked record, not duplicate it.

    Rows written by the old upload path already sit in ``activity_records``
    unconfirmed. The backfill links a draft to each one; confirming has to flip
    that record in place instead of creating a second row for the same month.
    """
    headers, facility_id = e2e_setup
    period_start = datetime(2023, 5, 1)

    with SessionLocal() as db:
        admin = db.query(User).filter(User.email == ADMIN_EMAIL).one()
        legacy = ActivityRecord(
            facility_id=facility_id,
            period_start=period_start,
            period_end=datetime(2023, 6, 1),
            activity_type="electricity",
            quantity=555.0,
            unit="kWh",
            source="csv",
            confirmed_by_user=False,
        )
        db.add(legacy)
        db.flush()
        draft = OCRDraft(
            user_id=admin.id,
            source_filename="legacy.csv",
            source_type="upload",
            facility_id=facility_id,
            period_start=period_start,
            period_end=datetime(2023, 6, 1),
            activity_type="electricity",
            quantity=555.0,
            unit="kWh",
            status="draft",
            activity_record_id=legacy.id,
        )
        db.add(draft)
        db.commit()
        legacy_id = legacy.id
        draft_id = draft.id

    response = client.post(f"/api/activity/ocr/{draft_id}/confirm", headers=headers)
    assert response.status_code == 201, response.text
    assert response.json()["id"] == str(legacy_id), "confirm created a duplicate record"

    with SessionLocal() as db:
        rows = (
            db.query(ActivityRecord)
            .filter(
                ActivityRecord.facility_id == facility_id,
                ActivityRecord.period_start == period_start,
            )
            .all()
        )
        assert len(rows) == 1, "legacy row was duplicated"
        assert rows[0].confirmed_by_user is True
        emissions = (
            db.query(CalculatedEmission)
            .filter(CalculatedEmission.activity_record_id == legacy_id)
            .all()
        )
        assert len(emissions) == 1, "adopted record gained a second emission"


def test_discard_removes_an_adopted_legacy_record(
    client: TestClient, e2e_setup: tuple[dict[str, str], UUID]
) -> None:
    """Discarding a backfilled draft cleans up the duplicate it represents."""
    headers, facility_id = e2e_setup
    period_start = datetime(2023, 7, 1)

    with SessionLocal() as db:
        admin = db.query(User).filter(User.email == ADMIN_EMAIL).one()
        legacy = ActivityRecord(
            facility_id=facility_id,
            period_start=period_start,
            period_end=datetime(2023, 8, 1),
            activity_type="electricity",
            quantity=777.0,
            unit="kWh",
            source="csv",
            confirmed_by_user=False,
        )
        db.add(legacy)
        db.flush()
        draft = OCRDraft(
            user_id=admin.id,
            source_filename="legacy-dup.csv",
            source_type="upload",
            facility_id=facility_id,
            period_start=period_start,
            period_end=datetime(2023, 8, 1),
            activity_type="electricity",
            quantity=777.0,
            unit="kWh",
            status="draft",
            activity_record_id=legacy.id,
        )
        db.add(draft)
        db.commit()
        legacy_id = legacy.id
        draft_id = draft.id

    response = client.delete(f"/api/activity/ocr/{draft_id}", headers=headers)
    assert response.status_code == 204, response.text

    with SessionLocal() as db:
        assert db.get(OCRDraft, draft_id) is None
        assert db.get(ActivityRecord, legacy_id) is None
        emissions = (
            db.query(CalculatedEmission)
            .filter(CalculatedEmission.activity_record_id == legacy_id)
            .all()
        )
        assert emissions == []


def test_xlsx_upload_also_stages_for_review(
    client: TestClient, e2e_setup: tuple[dict[str, str], UUID]
) -> None:
    """The electricity workbook follows the same review lifecycle."""
    headers, _ = e2e_setup
    before_records = _record_count()

    response = client.post(
        "/api/upload",
        headers=headers,
        files={
            "file": (
                "workbook.xlsx",
                ELECTRICITY_XLSX.read_bytes(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert response.status_code == 201, response.text
    staged_count = response.json()["row_count"]
    assert staged_count > 0

    with SessionLocal() as db:
        assert db.query(ActivityRecord).count() == before_records, "xlsx wrote to the ledger"
    assert len(_drafts_for("workbook.xlsx")) == staged_count
