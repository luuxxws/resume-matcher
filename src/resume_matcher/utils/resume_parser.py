# src/resume_matcher/utils/resume_parser.py
"""
Parsing structured data from resume text.

Main fields extracted:
- name / full name
- email
- phone number
- links (LinkedIn, GitHub, Telegram, etc.)
- location
- desired position / current position
- skills (Skills / Technologies) — the most difficult block, currently simple heuristics

Methods:
- regex + section rules (SUMMARY, EXPERIENCE, SKILLS, etc.)
- normalization and cleaning of extracted values
"""
import re
from typing import Dict, List, Optional, Any
import logging

from ..config import KNOWN_OCCUPATIONS, KNOWN_SKILLS, OCCUPATION_NORMALIZED

logger = logging.getLogger(__name__)

def parse_resume(text: str) -> Dict[str, Any]:
    """
    The main function of resume parsing.

    Arguments:
        text: cleaned resume text (after OCR and text_cleaner).

    Returns:
        a dictionary with extracted fields.
    """
    if not text or not text.strip():
        return {"error": "Text is empty"}

    result: Dict[str, Any] = {
        "raw_text_length": len(text),
        "extracted_fields": {},
        "confidence": {},  # confidence level in each field (0–1)
    }

    # Normalizing text for easy searching
    normalized = text.lower()

    # 1. Email
    email = extract_email(text)
    if email:
        result["extracted_fields"]["email"] = email
        result["confidence"]["email"] = 0.95 if "@" in email else 0.7

    # 2. Phone number
    phone = extract_phone(text)
    if phone:
        result["extracted_fields"]["phone"] = phone
        result["confidence"]["phone"] = 0.9

    # 3. Name / Full name
    name = extract_name(text)
    if name:
        result["extracted_fields"]["name"] = name
        result["confidence"]["name"] = 0.75

    # 4. Links (LinkedIn, GitHub, Telegram, etc.)
    links = extract_links(text)
    if links:
        result["extracted_fields"]["links"] = links

    # 5. Location (city, country)
    location = extract_location(text)
    if location:
        result["extracted_fields"]["location"] = location

    # 6. Skills
    skills = extract_skills(text)
    if skills:
        result["extracted_fields"]["skills"] = skills
        result["confidence"]["skills"] = 0.6

    # 7. Desired / Current position (often in SUMMARY or the header)
    position = extract_position(text)
    if position:
        result["extracted_fields"]["position"] = position

    logger.info(f"Fields extracted: {len(result['extracted_fields'])}")
    return result


# ─── Auxiliary extraction functions ─────────────────────────────────────────

def extract_email(text: str) -> Optional[str]:
    """Finds the first valid email in the text"""
    pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    match = re.search(pattern, text)
    return match.group(0) if match else None


def extract_phone(text: str) -> Optional[str]:
    """Finds phone number"""
    # Removing unnecessary characters from the search
    cleaned = re.sub(r'[\s\-\(\)\+]', '', text)

    patterns = [
        r'(\+?\d{1,3})?\s*(\d{3})\s*(\d{3})\s*(\d{2})\s*(\d{2})',  # +7 917 753 54 98
        r'(\+?\d{1,3})?[\s.-]*(\d{3})[\s.-]*(\d{3})[\s.-]*(\d{4})',  # +1 555-123-4567
        r'(\+?\d{1,3})?[\s(]*(\d{3})[\s)]*(\d{3})[\s-]*(\d{2})[\s-]*(\d{2})',
    ]

    for pattern in patterns:
        match = re.search(pattern, cleaned)
        if match:
            parts = [g for g in match.groups() if g]
            return ''.join(parts)
    return None


def extract_name(text: str) -> Optional[str]:
    """Attempts to find the full name at the beginning of the text"""
    lines = text.splitlines()
    for i, line in enumerate(lines[:10]):  # searching in first 10 lines
        line = line.strip()
        if not line:
            continue

        # Simple heuristics: 2–4 words, capital letters, no @ / http
        words = line.split()
        if 1 < len(words) <= 4 and not any(s in line.lower() for s in ['@', 'http', 'www', 'github', 'linkedin']):
            capitals = sum(w[0].isupper() for w in words if w)
            if capitals >= len(words) - 1:
                return line.strip()

    return None


def extract_links(text: str) -> Dict[str, str]:
    """Finds links to LinkedIn, GitHub, Telegram, a website"""
    links = {}
    patterns = {
        "linkedin": r'(?:linkedin\.com/in/|linkedin\.com/company/)[^\s<>"]+',
        "github": r'(?:github\.com/)[^\s<>"]+',
        "telegram": r'(?:t\.me/|telegram\.me/)[^\s<>"]+',
        "website": r'(?:https?://(?:www\.)?)[^\s<>"]+\.[a-z]{2,}(?:/[^\s<>"]*)?',
    }

    for name, pattern in patterns.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            # Taking first normalized link
            link = matches[0]
            if not link.startswith('http'):
                link = 'https://' + link
            links[name] = link

    return links


def extract_location(text: str) -> Optional[str]:
    """Searches for location (often in the title or SUMMARY)"""
    patterns = [
        r'(?:Madrid|Moscow|Saint Petersburg|Россия|Spain|Russian Federation)[,\s]*(?:[A-Z][a-z]+)?',
        r'(?:Москва|Санкт-Петербург|Мадрид|Россия|Испания)[,\s]*\w*',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    return None


def extract_position(text: str) -> Optional[str]:
    """Searches for position, using ESCO taxonomy"""
    lines = [line.strip() for line in text.splitlines()[:20] if line.strip()]

    for line in lines:
        lower_line = line.lower()

        # Option 1: Exact match with a known position
        if lower_line in OCCUPATION_NORMALIZED:
            return OCCUPATION_NORMALIZED[lower_line]

        # Option 2: at least 2 words from the string are in the taxonomy
        words = set(lower_line.split())
        matches = words & KNOWN_OCCUPATIONS
        if len(matches) >= 2:
            return line.strip()

        # Option 3: one word + level (Senior, Lead, Junior, etc.)
        level_words = {'senior', 'lead', 'junior', 'chief', 'head', 'principal'}
        if len(matches) >= 1 and any(lw in words for lw in level_words):
            return line.strip()

    return None


def extract_skills(text: str) -> List[str]:
    """Searches for skills, using ESCO skills"""
    skills_found = set()

    # Looking for the Skills / Technical Skills section, etc.
    start_markers = ["skills", "technical skills", "навыки", "технические навыки", "technologies", "stack"]
    end_markers = ["experience", "опыт", "education", "образование", "languages"]

    lines = text.splitlines()
    in_skills_section = False

    for line in lines:
        lower = line.lower().strip()
        if any(m in lower for m in start_markers):
            in_skills_section = True
            continue
        if any(m in lower for m in end_markers):
            in_skills_section = False
            continue

        if in_skills_section or len(line.strip()) < 100:  # Short lines after Skills
            # Breaking down into commas, semicolons, and hyphens
            candidates = re.split(r'[,;•|]\s*|\n+', line.strip())
            for cand in candidates:
                cand = cand.strip()
                if 3 <= len(cand) <= 40:
                    lower_cand = cand.lower()
                    if lower_cand in KNOWN_SKILLS:
                        skills_found.add(cand.strip())

    return sorted(list(skills_found))
