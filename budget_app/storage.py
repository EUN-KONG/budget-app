import json
from pathlib import Path


# 처음 실행할 때 자동으로 등록할 기본 카테고리입니다.
DEFAULT_CATEGORIES = ["food", "transport", "rent", "salary", "etc"]


def initialize_data_files(data_dir: Path) -> None:
    """저장 폴더와 필요한 JSONL 파일 3개를 만듭니다."""
    data_dir.mkdir(parents=True, exist_ok=True)

    transactions_file = data_dir / "transactions.jsonl"
    categories_file = data_dir / "categories.jsonl"
    budgets_file = data_dir / "budgets.jsonl"

    # 거래 및 예산 파일이 없으면 빈 파일로 만듭니다.
    transactions_file.touch(exist_ok=True)
    budgets_file.touch(exist_ok=True)

    # 카테고리 파일이 비어 있으면 기본 카테고리를 저장합니다.
    if not categories_file.exists() or categories_file.stat().st_size == 0:
        with categories_file.open("w", encoding="utf-8") as file:
            for name in DEFAULT_CATEGORIES:
                data = {"name": name}
                file.write(json.dumps(data, ensure_ascii=False) + "\n")