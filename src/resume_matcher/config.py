"""
src/resume_matcher/config.py
"""

import os
import torch
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Paths
BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent

DATA_DIR: Path = BASE_DIR / "data"
RESUMES_DIR: Path = DATA_DIR / "resumes"          # folder with 10k+ resumes
VACANCIES_DIR: Path = DATA_DIR / "vacancies"      # vacancy descriptions (txt, md, pdf...)
OUTPUT_DIR: Path = DATA_DIR / "output"            # results: csv, json, embeddings cache

for d in [DATA_DIR, RESUMES_DIR, VACANCIES_DIR, OUTPUT_DIR]:
    d.mkdir(parents=True, exist_ok=True)


EMBEDDING_MODEL_NAME = "intfloat/multilingual-e5-large"

EMBEDDING_CACHE_DIR = Path(__file__).parent.parent.parent / "data" / "embedding_cache"

DEVICE = "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"