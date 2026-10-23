"""PostgreSQL data access repository for exchange rates."""

from __future__ import annotations

from typing import Iterable

from sqlalchemy import text
from sqlalchemy.engine import Connection

from exchange_rates.models import ExchangeRate


class PostgreSQLExchangeRateRepository:
    """PostgreSQL persistence implementation.

    Fulfills the ExchangeRateRepository and SchemaInitializer protocols.
    Receives connection via Dependency Injection (DIP).
    """

    def __init__(self, connection: Connection):
        self.connection = connection

    def create_table_if_not_exists(self) -> None:
        """Create the public.exchange_rate table if it does not exist (SchemaInitializer)."""
        self.connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS public.exchange_rate (
                    rate_date DATE NOT NULL,
                    base_currency_code VARCHAR(3) NOT NULL,
                    quote_currency_code VARCHAR(3) NOT NULL,
                    rate NUMERIC(18, 8) NOT NULL CHECK (rate > 0),
                    source VARCHAR(50) NOT NULL DEFAULT 'Frankfurter',
                    PRIMARY KEY (
                        rate_date,
                        base_currency_code,
                        quote_currency_code
                    )
                )
                """
            )
        )

    def upsert_rates(self, rates: Iterable[ExchangeRate | dict]) -> int:
        """Insert or update exchange rates idempotently."""
        query = text(
            """
            INSERT INTO public.exchange_rate (
                rate_date,
                base_currency_code,
                quote_currency_code,
                rate,
                source
            )
            VALUES (
                :rate_date,
                :base_currency_code,
                :quote_currency_code,
                :rate,
                :source
            )
            ON CONFLICT (
                rate_date,
                base_currency_code,
                quote_currency_code
            )
            DO UPDATE SET
                rate = EXCLUDED.rate,
                source = EXCLUDED.source
            """
        )

        inserted = 0
        for item in rates:
            param_dict = item.to_dict() if isinstance(item, ExchangeRate) else item
            result = self.connection.execute(query, param_dict)
            inserted += result.rowcount

        return inserted


# Backward compatibility alias
ExchangeRateRepository = PostgreSQLExchangeRateRepository
