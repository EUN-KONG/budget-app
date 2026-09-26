import argparse
from collections.abc import Callable
from collections import deque
from pathlib import Path
from typing import TypeVar

from budget_app.models import Transaction
from budget_app.repositories import (
    BudgetStore,
    CategoryStore,
    TransactionRepository,
)
from budget_app.services import (
    search_transactions,
    summarize_month,
    validate_amount,
    validate_date,
    validate_month,
    validate_type,
)
from budget_app.storage import initialize_data_files


T = TypeVar("T")


def ask_valid(prompt: str, validator: Callable[[str], T]) -> T:
    """올바른 값이 입력될 때까지 반복해서 요청합니다."""
    while True:
        try:
            # 검사 함수를 통과한 값만 호출한 곳으로 돌려줍니다.
            return validator(input(prompt).strip())
        except ValueError as error:
            print(f"[오류] {error}")


def ask_optional(
    prompt: str,
    current: T,
    validator: Callable[[str], T],
) -> T:
    """새 값이 없으면 기존 값을 유지합니다."""
    while True:
        value = input(f"{prompt} [{current}]: ").strip()

        # 아무것도 입력하지 않으면 수정 전 값을 사용합니다.
        if not value:
            return current

        try:
            return validator(value)
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
        # 현재 파일을 확인해 겹치지 않는 다음 ID를 사용합니다.
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


def list_transactions(
    repository: TransactionRepository,
    limit: int,
) -> int:
    """최근 거래를 최신순으로 출력합니다."""
    if limit <= 0:
        print("[오류] --limit은 1 이상이어야 합니다.")
        return 1

    # 파일을 한 줄씩 읽고 최신 N건만 보관합니다.
    recent = deque(repository.stream(), maxlen=limit)

    if not recent:
        print("[안내] 저장된 거래가 없습니다.")
        return 0

    # 파일에는 오래된 순서로 있으므로 역순으로 최신 거래부터 출력합니다.
    for transaction in reversed(recent):
        print(
            f"{transaction.id} | {transaction.date} | "
            f"{transaction.type} | {transaction.category} | "
            f"{transaction.amount} | {transaction.memo}"
        )

    return 0


