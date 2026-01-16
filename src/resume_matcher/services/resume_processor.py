# src/resume_matcher/services/resume_processor.py
"""
Processing of one resume file:
- conversion to text (PDF, DOCX, image, OCR if necessary)
- minimal text cleaning
- embedding generation
- basic metadata (file name, text length, etc.)
- future plans: parsing structured fields (name, email, skills, etc.)
"""

import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional

from ..utils.convert_file_to_text import convert_file_to_text
from ..utils.text_cleaner import clean_ocr_text

from ..models.embedding import get_or_compute_embedding

logger = logging.getLogger(__name__)

def process_resume(
        file_path: str | Path,
        force_recompute_embedding: bool = False,
        use_cleaning: bool = True,
) -> Dict[str, Any]:
    """
    Complete processing of a single resume file.

    Arguments:
        file_path: path to the file (PDF, DOCX, JPG/PNG, TXT, etc.)
        force_recompute_embedding: recalculate embedding even if it is in the cache.
        use_cleaning: whether to apply text cleaning (True recommended).

    Returns:
        a dictionary with results or {“error”: “...”} if there is a problem.
    """
    path = Path(file_path)
    if not path.isFile():
        logger.error(f"File not found: {path}")
        return {"error": f"File not found: {path}"}
    
    result: Dict[str, Any] = {
        "file_name": path.name,
        "absolute_path": str(path.absolute()),
        "extension": path.suffix.lower(),
        "status": "success",
    }

    # 1. Text extraction
    logger.info(f"File processing: {path.name}")
    raw_text = convert_file_to_text(path)

    if not raw_text or not raw_text.strip():
        logger.warning(f"No text extracted from file: {path.name}")
        result["status"] = "no_text_extracted"
        result["raw_text"] = ""
        result["cleaned_text"] = ""
        result["embedding"] = None
        return result
    
    result["raw_text_length"] = len(raw_text)
    result["raw_text_preview"] = raw_text[:300] + ("..." if len(raw_text) > 300 else "")

    # 2. Text cleaning
    if use_cleaning:
        try:
            cleaned_text = clean_ocr_text(raw_text)
        except NameError:
            logger.warning("text_cleaner module was not found -> using raw text")
            cleaned_text = raw_text
    else:
        cleaned_text = raw_text

    result["cleaned_text_length"] = len(cleaned_text)
    result["cleaned_text_preview"] = cleaned_text[:300] + ("..." if len(cleaned_text) > 300 else "")

    # 3. Embedding generation
    try:
        embedding = get_or_compute_embedding(
            text=cleaned_text,
            file_path=path,
            force_recompute=force_recompute_embedding,
        )
        result["embedding"] = embedding
        result["embedding_shape"] = embedding.shape
        result["embedding_norm"] = float(np.linalg.norm(embedding))
        result["embedding_preview"] = embedding[:5].tolist()  # first 5 values for debugging
    except Exception as e:
        logger.exception(f"Ошибка при генерации эмбеддинга для {path.name}")
        result["status"] = "embedding_failed"
        result["embedding_error"] = str(e)
        result["embedding"] = None

    # 4. Structured parsing
    # try:
    #     parsed = parse_resume(cleaned_text)
    #     result["parsed"] = parsed  # {"name": "...", "email": "...", "skills": [...], ...}
    # except Exception as e:
    #     logger.warning(f"Resume parsing failed: {e}")
    #     result["parsed"] = {}

    logger.info(f"Processing completed: {path.name} | status: {result['status']}")
    return result

def batch_process_resumes(
    directory: str | Path,
    glob_pattern: str = "*.*",
    max_files: Optional[int] = None,
    **process_kwargs
) -> list[Dict[str, Any]]:
    """
    Processing all files in a folder (batch mode).
    """
    dir_path = Path(directory)
    if not dir_path.is_dir():
        raise ValueError(f"Directory not found: {dir_path}")

    files = list(dir_path.glob(glob_pattern))
    if max_files:
        files = files[:max_files]

    logger.info(f"Found files to process: {len(files)}")

    results = []
    for file_path in files:
        result = process_resume(file_path, **process_kwargs)
        results.append(result)

    return results