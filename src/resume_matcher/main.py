# src/resume_matcher/main.py
"""
Resume Matcher - AI-powered resume matching and ranking system.

This is the main entry point that provides:
1. Unified CLI with subcommands (import, match, serve)
2. REST API for integration
3. Programmatic API for Python integration

Usage:
    # Start the API server
    uv run resume-matcher serve --port 8000

    # Import resumes into database
    uv run resume-matcher import --dir data/resumes --workers 8

    # Match resumes against a vacancy (fast embedding mode)
    uv run resume-matcher match --vacancy data/vacancies/Vacancy1.docx --top 10

    # Match with LLM re-ranking (more accurate)
    uv run resume-matcher match --vacancy data/vacancies/Vacancy1.docx --llm --top 10

    # Show database info
    uv run resume-matcher info

    # Show help
    uv run resume-matcher --help
"""

import argparse
import logging
import multiprocessing as mp
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def cmd_import(args: argparse.Namespace) -> int:
    """Handle the 'import' subcommand."""
    from resume_matcher.scripts.cli_import import import_folder
    from resume_matcher.services.importer import sync_deleted_resumes

    resumes_dir = Path(args.dir)

    if args.only_sync:
        logger.info("Mode: only-sync - syncing deleted resumes")
        sync_deleted_resumes(resumes_dir)
        return 0

    import_folder(
        resumes_dir=resumes_dir,
        workers=args.workers,
        force_update=args.force,
        dry_run=args.dry_run,
        limit=args.limit,
        only_sync=False,
    )
    return 0


def cmd_match(args: argparse.Namespace) -> int:
    """Handle the 'match' subcommand."""
    import json
    from resume_matcher.services.matcher import (
        match_vacancy_file,
        match_vacancy_text,
        match_vacancy_file_with_llm,
        match_vacancy_with_llm,
        print_match_results,
    )
    from resume_matcher.scripts.cli_match import (
        result_to_dict,
        llm_result_to_dict,
        parse_score_range,
    )

    # Parse score range if provided
    score_range = parse_score_range(args.score_range) if args.score_range else None
    min_similarity = args.min_score / 100.0

    if args.llm:
        # LLM-powered matching
        logger.info("Using LLM-powered matching (2-stage: embedding + LLM re-ranking)")

        if args.vacancy:
            requirements, scores = match_vacancy_file_with_llm(
                args.vacancy,
                top_n=args.top,
                embedding_candidates=args.candidates,
                min_similarity=min_similarity,
            )
        else:
            requirements, scores = match_vacancy_with_llm(
                args.text,
                top_n=args.top,
                embedding_candidates=args.candidates,
                min_similarity=min_similarity,
            )

        # Apply score range filter
        if score_range:
            min_s, max_s = score_range
            scores = [s for s in scores if min_s <= s.combined_score <= max_s]

        # Output
        if args.json:
            print(json.dumps(llm_result_to_dict(requirements, scores), indent=2, ensure_ascii=False))
        else:
            from resume_matcher.models.llm_scorer import print_scored_results
            print_scored_results(requirements, scores)

        return 0 if scores else 1

    else:
        # Embedding-only matching
        logger.info("Using embedding-only matching (fast mode)")

        if args.vacancy:
            result = match_vacancy_file(
                args.vacancy,
                top_n=args.top,
                min_similarity=min_similarity,
            )
        else:
            result = match_vacancy_text(
                args.text,
                top_n=args.top,
                min_similarity=min_similarity,
            )

        # Apply score range filter
        if score_range:
            min_s, max_s = score_range
            result.matches = [m for m in result.matches if min_s <= m.score_percent <= max_s]

        # Output
        if args.json:
            print(json.dumps(result_to_dict(result), indent=2, ensure_ascii=False))
        else:
            print_match_results(result)

        return 0 if result.matches else 1


def cmd_serve(args: argparse.Namespace) -> int:
    """Handle the 'serve' subcommand - start the API server."""
    import uvicorn

    logger.info(f"Starting Resume Matcher API server on {args.host}:{args.port}")
    logger.info(f"API docs available at: http://{args.host}:{args.port}/docs")

    uvicorn.run(
        "resume_matcher.api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info" if not args.quiet else "warning",
    )
    return 0


