"""
utils/file_converter.py

Module for converting resumes in various formats into text.
The main task is to provide the rest of the system with a single input format (string).
"""

import mimetypes
from pathlib import Path
from typing import Union

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
# from ocr_handler import apply_ocr


def convert_file_to_text(file_path: Union[str, Path]) -> str:
    """
    Recieves a path to a file and returns the extracted text.

    Returns:
        - document text (str)
        - or an empty string + log on a critical error
    """

    path = Path(file_path)
    if not path.is_file():
        print(f"File is not found: {path}")
        return ""
    
    ext = path.suffix.lower()

    # 1. Microsoft Word (.docx)
    if ext == ".docx":
        if Document is None:
            print("python-docx is not installed -> skipping .docx")
            return ""
        try:
            doc = Document(path)
            return "\n".join(para.text for para in doc.paragraphs if para.text.strip())
        except Exception as e:
            print(f".docx reading error {path}: {e}")
            return ""
        
    # 2. PDF - two main scenarios
    if ext == ".pdf":
        if pdfplumber is None:
            print("pdfplumber is not installed -> trying OCR")
            # return apply_ocr(path)
        
        try:
            with pdfplumber.open(path) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        text += page_text + "\n"

                # If extracted almost nothing, most likely a scan.
                # if len(text.strip()) < 150: # Selected empirically
                #     print(f"Not enough text in PDF -> assuming scan: {path}")
                #     return apply_ocr(path)
                
                return text.strip()
        
        except Exception as e:
            print(f"pdfplumber error {path}: {e}")
            # return apply_ocr(path)
        
    # 3. Other formats
    elif ext in [".txt", ".md"]:
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            print(f"Reading text file error {path}: {e}")
            return ""
        
    else:
        print(f"Unknown file format: {ext} -> {path}")
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