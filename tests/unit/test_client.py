"""Unit tests for Frankfurter client."""

from datetime import date
from unittest.mock import patch

from exchange_rates.client import FrankfurterClient


@patch("exchange_rates.client.urlopen")
def test_fetch_rates_returns_list(mock_urlopen):
    import json

    mock_response = type(
        "MockResponse",
        (),
        {
            "read": lambda self: json.dumps(
                [
                    {
                        "base": "USD",
                        "quote": "COP",
                        "date": "2026-01-01",
                        "rate": 4000.50,
                    }
                ]
            ).encode("utf-8"),
        },
    )()
    mock_urlopen.return_value.__enter__.return_value = mock_response

    client = FrankfurterClient()
    rates = client.fetch_rates("USD", "COP", date(2026, 1, 1), date(2026, 1, 1))

    assert len(rates) == 1
    assert rates[0]["base_currency_code"] == "USD"
    assert rates[0]["quote_currency_code"] == "COP"
    assert rates[0]["rate"] == 4000.50


@patch("exchange_rates.client.urlopen")
def test_fetch_rates_raises_on_empty(mock_urlopen):
    import json

    mock_response = type(
        "MockResponse",
        (),
        {"read": lambda self: json.dumps([]).encode("utf-8")},
    )()
    mock_urlopen.return_value.__enter__.return_value = mock_response

    client = FrankfurterClient()
    try:
        client.fetch_rates("USD", "COP", date(2026, 1, 1), date(2026, 1, 1))
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "No historical rates" in str(e)
