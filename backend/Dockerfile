# CarbonTrace backend image — built with uv for fast, reproducible installs.
# We use the official uv image which bundles uv on top of a slim Python base.
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

# Keep Python output unbuffered (logs appear immediately in `docker logs`).
ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# 1) Copy only dependency manifests first so this layer is cached and only
#    re-runs when dependencies actually change (faster rebuilds).
COPY pyproject.toml uv.lock* ./

# 2) Install production dependencies into a project-local .venv.
#    --no-dev excludes ruff/pytest; --frozen fails if the lock is out of date.
RUN uv sync --no-dev --no-install-project --frozen || uv sync --no-dev --no-install-project

# 3) Copy the application code.
COPY . .

# Put the venv on PATH so `uvicorn`/`python` resolve to the installed env.
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

# 2 Uvicorn workers is plenty for a demo; bump for higher concurrency.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
