"""Fixture paths, snapshot load, baseline diff helpers."""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

_MODULE_KEYS = ("site", "pricing", "changelog", "careers")


def package_root() -> Path:
    """Repo root (parent of src/)."""
    return Path(__file__).resolve().parents[2]


def default_fixture_dir() -> Path:
    return package_root() / "fixtures"


def default_snapshot_dir() -> Path:
    return default_fixture_dir() / "snapshots"


def default_baseline_path() -> Path:
    return default_fixture_dir() / "baselines" / "baseline.json"


def quiet_baseline_path() -> Path:
    return default_fixture_dir() / "baselines" / "quiet.json"


def material_baseline_path() -> Path:
    return default_fixture_dir() / "baselines" / "material.json"


def default_watchlist() -> list[dict[str, Any]]:
    path = default_fixture_dir() / "watchlist.json"
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return []


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.lower())


def snapshot_filename(competitor: str, module: str) -> str:
    """Map competitor+module to fixture filename."""
    slug = _slug(competitor)
    ext = "txt" if module == "changelog" else "html"
    return f"{slug}_{module}.{ext}"


def load_fixture_snapshot(
    snapshot_dir: Path, competitor: str, module: str
) -> dict[str, Any] | None:
    fname = snapshot_filename(competitor, module)
    path = snapshot_dir / fname
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    return {
        "competitor": competitor,
        "module": module,
        "text": text,
        "content_hash": content_hash(text),
        "ok": True,
        "snapshot_file": fname,
        "source": "fixture",
    }


def load_baseline(path: Path) -> dict[str, dict[str, Any]]:
    """Index baseline entries by competitor|module."""
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = data.get("entries") or []
    out: dict[str, dict[str, Any]] = {}
    for e in entries:
        key = f"{e.get('competitor')}|{e.get('module')}"
        out[key] = e
    return out


def summarize_change(module: str, old_excerpt: str, new_text: str) -> str:
    """Short human delta summary (deterministic, no LLM)."""
    new_ex = new_text.strip()[:200]
    if module == "pricing":
        return f"Pricing page changed (was ~{len(old_excerpt)} chars → {len(new_text)})."
    if module == "changelog":
        first = new_text.strip().splitlines()[0] if new_text.strip() else "changelog update"
        return f"Changelog update: {first[:120]}"
    if module == "careers":
        return "Careers page content changed."
    # site
    return f"Site copy changed: {new_ex[:100]}…"


def change_type(module: str) -> str:
    return {
        "pricing": "pricing_change",
        "changelog": "changelog_entry",
        "careers": "careers_change",
        "site": "site_copy_change",
    }.get(module, "content_change")


def diff_snapshots(
    snapshots: list[dict[str, Any]],
    baseline_index: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return deltas where content_hash differs from baseline (or new module)."""
    deltas: list[dict[str, Any]] = []
    for snap in snapshots:
        if not snap.get("ok"):
            continue
        comp = snap.get("competitor") or ""
        module = snap.get("module") or ""
        key = f"{comp}|{module}"
        base = baseline_index.get(key)
        new_hash = snap.get("content_hash") or content_hash(snap.get("text") or "")
        if base and base.get("content_hash") == new_hash:
            continue
        old_excerpt = (base or {}).get("text_excerpt") or ""
        new_text = snap.get("text") or ""
        deltas.append(
            {
                "competitor": comp,
                "module": module,
                "change_type": change_type(module),
                "summary": summarize_change(module, old_excerpt, new_text),
                "evidence_url": snap.get("url") or (base or {}).get("url") or "",
                "old_hash": (base or {}).get("content_hash") or "",
                "new_hash": new_hash,
            }
        )
    return deltas


def allow_network() -> bool:
    """Network fetch allowed only when ALLOW_NET is truthy (default off for tests)."""
    val = (os.environ.get("ALLOW_NET") or "0").strip().lower()
    return val in {"1", "true", "yes", "on"}


def modules_from_watchlist(watchlist: list[dict[str, Any]]) -> list[str]:
    found: list[str] = []
    for item in watchlist:
        urls = item.get("urls") or {}
        for m in _MODULE_KEYS:
            if urls.get(m) and m not in found:
                found.append(m)
        # public_search is optional plan module when no URLs — skip in v1 fixtures
    if not found:
        found = ["site"]
    return found
