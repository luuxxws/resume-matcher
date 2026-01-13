from pathlib import Path

from src.resume_matcher.utils.convert_file_to_text import convert_file_to_text

def quick_test():
    
    test_files = [
        Path("data/resumes/_CV_.pdf"),
        Path("data/resumes/Julia_Mikheeva_QA.docx"),
        Path("data/resumes/OCRtestImage.png")
    ]

    for file_path in test_files:
        if not file_path.exists():
            print(f"File not found -> skip: {file_path}")
            continue

        print("\n" + "="*80)
        print(f"Обработка: {file_path.name}")
        print("-"*40)

        try:
            text = convert_file_to_text(file_path)
            print(f"Text length: {len(text):,} symbols")
            print(f"First 300 symbols:\n{text[:300]}...")
            print(f"Last 200 symbols:\n{text[-200:]}")
        except Exception as e:
            print(f"ERROR: {e.__class__.__name__}: {e}")

if __name__ == "__main__":
    quick_test()