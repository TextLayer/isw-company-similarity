from vaul import StructuredOutput


def extract_output(response: str) -> StructuredOutput | str | list:
    if hasattr(response, "__dict__") or not isinstance(response, (list, str)):
        return response
    else:
        try:
            return response[-1]["content"].strip()
        except Exception:
            return response
