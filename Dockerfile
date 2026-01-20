# syntax=docker/dockerfile:1

# =============================================================================
# Stage 1: Builder - install dependencies
# =============================================================================
FROM python:3.11-slim AS builder

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy ALL project files needed for installation
COPY pyproject.toml README.md ./
COPY src/ src/

# Create venv and install with CPU-only PyTorch
RUN uv venv && \
    # Install CPU-only torch first
    uv pip install --no-cache \
        torch==2.2.2+cpu \
        --index-url https://download.pytorch.org/whl/cpu && \
    # Install the project (not editable, proper install)
    uv pip install --no-cache . && \
    # Clean caches
    rm -rf /root/.cache

# =============================================================================
# Stage 2: Runtime - minimal production image  
# =============================================================================
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy the virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy docker init scripts
COPY docker/ docker/

# Copy taxonomy data (ESCO occupations and skills)
COPY data/taxonomy/ data/taxonomy/

ENV PATH="/app/.venv/bin:$PATH"

RUN mkdir -p data/resumes data/vacancies data/output data/embedding_cache

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "resume_matcher.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
