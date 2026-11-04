"""Merge family ledgers into the 24-candidate registry and build the machine-readable leaderboard.

Inputs: ``docs/sota_sprint/candidates.json`` (registry) and ``docs/sota_sprint/family_*/ledger.json``
(each a list or dict of entries with at least ``id`` and ``status``). Optional validation summaries
are merged from ``docs/sota_sprint/validation/leaderboard_inputs.json``. Development and validated
results are kept in separate fields; a candidate counts as executed only with a results artifact.

    uv run python scripts/sota_sprint/leaderboard.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs/sota_sprint"
IDS = [f"{f}{i}" for f in "ABCD" for i in range(1, 7)]
FIELDS = ["id", "parent", "added_components", "intended_failure_mechanism", "implementation",
          "status", "dev_environments", "n_runs", "dev_cost_vs_best_certified",
          "dev_efficacy", "null_safety", "strongest_comparator_beaten", "novelty",
          "ablation", "real_data", "validation", "main_track_potential", "sota_performance",
          "next_action", "results_artifact"]


def _entries(path: Path) -> list[dict]:
    d = json.loads(path.read_text())
    if isinstance(d, dict):
        d = d.get("candidates", d.get("entries", d))
        d = list(d.values()) if isinstance(d, dict) else d
    return [e for e in d if isinstance(e, dict) and "id" in e]


def main():
    reg = json.loads((DOCS / "candidates.json").read_text())
    for led in sorted(DOCS.glob("family_*/ledger.json")):
        for e in _entries(led):
            if e["id"] in reg:
                reg[e["id"]].update({k: v for k, v in e.items() if v is not None})
                reg[e["id"]]["ledger"] = str(led.relative_to(ROOT))
    val = DOCS / "validation/leaderboard_inputs.json"
    if val.exists():
        for cid, v in json.loads(val.read_text()).items():
            e = reg.setdefault(cid, {"id": cid})
            e["validation"] = v
            for k in ("status", "main_track_potential", "sota_performance", "next_action"):
                if k in v:
                    e[k] = v[k]
    (DOCS / "candidates.json").write_text(json.dumps(reg, indent=1, default=str) + "\n")
    executed = [i for i in IDS if reg[i].get("results_artifact") and reg[i]["status"] not in (
        "NOT_IMPLEMENTED", "IMPLEMENTED", "BLOCKED")]
    board = {"executed": executed, "missing": [i for i in IDS if i not in executed],
             "rows": [{k: reg[c].get(k) for k in FIELDS} for c in reg]}
    (DOCS / "leaderboard.json").write_text(json.dumps(board, indent=1, default=str) + "\n")
    print(f"{len(executed)}/24 mandatory candidates executed; missing: {board['missing']}")
    for c in reg:
        print(f"{c:>8} {reg[c].get('status', ''):<20} {str(reg[c].get('disposition', ''))[:90]}")


if __name__ == "__main__":
    main()
