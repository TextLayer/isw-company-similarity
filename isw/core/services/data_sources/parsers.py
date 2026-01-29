import re

from bs4 import BeautifulSoup


def parse_10k_business_section(html_content: str) -> str | None:
    """Extract Item 1. Business text from a 10-K HTML filing."""
    soup = BeautifulSoup(html_content, "lxml")

    # Remove script and style elements that shouldn't be parsed
    for element in soup(["script", "style"]):
        element.decompose()

    # Get all text with newlines preserved
    text = soup.get_text(separator="\n")

    # Find Item 1. Business section
    item1_match = _find_item1_content_section(text)
    if not item1_match:
        return None

    # Find Item 1A. Risk Factors (marks end of Item 1)
    item1a_pattern = re.compile(
        r"Item\s*1A\.?\s+Risk\s*Factors",
        re.IGNORECASE,
    )
    item1a_match = item1a_pattern.search(text, item1_match.end())

    # Extract text between Item 1 and Item 1A
    if item1a_match:
        business_text = text[item1_match.end() : item1a_match.start()]
    else:
        # If no Item 1A found, take a reasonable amount of text after Item 1
        business_text = text[item1_match.end() : item1_match.end() + 50000]

    # Clean up the extracted text
    business_text = clean_extracted_text(business_text)

    # Ensure we have meaningful content (Item 1 should be substantial)
    if len(business_text) < 500:
        return None

    return business_text


def _find_item1_content_section(text: str) -> re.Match | None:
    """
    Find the actual Item 1. Business content section, skipping TOC.

    10-K filings typically have "Item 1. Business" in both the table
    of contents (with page numbers) and in the actual content. This
    function identifies the content section by checking what follows
    the header - TOC entries have page numbers, content has descriptions.

    Args:
        text: Plain text extracted from the 10-K HTML.

    Returns:
        Regex match object for the Item 1 header in the content section,
        or None if not found.
    """
    item1_pattern = re.compile(
        r"Item\s*1\.?\s+Business",
        re.IGNORECASE,
    )
    item1_matches = list(item1_pattern.finditer(text))

    if not item1_matches:
        return None

    # Find the content section (not TOC)
    for match in item1_matches:
        # Check what follows the match
        next_100_chars = text[match.end() : match.end() + 100]
        # TOC entries have page numbers immediately after
        # Content sections have actual text (company description, etc.)
        if not re.match(r"^\s*\d+\s*\n", next_100_chars):
            return match

    # Fall back to last match (most likely to be content in unusual formats)
    return item1_matches[-1]


def clean_extracted_text(text: str) -> str:
    """
    Clean up text extracted from HTML.

    Removes:
    - Lines that are just page numbers
    - Very short navigation/header lines
    - Excessive newlines
    - Common boilerplate text

    Args:
        text: Raw extracted text from HTML.

    Returns:
        Cleaned text with normalized whitespace.
    """
    lines = []
    for line in text.split("\n"):
        line = line.strip()
        if line:
            # Skip lines that are just numbers (page numbers, TOC numbers)
            if re.match(r"^\d+$", line):
                continue
            # Skip very short lines that are likely navigation/headers
            if len(line) < 3 and not line[0].isupper():
                continue
            lines.append(line)

    text = "\n".join(lines)

    # Remove excessive newlines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove common SEC filing boilerplate patterns
    # Pattern: "Company Inc. | 2025 Form 10-K | 1"
    text = re.sub(r"^[A-Za-z\s,\.]+\|\s*\d{4}\s*Form\s*10-K\s*\|\s*\d+\s*\n*", "", text)

    return text.strip()
