# Stage 1: Build frontend
FROM node:22-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend + built frontend
FROM python:3.11-slim
WORKDIR /app

# Install backend deps
COPY backend/pyproject.toml ./
COPY backend/src/ ./src/
RUN pip install --no-cache-dir .

# Copy built frontend
COPY --from=frontend-build /app/frontend/build /app/frontend-build

ENV FRONTEND_DIR=/app/frontend-build
ENV DATA_DIR=/data
ENV PORT=8000

EXPOSE 8000

CMD ["sh", "-c", "python -m uvicorn rewind.main:app --host 0.0.0.0 --port ${PORT}"]
