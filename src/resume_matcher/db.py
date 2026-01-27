# src/resume_matcher/db.py

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any

import numpy as np
import psycopg
from dotenv import load_dotenv
from pgvector.psycopg import register_vector
from psycopg.rows import dict_row

load_dotenv()

logger = logging.getLogger(__name__)

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "resumes_db"),
    "user": os.getenv("DB_USER", "resumes_user"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5433"),
}


def get_connection():
    """Returns the connection to PostgreSQL with pgvector"""
    try:
        conn = psycopg.connect(**DB_CONFIG, row_factory=dict_row, autocommit=True)
        register_vector(conn)
        logger.debug("Connection to PostgreSQL established")
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise


def get_file_hash(path: Path) -> str:
    """Calculates the SHA256-hash of a file"""
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def resume_exists(file_path: Path) -> bool:
    """Checks whether there is a resume in the database at file_path"""
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT 1 FROM resumes WHERE file_path = %s", (str(file_path.absolute()),))
        return bool(cur.fetchone())


def store_resume(
    file_path: Path,
    raw_text: str,
    cleaned_text: str,
    json_data: dict[str, Any],
    embedding: np.ndarray,
    force_update: bool = False,
) -> int:
    """
    Saves or updates resume in PostgreSQL
    Returns the ID of the record.
    """
    file_hash = get_file_hash(file_path)
    abs_path = str(file_path.absolute())

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
                INSERT INTO resumes (
                    file_name, file_path, file_hash, raw_text, cleaned_text, json_data, embedding
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (file_path) DO UPDATE SET
                    file_hash = EXCLUDED.file_hash,
                    raw_text = EXCLUDED.raw_text,
                    cleaned_text = EXCLUDED.cleaned_text,
                    json_data = EXCLUDED.json_data,
                    embedding = EXCLUDED.embedding,
                    updated_at = NOW()
                RETURNING id
            """,
            (
                file_path.name,
                abs_path,
                file_hash,
                raw_text,
                cleaned_text,
                json.dumps(json_data),
                embedding.tolist(),
            ),
        )

        inserted_id = cur.fetchone()["id"]
        logger.info(f"Saved/Updated resume: {file_path.name} (id={inserted_id})")
        return inserted_id


def get_resume_by_path(file_path: Path) -> dict[str, Any] | None:
    """Gets a resume record by file_path"""
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
                SELECT id, file_name, file_hash, json_data, embedding
                FROM resumes
                WHERE file_path = %s
            """,
            (str(file_path.absolute()),),
        )
        row = cur.fetchone()
        if row:
            if row["embedding"] is not None:
                row["embedding"] = np.array(row["embedding"])
            return row
        return None


def content_hash_exists(file_path: Path) -> dict[str, Any] | None:
    """
    Checks if a resume with the same content (file_hash) already exists.
    Returns the existing resume info if found, None otherwise.
    """
    file_hash = get_file_hash(file_path)
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
                SELECT id, file_name, file_path
                FROM resumes
                WHERE file_hash = %s
                LIMIT 1
            """,
            (file_hash,),
        )
        return cur.fetchone()


def find_duplicates() -> list[dict[str, Any]]:
    """
    Finds all duplicate resumes (same file_hash).
    Returns groups of duplicates with their info.
    """
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT 
                file_hash,
                COUNT(*) as count,
                array_agg(id ORDER BY updated_at DESC) as ids,
                array_agg(file_name ORDER BY updated_at DESC) as file_names
            FROM resumes
            GROUP BY file_hash
            HAVING COUNT(*) > 1
            ORDER BY COUNT(*) DESC
            """
        )
        return cur.fetchall() or []


def clean_duplicates(dry_run: bool = True) -> dict[str, Any]:
    """
    Removes duplicate resumes, keeping the most recently updated version.
    
    Args:
        dry_run: If True, only reports what would be deleted without actually deleting.
    
    Returns:
        Summary of duplicates found and (optionally) deleted.
    """
    duplicates = find_duplicates()
    
    if not duplicates:
        return {
            "duplicate_groups": 0,
            "total_duplicates": 0,
            "deleted_count": 0,
            "deleted_ids": [],
            "dry_run": dry_run,
        }
    
    ids_to_delete = []
    for group in duplicates:
        # Keep the first ID (most recently updated), delete the rest
        ids_to_delete.extend(group["ids"][1:])
    
    deleted_count = 0
    if not dry_run and ids_to_delete:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                "DELETE FROM resumes WHERE id = ANY(%s) RETURNING id",
                (ids_to_delete,),
            )
            deleted_count = cur.rowcount
            logger.info(f"Deleted {deleted_count} duplicate resumes")
    
    return {
        "duplicate_groups": len(duplicates),
        "total_duplicates": sum(d["count"] - 1 for d in duplicates),
        "deleted_count": deleted_count if not dry_run else 0,
        "would_delete": len(ids_to_delete),
        "deleted_ids": ids_to_delete if not dry_run else [],
        "dry_run": dry_run,
        "details": [
            {
                "file_hash": d["file_hash"][:16] + "...",
                "count": d["count"],
                "keep": d["file_names"][0],
                "delete": d["file_names"][1:],
            }
            for d in duplicates
        ],
    }
