"""Drift watch v0 (round-8 B3) — pure code, honest.

Snapshots the evidence pack (sha256 per file) at baseline time; on demand,
compares current files against the snapshot and reports drift as structured
deltas the chat surface renders as messages. Changed evidence names the wiki
claims that cited it, so the user sees exactly which decisions are now
standing on moved ground. No model calls; re-debating is a human choice.
"""

import hashlib
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
EVIDENCE_DIR = DATA_DIR / "andigi"
SNAPSHOT_FILE = EVIDENCE_DIR / ".evidence-snapshot.json"


def _hash(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def _files() -> dict[str, str]:
    return {p.name: _hash(p) for p in sorted(EVIDENCE_DIR.iterdir())
            if p.is_file() and not p.name.startswith(".")}


def snapshot() -> dict:
    snap = _files()
    SNAPSHOT_FILE.write_text(json.dumps(snap, indent=2))
    return snap


def check(run: dict) -> list[dict]:
    """Compare evidence on disk vs the baseline snapshot. Returns drift deltas."""
    if not SNAPSHOT_FILE.exists():
        snapshot()
        return [{"kind": "info", "text": "evidence snapshot created — drift will be detected from now on"}]

    old = json.loads(SNAPSHOT_FILE.read_text())
    now = _files()
    deltas: list[dict] = []

    claims_by_file: dict[str, list[str]] = {}
    for c in run["stages"]["wiki"]["claims"]:
        for s in c["sources"]:
            claims_by_file.setdefault(s["source_file"], []).append(c["id"])

    for name, h in now.items():
        if name not in old:
            deltas.append({"kind": "added", "text": f"NEW EVIDENCE: {name} — not part of the signed baseline; a re-cycle would ingest it"})
        elif old[name] != h:
            touched = sorted(set(claims_by_file.get(name, [])))
            conflicts = [c["id"] for c in run["stages"]["conflicts"]["conflicts"]
                         if any(cid in c["claim_ids"] for cid in touched)]
            deltas.append({
                "kind": "changed",
                "text": (f"DRIFT: {name} changed since the baseline · claims standing on it: "
                          f"{', '.join(touched) or 'none traced'}"
                          + (f" · conflicts to re-check: {', '.join(conflicts)}" if conflicts else "")
                          + " — the signed spec now cites moved ground"),
            })
    for name in old:
        if name not in now:
            deltas.append({"kind": "removed", "text": f"EVIDENCE REMOVED: {name} — claims citing it are now unbacked"})

    if not deltas:
        deltas.append({"kind": "ok", "text": f"no drift — {len(now)} evidence files match the signed snapshot"})
    return deltas
