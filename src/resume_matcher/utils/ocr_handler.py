"""
src/resume_matcher/utils/ocr_handler.py
"""

import logging
from pathlib import Path

import cv2
import numpy as np
import pytesseract
from pdf2image import convert_from_path
from pdf2image.exceptions import (
    PDFInfoNotInstalledError,
    PDFPageCountError,
    PDFPopplerTimeoutError,
    PDFSyntaxError,
)
from PIL import Image

logger = logging.getLogger(__name__)


def preprocess_image(image: Image.Image) -> Image.Image:
    """Preprocessing for better OCR"""
    # PIL -> OpenCV (BGR)
    img_cv = np.array(image.convert("RGB"))  # на всякий случай
    img_cv = cv2.cvtColor(img_cv, cv2.COLOR_RGB2BGR)

    # Grayscale + CLAHE (contrast limited adaptive histogram equalization)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # Adaptive Threshold
    binary = cv2.adaptiveThreshold(
        enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )

    # Denoise + sharpen
    denoised = cv2.fastNlMeansDenoising(binary, h=10)
    kernel_sharp = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
    sharpened = cv2.filter2D(denoised, -1, kernel_sharp)

    # Slight dilate for joining letters
    kernel = np.ones((2, 2), np.uint8)
    dilated = cv2.dilate(sharpened, kernel, iterations=1)

    # Back to PIL
    return Image.fromarray(dilated)


def ocr_from_image(image: Image.Image | str | Path, lang: str = "eng+rus") -> str:
    """OCR of a single image"""
    try:
        image = image.resize((int(image.width * 2), int(image.height * 2)), Image.LANCZOS)
        preprocess_image(image)

        custom_config = r"--oem 3 --psm 11 -c preserve_interword_spaces=1"
        text = pytesseract.image_to_string(image, lang=lang, config=custom_config)
        return text.strip()
    except Exception as e:
        logger.error(f"OCR error on image: {e}")
        return ""


def ocr_from_pdf(pdf_path: Path | str, lang: str = "eng+rus") -> str:
    """OCR of a multilateral PDF"""
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        logger.error(f"PDF not found: {pdf_path}")
        return ""

    text_pages = []
    try:
        images = convert_from_path(
            pdf_path,
            dpi=300,  # Optimal balance between speed/quality around 200-400
            fmt="png",
            thread_count=4,  # Using multiple threads
            first_page=None,
            last_page=None,
        )

        for i, img in enumerate(images, 1):
            logger.info(f"OCR page {i}/{len(images)}")
            page_text = ocr_from_image(img, lang=lang)
            text_pages.append(page_text)

        full_text = "\n\n".join(text_pages)
        return full_text.strip()

    except PDFInfoNotInstalledError:
        logger.error("Poppler is not installed or pdfinfo is not in PATH.")
        return ""
    except PDFPageCountError:
        logger.error("Could not determine the amount of pages in PDF (file may be corrupted).")
        return ""
    except PDFSyntaxError:
        logger.error("Syntax error in PDF-file.")
        return ""
    except PDFPopplerTimeoutError:
        logger.error("PDF processing time exceeded (file too large/complex).")
        return ""
    except Exception as e:
        logger.exception(f"Unexpected error during PDF->OCR conversion: {e}")
        return ""
