"""System validators and pre-flight health checks."""

from __future__ import annotations

import os
from datetime import date
from typing import Sequence

from sqlalchemy import text
from sqlalchemy.engine import Engine


class EnvironmentValidator:
    """Validate system environment configuration and runtime variables (SRP)."""

    REQUIRED_VARS = (
        "POS_DB_HOST",
        "POS_DB_PORT",
        "POS_DB_NAME",
        "POS_DB_USER",
        "POS_DB_PASSWORD",
    )

    @classmethod
    def get_missing_variables(cls) -> list[str]:
        """Return a list of required environment variables that are missing."""
        return [var for var in cls.REQUIRED_VARS if not os.getenv(var)]

    @classmethod
    def validate_dates(cls, start_date_str: str, end_date_str: str) -> None:
        """Ensure date strings are valid ISO format and start_date precedes end_date."""
        start_date = date.fromisoformat(start_date_str)
        end_date = date.fromisoformat(end_date_str)
        if start_date >= end_date:
            raise ValueError(
                f"START_DATE ({start_date_str}) must be prior to END_DATE ({end_date_str})."
            )

    @classmethod
    def validate_target_currencies(cls, currencies: Sequence[str]) -> None:
        """Ensure target currency collection is not empty."""
        if not currencies:
            raise ValueError("TARGET_CURRENCIES cannot be empty.")


class DatabaseHealthChecker:
    """Health check verifier for relational database connectivity."""

    def __init__(self, engine: Engine):
        self.engine = engine

    def is_healthy(self) -> bool:
        """Test database connection with a lightweight probe."""
        try:
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
