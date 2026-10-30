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
    from sqlalchemy import text

    # Uvicorn workers must not migrate or seed the same database concurrently.
    with engine.connect() as lock:
        postgres = engine.dialect.name == 'postgresql'
        if postgres:
            lock.execute(text('SELECT pg_advisory_lock(73641920)'))
        try:
            Base.metadata.create_all(bind=engine)
            _ensure_account_schema()
            _ensure_ingest_schema()
            _seed_roles()
            _seed_defaults()
        finally:
            if postgres:
                lock.execute(text('SELECT pg_advisory_unlock(73641920)'))


def _ensure_account_schema() -> None:
    """One-time adoption of legacy data into its own organization."""
    from sqlalchemy import inspect, text
    import uuid
    with engine.begin() as connection:
        columns = {c["name"] for c in inspect(connection).get_columns("users")}
        legacy = "organization_id" not in columns
        if legacy:
            connection.execute(text("ALTER TABLE users ADD COLUMN organization_id UUID REFERENCES organizations(id)"))
        for name, definition in [("email_verified", "BOOLEAN NOT NULL DEFAULT true"), ("last_login_at", "TIMESTAMP WITH TIME ZONE"), ("auth_version", "INTEGER NOT NULL DEFAULT 0")]:
            if name not in columns:
                connection.execute(text(f"ALTER TABLE users ADD COLUMN {name} {definition}"))
        if "organization_id" not in {c["name"] for c in inspect(connection).get_columns("facilities")}:
            connection.execute(text("ALTER TABLE facilities ADD COLUMN organization_id UUID REFERENCES organizations(id)"))
        if legacy:
            organization_id = str(uuid.uuid4())
            connection.execute(text("INSERT INTO organizations (id, name) VALUES (:id, 'College organization')"), {"id": organization_id})
            connection.execute(text("UPDATE users SET organization_id=:id"), {"id": organization_id})
            connection.execute(text("UPDATE facilities SET organization_id=:id"), {"id": organization_id})


def _ensure_ingest_schema() -> None:
    """Idempotently apply ingest-schema additions to pre-existing databases.

    Schema is managed without a migration tool: ``create_all`` only creates new
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
    """Seed emission factors without changing facility memberships."""
    from models.emission_factor import EmissionFactor

    with SessionLocal() as db:
        # emission factors (placeholders — replace with DEFRA/EPA authoritative values)
        defaults = [
            ("electricity", 0.82, "kg CO2e / kWh"),
            ("diesel", 2.68, "kg CO2e / litre"),
            ("petrol", 2.31, "kg CO2e / litre"),
            ("lpg", 2.94, "kg CO2e / kg"),
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

        # LPG was seeded at 1.51 (a per-litre figure) against a per-kg unit.
        db.query(EmissionFactor).filter(
            EmissionFactor.activity_type == "lpg",
            EmissionFactor.region.is_(None),
            EmissionFactor.factor_value == 1.51,
        ).update({"factor_value": 2.94})
        db.commit()
