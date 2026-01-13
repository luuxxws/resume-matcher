"""
utils/file_converter.py

Module for converting resumes in various formats into text.
The main task is to provide the rest of the system with a single input format (string).
"""

import mimetypes
from pathlib import Path
from typing import Union
from PIL import Image
import logging

logger = logging.getLogger(__name__)

# For .docx
try:
    from docx import Document
except ImportError:
    Document = None

# For text .pdf
try:
    import pdfplumber
except ImportError:
    Document = None

# Determine whether OCR is needed
from src.resume_matcher.utils.ocr_handler import ocr_from_pdf, ocr_from_image


def convert_file_to_text(file_path: Union[str, Path]) -> str:
    """
    Recieves a path to a file and returns the extracted text.

    Returns:
        - document text (str)
        - or an empty string + log on a critical error
    """

    path = Path(file_path)
    if not path.is_file():
        logger.error(f"File is not found: {path}")
        return ""
    
    ext = path.suffix.lower()

    # 1. Microsoft Word (.docx)
    if ext == ".docx":
        if Document is None:
            logger.info("python-docx is not installed -> skipping .docx")
            return ""
        try:
            doc = Document(path)
            return "\n".join(para.text for para in doc.paragraphs if para.text.strip())
        except Exception as e:
            logger.error(f".docx reading error {path}: {e}")
            return ""
        
    # 2. PDF - two main scenarios
    elif ext == ".pdf":
        if pdfplumber is None:
            logger.info("pdfplumber is not installed -> trying OCR")
            return ocr_from_pdf(path)
        
        try:
            with pdfplumber.open(path) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        text += page_text + "\n"

                # If extracted almost nothing, most likely a scan.
                if len(text.strip()) < 100: # Selected empirically
                    logger.info(f"Low text length -> trying OCR: {path.name}")
                    text = ocr_from_pdf(path, lang="eng+rus")
                
                return text.strip()
        
        except Exception as e:
            logger.error(f"pdfplumber error {path}: {e}")
            return ocr_from_pdf(path)
        
    # 3. Single image (.jpg, .jpeg, .png, .webp)
    elif ext in [".jpg", ".jpeg", ".png", ".webp"]:
        try:
            img = Image.open(path)
            text = ocr_from_image(img, lang="eng")
            return text.strip()
        except Exception as e:
            logger.error(f"Reading text file error {path}: {e}")
            return ""
        
    # 4. Other formats
    elif ext in [".txt", ".md"]:
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            logger.error(f"Reading text file error {path}: {e}")
            return ""
        
    else:
        logger.error(f"Unknown file format: {ext} -> {path}")
        return ""
    
def guess_file_type(file_path: Union[str, Path]) -> str:
    """Tries to determine file type based on extension and content"""

    path = Path(file_path)
    ext = path.suffix.lower()
    
    mime, _ = mimetypes.guess_type(path)
    
    if ext == ".pdf":
        return "pdf"
    if ext == ".docx":
        return "docx"
    if ext in (".txt", ".md"):
        return "text"
    if mime and "image" in mime:
        return "image"
    return "unknown"