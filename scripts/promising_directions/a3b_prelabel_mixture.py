"""A3b: pre-label public-coin mixture certificate (protocols/A3b-prelabel-mixture-certificate.md)."""

import json
import sys
import time
from fractions import Fraction as F
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import a1_exact_separation as a1
import a2_binding_alpha_screen as a2
import a3_calendar_certificates as a3

OUT = Path("docs/promising_directions/results/a3b")
ALPHA = "1/10"
B = 4


def released_any(outcomes, t: int, d: int) -> bool:
    return any(s + d <= t for s, _ in outcomes)


def branches(game, policy):
    """(lambda, prefix) for every positive-mass sequence of label-free choices."""
    d, T = game.config.delay, game.config.horizon
    out = []

    def walk(history, outcomes, lam):
        t = len(history) + 1
        if t > T or released_any(outcomes, t, d):
            out.append((lam, history))
            return
        for choice, m in zip(game.choices(history), policy(history, outcomes), strict=True):
            if not m:
                continue
            # unreleased outcomes cannot influence label-free choices; use label 0 as placeholder
            nxt = (*outcomes, (t, 0)) if choice[1] else outcomes
            walk((*history, choice), nxt, lam * m)

    walk((), (), F(1))
    return out


def branch_policy(game, policy, prefix):
    def pol(history, outcomes):
        n = len(history)
        if n < len(prefix) and tuple(history) == prefix[:n]:
            return tuple(F(c == prefix[n]) for c in game.choices(history))
        return policy(history, outcomes)

    return pol


def cell(fam: dict, deadline: float) -> dict:
    p = {**fam, "B": B, "alpha": ALPHA}
    cfg, model = a1.make(p)
    game = a1._SOLVER["Joint"](cfg, model)
    rep, policy, _ = game.solve()
    j, act = F(rep["calibrated_total_cost"]), F(rep["activation_probability"])
    row = {"params": p, "J": str(j), "activation": str(act), "status": "completed"}
    if act != 1:
        row["checkable"] = False
        return row
    tot_cost, tot_risk, rows = F(0), F(0), []
    for lam, prefix in branches(game, policy):
        bp = branch_policy(game, policy, prefix)
        flags = a3.enumerate_flags(game, bp, deadline)
        cost = sum(game.expected_metrics(bp)[:3], F(0))
        risk = game.null_risk(bp)
        tot_cost += lam * cost
        tot_risk += lam * risk
        rows.append(
            {
                "lambda": str(lam),
                "prefix": [list(c) for c in prefix],
                "support": flags["query_support"],
                "cost": str(cost),
                "risk": str(risk),
            }
        )
    row.update(
        checkable=True,
        branches=rows,
        cost_matches_J=tot_cost == j,
        mixture_risk=str(tot_risk),
        risk_le_alpha=tot_risk <= F(ALPHA),
        all_supports_le_B=all(len(b["support"]) <= B for b in rows),
    )
    row["certified"] = row["cost_matches_J"] and row["risk_le_alpha"] and row["all_supports_le_B"]
    return row


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "provenance.json").write_text(
        json.dumps(a1.verify_solver(Path(a1.DEFAULT_SOLVER_ROOT)), indent=2)
    )
    a1.load_solver(a1.DEFAULT_SOLVER_ROOT)
    path = OUT / "cells.jsonl"
    done = {a2.fam_key(r["params"]) for r in a1.read_jsonl(path)}
    deadline = time.time() + 2 * 3600
    for fam in a2.families():
        if a2.fam_key(fam) in done or time.time() > deadline:
            continue
        try:
            row = cell(fam, deadline)
        except (MemoryError, RuntimeError, TimeoutError) as e:
            row = {"params": {**fam, "B": B, "alpha": ALPHA}, "status": "failed", "error": repr(e)}
        with path.open("a") as f:
            f.write(json.dumps(row) + "\n")
        print(a2.fam_key(fam), row.get("certified"), flush=True)
    rows = a1.read_jsonl(path)
    chk = [r for r in rows if r.get("checkable")]
    summary = {
        "protocol": "protocols/A3b-prelabel-mixture-certificate.md",
        "n_rows": len(rows),
        "n_failed": sum(r["status"] == "failed" for r in rows),
        "n_checkable": len(chk),
        "n_certified": sum(r["certified"] for r in chk),
        "uncertified": [r["params"] for r in chk if not r["certified"]],
        "max_branches": max((len(r["branches"]) for r in chk), default=0),
        "decision": (
            "PRE-LABEL MIXTURE EXPLAINS"
            if chk and all(r["certified"] for r in chk) and len(chk) == len(rows)
            else "GENUINE ADAPTIVITY OR INCOMPLETE"
        ),
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2))
    print(summary["decision"], summary["n_certified"], "/", summary["n_checkable"], flush=True)


if __name__ == "__main__":
    main()
