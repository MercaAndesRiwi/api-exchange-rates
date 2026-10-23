"""Domain models for exchange rates."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass(frozen=True)
class ExchangeRate:
    """Immutable domain entity representing an exchange rate record."""

    rate_date: date
    base_currency_code: str
    quote_currency_code: str
    rate: float
    source: str = "Frankfurter"

    def __getitem__(self, item: str) -> Any:
        """Provide dictionary-style access for backwards compatibility."""
        if hasattr(self, item):
            return getattr(self, item)
        raise KeyError(item)

    def to_dict(self) -> dict[str, Any]:
        """Convert domain entity to a serializable dictionary."""
        return {
            "rate_date": self.rate_date,
            "base_currency_code": self.base_currency_code,
            "quote_currency_code": self.quote_currency_code,
            "rate": self.rate,
            "source": self.source,
        }
