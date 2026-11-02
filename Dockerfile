FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.11 /uv /bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --locked --no-dev --no-install-project
COPY app ./app

# Build with: docker build --build-arg RELEASE_SHA=$(git rev-parse HEAD) .
ARG RELEASE_SHA=unknown
ENV RELEASE_SHA=${RELEASE_SHA} \
    SERVICE_NAME=sample-fastapi \
    ENVIRONMENT=poc \
    DATABASE_PATH=/data/app.db \
    PATH="/app/.venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1

RUN useradd --system --no-create-home app && mkdir /data && chown app /data
USER app
# Mount a named volume here so the SQLite database survives container rebuilds
VOLUME /data

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
