# utils/text_cleaner.py
import re


def clean_ocr_text(text: str) -> str:
    """Minimal post-processing after OCR"""
    if not text:
        return ""

    # Remove single letters at the beginning of lines / after a new line
    text = re.sub(r"(?m)^[lLiI1]\s*", "", text)
    text = re.sub(r"\n[lLiI1]\s*", "\n", text)

    # Clean up emails
    text = re.sub(r"$$   \s*@", "@", text)
    text = re.sub(r"@\s*   $$", "", text)
    text = re.sub(r"\s+@\s+", "@", text)

    # Phone number standardization (7-10 digits with spaces)
    text = re.sub(r"(\+?\d)[\s.-]*(\d{3})[\s.-]*(\d{3})[\s.-]*(\d{2})[\s.-]*(\d{2})", r"\1\2\3\4\5", text)

    # Remove multiple line breaks and extra spaces
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = " ".join(text.split())

    return text.strip()