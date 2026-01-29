"""SEC EDGAR bulk data collector for US public companies."""

import io
import json
import zipfile
from datetime import datetime

import httpx
from dateutil.relativedelta import relativedelta

from isw.shared.config import config
from isw.shared.logging.logger import logger

from .base import (
    DownloadError,
    EntityCollector,
    EntityRecord,
    IdentifierType,
    Jurisdiction,
    ParseError,
)

BULK_SUBMISSIONS_URL = "https://www.sec.gov/Archives/edgar/daily-index/bulkdata/submissions.zip"


class SECEdgarCollector(EntityCollector):
    """
    Collector for SEC EDGAR bulk submissions data.

    Downloads the SEC bulk submissions.zip file and extracts companies
    that have filed 10-K (annual reports) within the specified lookback period.

    The bulk file contains JSON submissions for all SEC filers, organized
    by CIK (Central Index Key).

    Note: The bulk file is ~1GB. This implementation loads it into memory.
    Ensure sufficient RAM is available (recommend 2GB+ free).

    Exception handling: Individual malformed submission files are skipped
    with a warning (the bulk archive may contain corrupt entries), but
    network/download errors are propagated.
    """

    def __init__(
        self,
        user_agent: str | None = None,
        years_lookback: int = 3,
        timeout: float = 300.0,
    ):
        """
        Initialize the SEC EDGAR collector.

        Args:
            user_agent: User-Agent header for SEC requests (required by SEC).
                       Defaults to config value if not provided.
            years_lookback: Number of years to look back for 10-K filings.
            timeout: HTTP request timeout in seconds.
        """
        self.user_agent = user_agent or config().sec_user_agent
        self.years_lookback = years_lookback
        self.timeout = timeout
        self._cutoff_date = datetime.now() - relativedelta(years=years_lookback)

    def get_source_name(self) -> str:
        return "SEC EDGAR"

    def fetch_entities(self) -> list[EntityRecord]:
        """
        Fetch all US public companies from SEC EDGAR bulk data.

        Downloads the bulk submissions.zip file, parses each company's
        submission history, and returns companies with 10-K filings
        in the past N years.

        Returns:
            List of EntityRecord objects for US companies.

        Raises:
            DownloadError: If downloading the bulk file fails.
            ParseError: If parsing the bulk data fails.
        """
        logger.info(f"Fetching entities from {self.get_source_name()}")
        logger.info(f"Looking for 10-K filings since {self._cutoff_date.date()}")

        zip_data = self._download_bulk_file()
        entities = self._parse_bulk_submissions(zip_data)

        logger.info(f"Collected {len(entities)} entities from {self.get_source_name()}")
        return entities

    def _download_bulk_file(self) -> bytes:
        logger.info(f"Downloading SEC bulk submissions from {BULK_SUBMISSIONS_URL}")

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(
                    BULK_SUBMISSIONS_URL,
                    headers={"User-Agent": self.user_agent},
                    follow_redirects=True,
                )
                response.raise_for_status()
                logger.info(f"Downloaded {len(response.content) / 1024 / 1024:.1f} MB")
                return response.content
        except httpx.HTTPStatusError as e:
            raise DownloadError(f"SEC returned HTTP {e.response.status_code}: {e}") from e
        except httpx.RequestError as e:
            raise DownloadError(f"Failed to download SEC bulk file: {e}") from e

    def _parse_bulk_submissions(self, zip_data: bytes) -> list[EntityRecord]:
        entities = []

        try:
            with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
                json_files = [f for f in zf.namelist() if f.endswith(".json")]
                logger.info(f"Found {len(json_files)} JSON files in archive")

                for filename in json_files:
                    if filename == "submissions.json":
                        continue

                    try:
                        entity = self._parse_submission_file(zf, filename)
                        if entity:
                            entities.append(entity)
                    except Exception as e:
                        logger.warning(f"Failed to parse {filename}: {e}")
                        continue

        except zipfile.BadZipFile as e:
            raise ParseError(f"Invalid zip file: {e}") from e
        except Exception as e:
            raise ParseError(f"Failed to parse bulk submissions: {e}") from e

        return entities

    def _parse_submission_file(self, zf: zipfile.ZipFile, filename: str) -> EntityRecord | None:
        with zf.open(filename) as f:
            data = json.load(f)

        cik = str(data.get("cik", "")).zfill(10)
        if not cik or cik == "0000000000":
            return None

        name = data.get("name", "").strip()
        if not name:
            return None

        if not self._has_recent_10k(data):
            return None

        return EntityRecord(
            name=name,
            identifier=cik,
            jurisdiction=Jurisdiction.US,
            identifier_type=IdentifierType.CIK,
        )

    def _has_recent_10k(self, submission_data: dict) -> bool:
        filings = submission_data.get("filings", {})
        recent = filings.get("recent", {})

        forms = recent.get("form", [])
        filing_dates = recent.get("filingDate", [])

        for form, date_str in zip(forms, filing_dates, strict=False):
            if form in ("10-K", "10-K/A"):
                try:
                    filing_date = datetime.strptime(date_str, "%Y-%m-%d")
                    if filing_date >= self._cutoff_date:
                        return True
                except ValueError:
                    continue

        return False
