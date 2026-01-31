from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class RevenueTagConfig:
    sec_tags: tuple[str, ...] = (
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
    )

    ifrs_tags: tuple[str, ...] = (
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
    )

    supported_currencies: tuple[str, ...] = ("USD", "CAD", "GBP", "EUR")


@dataclass(frozen=True)
class DescriptionTagConfig:
    ifrs_tags: tuple[str, ...] = (
        "ifrs-full:DisclosureOfGeneralInformationAboutFinancialStatementsExplanatory",
        "ifrs-full:DescriptionOfNatureOfEntitysOperationsAndPrincipalActivities",
        "ifrs-full:DisclosureOfEntitysReportableSegmentsExplanatory",
    )

    tag_field_names: dict[str, str] = field(
        default_factory=lambda: {
            "ifrs-full:DisclosureOfGeneralInformationAboutFinancialStatementsExplanatory": "general_information",
            "ifrs-full:DescriptionOfNatureOfEntitysOperationsAndPrincipalActivities": "nature_of_operations",
            "ifrs-full:DisclosureOfEntitysReportableSegmentsExplanatory": "reportable_segments",
        }
    )


@dataclass
class EntityServiceConfig:
    sec_user_agent: str = "ISW Company Similarity admin@example.com"
    timeout: float = 30.0
    use_ai_extraction: bool = True
    use_web_search_fallback: bool = True
    web_search_backend: Literal["perplexity", "firecrawl"] = "perplexity"
    llm_model: str = "gpt-4o-mini"
    revenue_tags: RevenueTagConfig = field(default_factory=RevenueTagConfig)
    description_tags: DescriptionTagConfig = field(default_factory=DescriptionTagConfig)
