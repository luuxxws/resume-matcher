# src/resume_matcher/tests/test_db_connection.py

import sys
from pathlib import Path
import logging
import json
import numpy as np

# Adding project root to sys.path
project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.resume_matcher.db import (
    get_connection,
    get_file_hash,
    resume_exists,
    store_resume,
    get_resume_by_path,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def test_connection():
    """Test 1: Simple connection and basic checks"""
    print("\n=== Test 1: Connecting to PostgreSQL ===")
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                print("PostgreSQL version:", cur.fetchone()["version"])
                cur.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
                print("pgvector installed:", bool(cur.fetchone()))
                cur.execute("SELECT COUNT(*) FROM resumes;")
                print("Records in the resumes table:", cur.fetchone()["count"])
        print("Test 1 completed ✓")
    except Exception as e:
        print(f"Error in test 1: {e}")
        sys.exit(1)


def test_hash_and_exists():
    """Test 2: File hash and existence check"""
    print("\n=== Test 2: Hash and existence check ===")
    test_file = Path("data/resumes/ATS Resume.pdf")
    if not test_file.exists():
        print(f"Test file not found: {test_file}")
        return

    file_hash = get_file_hash(test_file)
    print(f"SHA256-hash of the file: {file_hash[:16]}...")

    exists = resume_exists(test_file)
    print(f"Resume is already in database: {exists}")


def test_store_and_read():
    """Test 3: Saving and reading a test resume"""
    print("\n=== Test 3: Saving and reading resumes ===")
    test_file = Path("data/resumes/A_Yakovkin_CY_new.pdf")
    if not test_file.exists():
        test_file.touch()

    raw_text = "This is a test raw text of resume after OCR."
    cleaned_text = "Test text of the resume after cleaning"
    json_data = {
        "full_name": "John Doe",
        "email": "test@example.com",
        "position": "Senior Test Engineer"
    }
    embedding = np.random.rand(1024).astype(np.float32) 

    print("Saving test resume...")
    try:
        store_resume(
            file_path=test_file,
            raw_text=raw_text,
            cleaned_text=cleaned_text,
            json_data=json_data,
            embedding=embedding,
            force_update=True
        )
    except Exception as e:
        print(f"Saving error: {e}")
        return

    # Reading 
    print("Reading saved resume...")
    loaded = get_resume_by_path(test_file)
    if loaded:
        print("Read successfully:")
        print(f"  ID: {loaded['id']}")
        print(f"  file_name: {loaded['file_name']}")
        print(f"  json_data: {json.dumps(loaded['json_data'], ensure_ascii=False, indent=2)}")
        emb_shape = loaded['embedding'].shape if loaded['embedding'] is not None else 'None'
        print(f"  embedding shape: {emb_shape}")
    else:
        print("Resume not found after saving")


def main():
    print("=== Complete test of the db.py module ===\n")
    test_connection()
    test_hash_and_exists()
    test_store_and_read()
    print("\nAll tests completed!")


if __name__ == "__main__":
    main()
