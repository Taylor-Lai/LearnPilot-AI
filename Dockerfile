# syntax=docker/dockerfile:1

FROM python:3.11-slim-bookworm AS runtime

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=600 \
    PIP_RETRIES=10

RUN groupadd --gid 10001 learnpilot \
    && useradd --uid 10001 --gid learnpilot --create-home --shell /usr/sbin/nologin learnpilot


FROM runtime AS backend

ENV LEARNPILOT_BACKEND_ROOT=/app/backend
COPY --chown=learnpilot:learnpilot backend /app/backend
RUN --mount=type=cache,id=learnpilot-backend-pip,target=/root/.cache/pip,sharing=locked \
    pip install /app/backend

USER learnpilot

EXPOSE 8001
HEALTHCHECK --interval=10s --timeout=5s --start-period=20s --retries=12 \
    CMD python -c "import json,urllib.request; data=json.load(urllib.request.urlopen('http://127.0.0.1:8001/health', timeout=3)); assert data['status']=='ok'" || exit 1
CMD ["learnpilot-backend"]


FROM runtime AS ml

RUN sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list.d/debian.sources \
    && apt-get -o Acquire::Retries=5 -o Acquire::https::Timeout=60 update \
    && apt-get install --yes --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY --chown=learnpilot:learnpilot ml /app/ml
RUN --mount=type=cache,id=learnpilot-ml-pip-v2,target=/root/.cache/pip,sharing=locked \
    set -eu; \
    for requirement in \
        "numpy==2.4.6" \
        "scipy==1.17.1" \
        "pandas==2.3.3" \
        "scikit-learn==1.9.0" \
        "lightgbm==4.6.0"; do \
        attempt=1; \
        until pip install --no-deps "$requirement"; do \
            if [ "$attempt" -ge 10 ]; then \
                echo "Failed to download a verified wheel for $requirement after $attempt attempts" >&2; \
                exit 1; \
            fi; \
            package="${requirement%%==*}"; \
            pip cache remove "$package" >/dev/null 2>&1 || true; \
            attempt=$((attempt + 1)); \
            echo "Retrying $requirement ($attempt/10)" >&2; \
        done; \
    done; \
    pip install /app/ml

ENV LEARNPILOT_ML_ROOT=/app/ml
ENV LEARNPILOT_RANKER_MODEL_DIR=/app/ml/models/ranker
USER learnpilot
RUN python -c "from ml_service.infrastructure.ranker import TrainableRanker; status=TrainableRanker().status(); assert status['dataset_name']=='Open University Learning Analytics Dataset (OULAD)'; assert status['artifact_format']=='lightgbm-text'; assert status['fallback_reason'] is None"

EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=5s --start-period=20s --retries=12 \
    CMD python -c "import json,urllib.request; data=json.load(urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)); assert data['status']=='ok'" || exit 1
CMD ["learnpilot-ml-api"]


FROM node:22-alpine AS web-build

WORKDIR /app/web
COPY web/package.json web/package-lock.json ./
RUN --mount=type=cache,id=learnpilot-web-npm,target=/root/.npm,sharing=locked npm ci --prefer-offline --no-audit
COPY web ./
ARG VITE_API_BASE_URL=""
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build


FROM nginx:1.27-alpine AS web

COPY web/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=web-build /app/web/dist /usr/share/nginx/html

EXPOSE 80
HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=6 \
    CMD wget -qO- http://127.0.0.1/health >/dev/null || exit 1
STOPSIGNAL SIGQUIT
