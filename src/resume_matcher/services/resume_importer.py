# src/resume_matcher/services/resume_importer.py
"""
Processing of one resume file:
- conversion to text (PDF, DOCX, image, OCR if necessary)
- minimal text cleaning
- embedding generation
- basic metadata (file name, text length, etc.)
- future plans: parsing structured fields (name, email, skills, etc.)
"""

import json
import logging
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from groq import Groq

from ..db import get_connection, store_resume
from ..models.embedding import get_or_compute_embedding
from ..utils.convert_file_to_text import convert_file_to_text
from ..utils.text_cleaner import clean_ocr_text

load_dotenv()

logger = logging.getLogger(__name__)

GROQ_CLIENT = Groq(api_key=os.getenv("GROQ_API_KEY"))
GROQ_MODEL = "llama-3.3-70b-versatile"


def extract_structured_json_via_llm(text: str) -> dict[str, Any]:
    """
    Extracts structured data from resume text via Groq (Llama 3.1).
    Returns a dict with fields.
    """
    prompt = f"""You are an expert in parsing resumes.
Extract structured data in JSON format from the resume text.
Return ONLY a valid JSON object, without extra text, without markdown, without ```json.

Required fields (if no information is available, return null or an empty list):
{{
  “full_name”: str or null,
  “email”: str or null,
  “phone”: str or null,
  “location”: str or null,
  “current_position”: str or null,
  “years_experience”: int or null,
  “skills”: list[str],
  “languages”: list[str],
  “linkedin”: str or null,
  “github”: str or null,
  “summary”: brief profile description (2–3 sentences) or null
}}

Resume text (can be in Russian and English):
{text[:15000]}
"""

    try:
        response = GROQ_CLIENT.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,          # maximum determinism
            max_tokens=1000,
            top_p=1.0
        )

        content = response.choices[0].message.content.strip()

        # Remove possible markdown
        if content.startswith("```json"):
            content = content.split("```json")[1].split("```")[0].strip()

        parsed = json.loads(content)
        logger.info("LLM-parsing successful")
        return parsed

    except json.JSONDecodeError as e:
        logger.error(f"LLM returned invalid JSON: {e}")
        return {}
    except Exception as e:
        logger.error(f"Error with Groq API: {e}")
        return {}


def import_resume(file_path: Path | str, force_update: bool = False) -> dict[str, Any]:
    """
    Imports a single resume into the database.
    """
    path = Path(file_path)
    if not path.is_file():
        return {"error": f"File not found: {path}"}

    result = {
        "file_name": path.name,
        "status": "success",
    }

    # Text extraction
    raw_text = convert_file_to_text(path)
    if not raw_text.strip():
        return {"error": "Text was not extracted"}
    
    # Cleaning
    cleaned_text = clean_ocr_text(raw_text)

    # Embedding
    embedding = get_or_compute_embedding(cleaned_text, file_path=path)

    # Parsing via LLM (Most expensive step)
    try:
        json_data = extract_structured_json_via_llm(cleaned_text)
    except Exception as e:
        logger.error(f"LLM-parsing failed: {e}")
        json_data = {}
        result["status"] = "llm_failed"

    # Storing in DB
    try:
        store_resume(
            file_path=path,
            raw_text=raw_text,
            cleaned_text=cleaned_text,
            json_data=json_data,
            embedding=embedding,
            force_update=force_update
        )
        result["stored"] = True
    except Exception as e:
        logger.error(f"Error saving to database: {e}")
        result["stored"] = False
        result["status"] = "db_failed"

    return result


def sync_deleted_resumes(resumes_dir: Path):
    """
    Removes resume records from the database that are no longer in the folder.
    """
    current_files: set[str] = {str(f.absolute()) for f in resumes_dir.rglob("*.*") if f.is_file()}

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT file_path FROM resumes")
        db_paths: set[str] = {row["file_path"] for row in cur.fetchall()}

        deleted_paths = db_paths - current_files

        if not deleted_paths:
            logger.info("No deleted rusumes found")
            return

        logger.info(f"Found deleted files in folder: {len(deleted_paths)}")

        deleted_count = 0
        for path in deleted_paths:
            cur.execute("DELETE FROM resumes WHERE file_path = %s", (path,))
            deleted_count += 1
            logger.info(f"Record deleted from BD: {Path(path).name}")

        conn.commit()
        logger.info(f"Records deleted from BD: {deleted_count}")