from datetime import datetime


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
