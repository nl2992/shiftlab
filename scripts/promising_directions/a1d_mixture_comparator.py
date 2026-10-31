"""A1d: does the A1c gap survive public-coin mixtures of calendars?

Executes the registered protocol docs/promising_directions/protocols/A1d-mixture-comparator.md.
Development/theory probe; no method claim.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing as mp
import sys
import time
from datetime import UTC, datetime
from fractions import Fraction as F
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import a1_exact_separation as a1

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/promising_directions/results/a1d"
A1C = ROOT / "docs/promising_directions/results/a1c"
PROTOCOL_SHA256 = "4f3ccc35e957199e1c824664fb5b7f3e8fb8506206830ec571335fdd2561e97e"
PROTOCOL_COMMIT = "bf165a7"
BASE = {
    "T": 9,
    "B": 3,
    "d": 1,
    "trans": "1/20",
    "e0": "1/50",
    "e1": "49/50",
    "cq": "1/100",
    "cs": "1/20",
}
PRIORS = ["1/10", "1/5", "3/10"]
GRID = [
    "0", "1/20", "1/10", "1/8", "3/20", "1/6", "9/50", "1/5", "1/4", "3/10", "2/5", "1/2", "3/4",
    "1",
]  # fmt: skip
EFFECT = F(1, 200)
CAP_SECONDS = 2 * 3600


def key_of(prior1: str, a: str, cal) -> str:
    return json.dumps([prior1, a, list(cal)])


def work(task: tuple[str, str, list[int]]) -> dict:
    prior1, a, cal = task
    p = {**BASE, "prior1": prior1, "alpha": a}
    row = {"prior1": prior1, "a": a, "calendar": list(cal)}
    try:
        cfg, model = a1.make(p)
        rep = a1._SOLVER["Calendar"](cfg, model, tuple(cal)).solve()[0]
        row.update(
            status="completed",
            cost=str(F(rep["calibrated_total_cost"])),
            risk_bound=str(F(rep["calibrated_risk_bound"])),
        )
    except (MemoryError, RuntimeError) as exc:
        row.update(status="failed", error=f"{type(exc).__name__}: {exc}")
    return row


def init(root: str) -> None:
    a1.load_solver(root)


def run_solves(workers: int, deadline: float) -> None:
    path = OUT / "calendar_values.jsonl"
    done = {
        key_of(r["prior1"], r["a"], r["calendar"])
        for r in a1.read_jsonl(path)
        if r.get("status") in ("completed", "failed")
    }
    cals = a1.calendars(BASE["T"], BASE["B"], BASE["d"])
    tasks = [
        (pr, a, list(c))
        for pr in PRIORS
        for a in GRID
        for c in cals
        if key_of(pr, a, c) not in done
    ]
    print(f"{len(tasks)} solves to run, workers={workers}", flush=True)
    if not tasks:
        return
    n = 0
    with mp.Pool(workers, initializer=init, initargs=(a1.DEFAULT_SOLVER_ROOT,)) as pool:
        for row in pool.imap_unordered(work, tasks, chunksize=4):
            with path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(row) + "\n")
            n += 1
            if n % 100 == 0:
                print(n, "done", flush=True)
            if time.time() > deadline:
                print("deadline reached; stopping", flush=True)
                pool.terminate()
                break


# ------------------------------------------------------------------ exact hull


def lower_hull(points: list[tuple[F, F]]) -> list[tuple[F, F]]:
    """Lower convex hull (monotone chain), exact. Collinear interior points are dropped."""
    best: dict[F, F] = {}
    for x, y in points:
        best[x] = min(y, best.get(x, y))
    hull: list[tuple[F, F]] = []
    for p in sorted(best.items()):
        while len(hull) >= 2:
            (x1, y1), (x2, y2) = hull[-2], hull[-1]
            if (x2 - x1) * (p[1] - y1) - (y2 - y1) * (p[0] - x1) <= 0:
                hull.pop()
            else:
                break
        hull.append(p)
    return hull


def evaluate(hull: list[tuple[F, F]], target: F) -> tuple[F, list[tuple[F, F]]]:
    """Value at target of min(envelope interpolation, min hull vertex with a <= target).

    Vertices with a <= target are feasible (smaller risk is feasible); the envelope is
    interpolated between the bracketing vertices. Returns (value, supporting vertices).
    """
    left = [v for v in hull if v[0] <= target]
    if not left:
        raise ValueError("target below smallest hull abscissa")
    vmin = min(left, key=lambda v: (v[1], v[0]))
    right = [v for v in hull if v[0] > target]
    if right:
        (x1, y1), (x2, y2) = left[-1], right[0]
        interp = y1 + (y2 - y1) * (target - x1) / (x2 - x1)
        if interp < vmin[1]:
            return interp, [left[-1], right[0]]
    return vmin[1], [vmin]


# ------------------------------------------------------------------ summary


def summarize(provenance: dict, runtime: float | None) -> dict:
    vals = a1.read_jsonl(OUT / "calendar_values.jsonl")
    failed = [r for r in vals if r["status"] == "failed"]
    ok = [r for r in vals if r["status"] == "completed"]
    j_rows: dict[tuple[str, str], dict] = {}
    for part in ("p1", "p2"):
        for r in a1.read_jsonl(A1C / f"{part}.jsonl"):
            if r["status"] == "completed":
                p = r["params"]
                j_rows[(p["prior1"], p["alpha"])] = r
    sanity, tables, anomalies = [], {}, []
    for pr in PRIORS:
        pts: list[tuple[F, F]] = []
        meta: dict[tuple[F, F], list[list[int]]] = {}
        bya: dict[str, list[F]] = {}
        for r in ok:
            if r["prior1"] != pr:
                continue
            x, y = F(r["a"]), F(r["cost"])
            pts.append((x, y))
            meta.setdefault((x, y), []).append(r["calendar"])
            bya.setdefault(r["a"], []).append(y)
        hull = lower_hull(pts)
        rows = []
        for (p_, alpha), r in sorted(j_rows.items(), key=lambda kv: (kv[0][0], F(kv[0][1]))):
            if p_ != pr:
                continue
            t, j, cstar = F(alpha), F(r["J"]), F(r["C_star"])
            if len(bya.get(alpha, [])) == r["n_calendars"]:
                m = min(bya[alpha])
                sanity.append(
                    {
                        "prior1": pr,
                        "alpha": alpha,
                        "min_c": str(m),
                        "C_star": str(cstar),
                        "match": m == cstar,
                    }
                )
            cmix, sup = evaluate(hull, t)
            g, gm = (cstar - j) / j, (cmix - j) / j
            if j > cmix:
                anomalies.append({"prior1": pr, "alpha": alpha, "J": str(j), "C_mix": str(cmix)})
            rows.append(
                {
                    "alpha": alpha,
                    "J": str(j),
                    "C_star": str(cstar),
                    "C_mix": str(cmix),
                    "g": str(g),
                    "g_float": float(g),
                    "g_mix": str(gm),
                    "g_mix_float": float(gm),
                    "removed_fraction": str((g - gm) / g) if g else None,
                    "removed_fraction_float": float((g - gm) / g) if g else None,
                    "J_le_C_mix": j <= cmix,
                    "C_mix_le_C_star": cmix <= cstar,
                    "supporting_vertices": [
                        {"a": str(x), "cost": str(y), "calendars": meta[(x, y)]} for x, y in sup
                    ],
                }
            )
        tables[pr] = {"n_hull_vertices": len(hull), "rows": rows}
    violations = []
    for pr, tb in tables.items():
        base = F(next(r for r in tb["rows"] if r["alpha"] == "1")["g_mix"])
        for r in tb["rows"]:
            if r["alpha"] != "1" and F(r["g_mix"]) >= base + EFFECT:
                violations.append(
                    {
                        "prior1": pr,
                        "alpha": r["alpha"],
                        "g_mix": r["g_mix_float"],
                        "g_mix_at_1": float(base),
                    }
                )
    complete = not failed and len(ok) == len(PRIORS) * len(GRID) * 93
    sanity_ok = bool(sanity) and all(s["match"] for s in sanity)
    outcome = "H-risk SURVIVES" if violations else "CONVEXIFICATION EXPLAINS"
    return {
        "protocol": {"sha256": PROTOCOL_SHA256, "commit": PROTOCOL_COMMIT},
        "n_solves_completed": len(ok),
        "n_solves_failed": len(failed),
        "complete": complete,
        "sanity_C_star_matches": sanity,
        "sanity_ok": sanity_ok,
        "J_gt_C_mix_anomalies": anomalies,
        "all_J_le_C_mix": all(r["J_le_C_mix"] for t in tables.values() for r in t["rows"]),
        "all_C_mix_le_C_star": all(
            r["C_mix_le_C_star"] for t in tables.values() for r in t["rows"]
        ),
        "tables": tables,
        "survive_violations": violations,
        "decision": outcome
        if (complete and sanity_ok)
        else "INVALID (incomplete or sanity failed)",
        "decision_rule": "H-risk SURVIVES iff some g_mix(alpha) >= g_mix(1)+0.005, alpha<1",
        "runtime_seconds_last_invocation": runtime,
        "provenance": provenance,
        "generated_utc": datetime.now(UTC).isoformat(),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--solver-root", default=a1.DEFAULT_SOLVER_ROOT)
    ap.add_argument("--skip-solve", action="store_true")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    prov = a1.verify_solver(Path(args.solver_root))
    proto = ROOT / "docs/promising_directions/protocols/A1d-mixture-comparator.md"
    if hashlib.sha256(proto.read_bytes()).hexdigest() != PROTOCOL_SHA256:
        raise SystemExit("protocol hash mismatch")
    t0 = time.time()
    if not args.skip_solve:
        run_solves(min(args.workers, 2), t0 + CAP_SECONDS)
    summary = summarize(prov, time.time() - t0)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    lines = [
        f"{hashlib.sha256((OUT / n).read_bytes()).hexdigest()} *{n}"
        for n in ("calendar_values.jsonl", "summary.json")
    ]
    (OUT / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(summary["decision"], "complete=", summary["complete"], flush=True)


if __name__ == "__main__":
    main()
