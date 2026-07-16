# Optional separate ML worker image — only needed once you split the ML
# engine out of the backend process for scaling. Not used by
# docker-compose.yml by default (ML runs in-process in the backend,
# gated by ML_ENABLED).
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt torch transformers
COPY backend/ .
CMD ["python", "-m", "app.ml_worker"]
