"""Driver for FCG scaling screen v2: each (cell, method) pair in its own fresh process.

Writes docs/paper4/experiments/results/fcg_scale_v2.json (refuses to overwrite).
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from fractions import Fraction as F
from pathlib import Path

sys.set_int_max_str_digits(0)  # exact dual bounds exceed the 4300-digit default

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "scripts/paper4/run_fcg_scale.py"
PROTOCOL = ROOT / "docs/paper4/experiments/protocols/FCG_SCALE_PROTOCOL_V2.md"
MODULES = {
    "frontier_cuts_fast": ROOT / "src/shiftlab/paper4/frontier_cuts_fast.py",
    "frontier_cuts_v1": ROOT / "src/shiftlab/paper4/frontier_cuts.py",
}
OUTPUT = ROOT / "docs/paper4/experiments/results/fcg_scale_v2.json"
TIMEOUT_SECONDS = 1200
ALPHA = F(1, 10)
PAIRS = [
    ("S1", "ref"),
    ("S1", "fast"),
    ("S2", "ref"),
    ("S2", "fast"),
    ("C6", "ref"),
    ("C6", "fast"),
    ("C6", "v1"),
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_pair(cell: str, method: str) -> dict:
    command = [sys.executable, str(RUNNER), "--cell", cell, "--method", method]
    started = time.perf_counter()
    try:
        proc = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            cwd=ROOT,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "cell": cell,
            "method": method,
            "status": "failed_timeout",
            "error": f"subprocess exceeded {TIMEOUT_SECONDS}s wall-clock cap",
            "end_to_end_seconds": time.perf_counter() - started,
            "stdout_tail": (exc.stdout or "")[-2000:] if isinstance(exc.stdout, str) else None,
        }
    wall = time.perf_counter() - started
    lines = [line for line in proc.stdout.splitlines() if line.startswith("{")]
    if proc.returncode != 0 or not lines:
        return {
            "cell": cell,
            "method": method,
            "status": "failed_process",
            "returncode": proc.returncode,
            "stdout_tail": proc.stdout[-2000:],
            "stderr_tail": proc.stderr[-4000:],
            "end_to_end_seconds": wall,
        }
    result = json.loads(lines[-1])
    result["process_wall_seconds"] = wall
    return result


def evaluate(runs: dict) -> dict:
    gates: dict = {}
    for cell in ("S1", "S2", "C6"):
        fast = runs.get((cell, "fast"))
        ref = runs.get((cell, "ref"))
        entry: dict = {"fast_status": fast and fast["status"], "ref_status": ref and ref["status"]}
        if fast and fast["status"] == "ok":
            u, lower = F(fast["U"]), F(fast["L"])
            risk_ok = F(fast["final_robust_risk"]) <= ALPHA
            gap_ok = u - lower <= F(1, 10**6) * max(F(1), abs(u))
            ref_ok = bool(ref and ref["status"] == "ok")
            match = None
            if ref_ok:
                match = abs(float(u - F(ref["V_ref"]))) <= 1e-6
            entry["g_correct_parts"] = {
                "risk_le_alpha": risk_ok,
                "L_le_U": lower <= u,
                "gap_le_1e-6_max1_absU": gap_ok,
                "reference_completed": ref_ok,
                "U_equals_Vref_1e-6": match,
                "abs_U_minus_Vref": float(abs(u - F(ref["V_ref"]))) if ref_ok else None,
            }
            entry["g_correct"] = bool(risk_ok and lower <= u and gap_ok and (match is not False))
            entry["g_correct_note"] = (
                "complete"
                if ref_ok
                else "reference did not complete: U = V_ref check not evaluable; other parts only"
            )
            entry["g_compute"] = {
                "fast_seconds": fast["end_to_end_seconds"],
                "ref_seconds": ref["end_to_end_seconds"] if ref_ok else None,
                "ref_status": ref["status"] if ref else None,
                "fast_faster_measured": (
                    fast["end_to_end_seconds"] < ref["end_to_end_seconds"] if ref_ok else None
                ),
                "fast_timing_split": {
                    k: fast[k]
                    for k in (
                        "build_seconds",
                        "lp_seconds",
                        "verify_seconds",
                        "row_seconds",
                        "u0_seconds",
                        "final_certificate_seconds",
                    )
                },
                "K_rows": fast["n_rows"],
                "reference_opponent_sequences": ref.get("opponent_sequences") if ref_ok else None,
                "reference_learner_sequences": ref.get("learner_sequences") if ref_ok else None,
                "fast_learner_variables": fast["learner_variables"],
            }
        else:
            entry["g_correct"] = False
            entry["g_correct_note"] = "FCG-fast did not complete"
        gates[cell] = entry
    s2 = gates["S2"]
    comp = s2.get("g_compute")
    if comp and comp["fast_faster_measured"] is True:
        outcome = "S2: FCG-fast faster than reference -> CONDITIONAL GO candidate (pending prior-art check)"
    elif comp and comp["fast_faster_measured"] is False:
        outcome = "S2: FCG-fast not faster than reference -> NO-GO computational feasibility"
    elif comp and comp["ref_seconds"] is None and s2["g_correct"]:
        outcome = (
            "S2: reference did not complete, FCG-fast did -> UNDETERMINED by rule; report verbatim"
        )
    else:
        outcome = "S2: FCG-fast did not complete -> NO-GO computational feasibility"
    return {
        "by_cell": gates,
        "G_correct_all_cells": all(g["g_correct"] for g in gates.values()),
        "decision_rule_s2": outcome,
    }


def main() -> None:
    if OUTPUT.exists():
        raise FileExistsError(f"Refusing to overwrite {OUTPUT}")
    runs: dict = {}
    for cell, method in PAIRS:
        print(f"[{cell}/{method}] start", flush=True)
        result = run_pair(cell, method)
        runs[cell, method] = result
        brief = {
            k: result.get(k)
            for k in ("status", "end_to_end_seconds", "error", "n_rows", "learner_variables")
        }
        print(f"[{cell}/{method}] {json.dumps(brief)}", flush=True)
    failures = [
        {"cell": c, "method": m, **{k: r.get(k) for k in ("status", "error", "trace")}}
        for (c, m), r in runs.items()
        if r["status"] != "ok"
    ]
    out = {
        "protocol_sha256": sha(PROTOCOL),
        "runner_sha256": sha(RUNNER),
        "driver_sha256": sha(Path(__file__)),
        "module_sha256": {name: sha(path) for name, path in MODULES.items()},
        "subprocess_timeout_seconds": TIMEOUT_SECONDS,
        "python": sys.version,
        "runs": [runs[pair] for pair in PAIRS],
        "failures": failures,
        "gates": evaluate(runs),
    }
    OUTPUT.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out["gates"], indent=2), flush=True)


if __name__ == "__main__":
    main()
