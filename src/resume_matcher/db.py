# src/resume_matcher/db.py

import os
import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, Any

import psycopg
from psycopg.rows import dict_row
from pgvector.psycopg import register_vector
from dotenv import load_dotenv
import numpy as np

load_dotenv()

logger = logging.getLogger(__name__)

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "resumes_db"),
    "user": os.getenv("DB_USER", "resumes_user"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5433"),
}