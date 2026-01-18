# src/resume_matcher/scripts/cli_match.py
"""
CLI for matching resumes against a vacancy.

Usage:
    # Fast embedding-only matching
    uv run match-vacancy --vacancy data/vacancies/Vacancy1.docx --top 10
    
    # Intelligent LLM-powered matching (recommended)
    uv run match-vacancy --vacancy data/vacancies/Vacancy1.docx --top 10 --llm

Flags:
    --vacancy      Path to vacancy file (PDF, DOCX, TXT)
    --text         Vacancy text directly (alternative to --vacancy)
    --top          Number of top matches to return (default: 10)
    --min-score    Minimum similarity score 0-100 (default: 0)
    --score-range  Score range filter, e.g. "80-100" (default: show all)
    --llm          Use LLM for intelligent re-ranking (slower but more accurate)
    --candidates   Number of embedding candidates for LLM to re-rank (default: 30)
    --json         Output results as JSON instead of pretty print
"""

import argparse
import json
import logging
import sys
from dataclasses import asdict

from resume_matcher.services.matcher import (
    MatchResult,
    match_vacancy_file,
    match_vacancy_text,
    match_vacancy_file_with_llm,
    match_vacancy_with_llm,
    print_match_results,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def parse_score_range(range_str: str | None) -> tuple[float, float] | None:
    """
    Parse score range string like '80-100' into (min, max) tuple.
    Returns None if no range specified.
    """
    if not range_str:
        return None
    
    try:
        parts = range_str.split("-")
        if len(parts) != 2:
            raise ValueError(f"Invalid range format: {range_str}. Use 'MIN-MAX' format, e.g. '80-100'")
        
        min_score = float(parts[0].strip())
        max_score = float(parts[1].strip())
        
        if min_score < 0 or max_score > 100:
            raise ValueError(f"Score range must be between 0 and 100")
        if min_score > max_score:
            raise ValueError(f"Min score ({min_score}) cannot be greater than max score ({max_score})")
        
        return (min_score, max_score)
    except ValueError as e:
        logger.error(f"Invalid score range: {e}")
        raise


def result_to_dict(result: MatchResult) -> dict:
    """Convert MatchResult to a JSON-serializable dict."""
    return {
        "mode": "embedding",
        "total_resumes_in_db": result.total_resumes_in_db,
        "matches_found": len(result.matches),
        "matches": [
            {
                "rank": i + 1,
                "id": m.id,
                "file_name": m.file_name,
                "file_path": m.file_path,
                "similarity_percent": m.score_percent,
                "candidate": {
                    "name": m.json_data.get("full_name"),
                    "position": m.json_data.get("current_position"),
                    "email": m.json_data.get("email"),
                    "phone": m.json_data.get("phone"),
                    "skills": m.json_data.get("skills", []),
                    "years_experience": m.json_data.get("years_experience"),
                    "summary": m.json_data.get("summary"),
                },
            }
            for i, m in enumerate(result.matches)
        ],
    }


def llm_result_to_dict(requirements, scores) -> dict:
    """Convert LLM results to a JSON-serializable dict."""
    return {
        "mode": "llm",
        "vacancy": {
            "job_title": requirements.job_title,
            "seniority_level": requirements.seniority_level,
            "must_have_skills": requirements.must_have_skills,
            "nice_to_have_skills": requirements.nice_to_have_skills,
            "min_years_experience": requirements.min_years_experience,
            "summary": requirements.summary,
        },
        "matches_found": len(scores),
        "matches": [
            {
                "rank": i + 1,
                "id": s.candidate_id,
                "file_name": s.file_name,
                "combined_score": s.combined_score,
                "llm_score": s.llm_score,
                "embedding_score_percent": round(s.embedding_score * 100, 2),
                "match_level": s.match_level,
                "matching_skills": s.matching_skills,
                "missing_skills": s.missing_skills,
                "strengths": s.strengths,
                "concerns": s.concerns,
                "explanation": s.explanation,
            }
            for i, s in enumerate(scores)
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Match resumes against a vacancy description"
    )

    # Input options (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--vacancy", type=str, help="Path to vacancy file (PDF, DOCX, TXT)"
    )
    input_group.add_argument("--text", type=str, help="Vacancy text directly")

    # Matching options
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of top matches to return (default: 10)",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=0,
        help="Minimum similarity score 0-100 (default: 0)",
    )
    parser.add_argument(
        "--score-range",
        type=str,
        default=None,
        help="Score range filter, e.g. '80-100' to show only scores in that range",
    )

    # LLM options
    parser.add_argument(
        "--llm",
        action="store_true",
        help="Use LLM for intelligent re-ranking (slower but more accurate)",
    )
    parser.add_argument(
        "--candidates",
        type=int,
        default=30,
        help="Number of embedding candidates for LLM re-ranking (default: 30)",
    )

    # Output options
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument(
        "--quiet", action="store_true", help="Suppress logging output"
    )

    args = parser.parse_args()

    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)

    # Convert min-score from percentage to 0-1 range
    min_similarity = args.min_score / 100.0

    # Parse score range filter
    score_range = parse_score_range(args.score_range)
    if score_range:
        logger.info(f"Filtering results to score range: {score_range[0]}-{score_range[1]}")

    # Determine vacancy text
    vacancy_input = args.vacancy or args.text
    is_file = args.vacancy is not None

    if args.llm:
        # LLM-powered matching
        logger.info("Using LLM-powered matching (2-stage: embedding + LLM re-ranking)")

        if is_file:
            requirements, scores = match_vacancy_file_with_llm(
                args.vacancy,
                top_n=args.top,
                embedding_candidates=args.candidates,
                min_similarity=min_similarity,
            )
        else:
            requirements, scores = match_vacancy_with_llm(
                args.text,
                top_n=args.top,
                embedding_candidates=args.candidates,
                min_similarity=min_similarity,
            )

        # Apply score range filter (LLM uses combined_score)
        if score_range:
            min_s, max_s = score_range
            scores = [s for s in scores if min_s <= s.combined_score <= max_s]
            logger.info(f"After range filter: {len(scores)} candidates")

        # Output
        if args.json:
            print(json.dumps(llm_result_to_dict(requirements, scores), indent=2, ensure_ascii=False))
        else:
            from resume_matcher.models.llm_scorer import print_scored_results
            print_scored_results(requirements, scores)

        if not scores:
            sys.exit(1)

    else:
        # Embedding-only matching (fast)
        logger.info("Using embedding-only matching (fast mode)")

        if is_file:
            result = match_vacancy_file(
                args.vacancy,
                top_n=args.top,
                min_similarity=min_similarity,
            )
        else:
            result = match_vacancy_text(
                args.text,
                top_n=args.top,
                min_similarity=min_similarity,
            )

        # Apply score range filter (embedding uses score_percent)
        if score_range:
            min_s, max_s = score_range
            result.matches = [m for m in result.matches if min_s <= m.score_percent <= max_s]
            logger.info(f"After range filter: {len(result.matches)} candidates")

        # Output
        if args.json:
            print(json.dumps(result_to_dict(result), indent=2, ensure_ascii=False))
        else:
            print_match_results(result)

        if not result.matches:
            sys.exit(1)


if __name__ == "__main__":
    main()
