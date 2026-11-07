"""A1b: exact gap along one parameter family (protocols/A1b-growing-family.md)."""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import a1_exact_separation as a1

OUT = Path("docs/promising_directions/results/a1b")
BASE = {
    "B": 3,
    "d": 1,
    "trans": "1/20",
    "e0": "1/50",
    "e1": "49/50",
    "cq": "1/100",
    "cs": "1/20",
    "prior1": "1/5",
}
PLAN = [("1/5", T) for T in range(6, 13)] + [("1/10", T) for T in (9, 10, 11)]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    prov = a1.verify_solver(Path(a1.DEFAULT_SOLVER_ROOT))
    (OUT / "provenance.json").write_text(json.dumps(prov, indent=2))
    a1.load_solver(a1.DEFAULT_SOLVER_ROOT)
    path = OUT / "cells.jsonl"
    done = {(r["params"]["alpha"], r["params"]["T"]) for r in a1.read_jsonl(path)}
    deadline = time.time() + 4 * 3600
    for alpha, T in PLAN:
        if (alpha, T) in done or time.time() > deadline:
            continue
        p = {**BASE, "alpha": alpha, "T": T}
        try:
            row = a1.solve_cell(p)
        except (MemoryError, RuntimeError) as e:
            row = {"params": p, "status": "failed", "error": repr(e)}
        with path.open("a") as f:
            f.write(json.dumps(row) + "\n")
        print(alpha, T, row.get("rel_gap_float"), row.get("solve_seconds"), flush=True)


if __name__ == "__main__":
    main()
