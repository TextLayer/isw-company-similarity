import re


class Keyword:
    def __init__(self, text: str):
        self.text = text

    def clean(self) -> str:
        """
        Remove all non-alphanumeric characters and trim output.
        """
        return re.sub(r"[^a-zA-Z0-9\s]", "", self.text).strip()

    def split_into_phrases(self) -> list[str]:
        """
        Extract double-quoted phrases and return them as a sanitized list.
        """
        independent_phrases = re.findall(r'"([^"]*)"', self.text)
        return list(map(lambda x: Keyword(x).clean(), independent_phrases))
