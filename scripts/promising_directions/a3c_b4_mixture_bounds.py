"""A3c: exact mixture-gap bounds at B=4, alpha=1/10 (protocols/A3c-b4-mixture-bounds.md)."""

import json
import multiprocessing as mp
import sys
import time
from fractions import Fraction as F
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import a1_exact_separation as a1
import a2_binding_alpha_screen as a2
from mixture_bounds import mixture_bounds

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/promising_directions/results/a3c"
A3 = ROOT / "docs/promising_directions/results/a3/part2.jsonl"
FAMS = [
    ("49/50", "1/20", "1/20", "1/20"),
    ("49/50", "1/20", "1/20", "1/5"),
    ("49/50", "1/20", "1/10", "1/20"),
    ("49/50", "1/20", "1/10", "1/5"),
    ("19/20", "1/20", "1/20", "1/20"),
    ("19/20", "1/20", "1/20", "1/5"),
]
GRID = [
    "0", "1/40", "1/20", "3/40", "1/10", "1/8", "3/20",
    "1/5", "1/4", "3/10", "2/5", "1/2", "3/4", "1",
]  # fmt: skip
EFFECT = F(1, 200)


def family(acc: str, trans: str, prior1: str, cs: str) -> dict:
    return {
        "T": 8,
        "B": 4,
        "d": 1,
        "trans": trans,
        "e0": str(1 - F(acc)),
        "e1": acc,
        "cq": "1/100",
        "cs": cs,
        "prior1": prior1,
    }


def key(fam_key: str, a: str, cal) -> str:
    return f"{fam_key}|{a}|{list(cal)}"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "provenance.json").write_text(
        json.dumps(a1.verify_solver(Path(a1.DEFAULT_SOLVER_ROOT)), indent=2)
    )
    path = OUT / "calendar_values.jsonl"
    done = {key(r["family"], r["a"], r["calendar"]) for r in a1.read_jsonl(path)}
    fams = [family(*f) for f in FAMS]
    tasks = [
        (fam, a, cal)
        for fam in fams
        for a in GRID
        for cal in a1.calendars(8, 4, 1)
        if key(a2.fam_key(fam), a, cal) not in done
    ]
    deadline = time.time() + 3 * 3600
    if tasks:
        with mp.Pool(2, initializer=a2.init, initargs=(a1.DEFAULT_SOLVER_ROOT,)) as pool:
            for row in pool.imap_unordered(a2.calendar_work, tasks, chunksize=4):
                with path.open("a") as f:
                    f.write(json.dumps(row) + "\n")
                if time.time() > deadline:
                    pool.terminate()
                    break
    summarize(fams, path)


def summarize(fams: list[dict], path: Path) -> None:
    rows = a1.read_jsonl(path)
    a3 = {}
    for r in a1.read_jsonl(A3):
        if r.get("status") == "completed":
            a3[(a2.fam_key(r["params"]), r["params"]["alpha"])] = r
    out = []
    for fam in fams:
        fk = a2.fam_key(fam)
        per: dict = {}
        failed = 0
        for r in rows:
            if r["family"] != fk:
                continue
            if r["status"] != "completed":
                failed += 1
                continue
            per.setdefault(tuple(r["calendar"]), []).append((F(r["a"]), F(r["cost"])))
        complete = failed == 0 and all(len(v) == len(GRID) for v in per.values()) and len(per) == 99
        res = {"family": fk, "complete": complete, "failed_solves": failed}
        if not complete:
            out.append(res)
            continue
        convex = True
        for v in per.values():
            v.sort()
            xs, ys = [x for x, _ in v], [y for _, y in v]
            s = [(ys[i + 1] - ys[i]) / (xs[i + 1] - xs[i]) for i in range(len(v) - 1)]
            if any(ys[i + 1] > ys[i] for i in range(len(v) - 1)) or any(
                s[i + 1] < s[i] for i in range(len(s) - 1)
            ):
                convex = False
        tight, ref = a3[(fk, "1/10")], a3[(fk, "1")]
        j = F(tight["J"])
        cstar = min(dict(v)[F(1, 10)] for v in per.values())
        lo, up = mixture_bounds(per, F(1, 10))
        j1 = F(ref["computed"]["J"])
        c1 = F(ref["computed"]["C_star"])
        res.update(
            convex_monotone=convex,
            cstar_matches_a3=cstar == F(tight["computed"]["C_star"]),
            g_pure=float((cstar - j) / j),
            g_lo=str((lo - j) / j),
            g_up=str((up - j) / j),
            g_lo_float=float((lo - j) / j),
            g_up_float=float((up - j) / j),
            g1=float((c1 - j1) / j1),
            g1_exact=str((c1 - j1) / j1),
            g_lo_minus_g1=float((lo - j) / j - (c1 - j1) / j1),
        )
        out.append(res)
    ok = [r for r in out if r.get("complete") and r["convex_monotone"] and r["cstar_matches_a3"]]
    if len(ok) < len(fams):
        decision = "INCOMPLETE OR INVALID"
    elif all(F(r["g_up"]) <= 0 for r in ok):
        decision = "MIXTURES CLOSE IT"
    elif any(F(r["g_lo"]) - F(r["g1_exact"]) >= EFFECT for r in ok):
        decision = "RISK-SPECIFIC AT alpha = 0.10"
    elif any(F(r["g_lo"]) > 0 for r in ok):
        decision = "GENUINE GAP AT alpha = 0.10"
    else:
        decision = "INCONCLUSIVE"
    summary = {
        "protocol": "protocols/A3c-b4-mixture-bounds.md",
        "families": out,
        "decision": decision,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2))
    print(decision, flush=True)


if __name__ == "__main__":
    main()
