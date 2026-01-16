# src/resume_matcher/services/resume_importer.py
"""
Processing of one resume file:
- conversion to text (PDF, DOCX, image, OCR if necessary)
- minimal text cleaning
- embedding generation
- basic metadata (file name, text length, etc.)
- future plans: parsing structured fields (name, email, skills, etc.)
"""

import logging
from pathlib import Path
from typing import Dict, Any

from ..utils.convert_file_to_text import convert_file_to_text
from ..utils.text_cleaner import clean_ocr_text
from ..models.embedding import get_or_compute_embedding
from ..db import store_resume, get_connection

logger = logging.getLogger(__name__)


def import_resume(file_path: Path | str, force_update: bool = False) -> Dict[str, Any]:
    """
    Imports a single resume into the database:
    - extracts text
    - cleans it up
    - generates embedding
    - parses it through LLM into JSON
    - saves everything in PostgreSQL
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


def extract_structured_json_via_llm(text: str) -> Dict[str, Any]:
    """
    Extracts structured data once via LLM.
    This is where your call to LLM (OpenAI, Grok, Ollama, etc.) should be.
    """
    # Prompt example
    prompt = f"""
    Extract structured data from the resume text in JSON format.
Return ONLY a valid JSON object with the following fields:
    {{
      "full_name": str or null,
      "email": str or null,
      "phone": str or null,
      "location": str or null,
      "current_position": str or null,
      "years_experience": int or null,
      "skills": list[str],
      "languages": list[str],
      "linkedin": str or null,
      "github": str or null,
      "summary": brief profile description (2–3 sentences)
    }}

    Resume text:
    {text[:12000]}
    """

    # Здесь вызов твоей LLM-функции
    # Пример для OpenAI:
    # response = openai.ChatCompletion.create(...)
    # json_str = response.choices[0].message.content

    # Пока заглушка
    return {
        "full_name": "Evgeny Taychinov",
        "email": "helloevgenyy@gmail.com",
        "phone": "79177535498",
        "location": "Moscow, Russia",
        "current_position": "Senior Machine Learning Engineer",
        "years_experience": 4,
        "skills": ["Python", "PyTorch", "NLP", "Computer Vision"],
        "languages": ["Russian", "English"],
        "linkedin": "https://linkedin.com/in/evgeny-taychinov",
        "summary": "Senior ML Engineer with 4 years in RecSys, NLP and CV."
    }