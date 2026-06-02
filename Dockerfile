FROM python:3.12-slim

# uv: fast, reproducible Python dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Keep the virtualenv outside the mounted project so it does not collide with a
# host-side .venv and survives across runs in a named volume.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_LINK_MODE=copy \
    UV_PYTHON=python3.12

WORKDIR /app

# Dependencies are synced at runtime from the mounted project (`uv run` auto-syncs),
# kept out of the image so the skeleton can evolve during the hackathon without rebuilds.
ENTRYPOINT ["uv", "run"]
CMD ["python", "-m", "ingest", "--help"]
