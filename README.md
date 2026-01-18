# Resume Matcher

[![CI](https://github.com/luuxxws/resume-matcher/actions/workflows/ci.yml/badge.svg)](https://github.com/luuxxws/resume-matcher/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An AI-powered resume matching system that finds the best candidates for job vacancies using semantic search and LLM-based scoring.

## Features

- **Semantic Search**: Uses multilingual embeddings (`intfloat/multilingual-e5-large`) to find semantically similar resumes
- **LLM Re-ranking**: Optional Groq/Llama-powered intelligent scoring with detailed explanations
- **Multi-format Support**: PDF, DOCX, DOC, images (with OCR)
- **Multilingual**: Supports resumes in multiple languages
- **REST API**: FastAPI-based API with auto-generated documentation
- **CLI**: Command-line interface for batch operations
- **PostgreSQL + pgvector**: Efficient vector similarity search

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Groq API key (for LLM features)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd resume-matcher

# Install dependencies with uv
uv sync
```

### 2. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your settings
# Required: GROQ_API_KEY for LLM features
# Database settings have defaults that work with docker-compose
```

### 3. Start Database

```bash
# Start PostgreSQL with pgvector
docker compose up -d

# The database will be automatically initialized with the required schema
```

### 4. Import Resumes

```bash
# Import all resumes from a directory
uv run resume-matcher import ./data/resumes/

# Or import a single file
uv run resume-matcher import ./path/to/resume.pdf
```

### 5. Match Vacancies

```bash
# Using CLI
uv run resume-matcher match ./data/vacancies/Vacancy1.docx

# With LLM re-ranking (more accurate)
uv run resume-matcher match ./data/vacancies/Vacancy1.docx --llm

# Filter by score range
uv run resume-matcher match ./data/vacancies/Vacancy1.docx --llm --score-range 80-100
```

### 6. Start API Server

```bash
uv run resume-matcher serve

# API docs available at: http://localhost:8000/docs
```

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
| `POST` | `/import` | Import resumes from directory |
| `POST` | `/import/file` | Import single resume file |

### Example API Usage

```bash
# Match vacancy text
curl -X POST http://localhost:8000/match \
  -H "Content-Type: application/json" \
  -d '{"vacancy_text": "Looking for a Senior DevOps Engineer...", "top_n": 10}'

# Match with LLM scoring
curl -X POST http://localhost:8000/match \
  -H "Content-Type: application/json" \
  -d '{"vacancy_text": "...", "use_llm": true, "top_n": 5}'
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
│   │   └── app.py           # FastAPI application
│   ├── models/
│   │   ├── embedding.py     # Sentence transformer embeddings
│   │   └── llm_scorer.py    # LLM-based candidate scoring
│   ├── scripts/
│   │   ├── cli_import.py    # Import CLI
│   │   └── cli_match.py     # Match CLI
│   ├── services/
│   │   ├── importer.py      # Resume import logic
│   │   └── matcher.py       # Matching logic
│   ├── utils/
│   │   ├── convert_file_to_text.py
│   │   ├── ocr_handler.py
│   │   └── text_cleaner.py
│   ├── config.py            # Configuration
│   ├── db.py                # Database operations
│   └── main.py              # Unified CLI entry point
├── data/
│   ├── resumes/             # Place resumes here
│   ├── vacancies/           # Place vacancy files here
│   └── taxonomy/            # ESCO taxonomy files
├── docker/
│   └── init-db.sql          # Database initialization
├── docker-compose.yml
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
```

## How It Works

1. **Resume Import**: Resumes are parsed (with OCR if needed), cleaned, and processed by an LLM to extract structured data (name, skills, experience, etc.)

2. **Embedding Generation**: Text is converted to 1024-dimensional vectors using a multilingual sentence transformer

3. **Similarity Search**: When matching, the vacancy is embedded and compared against all resumes using cosine similarity in pgvector

4. **LLM Re-ranking** (optional): Top candidates are re-scored by an LLM that considers role fit, skills match, and experience relevance

## License

MIT
