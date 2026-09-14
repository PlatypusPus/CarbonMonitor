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
    _seed_roles()
    _seed_defaults()


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
            ("lpg", 1.51, "kg CO2e / litre"),
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