def update_transaction(
    transaction_id: str,
    category_store: CategoryStore,
    repository: TransactionRepository,
) -> int:
    """기존 거래에서 입력한 항목만 수정합니다."""
    current = repository.find_by_id(transaction_id)

    # 요청한 ID가 없으면 수정하지 않고 오류 코드 1로 종료합니다.
    if current is None:
        print(f"[오류] 존재하지 않는 거래입니다: {transaction_id}")
        return 1

    date = ask_optional("날짜", current.date, validate_date)
    transaction_type = ask_optional(
        "타입",
        current.type,
        validate_type,
    )

    # 엔터를 누르면 기존 카테고리를 유지합니다.
    while True:
        category = input(f"카테고리 [{current.category}]: ").strip()

        if not category:
            category = current.category
            break

        if category_store.exists(category):
            break

        print("[오류] 등록되지 않은 카테고리입니다.")

    amount = ask_optional("금액", current.amount, validate_amount)

    # 메모와 태그에서 '-'를 입력하면 기존 값을 삭제합니다.
    memo_input = input(
        f"메모 [{current.memo}] (엔터: 유지, -: 삭제): "
    ).strip()
    memo = current.memo if not memo_input else memo_input
    if memo_input == "-":
        memo = ""

    tags_input = input(
        f"태그 [{','.join(current.tags)}] (엔터: 유지, -: 삭제): "
    ).strip()

    if not tags_input:
        tags = current.tags
    elif tags_input == "-":
        tags = []
    else:
        tags = [
            tag.strip()
            for tag in tags_input.split(",")
            if tag.strip()
        ]

    updated = Transaction(
        # ID는 그대로 두고 사용자가 입력한 내용만 새 객체에 담습니다.
        id=current.id,
        type=transaction_type,
        date=date,
        amount=amount,
        category=category,
        memo=memo,
        tags=tags,
    )
    repository.update(updated)

    print(f"[수정 완료] id={updated.id}")
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

    # add, list, delete, category 같은 하위 명령을 등록합니다.
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("add", help="거래를 추가합니다.")

    # list 명령은 출력할 거래 수를 --limit으로 받습니다.
    list_parser = commands.add_parser(
        "list",
        help="최근 거래를 조회합니다.",
    )
    list_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="출력할 거래 수 (기본값: 10)",
    )

    # search 명령에서 사용할 검색 조건 6개를 등록합니다.
    search_parser = commands.add_parser(
        "search",
        help="조건에 맞는 거래를 검색합니다.",
    )
    search_parser.add_argument(
        "--from",
        dest="date_from",
        help="검색 시작일 (YYYY-MM-DD)",
    )
    search_parser.add_argument(
        "--to",
        dest="date_to",
        help="검색 종료일 (YYYY-MM-DD)",
    )
    search_parser.add_argument("--category", help="카테고리")
    search_parser.add_argument(
        "--type",
        dest="transaction_type",
        help="거래 타입 (income/expense)",
    )
    search_parser.add_argument("--q", help="메모 검색어")
    search_parser.add_argument("--tag", help="태그")

    # update 명령은 수정할 거래의 ID를 필수로 받습니다.
    update_parser = commands.add_parser(
        "update",
        help="거래를 수정합니다.",
    )
    update_parser.add_argument(
        "--id",
        required=True,
        help="수정할 거래 ID",
    )

    # 거래 삭제 명령과 필수 ID 옵션을 등록합니다.
    delete_parser = commands.add_parser(
        "delete",
        help="거래를 삭제합니다.",
    )
    delete_parser.add_argument(
        "--id",
        required=True,
        help="삭제할 거래 ID",
    )

    # category 명령 아래에 add, list, remove를 등록합니다.
    category_parser = commands.add_parser(
        "category",
        help="카테고리를 관리합니다.",
    )
    category_commands = category_parser.add_subparsers(
        dest="category_command"
    )
    category_commands.add_parser("add", help="카테고리를 추가합니다.")
    category_commands.add_parser("list", help="카테고리를 조회합니다.")
    category_commands.add_parser("remove", help="카테고리를 삭제합니다.")

    # budget set 명령으로 월과 예산 금액을 입력받습니다.
    budget_parser = commands.add_parser(
        "budget",
        help="월별 예산을 관리합니다.",
    )
    budget_commands = budget_parser.add_subparsers(
        dest="budget_command"
    )
    budget_set_parser = budget_commands.add_parser(
        "set",
        help="월별 예산을 설정합니다.",
    )
    budget_set_parser.add_argument(
        "--month",
        required=True,
        help="예산을 설정할 월 (YYYY-MM)",
    )
    budget_set_parser.add_argument(
        "--amount",
        required=True,
        help="예산 금액",
    )

    # summary 명령은 요약할 월과 출력할 카테고리 수를 받습니다.
    summary_parser = commands.add_parser(
        "summary",
        help="월별 수입과 지출을 요약합니다.",
    )
    summary_parser.add_argument(
        "--month",
        required=True,
        help="요약할 월 (YYYY-MM)",
    )
    summary_parser.add_argument(
        "--top",
        type=int,
        default=3,
        help="출력할 지출 카테고리 수 (기본값: 3)",
    )

    # 터미널에서 입력받은 명령과 옵션을 분석합니다.
    args = parser.parse_args()
    data_dir = Path(args.data_dir)

    # 저장 파일과 저장소 객체를 준비합니다.
    initialize_data_files(data_dir)
    category_store = CategoryStore(data_dir / "categories.jsonl")
    # budgets.jsonl 파일을 관리할 예산 저장소입니다.
    budget_store = BudgetStore(data_dir / "budgets.jsonl")
    repository = TransactionRepository(
        data_dir / "transactions.jsonl"
    )

    # 입력된 명령에 맞는 기능을 실행합니다.
    if args.command == "add":
        return add_transaction(category_store, repository)

    if args.command == "list":
        return list_transactions(repository, args.limit)

    # search 명령이면 입력된 조건을 검사한 뒤 거래를 검색합니다.
    if args.command == "search":
        try:
            if args.date_from:
                validate_date(args.date_from)

            if args.date_to:
                validate_date(args.date_to)

            if args.transaction_type:
                validate_type(args.transaction_type)
        except ValueError as error:
            print(f"[오류] {error}")
            return 1

        # 시작일이 종료일보다 늦은 잘못된 기간을 막습니다.
        if (
            args.date_from
            and args.date_to
            and args.date_from > args.date_to
        ):
            print("[오류] 시작일은 종료일보다 늦을 수 없습니다.")
            return 1

        # 등록되지 않은 카테고리는 검색 조건으로 사용할 수 없습니다.
        if args.category and not category_store.exists(args.category):
            print("[오류] 등록되지 않은 카테고리입니다.")
            return 1

        found = False

        for transaction in search_transactions(
            repository=repository,
            date_from=args.date_from,
            date_to=args.date_to,
            category=args.category,
            transaction_type=args.transaction_type,
            keyword=args.q,
            tag=args.tag,
        ):
            found = True
            print(
                f"{transaction.id} | {transaction.date} | "
                f"{transaction.type} | {transaction.category} | "
                f"{transaction.amount} | {transaction.memo}"
            )

        if not found:
            print("[안내] 검색 결과가 없습니다.")

        return 0
    
    # update 명령이면 해당 ID의 거래를 대화형으로 수정합니다.
    if args.command == "update":
        return update_transaction(
            args.id,
            category_store,
            repository,
        )
    
    if args.command == "delete":
        if repository.delete(args.id):
            print(f"[삭제 완료] id={args.id}")
            return 0

        print(f"[오류] 존재하지 않는 거래입니다: {args.id}")
        return 1

    # budget set 명령이면 입력을 검사한 뒤 예산을 저장합니다.
    if args.command == "budget":
        if args.budget_command == "set":
            try:
                month = validate_month(args.month)
                amount = validate_amount(args.amount)
            except ValueError as error:
                print(f"[오류] {error}")
                return 1

            budget_store.set(month, amount)
            print(f"[저장 완료] {month} 예산 {amount}원")
            return 0

        # budget 뒤에 set이 없으면 사용 방법을 출력합니다.
        budget_parser.print_help()
        return 0

    # summary 명령이면 월별 합계와 예산 사용 정보를 출력합니다.
    if args.command == "summary":
        try:
            month = validate_month(args.month)
        except ValueError as error:
            print(f"[오류] {error}")
            return 1

        if args.top <= 0:
            print("[오류] --top은 1 이상이어야 합니다.")
            return 1

        total_income, total_expense, category_expenses = (
            summarize_month(repository, month)
        )

        # 수입과 지출이 모두 0이면 해당 월에는 거래가 없습니다.
        if total_income == 0 and total_expense == 0:
            print("[안내] 데이터가 없습니다.")
            return 0

        balance = total_income - total_expense

        print(f"총 수입: {total_income}원")
        print(f"총 지출: {total_expense}원")
        print(f"잔액: {balance}원")

        # 설정된 예산이 있으면 사용률과 초과 여부를 출력합니다.
        budget = budget_store.get(month)

        if budget is not None:
            usage_rate = total_expense / budget * 100
            print(f"예산: {budget}원 (사용률 {usage_rate:.1f}%)")

            if total_expense > budget:
                print("[경고] 월 예산을 초과했습니다.")

        # 카테고리 지출액이 큰 순서대로 TOP N을 출력합니다.
        top_categories = sorted(
            category_expenses.items(),
            key=lambda item: item[1],
            reverse=True,
        )[:args.top]

        if top_categories:
            print(f"\n지출 TOP {args.top}")

            for rank, (category, amount) in enumerate(
                top_categories,
                start=1,
            ):
                print(f"{rank}) {category} {amount}원")

        return 0
    
    if args.command == "category":
        # category list는 저장된 이름을 한 줄씩 출력합니다.
        if args.category_command == "list":
            for name in category_store.get_all():
                print(f"- {name}")
            return 0

        # category add는 사용자에게 새 이름을 입력받습니다.
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

        # category remove는 없는 이름과 사용 중인 이름을 보호합니다.
        if args.category_command == "remove":
            name = input("삭제할 카테고리명: ").strip()

            if not category_store.exists(name):
                print("[오류] 존재하지 않는 카테고리입니다.")
                return 1

            # 거래에서 사용 중인 카테고리는 삭제하지 않습니다.
            if repository.uses_category(name):
                print("[오류] 거래에서 사용 중인 카테고리입니다.")
                return 1

            category_store.remove(name)
            print(f"[삭제 완료] category={name}")
            return 0

        # category 뒤에 세부 명령이 없으면 도움말을 보여줍니다.
        category_parser.print_help()
        return 0

    # 아무 명령도 입력하지 않았을 때 전체 도움말을 보여줍니다.
    parser.print_help()
    return 0
