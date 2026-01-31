from abc import ABC, abstractmethod


class ExchangeRateError(Exception):
    """Raised when exchange rate cannot be retrieved."""


class ExchangeRateProvider(ABC):
    """Abstract base class for exchange rate providers."""

    @property
    @abstractmethod
    def supported_currencies(self) -> list[str]:
        """Return list of supported currency codes."""

    @abstractmethod
    def fetch_rate(
        self,
        from_currency: str,
        to_currency: str,
        date: str | None = None,
    ) -> float:
        """
        Fetch exchange rate from the provider.

        Args:
            from_currency: Source currency code (e.g., 'EUR')
            to_currency: Target currency code (e.g., 'USD')
            date: Optional date string (YYYY-MM-DD). If None, fetches latest.

        Returns:
            Exchange rate as float

        Raises:
            ExchangeRateError: If rate cannot be retrieved
        """
