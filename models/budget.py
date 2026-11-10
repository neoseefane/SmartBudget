from dataclasses import dataclass
from typing import Optional

@dataclass
class Budget:
    """Represents a monthly spending limit for a category."""

    id: Optional[int]
    category: str
    monthly_limit: float

    def __post_init__(self):
        if not self.category.strip():
            raise ValueError("Budget category cannot be empty.")
        if self.monthly_limit <= 0:
            raise ValueError("Monthly budget must be greater than 0.")