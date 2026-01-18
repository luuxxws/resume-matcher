# src/resume_matcher/scripts/import_resumes.py
"""
Mass import of resumes from a folder into PostgreSQL with deletion synchronization.

Launch:
    uv run import-resumes --dir data/resumes --workers 8 --force
    # or
    uv run python -m resume_matcher.scripts.import_resumes --dir data/resumes --workers 8 --force

Flags:
    --dir         Folder with resumes (default data/resumes)
    --workers     Number of processes (default 8)
    --force       Overwrite all files (ignore hash)
    --dry-run     Simulation only, without writing to the database
    --limit       Limit the number of files for testing
    --only-sync   Only sync deleted files (no imports whatsoever)
"""

import argparse
import logging
import multiprocessing as mp
from pathlib import Path

from tqdm import tqdm

from resume_matcher.services.resume_importer import import_resume, sync_deleted_resumes

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def process_wrapper(args):
    file_path, force_update, dry_run = args
    if dry_run:
        logger.info(f"[dry-run] Skipping: {file_path.name}")
        return file_path, True, "dry-run"

    result = import_resume(file_path, force_update=force_update)
    success = "error" not in result
    error = result.get("error")
    return file_path, success, error

def import_folder(
    resumes_dir: Path,
    workers: int = 8,
    force_update: bool = False,
    dry_run: bool = False,
    limit: int = None,
    only_sync: bool = False,
):
    if not resumes_dir.is_dir():
        logger.error(f"Folder not found: {resumes_dir}")
        return
    
    if only_sync:
        print("Mode: only-sync - only syncing deleted resumes")
        sync_deleted_resumes(resumes_dir)
        return

    files = list(resumes_dir.rglob("*.*"))
    if limit:
        files = files[:limit]

    total = len(files)
    logger.info(f"Files found: {total}")
    if dry_run:
        logger.info("Mode: dry-run - nothing gets saved")

    args = [(f, force_update, dry_run) for f in files]

    with mp.Pool(processes=workers) as pool:
        results = list(tqdm(
            pool.imap(process_wrapper, args),
            total=total,
            desc="Resume processing",
            unit="file"
        ))

    success = sum(1 for _, ok, _ in results if ok)
    errors = [(p.name, err) for p, ok, err in results if not ok and err]

    print("\nImport results:")
    print(f"  Sucessful: {success}/{total}")
    if errors:
        print(f"  Errors: {len(errors)}")
        for fname, err in errors[:5]:
            print(f"  {fname}: {err}")
        if len(errors) > 5:
            print(f"  ... and {len(errors)-5} more")

    if not dry_run:
        print("\nDeletion synchronization...")
        sync_deleted_resumes(resumes_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description="Mass import of resumes into PostgreSQL")
    parser.add_argument("--dir", default="data/resumes", help="Resume folder")
    parser.add_argument("--workers", type=int, default=mp.cpu_count(), help="Number of processes")
    parser.add_argument("--force", action="store_true", help="Overwrite all files")
    parser.add_argument("--dry-run", action="store_true", help="Only simulation")
    parser.add_argument("--limit", type=int, help="Limit the number of files")
    parser.add_argument("--only-sync", action="store_true", help="Only sync deleted files (no imports whatsoever)")
    args = parser.parse_args()

    import_folder(
        Path(args.dir),
        workers=args.workers,
        force_update=args.force,
        dry_run=args.dry_run,
        limit=args.limit,
        only_sync=args.only_sync,
    )


if __name__ == "__main__":
    main()