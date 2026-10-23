"""Configuration settings for exchange rates API."""

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

API_URL = os.getenv("API_URL", "https://api.frankfurter.dev/v2/rates")
START_DATE = os.getenv("START_DATE", "2025-01-01")
END_DATE = os.getenv("END_DATE", "2026-12-31")

_TARGET_CURRENCIES_RAW = os.getenv("TARGET_CURRENCIES", "COP,PEN,BOB,CLP")
TARGET_CURRENCIES = [c.strip() for c in _TARGET_CURRENCIES_RAW.split(",") if c.strip()]

# Database configuration settings
DB_HOST = os.getenv("POS_DB_HOST", "localhost")
DB_PORT = int(os.getenv("POS_DB_PORT", "5432"))
DB_NAME = os.getenv("POS_DB_NAME", "")
DB_USER = os.getenv("POS_DB_USER", "")
DB_PASSWORD = os.getenv("POS_DB_PASSWORD", "")
