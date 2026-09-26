from dataclasses import dataclass, field


@dataclass
class Transaction:
    """수입 또는 지출 한 건을 나타내는 데이터입니다."""

    # 모든 거래에 반드시 필요한 기본 정보입니다.
    id: str
    type: str
    date: str
    amount: int
    category: str

    # 메모와 태그는 입력하지 않아도 되는 선택 정보입니다.
    memo: str = ""
    tags: list[str] = field(default_factory=list)
