# ==============================================================================
# Multi-Stage Production Dockerfile for FreshCart Recommender System
# Supports both FastAPI Backend (port 8000) and Streamlit Frontend (port 8501)
# ==============================================================================

# --- Base Image with Security Updates and System Dependencies ---
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install minimal system tools (curl required for container healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (cached Docker layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root application user for container security
RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -s /bin/bash -m appuser

# Copy application source code and models
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY ml/ ./ml/
COPY models/ ./models/
COPY data/ ./data/

# Ensure application directories and database are writable by appuser
RUN chown -R appuser:appuser /app

USER appuser

# Expose microservice ports
EXPOSE 8000 8501

# Default command launches FastAPI backend microservice
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
