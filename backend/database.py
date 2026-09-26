"""SQLAlchemy engine, session factory, declarative base, and session dependency."""

from collections.abc import Generator
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config import get_settings

engine = create_engine(get_settings().database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _ensure_ingest_schema()
    _seed_roles()
    _seed_defaults()
    _backfill_legacy_uploads()
    _backfill_missing_emissions()


def _backfill_missing_emissions() -> None:
    """Give already-confirmed activity the emission it never received.

    Confirming a draft used to create only the ``ActivityRecord``, never the
    matching ``CalculatedEmission``, so every OCR/Excel row confirmed before
    that was fixed is invisible to reporting. Now that confirmation credits the
    emission, this tops up the historical rows. Idempotent — a record that
    already has an emission is skipped, and a record with no resolvable factor
    is left alone rather than guessed at.
    """
    from sqlalchemy import select

    from models.activity_record import ActivityRecord
    from models.calculated_emission import CalculatedEmission
    from models.facility import Facility
    from services.calculation import calculate_emissions
    from services.factors import resolve_factor

    with SessionLocal() as db:
        calculated = select(CalculatedEmission.activity_record_id)
        orphans = (
            db.query(ActivityRecord)
            .filter(ActivityRecord.confirmed_by_user.is_(True))
            .filter(~ActivityRecord.id.in_(calculated))
            .all()
        )
        if not orphans:
            return

        created = 0
        for record in orphans:
            facility = db.get(Facility, record.facility_id)
            factor = resolve_factor(
                db,
                record.activity_type,
                record.period_end,
                region_code=facility.region_code if facility else None,
            )
            if factor is None:
                continue
            db.add(calculate_emissions(record, factor))
            created += 1
        if created:
            db.commit()


def _backfill_legacy_uploads() -> None:
    """Make pre-existing unconfirmed upload rows reviewable.

    Older builds wrote CSV/XLSX uploads straight into ``activity_records`` with
    ``confirmed_by_user=False`` and no draft to review. Those rows are now
    excluded from reports, so each one gets a draft linked back to it: a
    reviewer can confirm it in place (the confirm step adopts the existing
    record) or discard it. Idempotent — a record already linked to a draft is
    skipped.
    """
    from collections import defaultdict
    from sqlalchemy import select

    from models.activity_record import ActivityRecord, SOURCES
    from models.ocr_draft import OCRDraft
    from models.upload import Upload
    from models.user import User
    from services.drafts import SOURCE_TYPE_OCR, SOURCE_TYPE_EXCEL, SOURCE_TYPE_UPLOAD

    # Map ActivityRecord.source -> OCRDraft.source_type
    SOURCE_MAP = {
        "csv": SOURCE_TYPE_UPLOAD,
        "ocr": SOURCE_TYPE_OCR,
        "excel": SOURCE_TYPE_EXCEL,
        "manual": SOURCE_TYPE_UPLOAD,
    }

    with SessionLocal() as db:
        # NULL activity_record_id must be excluded from the subquery: NOT IN
        # against a set containing NULL never matches.
        already_linked = select(OCRDraft.activity_record_id).where(
            OCRDraft.activity_record_id.isnot(None)
        )
        pending = (
            db.query(ActivityRecord)
            .filter(ActivityRecord.confirmed_by_user.is_(False))
            .filter(~ActivityRecord.id.in_(already_linked))
            .all()
        )
        if not pending:
            return

        # Group records by facility to assign each facility's drafts to a user from that facility
        by_facility: dict[str, list[ActivityRecord]] = defaultdict(list)
        for record in pending:
            by_facility[str(record.facility_id)].append(record)

        for facility_id, records in by_facility.items():
            upload = db.query(Upload).filter(Upload.facility_id == facility_id).first()
            owner = db.query(User).filter(User.facility_id == facility_id).first()
            owner_id = upload.user_id if upload else (owner.id if owner else None)
            if owner_id is None:
                continue

            db.add_all(
                [
                    OCRDraft(
                        user_id=owner_id,
                        source_filename=upload.filename if upload else "legacy-upload.csv",
                        source_type=SOURCE_MAP.get(record.source, SOURCE_TYPE_UPLOAD),
                        facility_id=record.facility_id,
                        period_start=record.period_start,
                        period_end=record.period_end,
                        activity_type=record.activity_type,
                        quantity=record.quantity,
                        unit=record.unit,
                        status="draft",
                        activity_record_id=record.id,
                    )
                    for record in records
                ]
            )
        db.commit()


def _ensure_ingest_schema() -> None:
    """Idempotently apply ingest-schema additions to pre-existing databases.

    The project has no alembic migrations — ``create_all`` only creates new
    tables, so columns/enum values added later need explicit additive DDL.
    Every statement here is a no-op when the schema is already up to date.
    """
    from sqlalchemy import text

    with SessionLocal() as db:
        db.execute(
            text(
                "ALTER TABLE ocr_drafts "
                "ADD COLUMN IF NOT EXISTS source_type VARCHAR(20) NOT NULL DEFAULT 'ocr'"
            )
        )
        db.execute(
            text(
                "ALTER TABLE ocr_drafts ADD COLUMN IF NOT EXISTS source_row INTEGER"
            )
        )
        db.execute(
            text(
                "ALTER TABLE ocr_drafts ADD COLUMN IF NOT EXISTS source_column VARCHAR(200)"
            )
        )
        try:
            db.execute(text("ALTER TYPE activity_source_enum ADD VALUE 'excel'"))
            db.commit()
        except Exception as e:
            # Only swallow "already exists" error (PostgreSQL SQLSTATE 42710)
            # Re-raise other errors (e.g., permissions, syntax) so they surface.
            if "already exists" not in str(e).lower():
                db.rollback()
                raise
            db.rollback()


def _seed_roles() -> None:
    from models.role import Role

    defaults = ["admin", "facility_manager", "auditor"]
    with SessionLocal() as db:
        existing = {name for (name,) in db.query(Role.name).all()}
        missing = [Role(name=name) for name in defaults if name not in existing]
        if missing:
            db.add_all(missing)
            db.commit()


def _seed_defaults() -> None:
    """Seed default facility + electricity emission factor; assign unassigned users."""
    from models.emission_factor import EmissionFactor
    from models.facility import Facility
    from models.user import User

    with SessionLocal() as db:
        # default facility
        fac = db.query(Facility).first()
        if fac is None:
            fac = Facility(name="HQ")
            db.add(fac)
            db.flush()

        # assign admin user to HQ
        for u in db.query(User).filter(User.facility_id.is_(None)).all():
            u.facility_id = fac.id

        # emission factors (placeholders — replace with DEFRA/EPA authoritative values)
        defaults = [
            ("electricity", 0.82, "kg CO2e / kWh"),
            ("diesel", 2.68, "kg CO2e / litre"),
            ("petrol", 2.31, "kg CO2e / litre"),
            ("lpg", 1.51, "kg CO2e / kg"),
        ]
        for activity_type, factor_value, unit in defaults:
            if not db.query(EmissionFactor).filter(
                EmissionFactor.activity_type == activity_type,
                EmissionFactor.region.is_(None),
            ).first():
                db.add(
                    EmissionFactor(
                        activity_type=activity_type,
                        region=None,
                        factor_value=factor_value,
                        unit=unit,
                        valid_from=datetime(2020, 1, 1, tzinfo=timezone.utc),
                    )
                )

        db.commit()