def cmd_info(args: argparse.Namespace) -> int:
    """Handle the 'info' subcommand - show database statistics."""
    from resume_matcher.db import get_connection

    with get_connection() as conn, conn.cursor() as cur:
        # Total resumes
        cur.execute("SELECT COUNT(*) as count FROM resumes")
        total = cur.fetchone()["count"]

        # With embeddings
        cur.execute("SELECT COUNT(*) as count FROM resumes WHERE embedding IS NOT NULL")
        with_embedding = cur.fetchone()["count"]

        # With JSON data
        cur.execute("SELECT COUNT(*) as count FROM resumes WHERE json_data IS NOT NULL AND json_data != '{}'")
        with_json = cur.fetchone()["count"]

    print("\n" + "=" * 50)
    print("RESUME DATABASE INFO")
    print("=" * 50)
    print(f"Total resumes:        {total}")
    print(f"With embeddings:      {with_embedding}")
    print(f"With parsed data:     {with_json}")
    print("=" * 50 + "\n")

    return 0


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser with all subcommands."""
    parser = argparse.ArgumentParser(
        prog="resume-matcher",
        description="AI-powered resume matching and ranking system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s serve --port 8000              # Start API server
  %(prog)s import --dir data/resumes      # Import resumes
  %(prog)s match -v vacancy.docx --top 10 # Match resumes
  %(prog)s match -v vacancy.docx --llm    # Match with LLM
  %(prog)s info                           # Show DB stats
        """,
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress logging output",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # =========================================================================
    # IMPORT subcommand
    # =========================================================================
    import_parser = subparsers.add_parser(
        "import",
        help="Import resumes from a folder into the database",
        description="Mass import of resumes with OCR, text extraction, and LLM parsing",
    )
    import_parser.add_argument(
        "--dir", "-d",
        default="data/resumes",
        help="Folder containing resume files (default: data/resumes)",
    )
    import_parser.add_argument(
        "--workers", "-w",
        type=int,
        default=mp.cpu_count(),
        help=f"Number of parallel workers (default: {mp.cpu_count()})",
    )
    import_parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force re-import all files (ignore hash check)",
    )
    import_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulation only, don't write to database",
    )
    import_parser.add_argument(
        "--limit", "-l",
        type=int,
        help="Limit number of files to import (for testing)",
    )
    import_parser.add_argument(
        "--only-sync",
        action="store_true",
        help="Only sync deleted files, don't import new ones",
    )

    # =========================================================================
    # MATCH subcommand
    # =========================================================================
    match_parser = subparsers.add_parser(
        "match",
        help="Match resumes against a vacancy",
        description="Find best matching resumes for a job vacancy using embeddings and/or LLM",
    )
    match_input = match_parser.add_mutually_exclusive_group(required=True)
    match_input.add_argument(
        "--vacancy", "-v",
        type=str,
        help="Path to vacancy file (PDF, DOCX, TXT)",
    )
    match_input.add_argument(
        "--text", "-t",
        type=str,
        help="Vacancy text directly",
    )
    match_parser.add_argument(
        "--top", "-n",
        type=int,
        default=10,
        help="Number of top matches to return (default: 10)",
    )
    match_parser.add_argument(
        "--min-score",
        type=float,
        default=0,
        help="Minimum similarity score 0-100 (default: 0)",
    )
    match_parser.add_argument(
        "--score-range",
        type=str,
        help="Score range filter, e.g. '80-100'",
    )
    match_parser.add_argument(
        "--llm",
        action="store_true",
        help="Use LLM for intelligent re-ranking (slower but more accurate)",
    )
    match_parser.add_argument(
        "--candidates",
        type=int,
        default=30,
        help="Number of embedding candidates for LLM re-ranking (default: 30)",
    )
    match_parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )

    # =========================================================================
    # INFO subcommand
    # =========================================================================
    info_parser = subparsers.add_parser(
        "info",
        help="Show database statistics",
        description="Display information about the resume database",
    )

    # =========================================================================
    # SERVE subcommand
    # =========================================================================
    serve_parser = subparsers.add_parser(
        "serve",
        help="Start the REST API server",
        description="Start the FastAPI server for REST API access",
    )
    serve_parser.add_argument(
        "--host", "-H",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)",
    )
    serve_parser.add_argument(
        "--port", "-p",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)",
    )
    serve_parser.add_argument(
        "--reload", "-r",
        action="store_true",
        help="Enable auto-reload for development",
    )

    return parser


def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)

    if not args.command:
        parser.print_help()
        return 0

    # Dispatch to the appropriate command handler
    commands = {
        "import": cmd_import,
        "match": cmd_match,
        "info": cmd_info,
        "serve": cmd_serve,
    }

    handler = commands.get(args.command)
    if handler:
        return handler(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
