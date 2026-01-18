# src/resume_matcher/services/matcher.py
"""
Resume matching service.

Takes a vacancy description, generates its embedding, and finds
the most similar resumes using pgvector cosine similarity search.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from resume_matcher.models.llm_scorer import CandidateScore, VacancyRequirements

from resume_matcher.db import get_connection
from resume_matcher.models.embedding import get_embedding
from resume_matcher.utils.convert_file_to_text import convert_file_to_text
from resume_matcher.utils.text_cleaner import clean_ocr_text

logger = logging.getLogger(__name__)


@dataclass
class MatchedResume:
    """A single matched resume with similarity score."""

    id: int
    file_name: str
    file_path: str
    similarity_score: float  # 0.0 to 1.0, higher = better match
    json_data: dict[str, Any]

    @property
    def score_percent(self) -> float:
        """Returns similarity as percentage (0-100)."""
        return round(self.similarity_score * 100, 2)


@dataclass
class MatchResult:
    """Result of a matching operation."""

    vacancy_text: str
    total_resumes_in_db: int
    matches: list[MatchedResume]

    @property
    def top_match(self) -> MatchedResume | None:
        """Returns the best match, if any."""
        return self.matches[0] if self.matches else None


def match_vacancy_text(
    vacancy_text: str,
    top_n: int = 10,
    min_similarity: float = 0.0,
) -> MatchResult:
    """
    Finds top-N resumes most similar to the given vacancy text.

    Args:
        vacancy_text: The vacancy/job description text.
        top_n: Maximum number of results to return.
        min_similarity: Minimum similarity threshold (0.0 to 1.0).

    Returns:
        MatchResult with ranked candidates.
    """
    if not vacancy_text or not vacancy_text.strip():
        logger.warning("Empty vacancy text provided")
        return MatchResult(vacancy_text="", total_resumes_in_db=0, matches=[])

    # Clean and generate embedding for vacancy
    cleaned_vacancy = clean_ocr_text(vacancy_text)
    logger.info(f"Generating embedding for vacancy ({len(cleaned_vacancy)} chars)")
    vacancy_embedding = get_embedding(cleaned_vacancy)

    # Query database for similar resumes using pgvector
    matches = _find_similar_resumes(
        vacancy_embedding,
        top_n=top_n,
        min_similarity=min_similarity,
    )

    # Get total count
    total_count = _get_total_resume_count()

    logger.info(f"Found {len(matches)} matches out of {total_count} resumes")

    return MatchResult(
        vacancy_text=cleaned_vacancy,
        total_resumes_in_db=total_count,
        matches=matches,
    )


def match_vacancy_file(
    vacancy_path: str | Path,
    top_n: int = 10,
    min_similarity: float = 0.0,
) -> MatchResult:
    """
    Finds top-N resumes most similar to a vacancy from a file.

    Args:
        vacancy_path: Path to vacancy file (PDF, DOCX, TXT, etc.)
        top_n: Maximum number of results to return.
        min_similarity: Minimum similarity threshold (0.0 to 1.0).

    Returns:
        MatchResult with ranked candidates.
    """
    path = Path(vacancy_path)
    if not path.is_file():
        logger.error(f"Vacancy file not found: {path}")
        return MatchResult(vacancy_text="", total_resumes_in_db=0, matches=[])

    logger.info(f"Loading vacancy from: {path.name}")
    vacancy_text = convert_file_to_text(path)

    if not vacancy_text.strip():
        logger.error(f"Could not extract text from vacancy file: {path}")
        return MatchResult(vacancy_text="", total_resumes_in_db=0, matches=[])

    return match_vacancy_text(
        vacancy_text,
        top_n=top_n,
        min_similarity=min_similarity,
    )


def _find_similar_resumes(
    vacancy_embedding: np.ndarray,
    top_n: int,
    min_similarity: float,
) -> list[MatchedResume]:
    """
    Queries pgvector for resumes similar to the vacancy embedding.

    Uses cosine distance: 1 - cosine_similarity
    So we need to convert back: similarity = 1 - distance
    """
    # pgvector's <=> operator returns cosine distance (0 = identical, 2 = opposite)
    # similarity = 1 - distance (for normalized vectors)
    # We filter where distance <= (1 - min_similarity)
    max_distance = 1.0 - min_similarity

    with get_connection() as conn, conn.cursor() as cur:
        # Query using pgvector cosine distance operator <=>
        cur.execute(
            """
            SELECT
                id,
                file_name,
                file_path,
                json_data,
                1 - (embedding <=> %s::vector) AS similarity
            FROM resumes
            WHERE embedding IS NOT NULL
              AND (embedding <=> %s::vector) <= %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """,
            (
                vacancy_embedding.tolist(),
                vacancy_embedding.tolist(),
                max_distance,
                vacancy_embedding.tolist(),
                top_n,
            ),
        )

        rows = cur.fetchall()

    matches = []
    for row in rows:
        # Parse json_data if it's a string
        json_data = row["json_data"]
        if isinstance(json_data, str):
            import json

            try:
                json_data = json.loads(json_data)
            except json.JSONDecodeError:
                json_data = {}

        matches.append(
            MatchedResume(
                id=row["id"],
                file_name=row["file_name"],
                file_path=row["file_path"],
                similarity_score=float(row["similarity"]),
                json_data=json_data or {},
            )
        )

    return matches


def _get_total_resume_count() -> int:
    """Returns total number of resumes in the database."""
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) as count FROM resumes WHERE embedding IS NOT NULL")
        result = cur.fetchone()
        return int(result["count"]) if result else 0


def print_match_results(result: MatchResult) -> None:
    """Pretty-prints match results to console."""
    print(f"\n{'=' * 60}")
    print("VACANCY MATCHING RESULTS")
    print(f"{'=' * 60}")
    print(f"Total resumes in database: {result.total_resumes_in_db}")
    print(f"Matches found: {len(result.matches)}")
    print(f"{'=' * 60}\n")

    if not result.matches:
        print("No matching resumes found.")
        return

    for i, match in enumerate(result.matches, 1):
        json_data = match.json_data
        name = json_data.get("full_name") or "Unknown"
        position = json_data.get("current_position") or "N/A"
        skills = json_data.get("skills") or []
        skills_str = ", ".join(skills[:5]) + ("..." if len(skills) > 5 else "")

        print(f"#{i} | Score: {match.score_percent}%")
        print(f"    Name: {name}")
        print(f"    Position: {position}")
        print(f"    Skills: {skills_str or 'N/A'}")
        print(f"    File: {match.file_name}")
        print()


# ============================================================================
# LLM-POWERED MATCHING (Re-ranking with intelligent scoring)
# ============================================================================


def match_vacancy_with_llm(
    vacancy_text: str,
    top_n: int = 10,
    embedding_candidates: int = 30,
    min_similarity: float = 0.0,
) -> tuple[VacancyRequirements, list[CandidateScore]]:
    """
    Two-stage matching: embedding search + LLM re-ranking.

    Stage 1: Fast embedding search to get candidate pool
    Stage 2: LLM scores each candidate for role fit, skills, etc.

    Args:
        vacancy_text: The vacancy/job description text.
        top_n: Final number of results after LLM re-ranking.
        embedding_candidates: Number of candidates from embedding search (should be > top_n).
        min_similarity: Minimum embedding similarity threshold.

    Returns:
        Tuple of (VacancyRequirements, list of CandidateScore)
    """
    from resume_matcher.models.llm_scorer import (
        VacancyRequirements,
        rerank_with_llm,
    )

    if not vacancy_text or not vacancy_text.strip():
        logger.warning("Empty vacancy text provided")
        return VacancyRequirements(
            job_title="Unknown",
            department=None,
            seniority_level=None,
            must_have_skills=[],
            nice_to_have_skills=[],
            min_years_experience=None,
            responsibilities=[],
            location=None,
            remote_ok=False,
            summary="",
        ), []

    # Stage 1: Get candidates from embedding search
    logger.info(f"Stage 1: Finding top {embedding_candidates} candidates via embedding search...")
    cleaned_vacancy = clean_ocr_text(vacancy_text)
    vacancy_embedding = get_embedding(cleaned_vacancy)

    matches = _find_similar_resumes(
        vacancy_embedding,
        top_n=embedding_candidates,
        min_similarity=min_similarity,
    )

    if not matches:
        logger.warning("No candidates found in embedding search")
        return VacancyRequirements(
            job_title="Unknown",
            department=None,
            seniority_level=None,
            must_have_skills=[],
            nice_to_have_skills=[],
            min_years_experience=None,
            responsibilities=[],
            location=None,
            remote_ok=False,
            summary="",
        ), []

    # Convert to dict format for LLM scorer
    candidates = [
        {
            "id": m.id,
            "file_name": m.file_name,
            "file_path": m.file_path,
            "similarity_score": m.similarity_score,
            "json_data": m.json_data,
        }
        for m in matches
    ]

    # Stage 2: Re-rank with LLM
    logger.info(f"Stage 2: Re-ranking {len(candidates)} candidates with LLM...")
    requirements, scores = rerank_with_llm(
        vacancy_text=cleaned_vacancy,
        candidates=candidates,
        top_n=top_n,
    )

    return requirements, scores


def match_vacancy_file_with_llm(
    vacancy_path: str | Path,
    top_n: int = 10,
    embedding_candidates: int = 30,
    min_similarity: float = 0.0,
) -> tuple[VacancyRequirements, list[CandidateScore]]:
    """
    Two-stage matching from a vacancy file.

    Args:
        vacancy_path: Path to vacancy file (PDF, DOCX, TXT, etc.)
        top_n: Final number of results after LLM re-ranking.
        embedding_candidates: Number of candidates from embedding search.
        min_similarity: Minimum embedding similarity threshold.

    Returns:
        Tuple of (VacancyRequirements, list of CandidateScore)
    """
    from resume_matcher.models.llm_scorer import VacancyRequirements

    path = Path(vacancy_path)
    if not path.is_file():
        logger.error(f"Vacancy file not found: {path}")
        return VacancyRequirements(
            job_title="Unknown",
            department=None,
            seniority_level=None,
            must_have_skills=[],
            nice_to_have_skills=[],
            min_years_experience=None,
            responsibilities=[],
            location=None,
            remote_ok=False,
            summary="",
        ), []

    logger.info(f"Loading vacancy from: {path.name}")
    vacancy_text = convert_file_to_text(path)

    if not vacancy_text.strip():
        logger.error(f"Could not extract text from vacancy file: {path}")
        return VacancyRequirements(
            job_title="Unknown",
            department=None,
            seniority_level=None,
            must_have_skills=[],
            nice_to_have_skills=[],
            min_years_experience=None,
            responsibilities=[],
            location=None,
            remote_ok=False,
            summary="",
        ), []

    return match_vacancy_with_llm(
        vacancy_text,
        top_n=top_n,
        embedding_candidates=embedding_candidates,
        min_similarity=min_similarity,
    )
