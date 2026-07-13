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


FROM node:22-alpine AS web-build

WORKDIR /app/web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web ./
ARG VITE_API_BASE_URL=""
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build


FROM nginx:1.27-alpine AS web

COPY web/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=web-build /app/web/dist /usr/share/nginx/html

EXPOSE 80
