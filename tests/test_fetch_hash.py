from __future__ import annotations

from pathlib import Path

import pytest

from flyciv.data.fetch import fetch_dataset, parse_sha256sums
from flyciv.data.hashutil import HashMismatch, verify_sha256
from flyciv.data.manifest import STUB_SHA256, stub_path


def test_sha256_accepts_matching_fixture(tmp_path: Path):
    src = Path(stub_path())
    dst = tmp_path / "sha256-stub.txt"
    dst.write_bytes(src.read_bytes())
    actual = verify_sha256(dst, STUB_SHA256)
    assert actual == STUB_SHA256


def test_sha256_rejects_bitflipped_copy(tmp_path: Path):
    data = bytearray(Path(stub_path()).read_bytes())
    data[0] ^= 0x01
    dst = tmp_path / "flipped.txt"
    dst.write_bytes(bytes(data))
    with pytest.raises(HashMismatch):
        verify_sha256(dst, STUB_SHA256)


def test_fetch_writes_instructions_and_checks_sums(tmp_path: Path):
    out = tmp_path / "derived"
    stub = Path(stub_path()).read_bytes()
    (out).mkdir()
    (out / "tiny.bin").write_bytes(stub)
    (out / "SHA256SUMS").write_text(f"{STUB_SHA256}  tiny.bin\n", encoding="utf-8")
    result = fetch_dataset("male-cns:v1.0", out)
    assert (out / "DOWNLOAD.md").is_file()
    assert "tiny.bin" in result["checked"]
    assert parse_sha256sums(f"{STUB_SHA256}  tiny.bin\n")["tiny.bin"] == STUB_SHA256
