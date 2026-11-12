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
    note: str = ""

    def __post_init__(self):
        # Normalize the transaction type.
        self.kind = str(self.kind).strip().title()

        if self.kind not in ("Income", "Expense"):
            raise ValueError(
                f"Transaction type must be Income or Expense. "
                f"Received: {self.kind!r}"
            )

        self.title = str(self.title).strip()
        self.category = str(self.category).strip()

        if self.amount <= 0:
            raise ValueError("Transaction amount must be positive.")

        if not self.title:
            raise ValueError("Transaction description cannot be empty.")

        if not self.category:
            raise ValueError("Transaction category cannot be empty.")

        self.note = str(self.note).strip()
