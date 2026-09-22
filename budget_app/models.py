from dataclasses import dataclass, field


@dataclass
class Transaction:
    """수입 또는 지출 한 건을 나타내는 데이터입니다."""

    id: str
    type: str
    date: str
    amount: int
    category: str
    memo: str = ""
    tags: list[str] = field(default_factory=list)