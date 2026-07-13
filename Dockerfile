# syntax=docker/dockerfile:1

FROM python:3.11-slim AS runtime

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1


FROM runtime AS backend

COPY backend /app/backend
RUN pip install --no-cache-dir -e /app/backend

EXPOSE 8001
CMD ["learnpilot-backend"]


FROM runtime AS ml

COPY ml /app/ml
RUN pip install --no-cache-dir -e /app/ml \
    && learnpilot-ml-generate \
    && learnpilot-ml-train

EXPOSE 8000
CMD ["learnpilot-ml-api"]
