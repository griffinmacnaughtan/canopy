FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

RUN groupadd -r canopy && useradd -r -g canopy canopy
RUN chown -R canopy:canopy /app
USER canopy

# Build-time smoke test: if this fails the build log shows the exact traceback
RUN python -c "from app.main import app; print('Import OK')"

EXPOSE 8000
# Shell form so $PORT (injected by Railway) is expanded at runtime.
# Falls back to 8000 for local docker run without PORT set.
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
