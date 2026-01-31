from pathlib import Path

from isw.core.utils.prompts import load_prompt

_PROMPT_DIR = Path(__file__).parent

FILING_SYSTEM_PROMPT = load_prompt(_PROMPT_DIR, "filing_system.md")
FILING_USER_TEMPLATE = load_prompt(_PROMPT_DIR, "filing_user.md")

WEB_CONTENT_SYSTEM_PROMPT = load_prompt(_PROMPT_DIR, "web_content_system.md")
WEB_CONTENT_USER_TEMPLATE = load_prompt(_PROMPT_DIR, "web_content_user.md")
