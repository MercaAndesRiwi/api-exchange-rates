# api-exchange-rates — Exchange Rates Ingestion Service

[![CI - api-exchange-rates](https://github.com/MercadAndes/api-exchange-rates/actions/workflows/ci.yml/badge.svg)](https://github.com/MercadAndes/api-exchange-rates/actions/workflows/ci.yml)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

An autonomous, production-ready ETL ingestion microservice built for the **MercadAndes** platform. It retrieves historical foreign exchange rates from the public [Frankfurter API](https://api.frankfurter.dev) and synchronizes them into a PostgreSQL database with automated schema creation and idempotent upserts.

---

## Table of Contents

- [Overview](#overview)
- [Objective \& Core Functions](#objective--core-functions)
- [Architecture \& SOLID Principles](#architecture--solid-principles)
- [Project Structure](#project-structure)
- [Database Schema](#database-schema)
- [Configuration \& Environment Variables](#configuration--environment-variables)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Local Setup and Execution](#local-setup-and-execution)
  - [Running with Docker](#running-with-docker)
- [Testing \& Quality Assurance](#testing--quality-assurance)
- [CI/CD Pipeline](#cicd-pipeline)

---

## Overview

In multi-currency e-commerce and marketplace environments, maintaining accurate and consistent currency conversion rates is critical. **`api-exchange-rates`** acts as an ephemeral worker (batch job) that fetches daily exchange rates from a base currency (default: `USD`) against key Latin American target currencies (`COP`, `PEN`, `BOB`, `CLP`) and persists them into PostgreSQL.

---

## Objective & Core Functions

1. **Automated Rate Fetching**: Ingest historical exchange rates over a configurable date range using the Frankfurter API.
2. **Schema Self-Management**: Automatically initializes the target database table (`public.exchange_rate`) if it does not already exist.
3. **Idempotent Data Ingestion**: Uses PostgreSQL `ON CONFLICT (rate_date, base_currency_code, quote_currency_code) DO UPDATE` to ensure runs can be repeated safely without creating duplicates.
4. **Pre-flight Health Checks**: Verifies environment variables, database network connectivity, and external API responsiveness before starting ingestion.
5. **Portability**: Packaged with a slim Docker container optimized for deployment as a scheduled CronJob or cloud task (Kubernetes, AWS ECS, GCP Cloud Run Jobs).

---

## Architecture & SOLID Principles

The service is engineered following strict **SOLID** object-oriented design principles:

| Principle | Implementation in this project |
|---|---|
| **S (Single Responsibility)** | Separated into distinct layers: validation ([`validators.py`](src/exchange_rates/validators.py)), external HTTP client ([`client.py`](src/exchange_rates/client.py)), persistence ([`repository.py`](src/exchange_rates/repository.py)), business orchestration ([`service.py`](src/exchange_rates/service.py)), and entry point ([`main.py`](src/exchange_rates/main.py)). |
| **O (Open/Closed)** | The core service depends on `ExchangeRateProvider` and `ExchangeRateRepository` protocols. You can plug in a new data provider (e.g. European Central Bank, Yahoo Finance) or database without changing the service layer. |
| **L (Liskov Substitution)** | All implementations satisfying runtime protocols are interchangeable (demonstrated by fake providers and repositories in test suites). |
| **I (Interface Segregation)** | Granular protocols: `ExchangeRateProvider` for reading rates, `ExchangeRateRepository` for writing rates, and `SchemaInitializer` for DDL operations. |
| **D (Dependency Inversion)** | High-level orchestrators depend on abstractions (`typing.Protocol`), not concrete implementations. Dependencies are injected via class constructors. |

---

## Project Structure

```text
api-exchange-rates/
├── .env.example              # Sample environment configuration
├── .gitignore                # Git ignore patterns
├── Dockerfile                # Production-ready container specification
├── pyproject.toml            # Project dependencies and tool configurations
├── uv.lock                   # Deterministic dependency lockfile
├── README.md                 # Project documentation
├── src/
│   └── exchange_rates/
│       ├── __init__.py       # Package exports
│       ├── config.py         # Environment configuration loader
│       ├── db.py             # SQLAlchemy engine connection provider
│       ├── models.py         # Domain entities (ExchangeRate)
│       ├── protocols.py      # Abstract SOLID protocols
│       ├── client.py         # FrankfurterClient (HTTP client)
│       ├── repository.py     # PostgreSQLExchangeRateRepository
│       ├── service.py        # ExchangeRateService (orchestration)
│       ├── validators.py     # System validators & pre-flight health checks
│       └── main.py           # Composition Root & application entry point
└── tests/
    └── unit/
        ├── test_client.py    # Unit tests for Frankfurter HTTP client
        ├── test_repository.py# Unit tests for repository & table creation
        └── test_service.py   # Unit tests for service layer & protocol compliance
```

---

## Database Schema

The service manages the `public.exchange_rate` table in PostgreSQL:

```sql
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
);
```

---

## Configuration & Environment Variables

Create a `.env` file in the project root based on `.env.example`:

| Variable | Description | Default | Required |
|---|---|---|---|
| `POS_DB_HOST` | PostgreSQL hostname or IP | `localhost` | **Yes** |
| `POS_DB_PORT` | PostgreSQL port | `5432` | **Yes** |
| `POS_DB_NAME` | PostgreSQL database name | — | **Yes** |
| `POS_DB_USER` | Database user | — | **Yes** |
| `POS_DB_PASSWORD` | Database password | — | **Yes** |
| `API_URL` | Frankfurter API endpoint | `https://api.frankfurter.dev/v2/rates` | No |
| `START_DATE` | Initial date in `YYYY-MM-DD` | `2025-01-01` | No |
| `END_DATE` | Final date in `YYYY-MM-DD` | `2026-12-31` | No |
| `TARGET_CURRENCIES`| Comma-separated currency codes | `COP,PEN,BOB,CLP` | No |
| `APP_ENV` | Runtime environment name | `development` | No |

---

## Getting Started

### Prerequisites

- **Python 3.13+**
- **[uv](https://docs.astral.sh/uv/)** (recommended fast Python package manager)
- **PostgreSQL 14+** (running locally or via Docker)

---

### Local Setup and Execution

1. **Clone the repository:**
   ```bash
   git clone https://github.com/MercadAndes/api-exchange-rates.git
   cd api-exchange-rates
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your PostgreSQL credentials
   ```

3. **Install dependencies:**
   ```bash
   uv sync --locked --dev
   ```

4. **Run the ingestion process:**
   ```bash
   uv run python -m exchange_rates.main
   ```

---

### Running with Docker

1. **Build the container image:**
   ```bash
   docker build -t api-exchange-rates:latest .
   ```

2. **Run the container with your `.env` configuration:**
   ```bash
   docker run --rm --env-file .env api-exchange-rates:latest
   ```

---

## Testing & Quality Assurance

Run the test suite and static analysis tools using `uv`:

- **Run all unit tests:**
  ```bash
  uv run pytest
  ```

- **Run code linter (Ruff):**
  ```bash
  uv run ruff check
  ```

---

## CI/CD Pipeline

The repository includes a GitHub Actions workflow in [`.github/workflows/ci.yml`](.github/workflows/ci.yml) that automatically runs on every push or pull request to `main` or `develop`:

1. Installs dependencies deterministically with `uv sync --locked --dev`.
2. Validates code style with `ruff check`.
3. Runs the test suite with `pytest`.
4. Builds the production Docker image and publishes it to the GitHub Container Registry (GHCR).
