# src/resume_matcher/models/llm_scorer.py
"""
LLM-based scoring for resume-vacancy matching.

Provides intelligent re-ranking of embedding-based matches by:
1. Parsing vacancy requirements (job title, must-have skills, nice-to-have, experience)
2. Scoring each candidate against those specific requirements
3. Generating human-readable explanations for each match
"""

import json
import logging
import os
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

logger = logging.getLogger(__name__)

GROQ_CLIENT = Groq(api_key=os.getenv("GROQ_API_KEY"))
GROQ_MODEL = "llama-3.3-70b-versatile"


@dataclass
class VacancyRequirements:
    """Structured requirements extracted from a vacancy."""

    job_title: str
    department: str | None
    seniority_level: str | None  # junior, middle, senior, lead, etc.
    must_have_skills: list[str]
    nice_to_have_skills: list[str]
    min_years_experience: int | None
    responsibilities: list[str]
    location: str | None
    remote_ok: bool
    summary: str


@dataclass
class CandidateScore:
    """Scoring result for a single candidate."""

    candidate_id: int
    file_name: str
    llm_score: int  # 0-100
    embedding_score: float  # Original embedding similarity
    combined_score: float  # Weighted combination
    match_level: str  # "excellent", "good", "partial", "poor"
    explanation: str  # Human-readable explanation
    matching_skills: list[str]
    missing_skills: list[str]
    strengths: list[str]
    concerns: list[str]


def parse_vacancy(vacancy_text: str) -> VacancyRequirements:
    """
    Extracts structured requirements from vacancy text using LLM.
    """
    prompt = f"""You are an expert HR analyst. Extract structured requirements from this job vacancy.
Return ONLY a valid JSON object, without extra text, without markdown, without ```json.

Required JSON structure:
{{
  "job_title": "exact job title from the vacancy",
  "department": "department or team name if mentioned, or null",
  "seniority_level": "junior/middle/senior/lead/principal or null if unclear",
  "must_have_skills": ["list", "of", "required", "skills"],
  "nice_to_have_skills": ["list", "of", "optional", "skills"],
  "min_years_experience": integer or null,
  "responsibilities": ["key", "job", "responsibilities"],
  "location": "location if mentioned or null",
  "remote_ok": true/false based on vacancy text,
  "summary": "1-2 sentence summary of what this role is about"
}}

IMPORTANT: 
- must_have_skills should only include skills explicitly marked as required/mandatory
- nice_to_have_skills are skills marked as "preferred", "bonus", "plus", etc.
- Be specific with skills (e.g., "Kubernetes" not just "containers")

Vacancy text:
{vacancy_text[:12000]}
"""

    try:
        response = GROQ_CLIENT.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=1500,
            top_p=1.0,
        )

        content = response.choices[0].message.content.strip()

        # Remove possible markdown
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        data = json.loads(content)
        logger.info(f"Parsed vacancy: {data.get('job_title', 'Unknown')}")

        return VacancyRequirements(
            job_title=data.get("job_title", "Unknown"),
            department=data.get("department"),
            seniority_level=data.get("seniority_level"),
            must_have_skills=data.get("must_have_skills", []),
            nice_to_have_skills=data.get("nice_to_have_skills", []),
            min_years_experience=data.get("min_years_experience"),
            responsibilities=data.get("responsibilities", []),
            location=data.get("location"),
            remote_ok=data.get("remote_ok", False),
            summary=data.get("summary", ""),
        )

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse vacancy JSON: {e}")
        # Return minimal requirements
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
        )
    except Exception as e:
        logger.error(f"Error parsing vacancy: {e}")
        raise


