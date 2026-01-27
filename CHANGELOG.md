# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2026-01-27

### Added

#### Web UI (New)
- **React Frontend**: Modern cyberpunk-themed web interface
- **Dashboard**: Real-time statistics and overview
- **Match Interface**: Vacancy matching with file upload support
- **Resume Browser**: Search and filter resumes
- **Import Interface**: Upload individual files or batch import

#### Multilingual Support
- **UI Translations**: Full English and Russian interface
- **LLM Output Language**: API `lang` parameter for multilingual AI responses
- **Technical Term Preservation**: AI keeps technical terms (Python, Docker, etc.) in English even when responding in Russian

#### Export Features
- **CSV Export**: Download match results as spreadsheet
- **PDF Export**: Formatted reports (basic implementation)
- **One-Click Email Copy**: Copy candidate emails for outreach

#### UX Improvements
- **Keyboard Shortcuts**: Ctrl+Enter to submit search
- **Loading States**: Visual feedback during AI analysis
- **Error Handling**: User-friendly error messages for rate limits

#### Duplicate Management
- **Duplicate Detection**: Find resumes with identical content
- **Automatic Deduplication**: Matching results automatically deduplicated by content hash
- **Import Protection**: Skip duplicate content during import
- **Cleanup API**: Endpoints to detect and remove existing duplicates
  - `GET /resumes/duplicates` - List duplicate groups
  - `POST /resumes/duplicates/clean` - Remove duplicates (with dry-run option)

### Changed

- **Matching Query**: Now uses `DISTINCT ON (file_hash)` to prevent duplicate candidates in results
- **Import Logic**: Checks content hash before expensive operations (text extraction, embedding, LLM parsing)
- **API Routes**: Reorganized to fix routing conflicts

### Fixed

- **Duplicate Results**: Fixed issue where renamed copies of the same resume appeared multiple times
- **LLM Null Handling**: Added fallbacks for when LLM returns null for job_title and other fields
- **Route Ordering**: Fixed `/resumes/duplicates` being matched by `/resumes/{resume_id}`

## [1.0.0] - 2026-01-15

### Added

- Initial release
- **Semantic Search**: Multilingual embeddings with `intfloat/multilingual-e5-large`
- **LLM Re-ranking**: Groq/Llama-powered intelligent scoring
- **Multi-format Support**: PDF, DOCX, DOC, images with OCR
- **REST API**: FastAPI with auto-generated documentation
- **CLI**: Command-line interface for batch operations
- **PostgreSQL + pgvector**: Vector similarity search
- **Docker Support**: Full stack deployment with Docker Compose
