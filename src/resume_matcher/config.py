"""
src/resume_matcher/config.py
"""

import os
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

