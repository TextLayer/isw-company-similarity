import re
from typing import Any, Dict

import markdown
import requests
from notion_client import APIResponseError, Client
from notion_to_md import NotionToMarkdown


class NotionServiceError(Exception):
    """Raised when the NotionService encounters an unrecoverable error."""


class NotionService:
    """
    A lightweight wrapper around the Notion API that converts Notion pages to Markdown/HTML.
    """

    def __init__(self, api_token: str):
        self.client = Client(auth=api_token)
        self.notion_to_md = NotionToMarkdown(self.client)

    def retrieve_page_markdown_html(self, page_id: str) -> Dict[str, Any]:
        """
        Fetches a page and returns:
            {
              "page": <raw_page_dict>,
              "markdown": "<md_str>",
              "html": "<html_str>"
            }
        """
        try:
            page = self.client.pages.retrieve(page_id=page_id)

            md_blocks = self.notion_to_md.page_to_markdown(page_id)
            md_dict = self.notion_to_md.to_markdown_string(md_blocks)

            markdown_str = "\n\n".join(content for content in md_dict.values() if content.strip())

            html_body = markdown.markdown(markdown_str, extensions=["tables", "fenced_code", "nl2br"])

            html_body = self._fix_code_blocks(html_body)

            return {"page": page, "markdown": markdown_str, "html": html_body}

        except APIResponseError as e:
            raise NotionServiceError(f"Notion API error: {e.code} – {str(e)}") from e
        except requests.RequestException as e:
            raise NotionServiceError(f"Network error: {e}") from e

    def _fix_code_blocks(self, html: str) -> str:
        """Fix Notion's improper code block formatting"""
        bash_pattern = (
            r"<p>```bash</p>\s*<h1>(.*?)</h1>\s*(.*?)\s*<h1>(.*?)</h1>\s*(.*?)\s*<h1>(.*?)</h1>\s*(.*?)\s*```</p>"
        )

        def replace_bash_block(match):
            commands = []
            for i in range(1, 7, 2):
                header = match.group(i)
                content = match.group(i + 1) if i + 1 <= 6 else ""
                if content:
                    content = re.sub(r"<p>", "", content)
                    content = re.sub(r"</p>", "", content)
                    content = re.sub(r"<br\s*/?>", "\n", content)
                    content = content.strip()
                    if content:
                        if header:
                            commands.append(f"# {header}")
                        commands.append(content)
                        commands.append("")

            code_content = "\n".join(commands).strip()
            return f'<pre><code class="language-bash">{code_content}</code></pre>'

        html = re.sub(bash_pattern, replace_bash_block, html, flags=re.DOTALL)

        pattern = r"<p>```(\w+)\s*(.*?)```</p>"

        def replace_code_block(match):
            language = match.group(1)
            code_content = match.group(2)

            code_content = re.sub(r"<br\s*/?>", "\n", code_content)
            code_content = re.sub(r"<[^>]+>", "", code_content)
            code_content = code_content.replace("&quot;", '"')
            code_content = code_content.replace("&lt;", "<")
            code_content = code_content.replace("&gt;", ">")
            code_content = code_content.replace("&amp;", "&")

            return f'<pre><code class="language-{language}">{code_content.strip()}</code></pre>'

        html = re.sub(pattern, replace_code_block, html, flags=re.DOTALL)

        multiline_pattern = r"<p>```(\w+)</p>\s*<h1>(.*?)</h1>\s*(.*?)\s*<p>```</p>"

        def replace_multiline_code_block(match):
            language = match.group(1)
            header = match.group(2)
            code_content = match.group(3)

            code_content = re.sub(r"<p>", "\n", code_content)
            code_content = re.sub(r"</p>", "", code_content)
            code_content = re.sub(r"<br\s*/?>", "\n", code_content)
            code_content = re.sub(r"<[^>]+>", "", code_content)

            full_code = f"# {header}\n{code_content.strip()}"

            return f'<pre><code class="language-{language}">{full_code}</code></pre>'

        html = re.sub(multiline_pattern, replace_multiline_code_block, html, flags=re.DOTALL)

        return html
