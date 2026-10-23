"""Frankfurter API client for retrieving currency exchange rates."""

from __future__ import annotations

import json
from datetime import date
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from exchange_rates.models import ExchangeRate


class FrankfurterClient:
    """Synchronous HTTP client for querying exchange rates from Frankfurter API.

    Fulfills the ExchangeRateProvider and HealthCheckable protocols.
    """

    def __init__(self, base_url: str = "https://api.frankfurter.dev/v2/rates"):
        self.base_url = base_url

    def fetch_rates(
        self,
        base_currency: str,
        quote_currency: str,
        start_date: date,
        end_date: date,
    ) -> list[ExchangeRate]:
        """Fetch a list of exchange rates between two dates."""
        params = urlencode(
            {
                "base": base_currency,
                "quotes": quote_currency,
                "from": start_date.isoformat(),
                "to": end_date.isoformat(),
            }
        )
        url = f"{self.base_url}?{params}"

        request = Request(
            url,
            headers={"User-Agent": "MercadAndesExchangeRates/1.0"},
        )

        try:
            with urlopen(request, timeout=60) as response:
                data = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            details = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Frankfurter returned HTTP {error.code} "
                f"for {base_currency}/{quote_currency}: {details}"
            ) from error
        except (URLError, TimeoutError) as error:
            raise RuntimeError(
                f"Could not retrieve {base_currency}/{quote_currency} rates: {error}"
            ) from error

        if not isinstance(data, list):
            raise ValueError(
                f"Unexpected response for {base_currency}/{quote_currency}."
            )

        rates: list[ExchangeRate] = []
        for item in data:
            if item.get("base") != base_currency:
                continue
            if item.get("quote") != quote_currency:
                continue
            rate = float(item["rate"])
            if rate <= 0:
                continue
            rates.append(
                ExchangeRate(
                    rate_date=date.fromisoformat(item["date"]),
                    base_currency_code=base_currency,
                    quote_currency_code=quote_currency,
                    rate=rate,
                    source="Frankfurter",
                )
            )

        if not rates:
            raise ValueError(
                f"No historical rates returned for {base_currency}/{quote_currency}."
            )

        return rates

    def is_healthy(self) -> bool:
        """Verify that the Frankfurter API is responding properly."""
        try:
            # Minimal probe request
            today = date.today()
            self.fetch_rates("USD", "EUR", today, today)
            return True
        except Exception:
            return False
