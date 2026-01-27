# src/resume_matcher/api/app.py
"""
FastAPI application for Resume Matcher.

Run with:
    uv run resume-matcher serve
    # or directly:
    uv run uvicorn resume_matcher.api:app --reload --host 0.0.0.0 --port 8000

API Docs available at:
    http://localhost:8000/docs (Swagger UI)
    http://localhost:8000/redoc (ReDoc)
"""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Annotated, Any

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =============================================================================
# Pydantic Schemas
# =============================================================================


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "ok"
    version: str = "0.1.0"


class StatsResponse(BaseModel):
    """Database statistics response."""

    total_resumes: int
    with_embeddings: int
    with_parsed_data: int


class CandidateInfo(BaseModel):
    """Candidate information extracted from resume."""

    name: str | None = None
    position: str | None = None
    email: str | None = None
    phone: str | None = None
    skills: list[str] = []
    years_experience: int | None = None
    summary: str | None = None


class MatchedResumeResponse(BaseModel):
    """Single matched resume in embedding mode."""

    rank: int
    id: int
    file_name: str
    file_path: str
    similarity_percent: float
    candidate: CandidateInfo


class EmbeddingMatchResponse(BaseModel):
    """Response for embedding-only matching."""

    mode: str = "embedding"
    total_resumes_in_db: int
    matches_found: int
    matches: list[MatchedResumeResponse]


class LLMMatchedResumeResponse(BaseModel):
    """Single matched resume in LLM mode."""

    rank: int
    id: int
    file_name: str
    combined_score: float
    llm_score: int
    embedding_score_percent: float
    match_level: str
    matching_skills: list[str]
    missing_skills: list[str]
    strengths: list[str]
    concerns: list[str]
    explanation: str


class VacancyInfo(BaseModel):
    """Parsed vacancy information."""

    job_title: str
    seniority_level: str | None
    must_have_skills: list[str]
    nice_to_have_skills: list[str]
    min_years_experience: int | None
    summary: str


class LLMMatchResponse(BaseModel):
    """Response for LLM-powered matching."""

    mode: str = "llm"
    vacancy: VacancyInfo
    matches_found: int
    matches: list[LLMMatchedResumeResponse]


class ResumeResponse(BaseModel):
    """Single resume details."""

    id: int
    file_name: str
    file_path: str
    has_embedding: bool
    json_data: dict[str, Any]


class ResumeListResponse(BaseModel):
    """List of resumes."""

    total: int
    limit: int
    offset: int
    resumes: list[ResumeResponse]


class ImportResponse(BaseModel):
    """Import operation response."""

    status: str
    files_found: int
    message: str


class MatchRequest(BaseModel):
    """Request body for matching."""

    vacancy_text: str = Field(..., description="Vacancy/job description text")
    top_n: int = Field(default=10, ge=1, le=100, description="Number of results")
    min_score: float = Field(default=0, ge=0, le=100, description="Minimum score (0-100)")
    max_score: float = Field(default=100, ge=0, le=100, description="Maximum score (0-100)")
    use_llm: bool = Field(default=False, description="Use LLM for intelligent re-ranking")
    embedding_candidates: int = Field(
        default=30, ge=1, le=100, description="Candidates for LLM re-ranking"
    )
    lang: str = Field(default="en", description="Language for LLM responses: 'en' or 'ru'")


# =============================================================================
# FastAPI App
# =============================================================================


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Resume Matcher API",
        description="""
AI-powered resume matching and ranking system.

## Features
- **Semantic Search**: Find resumes similar to a job vacancy using embeddings
- **LLM Re-ranking**: Intelligent scoring with role-fit analysis
- **Batch Import**: Import resumes from files (PDF, DOCX, images with OCR)

## Matching Modes
- **Embedding mode** (default): Fast semantic similarity search
- **LLM mode** (`use_llm=true`): Slower but more accurate role-based matching
        """,
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS middleware for frontend integration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    register_routes(app)

    return app


