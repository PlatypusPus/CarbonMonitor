"""Create an initial user from the command line (no public signup endpoint)."""

import argparse

from database import SessionLocal, init_db
from models.role import Role
from models.user import User
from models.facility import Facility
from models.organization import Organization
from security import hash_password


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a CarbonTrace user.")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--full-name", default=None)
    parser.add_argument(
        "--role",
        default="facility_manager",
        choices=["admin", "facility_manager", "auditor"],
    )
    args = parser.parse_args()

    init_db()
    with SessionLocal() as db:
        if db.query(User).filter(User.email == args.email).first() is not None:
            print(f"User {args.email} already exists.")
            return
        role = db.query(Role).filter(Role.name == args.role).first()
        if role is None:
            print(f"Role {args.role} not found.")
            return
        organization = Organization(name=f"{args.full_name or args.email}'s organization")
        db.add(organization)
        db.flush()
        facility = Facility(name=f"{args.full_name or args.email}'s facility", organization_id=organization.id)
        db.add(facility)
        db.flush()
        db.add(
            User(
                email=args.email,
                hashed_password=hash_password(args.password),
                full_name=args.full_name,
                role_id=role.id,
                organization_id=organization.id,
                facility_id=facility.id if facility else None,
            )
        )
        db.commit()
        print(f"Created {args.role} user: {args.email}")


if __name__ == "__main__":
    main()
