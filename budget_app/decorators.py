from collections.abc import Callable
from functools import wraps


def handle_errors(
    function: Callable[[], int],
) -> Callable[[], int]:
    """예상 가능한 오류를 공통 형식으로 처리합니다."""

    @wraps(function)
    def wrapper() -> int:
        try:
            # 원래 함수를 실행하고 종료 코드를 그대로 반환합니다.
            return function()
        except (OSError, EOFError, KeyError, TypeError, ValueError) as error:
            # 오류가 발생해도 스택트레이스를 사용자에게 보여주지 않습니다.
            print(f"[오류] {error}")
            print("[힌트] 입력값과 data 폴더의 저장 파일을 확인해 주세요.")
            return 1

    return wrapper