def score_candidate(
    requirements: VacancyRequirements,
    candidate_json: dict[str, Any],
    candidate_name: str,
    embedding_similarity: float,
) -> CandidateScore:
    """
    Scores a single candidate against vacancy requirements using LLM.
    """
    candidate_skills = candidate_json.get("skills", [])
    candidate_position = candidate_json.get("current_position", "Unknown")
    candidate_experience = candidate_json.get("years_experience")
    candidate_summary = candidate_json.get("summary", "")

    prompt = f"""You are an expert technical recruiter. Score this candidate against the job requirements.
Return ONLY a valid JSON object, without extra text, without markdown.

Job Requirements:
- Title: {requirements.job_title}
- Seniority: {requirements.seniority_level or 'Not specified'}
- Must-have skills: {', '.join(requirements.must_have_skills) or 'None specified'}
- Nice-to-have skills: {', '.join(requirements.nice_to_have_skills) or 'None specified'}
- Min experience: {requirements.min_years_experience or 'Not specified'} years
- Summary: {requirements.summary}

Candidate Profile:
- Name: {candidate_name}
- Current position: {candidate_position}
- Years of experience: {candidate_experience or 'Unknown'}
- Skills: {', '.join(candidate_skills[:30]) if candidate_skills else 'Not listed'}
- Summary: {candidate_summary or 'Not provided'}

Scoring criteria:
1. Role fit: Is the candidate's background relevant to this specific role?
2. Must-have skills: How many required skills does the candidate have?
3. Experience level: Does their experience match the seniority required?
4. Nice-to-have: Any bonus skills that add value?

Return this exact JSON structure:
{{
  "score": 0-100 integer (0=completely irrelevant, 100=perfect match),
  "match_level": "excellent"/"good"/"partial"/"poor",
  "matching_skills": ["skills", "candidate", "has", "that", "match", "requirements"],
  "missing_skills": ["required", "skills", "candidate", "lacks"],
  "strengths": ["2-3 specific strengths for this role"],
  "concerns": ["1-2 potential concerns or gaps"],
  "explanation": "2-3 sentence explanation of why this score was given"
}}

IMPORTANT:
- A Software Engineer is NOT a good match for DevOps unless they have specific DevOps skills
- A Product Designer is NOT a match for engineering roles
- Score based on ROLE FIT first, then skills
- Be strict: partial matches should score 40-60, good matches 70-85, excellent 85+
"""

    try:
        response = GROQ_CLIENT.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=800,
            top_p=1.0,
        )

        content = response.choices[0].message.content.strip()

        # Remove possible markdown
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        data = json.loads(content)

        llm_score = int(data.get("score", 0))
        # Combined score: 70% LLM, 30% embedding similarity
        combined = (llm_score * 0.7) + (embedding_similarity * 100 * 0.3)

        return CandidateScore(
            candidate_id=0,  # Will be set by caller
            file_name="",  # Will be set by caller
            llm_score=llm_score,
            embedding_score=embedding_similarity,
            combined_score=round(combined, 2),
            match_level=data.get("match_level", "unknown"),
            explanation=data.get("explanation", "No explanation provided"),
            matching_skills=data.get("matching_skills", []),
            missing_skills=data.get("missing_skills", []),
            strengths=data.get("strengths", []),
            concerns=data.get("concerns", []),
        )

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse scoring JSON: {e}")
        return CandidateScore(
            candidate_id=0,
            file_name="",
            llm_score=0,
            embedding_score=embedding_similarity,
            combined_score=embedding_similarity * 30,
            match_level="error",
            explanation="Failed to score candidate",
            matching_skills=[],
            missing_skills=[],
            strengths=[],
            concerns=["Scoring failed"],
        )
    except Exception as e:
        logger.error(f"Error scoring candidate: {e}")
        raise


def rerank_with_llm(
    vacancy_text: str,
    candidates: list[dict[str, Any]],
    top_n: int = 10,
) -> tuple[VacancyRequirements, list[CandidateScore]]:
    """
    Re-ranks candidates using LLM scoring.

    Args:
        vacancy_text: The vacancy/job description text
        candidates: List of candidate dicts with keys:
            - id, file_name, file_path, similarity_score, json_data
        top_n: Number of results to return after re-ranking

    Returns:
        Tuple of (VacancyRequirements, list of CandidateScore sorted by combined_score)
    """
    logger.info(f"Parsing vacancy requirements...")
    requirements = parse_vacancy(vacancy_text)

    logger.info(f"Vacancy: {requirements.job_title}")
    logger.info(f"Must-have skills: {requirements.must_have_skills}")

    scores: list[CandidateScore] = []

    logger.info(f"Scoring {len(candidates)} candidates with LLM...")
    for i, candidate in enumerate(candidates):
        candidate_name = candidate.get("json_data", {}).get("full_name", "Unknown")
        logger.info(f"  [{i+1}/{len(candidates)}] Scoring: {candidate_name}")

        score = score_candidate(
            requirements=requirements,
            candidate_json=candidate.get("json_data", {}),
            candidate_name=candidate_name,
            embedding_similarity=candidate.get("similarity_score", 0.0),
        )

        # Set IDs from candidate data
        score.candidate_id = candidate.get("id", 0)
        score.file_name = candidate.get("file_name", "")

        scores.append(score)

    # Sort by combined score (descending)
    scores.sort(key=lambda x: x.combined_score, reverse=True)

    return requirements, scores[:top_n]


def print_scored_results(
    requirements: VacancyRequirements,
    scores: list[CandidateScore],
) -> None:
    """Pretty-prints LLM-scored results."""
    print("\n" + "=" * 70)
    print("VACANCY ANALYSIS")
    print("=" * 70)
    print(f"Position: {requirements.job_title}")
    print(f"Seniority: {requirements.seniority_level or 'Not specified'}")
    print(f"Must-have: {', '.join(requirements.must_have_skills[:5]) or 'None'}")
    if requirements.nice_to_have_skills:
        print(f"Nice-to-have: {', '.join(requirements.nice_to_have_skills[:5])}")
    print("=" * 70)

    print("\n" + "=" * 70)
    print("RANKED CANDIDATES (LLM-scored)")
    print("=" * 70 + "\n")

    if not scores:
        print("No candidates scored.")
        return

    for i, score in enumerate(scores, 1):
        match_emoji = {
            "excellent": "🟢",
            "good": "🟡", 
            "partial": "🟠",
            "poor": "🔴",
        }.get(score.match_level, "⚪")

        print(f"#{i} {match_emoji} {score.match_level.upper()} | Score: {score.combined_score:.1f}")
        print(f"   LLM: {score.llm_score}/100 | Embedding: {score.embedding_score*100:.1f}%")
        print(f"   File: {score.file_name}")
        print(f"   ✓ Matching: {', '.join(score.matching_skills[:5]) or 'None'}")
        if score.missing_skills:
            print(f"   ✗ Missing: {', '.join(score.missing_skills[:5])}")
        print(f"   → {score.explanation}")
        print()
