from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from flyciv.data.hashutil import verify_sha256
from flyciv.data.manifest import DOWNLOAD_MD, MALE_CNS_V1, STUB_SHA256, stub_path


def parse_sha256sums(text: str) -> dict[str, str]:
    """Parse GNU `sha256sum` lines: `<hex>  <filename>`."""
    out: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        hex_part, _, name = line.partition(" ")
        name = name.lstrip(" *")
        out[name] = hex_part.strip().lower()
    return out


def verify_tree(out_dir: Path, sums: dict[str, str]) -> list[str]:
    checked: list[str] = []
    for name, expected in sums.items():
        path = out_dir / name
        if not path.is_file():
            raise FileNotFoundError(f"missing {path} (listed in SHA256SUMS)")
        verify_sha256(path, expected)
        checked.append(name)
    return checked


def _try_neuprint_ping(timeout_s: float = 8.0) -> dict[str, Any]:
    """Optional anonymous Cypher. Network failure is recorded, never vendored around."""
    try:
        import urllib.error
        import urllib.request
    except ImportError:  # pragma: no cover
        return {"ok": False, "error": "urllib missing"}
    url = MALE_CNS_V1["neuprint_custom"]
    body = json.dumps(
        {
            "cypher": "MATCH (n:Neuron) RETURN count(n) AS n LIMIT 1",
            "dataset": MALE_CNS_V1["neuprint_dataset"],
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            raw = resp.read(2048)
            return {"ok": True, "status": getattr(resp, "status", 200), "body": raw[:500].decode("utf-8", "replace")}
    except Exception as exc:  # noqa: BLE001 — fetch is best-effort
        return {"ok": False, "error": str(exc)}


def fetch_dataset(
    dataset: str,
    out_dir: Path,
    *,
    try_network: bool = False,
) -> dict[str, Any]:
    if dataset != MALE_CNS_V1["dataset"]:
        raise ValueError(f"unsupported dataset {dataset!r}; default is {MALE_CNS_V1['dataset']}")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    download_path = out_dir / "DOWNLOAD.md"
    download_path.write_text(DOWNLOAD_MD, encoding="utf-8")
    (out_dir / "CITATION.txt").write_text(MALE_CNS_V1["cite"] + "\n", encoding="utf-8")

    result: dict[str, Any] = {
        "dataset": dataset,
        "out": str(out_dir),
        "download_md": str(download_path),
        "checked": [],
        "network": None,
        "note": "Data is downloaded, not vendored. Compact graphs stay under data/derived/.",
    }
    sums_path = out_dir / "SHA256SUMS"
    if sums_path.is_file():
        sums = parse_sha256sums(sums_path.read_text(encoding="utf-8"))
        result["checked"] = verify_tree(out_dir, sums)
    if try_network:
        result["network"] = _try_neuprint_ping()
    return result


def verify_stub() -> str:
    return verify_sha256(Path(stub_path()), STUB_SHA256)
