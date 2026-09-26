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
                # 빈 줄은 건너뛰고 JSON에서 이름만 꺼냅니다.
                if line.strip():
                    categories.append(json.loads(line)["name"])

        return categories

    def exists(self, name: str) -> bool:
        """카테고리가 이미 등록되어 있는지 확인합니다."""
        return name in self.get_all()

    def add(self, name: str) -> bool:
        """새 카테고리를 추가하고 성공 여부를 반환합니다."""
        # 빈 이름이나 중복된 이름은 추가하지 않습니다.
        if not name or self.exists(name):
            return False

        # a 모드는 기존 내용을 유지하면서 파일 끝에 추가합니다.
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

        # 삭제할 이름을 제외한 나머지 카테고리로 파일을 다시 씁니다.
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

class BudgetStore:
    """월별 예산 JSONL 파일을 관리합니다."""

    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path

    def get(self, month: str) -> int | None:
        """해당 월의 예산을 반환하고, 없으면 None을 반환합니다."""
        with self.file_path.open("r", encoding="utf-8") as file:
            for line in file:
                if line.strip():
                    data = json.loads(line)

                    if data["month"] == month:
                        return int(data["amount"])

        return None

    def set(self, month: str, amount: int) -> None:
        """월별 예산을 새로 저장하거나 기존 값을 변경합니다."""
        budgets = {}

        # 기존 예산을 월을 키로 하는 딕셔너리에 저장합니다.
        with self.file_path.open("r", encoding="utf-8") as file:
            for line in file:
                if line.strip():
                    data = json.loads(line)
                    budgets[data["month"]] = int(data["amount"])

        # 같은 월이 있으면 새 금액으로 덮어씁니다.
        budgets[month] = amount

        # 월 순서대로 예산 파일 전체를 다시 저장합니다.
        with self.file_path.open("w", encoding="utf-8") as file:
            for saved_month in sorted(budgets):
                data = {
                    "month": saved_month,
                    "amount": budgets[saved_month],
                }
                file.write(
                    json.dumps(data, ensure_ascii=False) + "\n"
                )
                
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
                    # yield는 한 건씩 전달하므로 파일 전체를 저장하지 않습니다.
                    yield Transaction(**data)
                    
    def stream_latest(self) -> Iterator[Transaction]:
        """거래 파일의 마지막 줄부터 최신순으로 반환합니다."""
        with self.file_path.open("rb") as file:
            # 파일 끝에서부터 4096바이트씩 나누어 읽습니다.
            file.seek(0, 2)
            position = file.tell()
            remaining = b""

            while position > 0:
                chunk_size = min(4096, position)
                position -= chunk_size
                file.seek(position)

                # 이전에 잘렸던 줄을 현재 조각 뒤에 연결합니다.
                chunk = file.read(chunk_size) + remaining
                lines = chunk.split(b"\n")
                remaining = lines[0]

                # 현재 조각 안의 완성된 줄을 뒤에서부터 처리합니다.
                for line in reversed(lines[1:]):
                    if line.strip():
                        data = json.loads(line.decode("utf-8"))
                        yield Transaction(**data)

            # 파일의 첫 번째 줄도 빠뜨리지 않고 반환합니다.
            if remaining.strip():
                data = json.loads(remaining.decode("utf-8"))
                yield Transaction(**data)

    def add(self, transaction: Transaction) -> None:
        """거래 한 건을 JSONL 파일 끝에 저장합니다."""
        with self.file_path.open("a", encoding="utf-8") as file:
            # dataclass 객체를 JSON으로 저장할 수 있는 딕셔너리로 바꿉니다.
            data = asdict(transaction)
            file.write(json.dumps(data, ensure_ascii=False) + "\n")

    def next_id(self) -> str:
        """현재 거래 다음에 사용할 고유 ID를 만듭니다."""
        largest_number = 0

        for transaction in self.stream():
            # TX-000001에서 숫자 부분만 꺼내 가장 큰 번호를 찾습니다.
            number = int(transaction.id.removeprefix("TX-"))
            largest_number = max(largest_number, number)

        return f"TX-{largest_number + 1:06d}"

    def uses_category(self, category: str) -> bool:
        """해당 카테고리를 사용 중인 거래가 있는지 확인합니다."""
        # 조건에 맞는 거래를 하나라도 찾으면 즉시 True를 반환합니다.
        return any(
            transaction.category == category
            for transaction in self.stream()
        )

    def delete(self, transaction_id: str) -> bool:
        """ID가 일치하는 거래를 삭제합니다."""
        remaining = []
        found = False

        # 삭제할 거래를 빼고 나머지 거래만 모읍니다.
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
        # 파일을 순서대로 읽다가 ID가 같으면 바로 반환합니다.
        for transaction in self.stream():
            if transaction.id == transaction_id:
                return transaction

        return None

    def update(self, updated: Transaction) -> bool:
        """같은 ID의 거래를 수정된 내용으로 교체합니다."""
        transactions = []
        found = False

        # 같은 ID를 만나면 기존 거래 대신 수정된 거래를 담습니다.
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
