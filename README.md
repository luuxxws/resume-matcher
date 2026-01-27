# Resume Matcher

[![CI](https://github.com/luuxxws/resume-matcher/actions/workflows/ci.yml/badge.svg)](https://github.com/luuxxws/resume-matcher/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An AI-powered resume matching system that finds the best candidates for job vacancies using semantic search and LLM-based scoring.

![Resume Matcher UI](docs/screenshot.png)

## Features

### Core
- **Semantic Search**: Uses multilingual embeddings (`intfloat/multilingual-e5-large`) to find semantically similar resumes
- **LLM Re-ranking**: Groq/Llama-powered intelligent scoring with detailed explanations
- **Multi-format Support**: PDF, DOCX, DOC, images (with OCR via Tesseract)
- **Multilingual**: Supports resumes in English, Russian, and other languages
- **Duplicate Detection**: Automatic detection and removal of duplicate resumes

### Web UI (New in v1.0.1)
- **Modern React Frontend**: Beautiful cyberpunk-themed interface
- **Dashboard**: Overview of your resume database with statistics
- **AI-Powered Matching**: Deep analysis with skill matching and explanations
- **Fast Mode**: Instant embedding-based semantic search
- **Multilingual UI**: English and Russian interface
- **Export Results**: Download matches as CSV or PDF
- **One-Click Copy**: Copy candidate emails for outreach
- **Keyboard Shortcuts**: Ctrl+Enter to search

### Backend
- **REST API**: FastAPI-based API with auto-generated documentation
- **CLI**: Command-line interface for batch operations
- **PostgreSQL + pgvector**: Efficient vector similarity search
- **Docker Ready**: Full stack deployment with Docker Compose

## Quick Start

### Option A: Run with Docker (Recommended)

The easiest way to run the entire stack (backend + frontend + database):

```bash
# 1. Clone the repository
git clone https://github.com/luuxxws/resume-matcher.git
cd resume-matcher

# 2. Configure environment
cp .env.example .env
# Edit .env and add your GROQ_API_KEY

# 3. Add your resumes to data/resumes/

# 4. Start everything
docker compose up -d

# Backend API: http://localhost:8000/docs
# Frontend UI: http://localhost:3000
```

### Option B: Local Development Setup

For local development with more control:

#### Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend)
- Docker & Docker Compose (for PostgreSQL)
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Groq API key (for LLM features)

#### 1. Clone and Setup

```bash
git clone https://github.com/luuxxws/resume-matcher.git
cd resume-matcher

# Install Python dependencies with uv
uv sync

# Install frontend dependencies
cd frontend && npm install && cd ..
```

#### 2. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your settings
# Required: GROQ_API_KEY for LLM features
```

#### 3. Start Database

```bash
# Start PostgreSQL with pgvector
docker compose up -d postgres
```

#### 4. Start Backend

```bash
# Start API server
uv run resume-matcher serve

# API docs available at: http://localhost:8000/docs
```

#### 5. Start Frontend

```bash
cd frontend
npm run dev

# UI available at: http://localhost:3000
```

#### 6. Import Resumes

```bash
# Via CLI
uv run resume-matcher import ./data/resumes/

# Or via the web UI: Navigate to "Import" section
```

## Web Interface

The frontend provides a modern, intuitive interface for:

### Dashboard
- View total resumes in database
- See import statistics
- Quick access to all features

### Match Candidates
- Paste vacancy text or upload a file
- Choose **Fast Mode** (embedding search) or **AI Mode** (LLM scoring)
- Adjust filters: top N results, score range
- View detailed candidate analysis with:
  - Combined score (embedding + LLM)
  - Matching and missing skills
  - Strengths and concerns
  - AI-generated explanations

### Resume Browser
- Search resumes by name or skills
- View parsed resume data
- Delete individual resumes

### Import
- Upload individual files (PDF, DOCX, images)
- Batch import from directories
- Automatic duplicate detection

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | API info |
| `GET` | `/health` | Health check |
| `GET` | `/stats` | Database statistics |
| `POST` | `/match` | Match vacancy text to resumes |
| `POST` | `/match/file` | Match vacancy file to resumes |
| `GET` | `/resumes` | List all resumes |
| `GET` | `/resumes/{id}` | Get resume by ID |
| `DELETE` | `/resumes/{id}` | Delete resume |
| `GET` | `/resumes/duplicates` | Find duplicate resumes |
| `POST` | `/resumes/duplicates/clean` | Remove duplicate resumes |
| `POST` | `/import` | Import resumes from directory |
| `POST` | `/import/file` | Import single resume file |

### Example API Usage

```bash
# Match vacancy text
curl -X POST http://localhost:8000/match \
  -H "Content-Type: application/json" \
  -d '{"vacancy_text": "Looking for a Senior DevOps Engineer...", "top_n": 10}'

# Match with LLM scoring (supports lang parameter for multilingual output)
curl -X POST "http://localhost:8000/match?lang=ru" \
  -H "Content-Type: application/json" \
  -d '{"vacancy_text": "...", "use_llm": true, "top_n": 5}'

# Find duplicates
curl http://localhost:8000/resumes/duplicates

# Clean duplicates (dry run)
curl -X POST "http://localhost:8000/resumes/duplicates/clean?dry_run=true"
```

## CLI Commands

```bash
# Main entry point
uv run resume-matcher --help

# Import resumes
uv run resume-matcher import <path> [--workers N] [--force] [--quiet]

# Match vacancy
uv run resume-matcher match <vacancy_file> [--top N] [--llm] [--score-range MIN-MAX]

# Database info
uv run resume-matcher info

# Start API server
uv run resume-matcher serve [--host HOST] [--port PORT]
```

## Project Structure

```
resume-matcher/
├── src/resume_matcher/
│   ├── api/
│   │   └── app.py              # FastAPI application
│   ├── models/
│   │   ├── embedding.py        # Sentence transformer embeddings
│   │   └── llm_scorer.py       # LLM-based candidate scoring
│   ├── scripts/
│   │   ├── cli_import.py       # Import CLI
│   │   └── cli_match.py        # Match CLI
│   ├── services/
│   │   ├── importer.py         # Resume import logic
│   │   └── matcher.py          # Matching logic
│   ├── utils/
│   │   ├── convert_file_to_text.py
│   │   ├── ocr_handler.py
│   │   └── text_cleaner.py
│   ├── config.py               # Configuration
│   ├── db.py                   # Database operations
│   └── main.py                 # Unified CLI entry point
├── frontend/                   # React web interface
│   ├── src/
│   │   ├── api/client.ts       # API client
│   │   ├── components/         # React components
│   │   ├── i18n/               # Internationalization (EN/RU)
│   │   └── utils/export.ts     # CSV/PDF export
│   ├── package.json
│   └── vite.config.ts
├── data/
│   ├── resumes/                # Place resumes here
│   ├── vacancies/              # Place vacancy files here
│   └── taxonomy/               # ESCO taxonomy files
├── docker/
│   └── init-db.sql             # Database initialization
├── Dockerfile                  # Application container
├── docker-compose.yml          # Full stack orchestration
├── pyproject.toml
└── .env.example
```

## Configuration

Environment variables (set in `.env`):

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | - | Required for LLM features |
| `DB_NAME` | `resumes_db` | PostgreSQL database name |
| `DB_USER` | `resumes_user` | PostgreSQL username |
| `DB_PASSWORD` | - | PostgreSQL password |
| `DB_HOST` | `localhost` | PostgreSQL host |
| `DB_PORT` | `5433` | PostgreSQL port |

## Cost Estimation (Groq)

Using `llama-3.3-70b-versatile` on Groq:

| Operation | Cost |
|-----------|------|
| Import 10k resumes | ~$27 |
| AI search (per query) | ~$0.02 |
| Monthly (moderate usage) | ~$30-50 |

Fast mode (embedding search) is free - no LLM calls required.

## Development

```bash
# Install dev dependencies
uv sync --group dev

# Run type checking
uv run mypy src

# Run linter
uv run ruff check src

# Run tests
uv run pytest

# Frontend development
cd frontend && npm run dev
```

## How It Works

1. **Resume Import**: Resumes are parsed (with OCR if needed), cleaned, and processed by an LLM to extract structured data (name, skills, experience, etc.)

2. **Duplicate Detection**: File hashes prevent importing the same content twice

3. **Embedding Generation**: Text is converted to 1024-dimensional vectors using a multilingual sentence transformer

4. **Similarity Search**: When matching, the vacancy is embedded and compared against all resumes using cosine similarity in pgvector

5. **LLM Re-ranking** (optional): Top candidates are re-scored by an LLM that considers role fit, skills match, and experience relevance

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for release history.

## License

MIT
