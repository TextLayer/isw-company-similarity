"""SEC EDGAR bulk data collector for US public companies."""

import io
import json
import zipfile
from datetime import datetime, timedelta

import httpx

from isw.shared.logging.logger import logger

from .base import (
    DownloadError,
    EntityCollector,
    EntityRecord,
    IdentifierType,
    Jurisdiction,
    ParseError,
)

# SEC EDGAR bulk submissions file URL
SEC_BULK_SUBMISSIONS_URL = "https://www.sec.gov/Archives/edgar/daily-index/bulkdata/submissions.zip"

# SEC requires a User-Agent header with contact information
DEFAULT_USER_AGENT = "ISW-Company-Similarity/1.0 (contact@example.com)"

# Number of years to look back for 10-K filings
YEARS_LOOKBACK = 3


class SECEdgarCollector(EntityCollector):
    """
    Collector for SEC EDGAR bulk submissions data.

    Downloads the SEC bulk submissions.zip file and extracts companies
    that have filed 10-K (annual reports) within the past 3 years.

    The bulk file contains JSON submissions for all SEC filers, organized
    by CIK (Central Index Key).
    """

    def __init__(
        self,
        user_agent: str = DEFAULT_USER_AGENT,
        years_lookback: int = YEARS_LOOKBACK,
        timeout: float = 300.0,
    ):
        """
        Initialize the SEC EDGAR collector.

        Args:
            user_agent: User-Agent header for SEC requests (required by SEC).
            years_lookback: Number of years to look back for 10-K filings.
            timeout: HTTP request timeout in seconds.
        """
        self.user_agent = user_agent
        self.years_lookback = years_lookback
        self.timeout = timeout
        self._cutoff_date = datetime.now() - timedelta(days=365 * years_lookback)

    def get_source_name(self) -> str:
        """Return the name of this data source."""
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

        # Download and extract bulk submissions
        zip_data = self._download_bulk_file()
        entities = self._parse_bulk_submissions(zip_data)

        logger.info(f"Collected {len(entities)} entities from {self.get_source_name()}")
        return entities

    def _download_bulk_file(self) -> bytes:
        """
        Download the SEC bulk submissions zip file.

        Returns:
            Raw bytes of the zip file.

        Raises:
            DownloadError: If the download fails.
        """
        logger.info(f"Downloading SEC bulk submissions from {SEC_BULK_SUBMISSIONS_URL}")

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(
                    SEC_BULK_SUBMISSIONS_URL,
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
        """
        Parse the bulk submissions zip file and extract entities.

        The zip file contains:
        - submissions.json: Index of all filers
        - CIK*.json: Individual company submission files

        Args:
            zip_data: Raw bytes of the zip file.

        Returns:
            List of EntityRecord objects.

        Raises:
            ParseError: If parsing fails.
        """
        entities = []

        try:
            with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
                # Get list of all JSON files in the archive
                json_files = [f for f in zf.namelist() if f.endswith(".json")]
                logger.info(f"Found {len(json_files)} JSON files in archive")

                for filename in json_files:
                    # Skip the index file - we process individual CIK files
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
        """
        Parse an individual company submission file.

        Args:
            zf: Open ZipFile object.
            filename: Name of the JSON file to parse.

        Returns:
            EntityRecord if the company has recent 10-K filings, None otherwise.
        """
        with zf.open(filename) as f:
            data = json.load(f)

        # Extract CIK (pad to 10 digits as SEC standard)
        cik = str(data.get("cik", "")).zfill(10)
        if not cik or cik == "0000000000":
            return None

        # Extract company name
        name = data.get("name", "").strip()
        if not name:
            return None

        # Check for recent 10-K filings
        if not self._has_recent_10k(data):
            return None

        return EntityRecord(
            name=name,
            identifier=cik,
            jurisdiction=Jurisdiction.US,
            identifier_type=IdentifierType.CIK,
        )

    def _has_recent_10k(self, submission_data: dict) -> bool:
        """
        Check if a company has filed a 10-K within the lookback period.

        Args:
            submission_data: Parsed JSON submission data.

        Returns:
            True if company has recent 10-K filing.
        """
        filings = submission_data.get("filings", {})
        recent = filings.get("recent", {})

        forms = recent.get("form", [])
        filing_dates = recent.get("filingDate", [])

        for form, date_str in zip(forms, filing_dates, strict=False):
            # Check for 10-K and 10-K/A (amended)
            if form in ("10-K", "10-K/A"):
                try:
                    filing_date = datetime.strptime(date_str, "%Y-%m-%d")
                    if filing_date >= self._cutoff_date:
                        return True
                except ValueError:
                    continue

        return False
