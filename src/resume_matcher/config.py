# src/resume_matcher/config.py

import csv
import logging
import os
from pathlib import Path

import torch
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()


# ─── Paths variables ────────────────────────────────────────–––––––––––––––––––––


def _get_data_dir() -> Path:
    """Get the data directory - supports both local dev and Docker deployment."""
    # 1. Check environment variable (highest priority)
    if env_data_dir := os.getenv("DATA_DIR"):
        return Path(env_data_dir)

    # 2. Check if we're in Docker (/app/data exists)
    docker_data = Path("/app/data")
    if docker_data.exists():
        return docker_data

    # 3. Local development: relative to project root
    # Try to find project root by looking for pyproject.toml
    current = Path(__file__).resolve().parent
    for _ in range(5):  # Go up max 5 levels
        if (current / "pyproject.toml").exists():
            return current / "data"
        current = current.parent

    # 4. Fallback: relative to this file (may not work when installed)
    return Path(__file__).resolve().parent.parent.parent / "data"


DATA_DIR: Path = _get_data_dir()
RESUMES_DIR: Path = DATA_DIR / "resumes"  # folder with 10k+ resumes
VACANCIES_DIR: Path = DATA_DIR / "vacancies"  # vacancy descriptions (txt, md, pdf...)
OUTPUT_DIR: Path = DATA_DIR / "output"  # results: csv, json, embeddings cache

for d in [DATA_DIR, RESUMES_DIR, VACANCIES_DIR, OUTPUT_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# ─── Embedding variables ────────────────────────────────────────–––––––––––––––––

EMBEDDING_MODEL_NAME = "intfloat/multilingual-e5-large"
EMBEDDING_CACHE_DIR = DATA_DIR / "embedding_cache"
DEVICE = (
    "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"
)


# ─── Taxonomy variables ────────────────────────────────────────––––––––––––––––––

KNOWN_OCCUPATIONS: set[str] = set()
OCCUPATION_NORMALIZED: dict[str, str] = {}
KNOWN_SKILLS: set[str] = set()
OCCUPATION_TO_SKILLS: dict[str, list[str]] = {}
ESCO_TAXONOMY_DIR = DATA_DIR / "taxonomy"


def load_esco_occupations():
    """Downloads occupations_en.csv - the main source of occupations"""
    global KNOWN_OCCUPATIONS, OCCUPATION_NORMALIZED

    file_path = ESCO_TAXONOMY_DIR / "occupations_en.csv"
    if not file_path.exists():
        logger.warning(f"The file occupations_en.csv was not found: {file_path}")
        return

    count = 0
    try:
        with open(file_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Main label
                pref = row.get("preferredLabel", "").strip()
                if pref:
                    lower_pref = pref.lower()
                    KNOWN_OCCUPATIONS.add(lower_pref)
                    OCCUPATION_NORMALIZED[lower_pref] = pref
                    count += 1

                # Alternative labels
                alts = row.get("altLabels", "")
                if alts:
                    for alt in alts.split(";"):
                        alt = alt.strip()
                        if alt:
                            lower_alt = alt.lower()
                            KNOWN_OCCUPATIONS.add(lower_alt)
                            OCCUPATION_NORMALIZED[lower_alt] = pref
                            count += 1

        logger.info(f"Downloaded {count:,} occupation labels from occupations_en.csv")
    except Exception as e:
        logger.error(f"Failed to download occupations_en.csv: {e}")


def load_esco_skills():
    """Downloads skills_en.csv — the list of all skills"""
    global KNOWN_SKILLS

    file_path = ESCO_TAXONOMY_DIR / "skills_en.csv"
    if not file_path.exists():
        logger.warning(f"File skills_en.csv was not found: {file_path}")
        return

    count = 0
    try:
        with open(file_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                pref = row.get("preferredLabel", "").strip()
                if pref:
                    KNOWN_SKILLS.add(pref.lower())
                    count += 1

                alts = row.get("altLabels", "")
                if alts:
                    for alt in alts.split(";"):
                        alt = alt.strip()
                        if alt:
                            KNOWN_SKILLS.add(alt.lower())
                            count += 1

        logger.info(f"Downloaded {count:,} skills from skills_en.csv")
    except Exception as e:
        logger.error(f"Failed to download skills_en.csv: {e}")


def load_esco_relations():
    """Downloads occupation-skills realtions"""
    global OCCUPATION_TO_SKILLS

    file_path = ESCO_TAXONOMY_DIR / "occupationSkillRelations_en.csv"
    if not file_path.exists():
        logger.warning("File occupationSkillRelations_en.csv was not found")
        return

    count = 0
    try:
        with open(file_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                occ_uri = row.get("occupationUri", "")
                skill_uri = row.get("skillUri", "")

                if occ_uri and skill_uri:
                    # Can be stored by URI or by name
                    # For now, we just count the number of links
                    count += 1

        logger.info(f"Downloaded {count:,} occupation-skills relations")
    except Exception as e:
        logger.error(f"Failed to download occupationSkillRelations_en.csv: {e}")


# ─── Download call during module import ──────────────────────────────────────────

load_esco_occupations()
load_esco_skills()
# load_esco_relations()

logger.info(f"Total unique occupations: {len(KNOWN_OCCUPATIONS):,}")
logger.info(f"Total unique skills: {len(KNOWN_SKILLS):,}")
