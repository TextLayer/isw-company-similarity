import os

from isw.core.utils.git.types import WorkingDirIndicator


def determine_working_dir(dir: str, indicators: list[WorkingDirIndicator] = None) -> str:
    """
    Determine the working directory for a given repository.

    Args:
        dir: The base directory
        indicators: Where to find the root (if nested)

    Returns:
        The working directory for the repository
    """
    if indicators is None:
        return dir

    for root, dirs, files in os.walk(dir):
        if all(indicator["name"] in (dirs if indicator["is_folder"] else files) for indicator in indicators):
            return root

    return dir


def format_private_key(key_string: str) -> str:
    """
    Format an RSA private key with appropriate line breaks.

    Args:
        key_string: The unformatted private key string

    Returns:
        The properly formatted private key string with line breaks
    """
    header = "-----BEGIN RSA PRIVATE KEY-----"
    footer = "-----END RSA PRIVATE KEY-----"

    start_idx = key_string.find(header)
    if start_idx == -1:
        raise ValueError("Header not found in the key string.")
    start_idx += len(header)

    end_idx = key_string.find(footer, start_idx)
    if end_idx == -1:
        raise ValueError("Footer not found in the key string.")

    base64_content = key_string[start_idx:end_idx].replace("\n", "").replace(" ", "").strip()

    formatted_content = "\n".join([base64_content[i : i + 64] for i in range(0, len(base64_content), 64)])

    formatted_key = f"{header}\n{formatted_content}\n{footer}"
    return formatted_key
