"""Application entry point and Composition Root for api-exchange-rates."""

from __future__ import annotations

import sys
from datetime import date

from exchange_rates.client import FrankfurterClient
from exchange_rates.config import API_URL, END_DATE, START_DATE, TARGET_CURRENCIES
from exchange_rates.db import get_engine
from exchange_rates.repository import PostgreSQLExchangeRateRepository
from exchange_rates.service import ExchangeRateService
from exchange_rates.validators import DatabaseHealthChecker, EnvironmentValidator


def run_preflight_checks() -> None:
    """Execute all system configuration and connectivity checks."""
    missing = EnvironmentValidator.get_missing_variables()
    if missing:
        print(f"ERROR: Missing environment variables: {missing}")
        print("Copy .env.example to .env and configure PostgreSQL credentials.")
        sys.exit(1)

    try:
        EnvironmentValidator.validate_dates(START_DATE, END_DATE)
        EnvironmentValidator.validate_target_currencies(TARGET_CURRENCIES)
    except ValueError as e:
        print(f"ERROR: Invalid configuration: {e}")
        sys.exit(1)
    print("Environment validation: OK")

    engine = get_engine()
    try:
        db_checker = DatabaseHealthChecker(engine)
        if not db_checker.is_healthy():
            print("ERROR: Could not connect to PostgreSQL database.")
            sys.exit(1)
        print("PostgreSQL connection validation: OK")
    finally:
        engine.dispose()

    client = FrankfurterClient(base_url=API_URL)
    try:
        client.fetch_rates(
            "USD",
            TARGET_CURRENCIES[0],
            date.fromisoformat(START_DATE),
            date.fromisoformat(START_DATE),
        )
        print("Frankfurter API validation: OK")
    except Exception as e:
        print(f"ERROR: Could not connect to Frankfurter API: {e}")
        sys.exit(1)


def load_exchange_rates() -> None:
    """Composition Root: assemble dependencies and run synchronization."""
    run_preflight_checks()

    provider = FrankfurterClient(base_url=API_URL)
    engine = get_engine()

    try:
        with engine.begin() as connection:
            repository = PostgreSQLExchangeRateRepository(connection)
            service = ExchangeRateService(
                provider=provider,
                repository=repository,
                schema_initializer=repository,
            )

            start = date.fromisoformat(START_DATE)
            end = date.fromisoformat(END_DATE)
            results = service.sync_rates(
                base_currency="USD",
                target_currencies=TARGET_CURRENCIES,
                start_date=start,
                end_date=end,
            )

            total_loaded = 0
            for currency, count in results.items():
                print(f"{currency}: {count} rates loaded.")
                total_loaded += count

            print(
                f"Exchange-rate loading completed: {total_loaded} records processed."
            )
    finally:
        engine.dispose()


if __name__ == "__main__":
    load_exchange_rates()
