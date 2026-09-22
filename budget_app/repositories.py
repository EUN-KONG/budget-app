import json
from pathlib import Path


class CategoryStore:
    """카테고리 JSONL 파일을 관리합니다."""

    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path

    def get_all(self) -> list[str]:
        """저장된 모든 카테고리를 반환합니다."""
        categories = []

        with self.file_path.open("r", encoding="utf-8") as file:
            for line in file:
                if line.strip():
                    categories.append(json.loads(line)["name"])

        return categories

    def exists(self, name: str) -> bool:
        """카테고리가 이미 등록되어 있는지 확인합니다."""
        return name in self.get_all()

    def add(self, name: str) -> bool:
        """새 카테고리를 추가하고 성공 여부를 반환합니다."""
        if not name or self.exists(name):
            return False

        with self.file_path.open("a", encoding="utf-8") as file:
            file.write(
                json.dumps({"name": name}, ensure_ascii=False) + "\n"
            )

        return True

    def remove(self, name: str) -> bool:
        """카테고리를 삭제하고 성공 여부를 반환합니다."""
        categories = self.get_all()

        if name not in categories:
            return False

        with self.file_path.open("w", encoding="utf-8") as file:
            for category in categories:
                if category != name:
                    file.write(
                        json.dumps(
                            {"name": category},
                            ensure_ascii=False,
                        )
                        + "\n"
                    )

        return True