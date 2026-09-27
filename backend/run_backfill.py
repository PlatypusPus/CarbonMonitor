#!/usr/bin/env python
"""One-time migration script to run startup backfills.

Run this once after deploying the schema changes:
    uv run python run_backfill.py

This script is idempotent and safe to run multiple times.
"""

from database import _backfill_legacy_uploads, _backfill_missing_emissions, init_db


def main():
    print("Initializing database schema...")
    init_db()

    print("Running legacy uploads backfill...")
    _backfill_legacy_uploads()
    print("Legacy uploads backfill complete.")

    print("Running missing emissions backfill...")
    _backfill_missing_emissions()
    print("Missing emissions backfill complete.")

    print("All backfills completed successfully.")


if __name__ == "__main__":
    main()