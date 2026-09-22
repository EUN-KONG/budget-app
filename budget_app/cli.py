import argparse
from pathlib import Path

from budget_app.repositories import CategoryStore
from budget_app.storage import initialize_data_files


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

    # category처럼 프로그램이 실행할 명령어를 등록합니다.
    commands = parser.add_subparsers(dest="command")
    category_parser = commands.add_parser(
        "category",
        help="카테고리를 관리합니다.",
    )

    # category 아래에서 사용할 add와 list를 등록합니다.
    category_commands = category_parser.add_subparsers(
        dest="category_command"
    )
    category_commands.add_parser("add", help="카테고리를 추가합니다.")
    category_commands.add_parser("list", help="카테고리를 조회합니다.")

    args = parser.parse_args()
    data_dir = Path(args.data_dir)

    # 데이터 파일을 준비하고 카테고리 저장소를 만듭니다.
    initialize_data_files(data_dir)
    category_store = CategoryStore(data_dir / "categories.jsonl")

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