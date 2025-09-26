import os
import tempfile
from pathlib import Path


def create_shared_temp_dir() -> Path:
    tmp = tempfile.mkdtemp()
    write_access_permissions(tmp)
    return Path(tmp)


def remove_leading_slash(path: str) -> str:
    return path.lstrip("/") if path.startswith("/") else path


def write_access_permissions(path: Path):
    os.chmod(path, 0o755)
