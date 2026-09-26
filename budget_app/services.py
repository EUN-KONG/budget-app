import csv
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

from budget_app.models import Transaction
from budget_app.repositories import CategoryStore, TransactionRepository

# 가져오기와 내보내기에서 공통으로 사용하는 CSV 열 순서입니다.
CSV_COLUMNS = ["date", "type", "category", "amount", "memo", "tags"]

def validate_date(value: str) -> str:
    """날짜가 YYYY-MM-DD 형식인지 검사합니다."""
    try:
        # 입력 문자열을 실제 날짜로 바꿀 수 있는지 확인합니다.
        parsed_date = datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise ValueError("날짜는 YYYY-MM-DD 형식이어야 합니다.")

    # 2026-9-2처럼 자릿수가 부족한 날짜도 막습니다.
    if parsed_date.strftime("%Y-%m-%d") != value:
        raise ValueError("날짜는 YYYY-MM-DD 형식이어야 합니다.")

    return value

def validate_month(value: str) -> str:
    """월이 YYYY-MM 형식인지 검사합니다."""
    try:
        # 입력 문자열을 실제 연도와 월로 바꿀 수 있는지 확인합니다.
        parsed_month = datetime.strptime(value, "%Y-%m")
    except ValueError:
        raise ValueError("월은 YYYY-MM 형식이어야 합니다.")

    # 2026-9처럼 자릿수가 부족한 입력도 막습니다.
    if parsed_month.strftime("%Y-%m") != value:
        raise ValueError("월은 YYYY-MM 형식이어야 합니다.")

    return value

def validate_type(value: str) -> str:
    """거래 유형이 income 또는 expense인지 검사합니다."""
    # 수입과 지출 이외의 값은 저장하지 않습니다.
    if value not in ("income", "expense"):
        raise ValueError("타입은 income 또는 expense만 가능합니다.")

    return value


def validate_amount(value: str) -> int:
    """입력받은 금액을 양수 정수로 변환합니다."""
    try:
        # input() 결과는 문자열이므로 계산 가능한 정수로 바꿉니다.
        amount = int(value)
    except ValueError:
        raise ValueError("금액은 정수로 입력해 주세요.")

    # 0원과 음수 금액은 거래로 저장할 수 없습니다.
    if amount <= 0:
        raise ValueError("금액은 0보다 커야 합니다.")

    return amount

def search_transactions(
    repository: TransactionRepository,
    date_from: str | None = None,
    date_to: str | None = None,
    category: str | None = None,
    transaction_type: str | None = None,
    keyword: str | None = None,
    tag: str | None = None,
) -> Iterator[Transaction]:
    """조건에 맞는 거래를 최신순으로 반환합니다."""
    # 최신 거래부터 한 건씩 읽으며 모든 검색 조건을 검사합니다.
    for transaction in repository.stream_latest():
        if date_from and transaction.date < date_from:
            continue

        if date_to and transaction.date > date_to:
            continue

        if category and transaction.category != category:
            continue

        if transaction_type and transaction.type != transaction_type:
            continue

        # 메모 검색은 영문 대소문자를 구분하지 않습니다.
        if keyword and keyword.lower() not in transaction.memo.lower():
            continue

        # 태그는 목록 안에 같은 값이 있는지 확인합니다.
        if tag and tag not in transaction.tags:
            continue

        # 모든 조건을 통과한 거래만 호출한 곳으로 전달합니다.
        yield transaction

def summarize_month(
    repository: TransactionRepository,
    month: str,
) -> tuple[int, int, dict[str, int]]:
    """해당 월의 수입, 지출, 카테고리별 지출을 계산합니다."""
    total_income = 0
    total_expense = 0
    category_expenses: dict[str, int] = {}

    # 거래를 한 건씩 읽으며 선택한 월의 거래만 계산합니다.
    for transaction in repository.stream():
        if not transaction.date.startswith(f"{month}-"):
            continue

        if transaction.type == "income":
            total_income += transaction.amount
            continue

        # 지출 총액과 해당 카테고리의 지출을 함께 더합니다.
        total_expense += transaction.amount
        previous_amount = category_expenses.get(transaction.category, 0)
        category_expenses[transaction.category] = (
            previous_amount + transaction.amount
        )

    return total_income, total_expense, category_expenses

def import_transactions_csv(
    source: Path,
    category_store: CategoryStore,
    repository: TransactionRepository,
) -> int:
    """CSV 거래를 검사한 뒤 JSONL 파일에 저장합니다."""
    if not source.is_file():
        raise ValueError("CSV 파일을 찾을 수 없습니다.")

    transactions = []

    # utf-8-sig는 일반 UTF-8과 BOM이 포함된 UTF-8을 모두 읽습니다.
    with source.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        # 필수 열이 하나라도 없으면 가져오기를 중단합니다.
        if (
            reader.fieldnames is None
            or not set(CSV_COLUMNS).issubset(reader.fieldnames)
        ):
            raise ValueError(
                "CSV 헤더는 date, type, category, amount, "
                "memo, tags를 포함해야 합니다."
            )

        for row_number, row in enumerate(reader, start=2):
            try:
                date = validate_date((row["date"] or "").strip())
                transaction_type = validate_type(
                    (row["type"] or "").strip()
                )
                category = (row["category"] or "").strip()
                amount = validate_amount((row["amount"] or "").strip())

                if not category_store.exists(category):
                    raise ValueError(
                        f"등록되지 않은 카테고리입니다: {category}"
                    )
            except ValueError as error:
                # 사용자가 CSV에서 잘못된 줄을 바로 찾을 수 있게 합니다.
                raise ValueError(
                    f"CSV {row_number}행 오류: {error}"
                ) from error

            memo = (row["memo"] or "").strip()
            tags = [
                tag.strip()
                for tag in (row["tags"] or "").split(",")
                if tag.strip()
            ]

            # 모든 행의 검사가 끝날 때까지 ID 없이 임시 보관합니다.
            transactions.append(
                Transaction(
                    id="",
                    type=transaction_type,
                    date=date,
                    amount=amount,
                    category=category,
                    memo=memo,
                    tags=tags,
                )
            )

    # 기존 마지막 ID 다음 번호부터 순서대로 ID를 부여합니다.
    next_number = int(repository.next_id().removeprefix("TX-"))

    for offset, transaction in enumerate(transactions):
        transaction.id = f"TX-{next_number + offset:06d}"
        repository.add(transaction)

    return len(transactions)

def export_transactions_csv(
    output: Path,
    repository: TransactionRepository,
    month: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> int:
    """조건에 맞는 거래를 UTF-8 CSV 파일로 저장합니다."""
    count = 0

    with output.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)

        # 첫 번째 줄에 CSV 열 이름을 저장합니다.
        writer.writeheader()

        # 최신 거래부터 한 건씩 읽으며 날짜 조건을 검사합니다.
        for transaction in repository.stream_latest():
            if month and not transaction.date.startswith(f"{month}-"):
                continue

            if date_from and transaction.date < date_from:
                continue

            if date_to and transaction.date > date_to:
                continue

            writer.writerow(
                {
                    "date": transaction.date,
                    "type": transaction.type,
                    "category": transaction.category,
                    "amount": transaction.amount,
                    "memo": transaction.memo,
                    "tags": ",".join(transaction.tags),
                }
            )
            count += 1

    return count