from dataclasses import dataclass
from typing import List, Optional


@dataclass
class EmailRecipients:
    """Represents email recipients."""

    to: List[str]
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    reply_to: Optional[str] = None
