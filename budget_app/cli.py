import argparse
from pathlib import Path

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

    args = parser.parse_args()

    # 프로그램 실행 시 저장 파일을 자동으로 준비합니다.
    initialize_data_files(Path(args.data_dir))

    parser.print_help()
    return 0