"""PostgreSQL adapter for the shared MercaAndes dimensions."""

from __future__ import annotations

from typing import Iterable
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

from sqlalchemy import text
from sqlalchemy.engine import Connection

from exchange_rates.models import ExchangeRate


class PostgreSQLExchangeRateRepository:
    """Persist Frankfurter rates in the POS dimensional schema."""

    def __init__(self, connection: Connection):
        self.connection = connection

    def create_table_if_not_exists(self) -> None:
        """Validate that the POS migrations created the required dimensions."""
        self.connection.execute(
            text(
                "SELECT 1 FROM public.dim_currency, public.dim_source, "
                "public.dim_exchange_rate LIMIT 0"
            )
        )

    def _source_id(self, source_name: str) -> UUID:
        source_id = self.connection.execute(
            text(
                "SELECT source_id FROM public.dim_source "
                "WHERE source_name = :source_name ORDER BY source_id LIMIT 1"
            ),
            {"source_name": source_name},
        ).scalar_one_or_none()
        if source_id is not None:
            return str(source_id)

        source_id = uuid5(NAMESPACE_URL, f"mercaandes:data-source:{source_name}")
        self.connection.execute(
            text(
                "INSERT INTO public.dim_source (source_id, source_name, description) "
                "VALUES (:source_id, :source_name, :description)"
            ),
            {
                "source_id": str(source_id),
                "source_name": source_name,
                "description": "Exchange rates provided by Frankfurter API",
            },
        )
        source_id = self.connection.execute(
            text(
                "SELECT source_id FROM public.dim_source "
                "WHERE source_name = :source_name ORDER BY source_id LIMIT 1"
            ),
            {"source_name": source_name},
        ).scalar_one()
        return str(source_id)

    def upsert_rates(self, rates: Iterable[ExchangeRate | dict]) -> int:
        """Insert or update rates by currency, source, and date."""
        affected = 0
        currency_query = text(
            "SELECT currency_id FROM public.dim_currency "
            "WHERE currency_code = :currency_code"
        )
        update_query = text(
            "UPDATE public.dim_exchange_rate SET rate = :rate "
            "WHERE currency_id = :currency_id AND source_id = :source_id "
            "AND rate_date = :rate_date"
        )
        insert_query = text(
            "INSERT INTO public.dim_exchange_rate "
            "(exchange_rate_id, currency_id, source_id, rate_date, rate) "
            "VALUES (:exchange_rate_id, :currency_id, :source_id, :rate_date, :rate)"
        )

        currency_cache = {}
        source_cache = {}

        for item in rates:
            rate = item.to_dict() if isinstance(item, ExchangeRate) else item
            c_code = rate["quote_currency_code"]
            if c_code not in currency_cache:
                c_id = self.connection.execute(
                    currency_query, {"currency_code": c_code}
                ).scalar_one_or_none()
                if c_id is None:
                    raise ValueError(
                        f"Currency is missing from public.dim_currency: {c_code}"
                    )
                currency_cache[c_code] = c_id
            currency_id = currency_cache[c_code]

            s_name = rate["source"]
            if s_name not in source_cache:
                source_cache[s_name] = self._source_id(s_name)
            source_id = source_cache[s_name]

            values = {
                "currency_id": currency_id,
                "source_id": source_id,
                "rate_date": rate["rate_date"],
                "rate": rate["rate"],
            }
            result = self.connection.execute(update_query, values)
            if result.rowcount:
                affected += result.rowcount
            else:
                self.connection.execute(
                    insert_query,
                    {**values, "exchange_rate_id": str(uuid4())},
                )
                affected += 1

        return affected


# Backward compatibility alias
ExchangeRateRepository = PostgreSQLExchangeRateRepository
