import argparse


def main() -> int:
    """가계부 프로그램의 명령어를 처리합니다."""
    parser = argparse.ArgumentParser(
        description="나만의 용돈 기입장 프로그램"
    )

    # 아직 명령어가 없으므로 도움말만 출력합니다.
    parser.parse_args()
    parser.print_help()
    return 0