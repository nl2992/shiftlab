"""Recompute sha256 of every artifact recorded in the state; exit 1 on any mismatch."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from research_loop import ROOT, STATE, sha256_file


def verify(root: Path) -> list[str]:
    state = json.loads((root / STATE).read_text(encoding="utf-8"))
    bad = []
    for tid, t in state["tasks"].items():
        for rel, want in t["artifacts"].items():
            p = root / rel
            got = sha256_file(p) if p.is_file() else "MISSING"
            if got != want:
                bad.append(f"{tid}: {rel} expected {want[:12]} got {got[:12]}")
    return bad


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=ROOT)
    bad = verify(ap.parse_args().root)
    print("\n".join(bad) if bad else "all artifacts verified")
    sys.exit(1 if bad else 0)
