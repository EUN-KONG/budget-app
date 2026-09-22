import argparse
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

from budget_app.models import Transaction
from budget_app.repositories import CategoryStore, TransactionRepository
from budget_app.services import validate_amount, validate_date, validate_type
from budget_app.storage import initialize_data_files


T = TypeVar("T")


def ask_valid(prompt: str, validator: Callable[[str], T]) -> T:
    """올바른 값이 입력될 때까지 반복해서 요청합니다."""
    while True:
        try:
            return validator(input(prompt).strip())
        except ValueError as error:
            print(f"[오류] {error}")


def add_transaction(
    category_store: CategoryStore,
    repository: TransactionRepository,
) -> int:
    """거래 정보를 입력받아 저장합니다."""
    date = ask_valid("날짜(YYYY-MM-DD): ", validate_date)
    transaction_type = ask_valid(
        "타입(income/expense): ",
        validate_type,
    )

    # 등록된 카테고리가 입력될 때까지 반복합니다.
    while True:
        category = input("카테고리: ").strip()

        if category_store.exists(category):
            break

        print("[오류] 등록되지 않은 카테고리입니다.")
        print("category list에서 목록을 확인해 주세요.")

    amount = ask_valid("금액(양수): ", validate_amount)
    memo = input("메모(선택): ").strip()
    tags_text = input("태그(쉼표로 구분, 없으면 엔터): ").strip()

    # 쉼표로 입력된 태그를 문자열 목록으로 바꿉니다.
    tags = [
        tag.strip()
        for tag in tags_text.split(",")
        if tag.strip()
    ]

    transaction = Transaction(
        id=repository.next_id(),
        type=transaction_type,
        date=date,
        amount=amount,
        category=category,
        memo=memo,
        tags=tags,
    )
    repository.add(transaction)

    print(f"[저장 완료] id={transaction.id}")
    return 0


def main() -> int:
    """가계부 프로그램의 명령어를 처리합니다."""
    parser = argparse.ArgumentParser(
        description="나만의 용돈 기입장 프로그램"
    )
    parser.add_argument(
        "--data-dir",
        default="./data",
        help="데이터 저장 폴더 (기본값: ./data)",
    )

    commands = parser.add_subparsers(dest="command")
    commands.add_parser("add", help="거래를 추가합니다.")

    category_parser = commands.add_parser(
        "category",
        help="카테고리를 관리합니다.",
    )
    category_commands = category_parser.add_subparsers(
        dest="category_command"
    )
    category_commands.add_parser("add", help="카테고리를 추가합니다.")
    category_commands.add_parser("list", help="카테고리를 조회합니다.")

    args = parser.parse_args()
    data_dir = Path(args.data_dir)

    # 저장 파일과 저장소 객체를 준비합니다.
    initialize_data_files(data_dir)
    category_store = CategoryStore(data_dir / "categories.jsonl")
    repository = TransactionRepository(
        data_dir / "transactions.jsonl"
    )

    if args.command == "add":
        return add_transaction(category_store, repository)

    if args.command == "category":
        if args.category_command == "list":
            for name in category_store.get_all():
                print(f"- {name}")
            return 0

        if args.category_command == "add":
            name = input("카테고리명: ").strip()

            if not name:
                print("[오류] 카테고리명을 입력해 주세요.")
                return 1

            if category_store.add(name):
                print(f"[저장 완료] category={name}")
                return 0

            print("[오류] 이미 존재하는 카테고리입니다.")
            return 1

        category_parser.print_help()
        return 0

    parser.print_help()
    return 0