from __future__ import annotations

import hashlib
from pathlib import Path


class HashMismatch(ValueError):
    def __init__(self, path: Path, expected: str, actual: str) -> None:
        self.path = Path(path)
        self.expected = expected.lower()
        self.actual = actual.lower()
        super().__init__(
            f"SHA256 mismatch for {self.path}: expected {self.expected}, got {self.actual}"
        )


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path, chunk_size: int = 65536) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as fh:
        while True:
            chunk = fh.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def verify_sha256(path: Path, expected: str) -> str:
    """Return the actual hex digest if it matches `expected`, else raise HashMismatch."""
    actual = sha256_file(path)
    if actual.lower() != expected.lower():
        raise HashMismatch(path, expected, actual)
    return actual