def register_routes(app: FastAPI) -> None:
    """Register all API routes."""

    # =========================================================================
    # Health & Info
    # =========================================================================

    @app.get("/", tags=["Health"])
    async def root() -> dict[str, str]:
        """Root endpoint with API info."""
        return {
            "name": "Resume Matcher API",
            "version": "0.1.0",
            "docs": "/docs",
        }

    @app.get("/health", response_model=HealthResponse, tags=["Health"])
    async def health_check() -> HealthResponse:
        """Health check endpoint."""
        return HealthResponse()

    @app.get("/stats", response_model=StatsResponse, tags=["Info"])
    async def get_stats() -> StatsResponse:
        """Get database statistics."""
        from resume_matcher.db import get_connection

        try:
            with get_connection() as conn, conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) as count FROM resumes")
                total = cur.fetchone()["count"]

                cur.execute("SELECT COUNT(*) as count FROM resumes WHERE embedding IS NOT NULL")
                with_embedding = cur.fetchone()["count"]

                cur.execute(
                    "SELECT COUNT(*) as count FROM resumes WHERE json_data IS NOT NULL AND json_data != '{}'"
                )
                with_json = cur.fetchone()["count"]

            return StatsResponse(
                total_resumes=total,
                with_embeddings=with_embedding,
                with_parsed_data=with_json,
            )
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise HTTPException(
                status_code=503,
                detail="Database unavailable. Make sure PostgreSQL is running and .env is configured correctly.",
            ) from None

    # =========================================================================
    # Matching
    # =========================================================================

    @app.post("/match", tags=["Matching"])
    async def match_vacancy(request: MatchRequest) -> EmbeddingMatchResponse | LLMMatchResponse:
        """
        Match resumes against a vacancy description.

        **Modes:**
        - `use_llm=false` (default): Fast embedding-based semantic search
        - `use_llm=true`: LLM re-ranks candidates for role fit, skills match, etc.
        """
        from resume_matcher.services.matcher import (
            match_vacancy_text,
            match_vacancy_with_llm,
        )

        min_similarity = request.min_score / 100.0

        if request.use_llm:
            # LLM-powered matching
            requirements, scores = match_vacancy_with_llm(
                vacancy_text=request.vacancy_text,
                top_n=request.top_n,
                embedding_candidates=request.embedding_candidates,
                min_similarity=min_similarity,
                lang=request.lang,
            )

            # Apply score range filter
            if request.min_score > 0 or request.max_score < 100:
                scores = [
                    s for s in scores if request.min_score <= s.combined_score <= request.max_score
                ]

            return LLMMatchResponse(
                vacancy=VacancyInfo(
                    job_title=requirements.job_title or "Unknown Position",
                    seniority_level=requirements.seniority_level,
                    must_have_skills=requirements.must_have_skills or [],
                    nice_to_have_skills=requirements.nice_to_have_skills or [],
                    min_years_experience=requirements.min_years_experience,
                    summary=requirements.summary or "No summary available",
                ),
                matches_found=len(scores),
                matches=[
                    LLMMatchedResumeResponse(
                        rank=i + 1,
                        id=s.candidate_id,
                        file_name=s.file_name,
                        combined_score=s.combined_score,
                        llm_score=s.llm_score,
                        embedding_score_percent=round(s.embedding_score * 100, 2),
                        match_level=s.match_level,
                        matching_skills=s.matching_skills,
                        missing_skills=s.missing_skills,
                        strengths=s.strengths,
                        concerns=s.concerns,
                        explanation=s.explanation,
                    )
                    for i, s in enumerate(scores)
                ],
            )

        else:
            # Embedding-only matching
            result = match_vacancy_text(
                vacancy_text=request.vacancy_text,
                top_n=request.top_n,
                min_similarity=min_similarity,
            )

            # Apply score range filter
            matches = result.matches
            if request.min_score > 0 or request.max_score < 100:
                matches = [
                    m for m in matches if request.min_score <= m.score_percent <= request.max_score
                ]

            return EmbeddingMatchResponse(
                total_resumes_in_db=result.total_resumes_in_db,
                matches_found=len(matches),
                matches=[
                    MatchedResumeResponse(
                        rank=i + 1,
                        id=m.id,
                        file_name=m.file_name,
                        file_path=m.file_path,
                        similarity_percent=m.score_percent,
                        candidate=CandidateInfo(
                            name=m.json_data.get("full_name"),
                            position=m.json_data.get("current_position"),
                            email=m.json_data.get("email"),
                            phone=m.json_data.get("phone"),
                            skills=m.json_data.get("skills", []),
                            years_experience=m.json_data.get("years_experience"),
                            summary=m.json_data.get("summary"),
                        ),
                    )
                    for i, m in enumerate(matches)
                ],
            )

    @app.post("/match/file", tags=["Matching"])
    async def match_vacancy_file(
        vacancy_file: Annotated[UploadFile, File(description="Vacancy file (PDF, DOCX, TXT)")],
        top_n: int = Query(default=10, ge=1, le=100),
        min_score: float = Query(default=0, ge=0, le=100),
        max_score: float = Query(default=100, ge=0, le=100),
        use_llm: bool = Query(default=False),
        embedding_candidates: int = Query(default=30, ge=1, le=100),
    ) -> EmbeddingMatchResponse | LLMMatchResponse:
        """
        Match resumes against a vacancy file upload.

        Supports PDF, DOCX, and TXT files.
        """
        from resume_matcher.utils.convert_file_to_text import convert_file_to_text

        # Save uploaded file temporarily
        suffix = Path(vacancy_file.filename or "vacancy.txt").suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await vacancy_file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            # Extract text from file
            vacancy_text = convert_file_to_text(tmp_path)
            if not vacancy_text.strip():
                raise HTTPException(
                    status_code=400,
                    detail="Could not extract text from vacancy file",
                )

            # Use the text-based matching
            request = MatchRequest(
                vacancy_text=vacancy_text,
                top_n=top_n,
                min_score=min_score,
                max_score=max_score,
                use_llm=use_llm,
                embedding_candidates=embedding_candidates,
            )
            return await match_vacancy(request)

        finally:
            # Clean up temp file
            Path(tmp_path).unlink(missing_ok=True)

    # =========================================================================
    # Resumes
    # =========================================================================

    @app.get("/resumes", response_model=ResumeListResponse, tags=["Resumes"])
    async def list_resumes(
        limit: int = Query(default=20, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
        search: str | None = Query(default=None, description="Search in file name or parsed data"),
    ) -> ResumeListResponse:
        """List resumes in the database."""
        from resume_matcher.db import get_connection

        try:
            with get_connection() as conn, conn.cursor() as cur:
                # Get total count
                if search:
                    cur.execute(
                        """
                        SELECT COUNT(*) as count FROM resumes
                        WHERE file_name ILIKE %s
                           OR json_data::text ILIKE %s
                        """,
                        (f"%{search}%", f"%{search}%"),
                    )
                else:
                    cur.execute("SELECT COUNT(*) as count FROM resumes")
                total = cur.fetchone()["count"]

                # Get resumes
                if search:
                    cur.execute(
                        """
                        SELECT id, file_name, file_path, embedding IS NOT NULL as has_embedding, json_data
                        FROM resumes
                        WHERE file_name ILIKE %s
                           OR json_data::text ILIKE %s
                        ORDER BY id DESC
                        LIMIT %s OFFSET %s
                        """,
                        (f"%{search}%", f"%{search}%", limit, offset),
                    )
                else:
                    cur.execute(
                        """
                        SELECT id, file_name, file_path, embedding IS NOT NULL as has_embedding, json_data
                        FROM resumes
                        ORDER BY id DESC
                        LIMIT %s OFFSET %s
                        """,
                        (limit, offset),
                    )
                rows = cur.fetchall()

            return ResumeListResponse(
                total=total,
                limit=limit,
                offset=offset,
                resumes=[
                    ResumeResponse(
                        id=row["id"],
                        file_name=row["file_name"],
                        file_path=row["file_path"],
                        has_embedding=row["has_embedding"],
                        json_data=row["json_data"] or {},
                    )
                    for row in rows
                ],
            )
        except Exception as e:
            logger.error(f"Database error: {e}")
            raise HTTPException(
                status_code=503,
                detail="Database unavailable. Make sure PostgreSQL is running.",
            ) from None

    # =========================================================================
    # Duplicates Management (must come before /resumes/{resume_id})
    # =========================================================================

    @app.get("/resumes/duplicates", tags=["Resumes"])
    async def find_duplicates() -> dict[str, Any]:
        """
        Find duplicate resumes (same content, different file names).
        
        Returns groups of duplicates with their file names and IDs.
        Useful for reviewing duplicates before cleaning.
        """
        from resume_matcher.db import find_duplicates as db_find_duplicates

        try:
            duplicates = db_find_duplicates()
            return {
                "duplicate_groups": len(duplicates),
                "total_duplicates": sum(d["count"] - 1 for d in duplicates),
                "groups": [
                    {
                        "file_hash": d["file_hash"][:16] + "...",
                        "count": d["count"],
                        "files": list(zip(d["ids"], d["file_names"], strict=True)),
                    }
                    for d in duplicates
                ],
            }
        except Exception as e:
            logger.error(f"Error finding duplicates: {e}")
            raise HTTPException(status_code=503, detail="Database unavailable") from None

    @app.post("/resumes/duplicates/clean", tags=["Resumes"])
    async def clean_duplicates_endpoint(
        dry_run: bool = Query(default=True, description="Preview only, don't actually delete"),
    ) -> dict[str, Any]:
        """
        Remove duplicate resumes, keeping the most recently updated version.
        
        By default, runs in dry_run mode (preview only).
        Set dry_run=false to actually delete duplicates.
        """
        from resume_matcher.db import clean_duplicates as db_clean_duplicates

        try:
            result = db_clean_duplicates(dry_run=dry_run)
            return result
        except Exception as e:
            logger.error(f"Error cleaning duplicates: {e}")
            raise HTTPException(status_code=503, detail="Database unavailable") from None

    @app.get("/resumes/{resume_id}", response_model=ResumeResponse, tags=["Resumes"])
    async def get_resume(resume_id: int) -> ResumeResponse:
        """Get a single resume by ID."""
        from resume_matcher.db import get_connection

        try:
            with get_connection() as conn, conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, file_name, file_path, embedding IS NOT NULL as has_embedding, json_data
                    FROM resumes
                    WHERE id = %s
                    """,
                    (resume_id,),
                )
                row = cur.fetchone()

            if not row:
                raise HTTPException(status_code=404, detail="Resume not found")

            return ResumeResponse(
                id=row["id"],
                file_name=row["file_name"],
                file_path=row["file_path"],
                has_embedding=row["has_embedding"],
                json_data=row["json_data"] or {},
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Database error: {e}")
            raise HTTPException(
                status_code=503,
                detail="Database unavailable. Make sure PostgreSQL is running.",
            ) from None

    @app.delete("/resumes/{resume_id}", tags=["Resumes"])
    async def delete_resume(resume_id: int) -> dict[str, str]:
        """Delete a resume by ID."""
        from resume_matcher.db import get_connection

        try:
            with get_connection() as conn, conn.cursor() as cur:
                cur.execute("DELETE FROM resumes WHERE id = %s RETURNING id", (resume_id,))
                deleted = cur.fetchone()
                conn.commit()

            if not deleted:
                raise HTTPException(status_code=404, detail="Resume not found")

            return {"status": "deleted", "id": str(resume_id)}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Database error: {e}")
            raise HTTPException(
                status_code=503,
                detail="Database unavailable. Make sure PostgreSQL is running.",
            ) from None

    # =========================================================================
    # Import
    # =========================================================================

    @app.post("/import", response_model=ImportResponse, tags=["Import"])
    async def import_resumes(
        directory: str = Form(default="data/resumes", description="Directory containing resumes"),
        force: bool = Form(default=False, description="Force re-import all files"),
        limit: int | None = Form(default=None, description="Limit number of files"),
    ) -> ImportResponse:
        """
        Trigger resume import from a directory.

        Note: This is a synchronous operation that may take a while for large directories.
        For production use, consider implementing as a background task.
        """
        from resume_matcher.scripts.cli_import import import_folder

        dir_path = Path(directory)
        if not dir_path.is_dir():
            raise HTTPException(status_code=400, detail=f"Directory not found: {directory}")

        files = list(dir_path.rglob("*.*"))
        total_files = len(files)

        if limit:
            files = files[:limit]

        # Note: For a production system, this should be a background task
        import_folder(
            resumes_dir=dir_path,
            workers=4,
            force_update=force,
            dry_run=False,
            limit=limit,
            only_sync=False,
        )

        return ImportResponse(
            status="completed",
            files_found=total_files,
            message=f"Import completed for {len(files)} files from {directory}",
        )

    @app.post("/import/file", tags=["Import"])
    async def import_single_file(
        file: Annotated[UploadFile, File(description="Resume file (PDF, DOCX, image)")],
        force: bool = Query(default=False, description="Force re-import if exists"),
    ) -> dict[str, Any]:
        """
        Import a single resume file.

        Supports PDF, DOCX, and image files (with OCR).
        """
        from resume_matcher.services.importer import import_resume

        # Save uploaded file temporarily
        suffix = Path(file.filename or "resume.pdf").suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            result = import_resume(tmp_path, force_update=force)

            if "error" in result:
                raise HTTPException(status_code=400, detail=result["error"])

            return {
                "status": "success",
                "file_name": file.filename,
                **result,
            }

        finally:
            # Clean up temp file
            Path(tmp_path).unlink(missing_ok=True)


# Create the default app instance
app = create_app()
