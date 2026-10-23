"""Service layer for exchange rate synchronization."""

from __future__ import annotations

from datetime import date
import logging
from typing import Sequence

from exchange_rates.protocols import (
    ExchangeRateProvider,
    ExchangeRateRepository,
    SchemaInitializer,
)

logger = logging.getLogger(__name__)


class ExchangeRateService:
    """Orchestration service for exchange rate ingestion and persistence.

    Strictly satisfies SOLID principles:
    - SRP: Dedicated exclusively to business logic and synchronization workflow.
    - OCP: Open to new providers or repositories without modifying this service.
    - LSP: Any implementation adhering to ExchangeRateProvider or ExchangeRateRepository is valid.
    - ISP: Only depends on methods required by the defined protocols.
    - DIP: Depends on abstractions (Protocols), not concrete implementations.
    """

    def __init__(
        self,
        provider: ExchangeRateProvider,
        repository: ExchangeRateRepository,
        schema_initializer: SchemaInitializer | None = None,
    ):
        self.provider = provider
        self.repository = repository
        self.schema_initializer = schema_initializer

    def initialize_storage(self) -> None:
        """Initialize the storage schema if a schema initializer is provided."""
        if self.schema_initializer is not None:
            self.schema_initializer.create_table_if_not_exists()

    def sync_rates(
        self,
        base_currency: str,
        target_currencies: Sequence[str],
        start_date: date,
        end_date: date,
    ) -> dict[str, int]:
        """Synchronize exchange rates for a list of target currencies."""
        self.initialize_storage()
        results: dict[str, int] = {}

        for currency in target_currencies:
            rates = self.provider.fetch_rates(
                base_currency=base_currency,
                quote_currency=currency,
                start_date=start_date,
                end_date=end_date,
            )
            affected = self.repository.upsert_rates(rates)
            results[currency] = affected

        return results
