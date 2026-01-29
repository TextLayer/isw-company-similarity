"""Integration tests verifying Filing dataclass against real API data.

These tests parse actual SEC EDGAR and ESEF API responses to ensure
the Filing dataclass can represent real-world data structures.
"""

import json
import unittest
from pathlib import Path

from isw.core.services.data_sources.base import Filing

FIXTURES_DIR = Path(__file__).parent.parent.parent.parent.parent / "fixtures"
SEC_FIXTURES = FIXTURES_DIR / "entity_collection" / "real_sec_data"
ESEF_FIXTURES = FIXTURES_DIR / "entity_collection" / "real_esef_data"


def parse_sec_filing(submission: dict, filing_index: int = 0) -> Filing:
    """Parse a Filing from SEC EDGAR submission data."""
    cik = str(submission.get("cik", "")).zfill(10)
    recent = submission.get("filings", {}).get("recent", {})

    forms = recent.get("form", [])
    filing_dates = recent.get("filingDate", [])
    report_dates = recent.get("reportDate", [])
    accessions = recent.get("accessionNumber", [])
    docs = recent.get("primaryDocument", [])

    accession = accessions[filing_index] if filing_index < len(accessions) else None
    doc = docs[filing_index] if filing_index < len(docs) else None

    document_url = None
    if accession and doc:
        accession_path = accession.replace("-", "")
        document_url = f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{accession_path}/{doc}"

    return Filing(
        identifier=cik,
        filing_type=forms[filing_index],
        period_end=report_dates[filing_index] if filing_index < len(report_dates) else "",
        filed_at=filing_dates[filing_index] if filing_index < len(filing_dates) else None,
        accession_number=accession,
        document_url=document_url,
        raw_data={
            "form": forms[filing_index],
            "filingDate": filing_dates[filing_index] if filing_index < len(filing_dates) else None,
            "accessionNumber": accession,
        },
    )


def parse_esef_filing(filing_data: dict, entity_data: dict | None = None) -> Filing:
    """Parse a Filing from ESEF API response."""
    attrs = filing_data.get("attributes", {})
    entity_attrs = entity_data.get("attributes", {}) if entity_data else {}

    identifier = entity_attrs.get("identifier", "")
    report_url = attrs.get("report_url", "")

    document_url = None
    if report_url:
        document_url = f"https://filings.xbrl.org{report_url}"

    return Filing(
        identifier=identifier,
        filing_type="AFR",
        period_end=attrs.get("period_end", ""),
        filed_at=None,
        accession_number=None,
        document_url=document_url,
        raw_data=attrs,
    )


class TestFilingFromSECData(unittest.TestCase):
    """Test Filing dataclass against real SEC EDGAR data."""

    @classmethod
    def setUpClass(cls):
        if not SEC_FIXTURES.exists():
            raise unittest.SkipTest("SEC fixtures not available")

    def _load_submission(self, name: str) -> dict:
        with open(SEC_FIXTURES / f"{name}_submission.json") as f:
            return json.load(f)

    def test_parses_apple_10k_filing(self):
        submission = self._load_submission("apple")
        recent = submission["filings"]["recent"]

        tenk_index = next(i for i, f in enumerate(recent["form"]) if f == "10-K")
        filing = parse_sec_filing(submission, tenk_index)

        assert filing.identifier == "0000320193"
        assert filing.filing_type == "10-K"
        assert filing.period_end  # Has a date
        assert filing.filed_at  # Has filing date
        assert filing.accession_number  # Has accession
        assert "sec.gov" in filing.document_url

    def test_parses_microsoft_10k_filing(self):
        submission = self._load_submission("microsoft")
        recent = submission["filings"]["recent"]

        tenk_index = next(i for i, f in enumerate(recent["form"]) if f == "10-K")
        filing = parse_sec_filing(submission, tenk_index)

        assert filing.identifier == "0000789019"
        assert filing.filing_type == "10-K"
        assert len(filing.accession_number) > 0

    def test_parses_tesla_10k_filing(self):
        submission = self._load_submission("tesla")
        recent = submission["filings"]["recent"]

        tenk_index = next(i for i, f in enumerate(recent["form"]) if f == "10-K")
        filing = parse_sec_filing(submission, tenk_index)

        assert filing.identifier == "0001318605"
        assert filing.filing_type == "10-K"

    def test_filing_raw_data_preserves_original(self):
        submission = self._load_submission("apple")
        filing = parse_sec_filing(submission, 0)

        assert "form" in filing.raw_data
        assert "filingDate" in filing.raw_data
        assert "accessionNumber" in filing.raw_data


class TestFilingFromESEFData(unittest.TestCase):
    """Test Filing dataclass against real ESEF API data."""

    @classmethod
    def setUpClass(cls):
        if not ESEF_FIXTURES.exists():
            raise unittest.SkipTest("ESEF fixtures not available")

    def _load_filings(self, name: str) -> dict:
        with open(ESEF_FIXTURES / f"{name}_filings.json") as f:
            return json.load(f)

    def test_parses_uk_filing(self):
        data = self._load_filings("gb")
        filing_data = data["data"][0]

        entity_id = filing_data["relationships"]["entity"]["data"]["id"]
        entity_data = next(e for e in data["included"] if e["id"] == entity_id)

        filing = parse_esef_filing(filing_data, entity_data)

        assert len(filing.identifier) == 20  # LEI is 20 chars
        assert filing.filing_type == "AFR"
        assert filing.period_end  # Has period end
        assert filing.filed_at is None  # ESEF doesn't have filing date
        assert filing.accession_number is None  # No accession in ESEF
        assert "filings.xbrl.org" in filing.document_url

    def test_parses_french_filing(self):
        data = self._load_filings("fr")
        filing_data = data["data"][0]

        entity_id = filing_data["relationships"]["entity"]["data"]["id"]
        entity_data = next(e for e in data["included"] if e["id"] == entity_id)

        filing = parse_esef_filing(filing_data, entity_data)

        assert len(filing.identifier) == 20
        assert filing.filing_type == "AFR"

    def test_parses_dutch_filing(self):
        data = self._load_filings("nl")
        filing_data = data["data"][0]

        entity_id = filing_data["relationships"]["entity"]["data"]["id"]
        entity_data = next(e for e in data["included"] if e["id"] == entity_id)

        filing = parse_esef_filing(filing_data, entity_data)

        assert len(filing.identifier) == 20
        assert filing.filing_type == "AFR"

    def test_filing_raw_data_preserves_original(self):
        data = self._load_filings("gb")
        filing_data = data["data"][0]

        filing = parse_esef_filing(filing_data)

        assert "period_end" in filing.raw_data
        assert "country" in filing.raw_data
        assert "report_url" in filing.raw_data
