"""
utils/file_converter.py

Модуль для преобразования резюме различных форматов в текст.
Основная задача - дать остальной системе единый входной формат (string).
"""

import mimetypes
from pathlib import Path
from typing import Union

# Для .docx
try:
    from docx import Document
except ImportError:
    Document = None

# Для текстовых .pdf
try:
    import pdfplumber
except ImportError:
    Document = None

# Для определения, нужен ли OCR
from ocr_handler import apply_ocr


def convert_to_text(file_path: Union[str, Path]) -> str:
    """
    Принимает путь к файлу и возвращает извлечённый текст.

    Возвращает:
        - текст документа (str)
        - или пустую строку + лог при критической ошибке
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
        
    # 2. PDF - два основных сценария
    if ext == ".pdf":
        if pdfplumber is None:
            print("pdfplumber is not installed -> trying OCR")
            return apply_ocr(path)
        
        try:
            with pdfplumber.open(path) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        text += page_text + "\n"

                # Если почти ничего не извлекли, скорее всего скан
                if len(text.strip()) < 150: # Подбирается опытным путём
                    print(f"Not enough text in PDF -> assuming scan: {path}")
                    return apply_ocr(path)
                
                return text.strip()
        
        except Exception as e:
            print(f"pdfplumber error {path}: {e}")
            return apply_ocr(path)
        
    # 3. Другие форматы
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
    """Пытается определить тип файла по расширению и содержимому"""

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