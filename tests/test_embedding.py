#!/usr/bin/env python3
"""
Test script for checking the embedding.py module

Requirements:
- Sentence-transformers and torch are installed
- There is at least one file in data/resumes/
- config.py and embedding.py are configured correctly
"""

import argparse
import logging
import sys
from pathlib import Path

import numpy as np

# Setting up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Adding project root in sys.path
project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Importing the required modules
try:
    from resume_matcher.config import EMBEDDING_MODEL_NAME
    from resume_matcher.models.embedding import (
        DIMENSION,
        batch_get_embeddings,
        get_embedding,
        get_or_compute_embedding,
    )
    from resume_matcher.utils.convert_file_to_text import convert_file_to_text
    from resume_matcher.utils.text_cleaner import clean_ocr_text
except ImportError as e:
    logger.error(f"Failed to import modules: {e}")
    logger.error("Ensure that you are running the script from the project root or using uv run.")
    sys.exit(1)


def test_single_embedding():
    """Embedding generation test for short text"""
    texts = [
        "Senior Machine Learning Engineer with Python and PyTorch experience",
        "Машинное обучение, глубокие нейронные сети, Python, PyTorch",
        "",  # empty text - should return zeroes
    ]

    print("\n" + "="*70)
    print("Test 1: Single embeddings")
    print("-"*70)

    for i, text in enumerate(texts, 1):
        emb = get_embedding(text)
        print(f"Text {i}: {text[:60]}{'...' if len(text)>60 else ''}")
        print(f"  Shape: {emb.shape}")
        print(f"  Norm: {np.linalg.norm(emb):.4f}")
        print(f"  First 5 values: {emb[:5]}")
        print()


def test_batch_embedding():
    """Batch generation test"""
    texts = [
        "Senior ML Engineer Python PyTorch NLP",
        "Data Scientist SQL Pandas Scikit-learn",
        "Разработчик Java Spring Boot микросервисы",
        "Пустой текст для теста",
    ]

    print("\n" + "="*70)
    print("Test 2: Batch generation of embeddings")
    print("-"*70)

    embeddings = batch_get_embeddings(texts, batch_size=2)
    print(f"Embeddings recieved: {embeddings.shape[0]}")
    print(f"Dimensionality: {embeddings.shape[1]} (expected {DIMENSION})")
    print("Vector norms:", np.linalg.norm(embeddings, axis=1))


def test_file_embedding(file_path: Path):
    """Test on a real file from data/resumes"""
    print("\n" + "="*70)
    print("Test 3: Embedding a real file")
    print(f"File: {file_path}")
    print("-"*70)

    if not file_path.exists():
        print(f"File not found: {file_path}")
        return

    raw_text = convert_file_to_text(file_path)
    if not raw_text:
        print("Failed extracting text from file")
        return

    print(f"Raw text length: {len(raw_text):,} symbols")
    print(f"First 200 symbols:\n{raw_text[:200]}...\n")

    # Cleaning
    try:
        cleaned = clean_ocr_text(raw_text)
        print(f"Cleaned text length: {len(cleaned):,} symbols")
    except NameError:
        cleaned = raw_text
        print("text_cleaner not found -> using raw text")

    emb = get_or_compute_embedding(cleaned, file_path=file_path)
    print("Embedding recieved")
    print(f"  Shape: {emb.shape}")
    print(f"  Norm: {np.linalg.norm(emb):.4f}")
    print(f"  First 5 values: {emb[:5]}")


def main():
    parser = argparse.ArgumentParser(description="Testing script for embedding.py")
    parser.add_argument("--file", type=str, help="Path to a specific file for testing")
    args = parser.parse_args()

    print(f"Embedding model: {EMBEDDING_MODEL_NAME}")
    print(f"Dimensionality: {DIMENSION}\n")

    test_single_embedding()
    test_batch_embedding()

    # Test on file, if specified
    if args.file:
        file_path = Path(args.file)
        test_file_embedding(file_path)
    else:
        # Trying to find any file in data/resumes
        resumes_dir = Path("data/resumes")
        if resumes_dir.exists():
            files = list(resumes_dir.glob("*.*"))
            if files:
                print("\nFile found for automated test:", files[0].name)
                test_file_embedding(files[0])
            else:
                print("\nThe data/resumes folder is empty - skip the file test")
        else:
            print("\nThe data/resumes folder was not found - skip the test on the file")


if __name__ == "__main__":
    main()