"""Small JSON writer shared by configuration and TPA settings."""

import json
import os
import tempfile
from pathlib import Path


_UNCHECKED = object()


class FileChangedError(OSError):
    """The file changed since the caller read it."""


def atomic_write_json(path, data, *, expected_content=_UNCHECKED) -> bytes:
    """Replace a complete JSON file; failures before replace leave it untouched.

    An optional byte snapshot rejects stale writes. This is a best-effort check
    against external editors, not a lock shared with other processes.
    """
    path = Path(path)
    content = json.dumps(data, indent=4, ensure_ascii=False, allow_nan=False).encode("utf-8")
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as f:
            temporary_path = f.name
            f.write(content)
            f.flush()
            os.fsync(f.fileno())

        if expected_content is not _UNCHECKED:
            try:
                current = path.read_bytes()
            except FileNotFoundError:
                current = None
            if current != expected_content:
                raise FileChangedError(f"{path} changed on disk; reload before saving")

        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            os.unlink(temporary_path)
    return content
