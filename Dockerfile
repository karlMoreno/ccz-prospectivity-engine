# E5.7 — the deployable: the read-only API serving ONE pinned run directory and the
# static viewer, in one process on one host (the API serves the page at /, so the
# two are same-origin and no CORS exists to configure — E5.3).
#
#   docker build --build-arg GIT_SHA=$(git rev-parse HEAD) -t ccz-viewer .
#   docker run --rm -p 8000:8000 ccz-viewer
#
# WHAT RUN IT SERVES: whatever sits in deploy/run/ at build time — the CI artifact
# `run-<sha>` downloaded from the E5.6 job (deploy/README.md), so the deployed bytes
# are the CI-built bytes, verifiable by hash through the URL (/runs/{id}/manifest
# is the record's bytes; every file's ETag is its recorded sha256). deploy/run/ is
# gitignored: SERVING IS NOT COMMITTING (E5.1), and a run directory never enters
# data/ (the author_inherited_from trigger, BACKLOG §3).
FROM python:3.11-slim

ARG GIT_SHA=unknown
LABEL org.opencontainers.image.title="CCZ prospectivity engine — run viewer (non-scientific until Checkpoints 1/3/4)" \
      org.opencontainers.image.revision="${GIT_SHA}" \
      org.opencontainers.image.source="https://github.com/karlMoreno/ccz-prospectivity-engine"

WORKDIR /srv/app
COPY pyproject.toml README.md ./
COPY engine ./engine
COPY services ./services
COPY apps ./apps
COPY data ./data
COPY tests/__init__.py ./tests/__init__.py
# the same install the suite and CI use (no dev extra): rasterio etc. as wheels only
RUN pip install --no-cache-dir --only-binary=:all: . && pip check

# THE PINNED RUN — one directory, the whole directory, nothing curated
COPY deploy/run /srv/runs/run
ENV CCZ_RUNS_ROOT=/srv/runs \
    CCZ_GIT_SHA=${GIT_SHA} \
    PYTHONUNBUFFERED=1
EXPOSE 8000
# read-only by construction (E5.1): only GET routes exist; a directory that is not a
# run is refused at startup, so a broken image fails to start rather than serving empty
CMD ["uvicorn", "services.api.app:app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
