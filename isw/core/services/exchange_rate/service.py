import json
import time
from datetime import datetime
from pathlib import Path

from isw.core.services.exchange_rate.base import ExchangeRateError, ExchangeRateProvider
from isw.core.services.exchange_rate.frankfurter import FrankfurterProvider
from isw.shared.logging.logger import logger


class ExchangeRateService:
    """Service for fetching and caching exchange rates."""

    CACHE_FILE = "exchange_rate_cache.json"
    LATEST_CACHE_TTL = 86400  # 24 hours

    def __init__(
        self,
        provider: ExchangeRateProvider | None = None,
        cache_dir: str | Path | None = None,
    ):
        self._provider = provider or FrankfurterProvider()
        self._cache_dir = Path(cache_dir) if cache_dir else Path(".")
        self._cache_file = self._cache_dir / self.CACHE_FILE
        self._cache = self._load_cache()

    def _load_cache(self) -> dict:
        if self._cache_file.exists():
            try:
                with open(self._cache_file) as f:
                    cache = json.load(f)
                    logger.debug(f"Loaded {len(cache.get('historical', {}))} historical rates from cache")
                    return cache
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Failed to load cache: {e}")
        return {"historical": {}, "latest": {}}

    def _save_cache(self):
        try:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
            with open(self._cache_file, "w") as f:
                json.dump(self._cache, f, indent=2)
        except OSError as e:
            logger.warning(f"Failed to save cache: {e}")

    def _cache_key(self, from_currency: str, to_currency: str, date: str) -> str:
        return f"{from_currency}_{to_currency}_{date}"

    def _is_latest_cache_valid(self, entry: dict) -> bool:
        if "timestamp" not in entry:
            return False
        return (time.time() - entry["timestamp"]) < self.LATEST_CACHE_TTL

    @property
    def supported_currencies(self) -> list[str]:
        return self._provider.supported_currencies

    def get_rate(
        self,
        from_currency: str,
        to_currency: str,
        date: str | None = None,
    ) -> float:
        """
        Get exchange rate with caching.

        Args:
            from_currency: Source currency code (e.g., 'EUR')
            to_currency: Target currency code (e.g., 'USD')
            date: Optional date string (YYYY-MM-DD). If None, uses latest.

        Returns:
            Exchange rate as float

        Raises:
            ExchangeRateError: If rate cannot be retrieved and no cache exists
            ValueError: If currency is not supported
        """
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        supported = self._provider.supported_currencies
        if from_currency not in supported:
            raise ValueError(f"Unsupported currency: {from_currency}. Supported: {supported}")
        if to_currency not in supported:
            raise ValueError(f"Unsupported currency: {to_currency}. Supported: {supported}")

        if from_currency == to_currency:
            return 1.0

        is_historical = date is not None
        cache_key = self._cache_key(from_currency, to_currency, date or "latest")

        # Check cache
        if is_historical:
            if cache_key in self._cache.get("historical", {}):
                rate = self._cache["historical"][cache_key]
                logger.debug(f"Cache hit (historical): {cache_key} = {rate}")
                return rate
        else:
            if cache_key in self._cache.get("latest", {}):
                entry = self._cache["latest"][cache_key]
                if self._is_latest_cache_valid(entry):
                    logger.debug(f"Cache hit (latest): {cache_key} = {entry['rate']}")
                    return entry["rate"]

        # Fetch from provider
        try:
            rate = self._provider.fetch_rate(from_currency, to_currency, date)

            # Update cache
            if is_historical:
                self._cache.setdefault("historical", {})[cache_key] = rate
            else:
                self._cache.setdefault("latest", {})[cache_key] = {
                    "rate": rate,
                    "timestamp": time.time(),
                }
            self._save_cache()
            return rate

        except ExchangeRateError:
            # Fall back to expired cache if available
            if is_historical and cache_key in self._cache.get("historical", {}):
                logger.warning(f"API failed, using cached historical rate for {cache_key}")
                return self._cache["historical"][cache_key]
            elif not is_historical and cache_key in self._cache.get("latest", {}):
                logger.warning(f"API failed, using expired cached rate for {cache_key}")
                return self._cache["latest"][cache_key]["rate"]
            raise

    def convert(
        self,
        amount: float,
        from_currency: str,
        to_currency: str,
        date: str | None = None,
    ) -> float:
        """Convert amount from one currency to another."""
        rate = self.get_rate(from_currency, to_currency, date)
        converted = amount * rate
        logger.debug(f"Converted {amount:,.2f} {from_currency} -> {converted:,.2f} {to_currency} (rate: {rate})")
        return converted

    def convert_to_usd(
        self,
        amount: float,
        from_currency: str,
        date: str | None = None,
    ) -> float:
        """Convenience method to convert any amount to USD."""
        return self.convert(amount, from_currency, "USD", date)

    def get_historical_average(
        self,
        from_currency: str,
        to_currency: str,
        year: int,
    ) -> float:
        """
        Calculate average exchange rate for a fiscal year.

        Samples rates at quarterly intervals and averages them.
        """
        current_year = datetime.now().year
        if year < 1999 or year > current_year:
            raise ValueError(f"Invalid year: {year}. Must be between 1999 and {current_year}")

        sample_dates = [
            f"{year}-01-01",
            f"{year}-04-01",
            f"{year}-07-01",
            f"{year}-10-01",
        ]

        today = datetime.now().strftime("%Y-%m-%d")
        sample_dates = [d for d in sample_dates if d <= today]

        if not sample_dates:
            raise ValueError(f"No historical data available for year {year}")

        rates = []
        for date in sample_dates:
            try:
                rate = self.get_rate(from_currency, to_currency, date)
                rates.append(rate)
            except ExchangeRateError as e:
                logger.warning(f"Failed to get rate for {date}: {e}")

        if not rates:
            raise ExchangeRateError(
                f"Cannot calculate average for {from_currency}/{to_currency} in {year}: No rates available"
            )

        return sum(rates) / len(rates)
