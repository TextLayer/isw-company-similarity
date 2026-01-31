from pathlib import Path


def load_prompt(prompt_dir: Path, filename: str) -> str:
    """Load a prompt template from a file."""
    return (prompt_dir / filename).read_text().strip()
