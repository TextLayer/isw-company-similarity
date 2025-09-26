from dataclasses import dataclass
from typing import Any, List, Optional, TypeAlias

OCRPages: TypeAlias = List["OCRPage"]


@dataclass
class OCRPage:
    markdown: str
    page_number: int


@dataclass
class OCRResult:
    pages: OCRPages
    metadata: Optional[dict[str, Any]] = None
