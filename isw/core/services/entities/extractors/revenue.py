from datetime import datetime, timedelta

import pandas as pd

from isw.core.services.entities.models import RevenueData
from isw.shared.logging.logger import logger


class RevenueExtractor:
    """
    Extracts annual revenue from SEC EDGAR facts and ESEF XBRL-JSON.

    Handles multiple revenue tag formats (US-GAAP, IFRS) with priority ordering.
    Falls back to quarterly data (annualized) if no annual figures are available.
    """

    SEC_REVENUE_TAGS = [
        "us-gaap:Revenues",
        "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
        "us-gaap:SalesRevenueNet",
        "us-gaap:TotalRevenuesAndOtherIncome",
        "us-gaap:RevenueFromContractWithCustomerIncludingAssessedTax",
        "us-gaap:ElectricUtilityRevenue",
        "us-gaap:RegulatedAndUnregulatedOperatingRevenue",
        "us-gaap:PublicUtilitiesRevenue",
        "us-gaap:RegulatedOperatingRevenue",
        "us-gaap:RegulatedOperatingRevenueElectric",
        "us-gaap:RegulatedOperatingRevenueElectricNonNuclear",
        "us-gaap:RegulatedOperatingRevenueGas",
        "us-gaap:RegulatedOperatingRevenueOther",
        "us-gaap:InterestAndDividendIncomeOperating",
        "us-gaap:InterestIncomeExpenseNet",
        "us-gaap:InsuranceServicesRevenue",
        "us-gaap:TotalInvestmentIncomeNet",
        "us-gaap:InvestmentIncomeNet",
        "us-gaap:InvestmentIncomeInterest",
        "us-gaap:InvestmentIncomeInterestAndDividend",
        "us-gaap:InterestAndFeeIncomeLoansCommercial",
        "us-gaap:OilAndGasRevenue",
        "us-gaap:NaturalGasProductionRevenue",
        "us-gaap:CrudeOilRevenue",
        "us-gaap:GasGatheringTransportationMarketingAndProcessingRevenue",
        "us-gaap:PassengerRevenue",
        "us-gaap:RevenueFromRelatedParties",
        "us-gaap:RealEstateRevenueNet",
        "us-gaap:OperatingLeasesIncomeStatementLeaseRevenue",
        "us-gaap:SalesRevenueGoodsNet",
        "us-gaap:SalesRevenueServicesNet",
        "us-gaap:NetSales",
    ]

    IFRS_REVENUE_TAGS = [
        "ifrs-full:Revenue",
        "ifrs-full:RevenueFromContractsWithCustomers",
        "ifrs-full:RevenueFromSaleOfGoods",
        "ifrs-full:RevenueFromRenderingOfServices",
        "ifrs-full:RevenueAndOperatingIncome",
        "ifrs-full:InterestRevenueCalculatedUsingEffectiveInterestMethod",
        "ifrs-full:InterestRevenue",
        "ifrs-full:InsuranceServiceRevenue",
        "ifrs-full:FeeAndCommissionIncome",
        "ifrs-full:NetInterestIncome",
        "ifrs-full:InvestmentIncome",
        "ifrs-full:DividendIncome",
        "ifrs-full:InterestIncomeOnFinancialAssetsAtAmortisedCost",
        "ifrs-full:InterestIncomeOnFinancialAssetsAtFairValueThroughOtherComprehensiveIncome",
        "ifrs-full:GainsLossesOnFinancialAssetsMeasuredAtFairValueThroughProfitOrLoss",
        "ifrs-full:RentalIncome",
        "ifrs-full:RentalIncomeFromInvestmentProperty",
        "ppehl:TotalNetIncome",
        "ppehl:NetIncomeFromPrivateEquity",
        "ifrs-full:OtherIncome",
        "ifrs-full:RevenueFromInterestAndSimilarIncome",
    ]

    SUPPORTED_CURRENCIES = ["USD", "CAD", "GBP", "EUR"]

    def __init__(
        self,
        sec_tags: list[str] | None = None,
        ifrs_tags: list[str] | None = None,
        supported_currencies: list[str] | None = None,
    ):
        self.sec_tags = sec_tags or self.SEC_REVENUE_TAGS
        self.ifrs_tags = ifrs_tags or self.IFRS_REVENUE_TAGS
        self.currencies = supported_currencies or self.SUPPORTED_CURRENCIES

    def from_edgar_facts_df(self, df: pd.DataFrame) -> RevenueData | None:
        """Extract revenue from an EdgarTools company facts DataFrame."""
        recent_cutoff = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")
        old_cutoff = (datetime.now() - timedelta(days=3650)).strftime("%Y-%m-%d")

        # Try recent annual data first (within 2 years)
        for tag in self.sec_tags:
            result = self._try_extract_annual_revenue(df, tag, recent_cutoff)
            if result:
                return result

        # Fall back to older annual data (up to 10 years)
        logger.debug("No recent annual revenue found, trying older data...")
        for tag in self.sec_tags:
            result = self._try_extract_annual_revenue(df, tag, old_cutoff)
            if result:
                logger.info("Using older revenue data (>2 years old)")
                return result

        # Last resort: annualize quarterly data
        logger.debug("No annual revenue found, trying quarterly data...")
        for tag in self.sec_tags:
            result = self._try_extract_quarterly_revenue(df, tag, recent_cutoff)
            if result:
                return result

        return None

    def from_xbrl_json(self, xbrl_data: dict, period_end: str) -> RevenueData | None:
        """Extract revenue from ESEF XBRL-JSON format."""
        facts = xbrl_data if "facts" not in xbrl_data else xbrl_data.get("facts", {})

        result = self._find_most_recent_ifrs_revenue(facts)
        if not result:
            return None

        revenue_fact, source_tag = result
        return self._parse_ifrs_revenue_fact(revenue_fact, period_end, source_tag)

    def _try_extract_annual_revenue(self, df: pd.DataFrame, tag: str, cutoff_date: str) -> RevenueData | None:
        annual_data = df[(df["concept"] == tag) & (df["fiscal_period"] == "FY") & (df["unit"].isin(self.currencies))]

        if len(annual_data) == 0:
            return None

        annual_data = annual_data.sort_values("period_end", ascending=False)
        latest = annual_data.iloc[0]

        value = latest["numeric_value"]
        if value is None or value < 1000:
            return None

        period_end = str(latest["period_end"])
        if period_end < cutoff_date:
            return None

        return RevenueData(
            amount=int(value),
            currency=str(latest["unit"]),
            period_end=period_end,
            source_tag=tag,
        )

    def _try_extract_quarterly_revenue(self, df: pd.DataFrame, tag: str, cutoff_date: str) -> RevenueData | None:
        quarterly_data = df[
            (df["concept"] == tag)
            & (df["fiscal_period"].isin(["Q1", "Q2", "Q3", "Q4"]))
            & (df["unit"].isin(self.currencies))
        ]

        if len(quarterly_data) == 0:
            return None

        quarterly_data = quarterly_data.sort_values("period_end", ascending=False)
        latest = quarterly_data.iloc[0]

        value = latest["numeric_value"]
        if value is None or value < 250:
            return None

        period_end = str(latest["period_end"])
        if period_end < cutoff_date:
            return None

        annualized_value = int(value) * 4

        logger.info(
            "Annualized quarterly revenue from %s: %s x 4 = %s",
            latest["fiscal_period"],
            value,
            annualized_value,
        )

        return RevenueData(
            amount=annualized_value,
            currency=str(latest["unit"]),
            period_end=period_end,
            source_tag=f"{tag} (annualized from {latest['fiscal_period']})",
        )

    def _find_most_recent_ifrs_revenue(self, facts: dict) -> tuple[dict, str] | None:
        """Find the most recent positive revenue fact from IFRS tags."""
        for tag in self.ifrs_tags:
            revenue_facts = []
            for fact in facts.values():
                dimensions = fact.get("dimensions", {})
                if dimensions.get("concept") == tag:
                    period = dimensions.get("period", "")
                    # Only consider period-based facts (start/end date format)
                    if "/" in period:
                        value = fact.get("value")
                        if value is not None:
                            try:
                                numeric_value = float(value)
                                revenue_facts.append((period, fact, numeric_value))
                            except (ValueError, TypeError):
                                continue

            if revenue_facts:
                # Sort by period descending to get most recent
                revenue_facts.sort(key=lambda x: x[0], reverse=True)

                # Prefer positive values but accept zero if that's all we have
                for _period, fact, value in revenue_facts:
                    if value > 0:
                        return (fact, tag)

                return (revenue_facts[0][1], tag)

        return None

    def _parse_ifrs_revenue_fact(self, fact: dict, period_end: str, source_tag: str) -> RevenueData | None:
        value = fact.get("value")
        if not value:
            return None

        try:
            amount = int(float(value))
        except ValueError:
            return None

        dimensions = fact.get("dimensions", {})
        unit = dimensions.get("unit", "")
        currency = self._extract_currency_from_unit(unit)

        return RevenueData(
            amount=amount,
            currency=currency,
            period_end=period_end,
            source_tag=source_tag,
        )

    def _extract_currency_from_unit(self, unit: str) -> str:
        """Extract currency code from unit string (e.g., 'iso4217:GBP' -> 'GBP')."""
        if ":" in unit:
            return unit.split(":")[-1]
        return unit or "Unknown"
