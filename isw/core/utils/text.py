import re

from bs4 import BeautifulSoup


def clean_text(text: str) -> str:
    text = re.sub(r"\[\d+\]", "", text)
    text = re.sub(r"  +", " ", text)
    text = re.sub(r" +([.,;:])", r"\1", text)
    return text.strip()


def strip_html(html_content: str | None) -> str | None:
    if not html_content:
        return None

    soup = BeautifulSoup(html_content, "lxml")

    for element in soup(["script", "style"]):
        element.decompose()

    text = soup.get_text(separator=" ")
    text = re.sub(r"\s+", " ", text).strip()

    return text if text else None


def clean_extracted_text(text: str) -> str:
    lines = []
    for line in text.split("\n"):
        line = line.strip()
        if line:
            if re.match(r"^\d+$", line):
                continue
            if len(line) < 3 and not line[0].isupper():
                continue
            lines.append(line)

    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"^[A-Za-z\s,\.]+\|\s*\d{4}\s*Form\s*10-K\s*\|\s*\d+\s*\n*", "", text)

    return text.strip()


def parse_10k_business_section(html_content: str) -> str | None:
    soup = BeautifulSoup(html_content, "lxml")

    for element in soup(["script", "style"]):
        element.decompose()

    text = soup.get_text(separator="\n")

    item1_match = _find_item1_content_section(text)
    if not item1_match:
        return None

    item1a_pattern = re.compile(
        r"Item\s*1A\.?\s+Risk\s*Factors",
        re.IGNORECASE,
    )
    item1a_match = item1a_pattern.search(text, item1_match.end())

    if item1a_match:
        business_text = text[item1_match.end() : item1a_match.start()]
    else:
        business_text = text[item1_match.end() : item1_match.end() + 50000]

    business_text = clean_extracted_text(business_text)

    if len(business_text) < 500:
        return None

    return business_text


def _find_item1_content_section(text: str) -> re.Match | None:
    item1_pattern = re.compile(
        r"Item\s*1\.?\s+Business",
        re.IGNORECASE,
    )
    item1_matches = list(item1_pattern.finditer(text))

    if not item1_matches:
        return None

    for match in item1_matches:
        next_100_chars = text[match.end() : match.end() + 100]
        if not re.match(r"^\s*\d+\s*\n", next_100_chars):
            return match

    return item1_matches[-1]
