"""Shared test bootstrap.

``DATABASE_URL`` is pinned to the isolated E2E database *before* any test module
imports the app: ``database.py`` builds its engine from settings at import time,
so whichever URL is in effect first decides where every write in the session
lands. Without this, a full-suite run could resolve to the development
``carbontrace`` database and plant test fixtures (E2E facilities, test users,
drafts) into real data.
"""

import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TEST_DATABASE_URL = "postgresql+psycopg://carbontrace:carbontrace@localhost:5432/carbontrace_e2e"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
