"""Abstract protocols and interfaces supporting SOLID principles (DIP, ISP, OCP, LSP)."""

from __future__ import annotations

from datetime import date
from typing import Iterable, Protocol, runtime_checkable

from exchange_rates.models import ExchangeRate


@runtime_checkable
class ExchangeRateProvider(Protocol):
    """External exchange rate data provider contract (ISP / DIP)."""

    def fetch_rates(
        self,
        base_currency: str,
        quote_currency: str,
        start_date: date,
        end_date: date,
    ) -> list[ExchangeRate]:
        """Fetch a list of exchange rates for a currency pair across a date range."""
        ...


@runtime_checkable
class ExchangeRateRepository(Protocol):
    """Storage and persistence contract for exchange rates (ISP / DIP)."""

    def upsert_rates(self, rates: Iterable[ExchangeRate | dict]) -> int:
        """Insert or update exchange rates idempotently."""
        ...


@runtime_checkable
class SchemaInitializer(Protocol):
    """Storage schema initialization contract (ISP).

    Segregates DDL responsibilities (table creation) from day-to-day DML operations.
    """

    def create_table_if_not_exists(self) -> None:
        """Create necessary tables or schema definitions if they do not exist."""
        ...


@runtime_checkable
class HealthCheckable(Protocol):
    """Contract for components capable of verifying operational health."""

    def is_healthy(self) -> bool:
        """Verify if the component or external dependency is healthy and reachable."""
        ...
