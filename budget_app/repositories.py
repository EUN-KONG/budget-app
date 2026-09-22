import json
from collections.abc import Iterator
from dataclasses import asdict
from pathlib import Path

from budget_app.models import Transaction

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

class TransactionRepository:
    """거래 JSONL 파일의 저장과 조회를 담당합니다."""

    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path

    def stream(self) -> Iterator[Transaction]:
        """거래를 파일에서 한 줄씩 읽어 반환합니다."""
        with self.file_path.open("r", encoding="utf-8") as file:
            for line in file:
                if line.strip():
                    data = json.loads(line)
                    yield Transaction(**data)

    def add(self, transaction: Transaction) -> None:
        """거래 한 건을 JSONL 파일 끝에 저장합니다."""
        with self.file_path.open("a", encoding="utf-8") as file:
            data = asdict(transaction)
            file.write(json.dumps(data, ensure_ascii=False) + "\n")

    def next_id(self) -> str:
        """현재 거래 다음에 사용할 고유 ID를 만듭니다."""
        largest_number = 0

        for transaction in self.stream():
            number = int(transaction.id.removeprefix("TX-"))
            largest_number = max(largest_number, number)

        return f"TX-{largest_number + 1:06d}"

    def uses_category(self, category: str) -> bool:
        """해당 카테고리를 사용 중인 거래가 있는지 확인합니다."""
        return any(
            transaction.category == category
            for transaction in self.stream()
        )

    def delete(self, transaction_id: str) -> bool:
        """ID가 일치하는 거래를 삭제합니다."""
        remaining = []
        found = False

        for transaction in self.stream():
            if transaction.id == transaction_id:
                found = True
            else:
                remaining.append(transaction)

        if not found:
            return False

        # 삭제할 거래를 제외하고 파일 전체를 다시 저장합니다.
        with self.file_path.open("w", encoding="utf-8") as file:
            for transaction in remaining:
                data = asdict(transaction)
                file.write(json.dumps(data, ensure_ascii=False) + "\n")

        return True

    def find_by_id(
        self,
        transaction_id: str,
    ) -> Transaction | None:
        """ID가 일치하는 거래를 찾아 반환합니다."""
        for transaction in self.stream():
            if transaction.id == transaction_id:
                return transaction

        return None

    def update(self, updated: Transaction) -> bool:
        """같은 ID의 거래를 수정된 내용으로 교체합니다."""
        transactions = []
        found = False

        for transaction in self.stream():
            if transaction.id == updated.id:
                transactions.append(updated)
                found = True
            else:
                transactions.append(transaction)

        if not found:
            return False

        # 수정된 거래 목록으로 파일을 다시 저장합니다.
        with self.file_path.open("w", encoding="utf-8") as file:
            for transaction in transactions:
                data = asdict(transaction)
                file.write(json.dumps(data, ensure_ascii=False) + "\n")

        return True