"""Auth router — placeholder.

Phase: Auth. Will implement login, refresh, logout using short-lived JWT
access tokens (in memory) + long-lived refresh tokens (HttpOnly cookie),
with roles Admin / Facility Manager / Auditor.
"""

from fastapi import APIRouter

router = APIRouter()

# Endpoints (login, refresh, logout, me) are added in the Auth phase.
