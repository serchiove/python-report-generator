FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install --no-cache-dir --requirement requirements.txt \
    && useradd --create-home --uid 10001 appuser

COPY --chown=appuser:appuser main.py postgres.py ./
COPY --chown=appuser:appuser src ./src
COPY --chown=appuser:appuser sql ./sql
COPY --chown=appuser:appuser data/examples ./data/examples

USER appuser
ENTRYPOINT ["python", "main.py"]
