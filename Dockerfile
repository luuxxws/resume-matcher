# syntax=docker/dockerfile:1

FROM python:3.11-slim AS base

# Prevents Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies for OCR and document processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-rus \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock README.md ./

# Install dependencies (without dev dependencies)
RUN uv sync --frozen --no-dev --no-install-project

# Copy source code
COPY src/ src/
COPY docker/ docker/

# Install the project itself
RUN uv sync --frozen --no-dev

# Create directories for data
RUN mkdir -p data/resumes data/vacancies data/output data/embedding_cache

# Expose the API port
EXPOSE 8000

# Default command: run the API server
CMD ["uv", "run", "uvicorn", "resume_matcher.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
