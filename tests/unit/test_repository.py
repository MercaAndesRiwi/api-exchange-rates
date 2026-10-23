"""Unit tests for exchange rates repository."""

from datetime import date
from sqlalchemy import create_engine
from exchange_rates.repository import ExchangeRateRepository


def test_repository_create_table_and_upsert():
    # Use SQLite in-memory to validate repository logic
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        from sqlalchemy import text

        connection.execute(text("ATTACH DATABASE ':memory:' AS public"))
        repo = ExchangeRateRepository(connection=connection)
        repo.create_table_if_not_exists()

        rates = [
            {
                "rate_date": date(2025, 1, 1),
                "base_currency_code": "USD",
                "quote_currency_code": "COP",
                "rate": 4300.25,
                "source": "Frankfurter",
            },
            {
                "rate_date": date(2025, 1, 2),
                "base_currency_code": "USD",
                "quote_currency_code": "COP",
                "rate": 4350.00,
                "source": "Frankfurter",
            },
        ]
        inserted = repo.upsert_rates(rates)
        assert inserted == 2

        # Upsert update test
        updated_rates = [
            {
                "rate_date": date(2025, 1, 1),
                "base_currency_code": "USD",
                "quote_currency_code": "COP",
                "rate": 4310.50,
                "source": "Frankfurter",
            }
        ]
        updated = repo.upsert_rates(updated_rates)
        assert updated == 1
