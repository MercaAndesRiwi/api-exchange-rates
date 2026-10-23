"""Unit tests for service layer and SOLID protocol compliance."""

from datetime import date
from typing import Iterable

from exchange_rates.client import FrankfurterClient
from exchange_rates.models import ExchangeRate
from exchange_rates.protocols import (
    ExchangeRateProvider,
    ExchangeRateRepository,
    SchemaInitializer,
)
from exchange_rates.repository import PostgreSQLExchangeRateRepository
from exchange_rates.service import ExchangeRateService
from exchange_rates.validators import EnvironmentValidator


class FakeProvider:
    """Mock implementation of ExchangeRateProvider (LSP / OCP)."""

    def __init__(self, sample_rate: float = 4200.0):
        self.sample_rate = sample_rate

    def fetch_rates(
        self,
        base_currency: str,
        quote_currency: str,
        start_date: date,
        end_date: date,
    ) -> list[ExchangeRate]:
        return [
            ExchangeRate(
                rate_date=start_date,
                base_currency_code=base_currency,
                quote_currency_code=quote_currency,
                rate=self.sample_rate,
                source="FakeSource",
            )
        ]


class FakeRepository:
    """In-memory implementation of ExchangeRateRepository and SchemaInitializer (LSP / OCP)."""

    def __init__(self):
        self.storage: list[dict] = []
        self.schema_created = False

    def create_table_if_not_exists(self) -> None:
        self.schema_created = True

    def upsert_rates(self, rates: Iterable[ExchangeRate | dict]) -> int:
        count = 0
        for rate in rates:
            item = rate.to_dict() if isinstance(rate, ExchangeRate) else rate
            self.storage.append(item)
            count += 1
        return count


def test_protocol_conformance():
    """Verify concrete classes satisfy runtime protocols (LSP / DIP)."""
    assert isinstance(FakeProvider(), ExchangeRateProvider)
    assert isinstance(FakeRepository(), ExchangeRateRepository)
    assert isinstance(FakeRepository(), SchemaInitializer)
    assert issubclass(FrankfurterClient, ExchangeRateProvider)
    assert issubclass(PostgreSQLExchangeRateRepository, ExchangeRateRepository)
    assert issubclass(PostgreSQLExchangeRateRepository, SchemaInitializer)


def test_service_sync_rates_with_fakes():
    """Verify service coordinates retrieval and persistence without coupling (SRP / DIP)."""
    provider = FakeProvider(sample_rate=4150.0)
    repository = FakeRepository()

    service = ExchangeRateService(
        provider=provider,
        repository=repository,
        schema_initializer=repository,
    )

    results = service.sync_rates(
        base_currency="USD",
        target_currencies=["COP", "PEN"],
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 5),
    )

    assert repository.schema_created is True
    assert results == {"COP": 1, "PEN": 1}
    assert len(repository.storage) == 2
    assert repository.storage[0]["quote_currency_code"] == "COP"
    assert repository.storage[0]["rate"] == 4150.0
    assert repository.storage[1]["quote_currency_code"] == "PEN"


def test_environment_validator():
    """Verify date validation rules in EnvironmentValidator."""
    EnvironmentValidator.validate_dates("2025-01-01", "2025-01-02")
    try:
        EnvironmentValidator.validate_dates("2025-01-02", "2025-01-01")
        assert False, "Should raise ValueError when start_date >= end_date"
    except ValueError as e:
        assert "must be prior to" in str(e)
