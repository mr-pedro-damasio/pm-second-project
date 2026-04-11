# Stage 1: build Next.js static export
FROM node:20-slim AS frontend-builder
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python runtime
FROM python:3.12-slim AS runtime
COPY --from=ghcr.io/astral-sh/uv:0.11.6 /uv /bin/uv
WORKDIR /app
COPY backend/pyproject.toml ./
RUN uv sync --no-dev --no-install-project
COPY backend/ ./
COPY --from=frontend-builder /frontend/out/ ./static/
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
