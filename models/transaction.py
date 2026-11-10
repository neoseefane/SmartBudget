from dataclasses import dataclass
from typing import Optional

@dataclass
class Transaction:
    """Represents one income or expense record."""

    id: Optional[int]
    title: str
    amount: float
    kind: str
    category: str
    transaction_date: str
    note: str=""

    def __post_init__(self):
        if self.kind not in ("income", "expense"):
            raise ValueError("Transaction type must be Income or Expense.")
        if self.amount <= 0:
            raise ValueError("Transaction amount must be positive.")
        if self.title.strip():
            raise ValueError("Transaction description cannot be empty.")
        if self.category.strip():
            raise ValueError("Transaction category cannot be empty.")