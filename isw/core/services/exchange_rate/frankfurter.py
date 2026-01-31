import httpx

from isw.core.services.exchange_rate.base import ExchangeRateError, ExchangeRateProvider
from isw.shared.logging.logger import logger


class FrankfurterProvider(ExchangeRateProvider):
    """Exchange rate provider using Frankfurter API (free, no API key required)."""

    BASE_URL = "https://api.frankfurter.app"
    SUPPORTED_CURRENCIES = ["USD", "EUR", "GBP", "CHF", "SEK", "NOK", "DKK", "PLN", "JPY", "CAD", "AUD"]

    def __init__(self):
        self._client = httpx.Client(timeout=10)

    @property
    def supported_currencies(self) -> list[str]:
        return self.SUPPORTED_CURRENCIES.copy()

    def fetch_rate(
        self,
        from_currency: str,
        to_currency: str,
        date: str | None = None,
    ) -> float:
        url = f"{self.BASE_URL}/{date}" if date else f"{self.BASE_URL}/latest"
        params = {"from": from_currency, "to": to_currency}

        try:
            response = self._client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            rate = data.get("rates", {}).get(to_currency)
            if rate is None:
                raise ExchangeRateError(f"No rate found for {from_currency} to {to_currency}")

            logger.info(f"Fetched rate: {from_currency}/{to_currency} = {rate} (date: {date or 'latest'})")
            return float(rate)

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching rate: {e}")
            raise ExchangeRateError(f"HTTP error: {e}") from e
        except httpx.RequestError as e:
            logger.error(f"Request error fetching rate: {e}")
            raise ExchangeRateError(f"Request failed: {e}") from e
