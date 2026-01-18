# tests/test_llm_parsing.py

"""
Resume parsing test via Groq LLM (Llama 3.1).

Run:
    uv run python src/resume_matcher/tests/test_llm_parsing.py --file data/resumes/your_file.pdf

Flags:
    --file       path to the resume file (required)
    --text       pass text directly (for testing without a file)
    --model      Groq model (default llama-3.1-70b-versatile)
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from resume_matcher.services.importer import import_resume

# Add project root to sys.path
project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def main():
    parser = argparse.ArgumentParser(description="Test processing of one resume via importer.py")
    parser.add_argument("--file", required=True, help="Path to resumes file")
    parser.add_argument("--force", action="store_true", help="Force overwrite (force_update)")
    parser.add_argument("--dry-run", action="store_true", help="Simulation only, without saving to the database")
    args = parser.parse_args()

    file_path = Path(args.file)
    if not file_path.exists() or not file_path.is_file():
        print(f"Файл не найден или не является файлом: {file_path}")
        sys.exit(1)

    print("=== Тест importer.py ===")
    print(f"Файл: {file_path.name}")
    print(f"Полный путь: {file_path.absolute()}")
    print(f"Force update: {args.force}")
    print(f"Dry-run: {args.dry_run}\n")

    try:
        result = import_resume(
            file_path=file_path,
            force_update=args.force,
        )

        print("Результат обработки:")
        print(json.dumps(result, ensure_ascii=False, indent=2))

        if "error" in result:
            print("\nОШИБКА:", result["error"])
        elif result.get("stored"):
            print("\nРезюме успешно сохранено/обновлено в БД ✓")
        else:
            print("\nСохранение не выполнено (возможно, из-за dry-run)")

    except Exception as e:
        print(f"\nКритическая ошибка при тесте: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()