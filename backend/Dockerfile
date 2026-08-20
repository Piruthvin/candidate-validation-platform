FROM python:3.12-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim

RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

WORKDIR /app

COPY --from=builder /usr/local /usr/local

COPY app/ app/
COPY scripts/ scripts/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

RUN chown -R appuser:appuser /app

EXPOSE 8000

USER appuser

CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]