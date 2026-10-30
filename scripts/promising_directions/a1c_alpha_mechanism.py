"""A1c: what creates the A1b gap, the risk constraint or plain adaptivity?

Executes the registered protocol docs/promising_directions/protocols/A1c-alpha-mechanism.md.
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
OUT = ROOT / "docs/promising_directions/results/a1c"
A1B_CELLS = ROOT / "docs/promising_directions/results/a1b/cells.jsonl"
PROTOCOL_SHA256 = "d439eb500fcc40e572de14805adb1b600558b91fe6f5ba31fdf5dd73d3874cba"
PROTOCOL_COMMIT = "892c3bd"
BASE = {
    "B": 3,
    "d": 1,
    "trans": "1/20",
    "e0": "1/50",
    "e1": "49/50",
    "cq": "1/100",
    "cs": "1/20",
}
P1_ALPHAS = ["1/10", "1/8", "3/20", "1/6", "9/50", "1/5", "1/4", "3/10", "1/2", "1"]
P2_ALPHAS = ["1/10", "3/20", "1/5", "1/4", "3/10", "1/2", "1"]
P2_PRIORS = ["1/10", "3/10"]
P4_MAX_NODES = 2_000_000
EFFECT = F(1, 200)  # 0.5 percentage points
TOL = F(1, 10**9)
CAP_SECONDS = 4 * 3600


def cell(prior1: str, alpha: str, T: int) -> dict:
    return {**BASE, "prior1": prior1, "alpha": alpha, "T": T}


def plan() -> dict[str, list[dict]]:
    return {
        "p1": [cell("1/5", a, 9) for a in P1_ALPHAS],
        "p2": [cell(pr, a, 9) for pr in P2_PRIORS for a in P2_ALPHAS],
        "p3": [cell("1/5", "1", T) for T in range(6, 12)],
        "p4": [cell("1/5", "1/5", 12)],
    }


def solve_cell_ext(p: dict) -> dict:
    """Same J and C* as a1.solve_cell, plus pre-activation risk and activation per report."""
    cfg, model = a1.make(p)
    t0 = time.perf_counter()
    jrep = a1._SOLVER["Joint"](cfg, model).solve()[0]
    j = F(jrep["calibrated_total_cost"])
    rows = []
    for cal in a1.calendars(p["T"], p["B"], p["d"]):
        rep = a1._SOLVER["Calendar"](cfg, model, cal).solve()[0]
        assert F(rep["calibrated_risk_bound"]) <= cfg.alpha
        rows.append((F(rep["calibrated_total_cost"]), cal, rep))
    c_star, best, brep = min(rows, key=lambda r: (r[0], len(r[1]), r[1]))
    abs_gap = c_star - j

    def risk_fields(rep: dict) -> dict:
        return {
            "raw_risk": rep["raw_causal_null_risk"],
            "raw_risk_float": float(F(rep["raw_causal_null_risk"])),
            "activation": rep["activation_probability"],
            "activation_float": float(F(rep["activation_probability"])),
            "calibrated_risk": rep["calibrated_risk_bound"],
            "raw_cost": rep["raw_recovered_cost"],
            "continue_cost": rep["continue_cost"],
        }

    return {
        "params": p,
        "J": str(j),
        "J_float": float(j),
        "C_star": str(c_star),
        "C_star_float": float(c_star),
        "best_calendar": list(best),
        "abs_gap": str(abs_gap),
        "abs_gap_float": float(abs_gap),
        "rel_gap": str(abs_gap / j),
        "rel_gap_float": float(abs_gap / j),
        "j_le_cstar_within_tol": bool(float(j) - float(c_star) <= a1.TOL),
        "n_calendars": len(rows),
        "joint_nodes": jrep["nodes"],
        "joint": risk_fields(jrep),
        "best_calendar_report": {**risk_fields(brep), "nodes": brep["nodes"]},
        "calendars": [
            {"calendar": list(c), "cost": str(cost), **risk_fields(rep)} for cost, c, rep in rows
        ],
        "solve_seconds": time.perf_counter() - t0,
    }


def work(task: tuple[str, dict, int]) -> tuple[str, dict]:
    part, p, max_nodes = task
    a1.MAX_NODES = max_nodes
    try:
        row = solve_cell_ext(p)
        row["status"] = "completed"
    except (MemoryError, RuntimeError) as exc:
        row = {"params": p, "status": "failed", "error": f"{type(exc).__name__}: {exc}"}
    row["max_nodes"] = max_nodes
    return part, row


def key_of(p: dict) -> str:
    return json.dumps(p, sort_keys=True)


def done_keys(part: str) -> set[str]:
    return {
        key_of(r["params"])
        for r in a1.read_jsonl(OUT / f"{part}.jsonl")
        if r.get("status") in ("completed", "failed")
    }


def init(root: str) -> None:
    a1.load_solver(root)


def run_parts(parts: list[str], workers: int, deadline: float) -> None:
    cells = plan()
    tasks = []
    for part in parts:
        mn = P4_MAX_NODES if part == "p4" else a1.MAX_NODES
        done = done_keys(part)
        tasks += [(part, p, mn) for p in cells[part] if key_of(p) not in done]
    print(f"{len(tasks)} cells to run ({parts}), workers={workers}", flush=True)
    if not tasks:
        return
    with mp.Pool(workers, initializer=init, initargs=(a1.DEFAULT_SOLVER_ROOT,)) as pool:
        for part, row in pool.imap_unordered(work, tasks, chunksize=1):
            with (OUT / f"{part}.jsonl").open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(row) + "\n")
            p = row["params"]
            print(
                part, p["prior1"], p["alpha"], p["T"], row["status"], row.get("rel_gap_float"),
                f"{row.get('solve_seconds', 0):.1f}s", row.get("error", ""), flush=True,
            )  # fmt: skip
            if time.time() > deadline:
                print("deadline reached; stopping", flush=True)
                pool.terminate()
                break


def sanity() -> bool:
    p = cell("1/5", "1/5", 8)
    r = solve_cell_ext(p)
    ok = float(r["rel_gap_float"]) == 0.011782801718918295
    (OUT / "sanity.json").write_text(
        json.dumps(
            {"passed": ok, "rel_gap_float": r["rel_gap_float"], "J": r["J"], "C_star": r["C_star"]},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print("sanity", "PASS" if ok else "FAIL", r["rel_gap_float"], flush=True)
    return ok


# ---------------------------------------------------------------- P5 (descriptive)


def enumerate_policy(game, policy, deadline: float) -> dict:
    """Exact enumeration over histories under the model for a recovered policy."""
    model, T, d = game.model, game.config.horizon, game.config.delay
    agg: dict[tuple, F] = {}
    nodes = 0

    def visit(history, outcomes, posterior, weight, st):
        nonlocal nodes
        nodes += 1
        if time.time() > deadline:
            raise TimeoutError("P5 enumeration deadline")
        t = len(history) + 1
        if t > T:
            agg[st] = agg.get(st, F(0)) + weight
            return
        state1 = model.propagate(posterior, 1)
        positive = model.emission(state1)
        fq, fl, prom, roll, sq = st
        for (action, query), mass in zip(
            game.choices(history), policy(history, outcomes), strict=True
        ):
            if not mass:
                continue
            nprom = prom if prom is not None else (t if action else None)
            nroll = roll or (prom is not None and action == 0)
            if query:
                for y, prob in ((0, 1 - positive), (1, positive)):
                    lik1 = model.emission1 if y else 1 - model.emission1
                    nfq = fq if fq is not None else t
                    nfl = fl if fq is not None else (y if t + d <= T else "unreleased")
                    visit(
                        history + ((action, query),),
                        outcomes + ((t, y),),
                        state1 * lik1 / prob,
                        weight * mass * prob,
                        (nfq, nfl, nprom, nroll, sq if (sq is not None or fq is None) else t),
                    )
            else:
                visit(
                    history + ((action, query),), outcomes, state1, weight * mass,
                    (fq, fl, nprom, nroll, sq),
                )  # fmt: skip

    visit((), (), model.prior1, F(1), (None, None, None, False, None))
    total = sum(agg.values(), F(0))
    assert total == 1
    p_prom = sum((w for s, w in agg.items() if s[2] is not None), F(0))
    p_roll = sum((w for s, w in agg.items() if s[3]), F(0))
    p_noq = sum((w for s, w in agg.items() if s[0] is None), F(0))
    first_label: dict[str, dict] = {}
    for label in (0, 1, "unreleased"):
        sel = {s: w for s, w in agg.items() if s[0] is not None and s[1] == label}
        mass = sum(sel.values(), F(0))
        if not mass:
            continue
        qt: dict[int, F] = {}
        for s, w in sel.items():
            qt[s[0]] = qt.get(s[0], F(0)) + w
        first_label[str(label)] = {
            "prob": str(mass),
            "query_time_given_label": {str(k): str(v / mass) for k, v in sorted(qt.items())},
            "query_time_given_label_float": {
                str(k): float(v / mass) for k, v in sorted(qt.items())
            },
            "second_query_time_given_label_float": {
                str(k): float(v / mass)
                for k, v in sorted(
                    (
                        (k, sum((w for s, w in sel.items() if s[4] == k), F(0)))
                        for k in {s[4] for s in sel}
                    ),
                    key=lambda kv: (kv[0] is None, kv[0] or 0),
                )
            },
            "promote_prob_given_label": str(
                sum((w for s, w in sel.items() if s[2] is not None), F(0)) / mass
            ),
            "rollback_prob_given_label": str(sum((w for s, w in sel.items() if s[3]), F(0)) / mass),
        }
    qt_all: dict[int, F] = {}
    for s, w in agg.items():
        if s[0] is not None:
            qt_all[s[0]] = qt_all.get(s[0], F(0)) + w
    return {
        "nodes": nodes,
        "p_promote_raw": str(p_prom),
        "p_promote_raw_float": float(p_prom),
        "p_rollback_raw": str(p_roll),
        "p_rollback_raw_float": float(p_roll),
        "p_no_query_raw": str(p_noq),
        "first_query_time_dist_raw_float": {str(k): float(v) for k, v in sorted(qt_all.items())},
        "by_first_label": first_label,
    }


def run_p5(budget_seconds: float = 45 * 60) -> None:
    a1.load_solver(a1.DEFAULT_SOLVER_ROOT)
    deadline = time.time() + budget_seconds
    p = cell("1/5", "1/5", 8)
    cfg, model = a1.make(p)
    res: dict = {"params": p, "note": "distributions are under the HMM model, raw (pre-activation)"}
    try:
        jgame = a1._SOLVER["Joint"](cfg, model)
        jrep, jpol, _ = jgame.solve()
        best = None
        best_cost = None
        for cal in a1.calendars(p["T"], p["B"], p["d"]):
            g = a1._SOLVER["Calendar"](cfg, model, cal)
            rep, pol, _ = g.solve()
            key = (F(rep["calibrated_total_cost"]), len(cal), cal)
            if best_cost is None or key < best_cost:
                best_cost, best = key, (cal, g, rep, pol)
        cal, cgame, crep, cpol = best
        res["feasible"] = True
        for name, game, rep, pol in (
            ("joint", jgame, jrep, jpol),
            ("best_calendar", cgame, crep, cpol),
        ):
            out = enumerate_policy(game, pol, deadline)
            act = F(rep["activation_probability"])
            out["raw_null_risk"] = rep["raw_causal_null_risk"]
            out["activation_probability"] = rep["activation_probability"]
            out["p_promote_activated_float"] = float(act * F(out["p_promote_raw"]))
            out["p_rollback_activated_float"] = float(act * F(out["p_rollback_raw"]))
            if name == "best_calendar":
                out["calendar"] = list(cal)
            res[name] = out
        res["reason"] = (
            "policy(history, outcomes) exposes the recovered behavior strategy; "
            "exact enumeration over histories under the model."
        )
    except (TimeoutError, MemoryError, RuntimeError, KeyError) as exc:
        res["feasible"] = False
        res["reason"] = f"{type(exc).__name__}: {exc}"
    (OUT / "p5_mechanism.json").write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")
    print("P5 feasible:", res["feasible"], res.get("reason"), flush=True)


# ---------------------------------------------------------------- decision / summary


def completed(part: str) -> list[dict]:
    return [r for r in a1.read_jsonl(OUT / f"{part}.jsonl") if r.get("status") == "completed"]


def gap(r: dict) -> F:
    return F(r["rel_gap"])


def by_prior(rows: list[dict]) -> dict[str, list[tuple[F, F, dict]]]:
    out: dict[str, list[tuple[F, F, dict]]] = {}
    for r in rows:
        p = r["params"]
        out.setdefault(p["prior1"], []).append((F(p["alpha"]), gap(r), r))
    return {k: sorted(v, key=lambda x: x[0]) for k, v in out.items()}


def decide() -> dict:
    p1, p2 = completed("p1"), completed("p2")
    n_expected = len(plan()["p1"]) + len(plan()["p2"])
    groups = by_prior(p1 + p2)
    # Same (prior1, alpha) cell can appear in P1 and P2 only if priors/alphas overlap (none do).
    per_prior = {}
    h_risk_hits = []
    a_ok = True
    b_ok = True
    for prior, seq in groups.items():
        g1 = next((g for a, g, _ in seq if a == 1), None)
        gaps = [g for _, g, _ in seq]
        mono = all(gaps[i] <= gaps[i + 1] + TOL for i in range(len(gaps) - 1))
        first_pos = next((a for a, g, _ in seq if g > TOL), None)
        zero_prefix = [str(a) for a, g, _ in seq if abs(g) <= TOL]
        a_ok &= mono
        if g1 is None:
            per_prior[prior] = {"error": "no alpha=1 cell"}
            a_ok = b_ok = False
            continue
        for a, g, _ in seq:
            if a < 1 and g >= g1 + EFFECT - TOL:
                h_risk_hits.append({"prior1": prior, "alpha": str(a), "g": float(g)})
        exceeds = [str(a) for a, g, _ in seq if g > g1 + EFFECT + TOL]
        b_ok &= not exceeds
        per_prior[prior] = {
            "alphas": [str(a) for a, _, _ in seq],
            "g_float": [float(g) for g in gaps],
            "g_exact": [str(g) for g in gaps],
            "g_at_alpha_1": float(g1),
            "monotone_nondecreasing_in_alpha": mono,
            "alpha_star_first_positive": str(first_pos) if first_pos is not None else None,
            "alpha_star_float": float(first_pos) if first_pos is not None else None,
            "zero_gap_alphas": zero_prefix,
            "max_g_minus_g1": float(max(g - g1 for g in gaps)),
        }
    complete = len(p1 + p2) == n_expected and len(groups) == 3
    if not complete:
        decision = "INCOMPLETE"
    elif h_risk_hits:
        decision = "H-risk SUPPORTED"
    elif a_ok and b_ok:
        decision = "H-slack SUPPORTED"
    else:
        decision = "MIXED"
    return {
        "decision": decision,
        "cells_p1_p2_completed": len(p1 + p2),
        "cells_p1_p2_expected": n_expected,
        "H_risk_hits": h_risk_hits,
        "condition_a_monotone_all_priors": a_ok,
        "condition_b_g_le_g1_plus_0.005": b_ok,
        "per_prior": per_prior,
    }


def descriptive() -> dict:
    out: dict = {}
    dec = decide()
    pp = dec["per_prior"]
    stars = {k: v.get("alpha_star_float") for k, v in pp.items()}
    # Common grid: P2's alphas, which all lie in P1's grid.
    common = {}
    for prior, seq in by_prior(completed("p1") + completed("p2")).items():
        sub = [(a, g) for a, g, _ in seq if str(a) in P2_ALPHAS]
        common[prior] = next((float(a) for a, g in sub if g > TOL), None)
    order = ["1/10", "1/5", "3/10"]
    vals = [common.get(k) for k in order]
    if None not in vals:
        if vals[0] >= vals[1] >= vals[2] and vals[0] > vals[2]:
            direction = "alpha* nonincreasing in prior1 (strict overall)"
        elif vals[0] <= vals[1] <= vals[2] and vals[0] < vals[2]:
            direction = "alpha* nondecreasing in prior1 (strict overall)"
        elif vals[0] == vals[1] == vals[2]:
            direction = "alpha* constant in prior1"
        else:
            direction = "alpha* not monotone in prior1"
    else:
        direction = "undefined (a prior has no positive gap)"
    out["alpha_star_per_prior1_full_grid"] = stars
    out["alpha_star_per_prior1_common_P2_grid"] = common
    out["alpha_star_direction_common_grid"] = direction

    p3 = sorted(completed("p3"), key=lambda r: r["params"]["T"])
    g3 = [gap(r) for r in p3]
    inc = [g3[i + 1] - g3[i] for i in range(len(g3) - 1)]
    out["p3_unconstrained"] = {
        "T": [r["params"]["T"] for r in p3],
        "g_float": [float(g) for g in g3],
        "g_exact": [str(g) for g in g3],
        "increments_float": [float(x) for x in inc],
        "monotone_nondecreasing": all(x >= -TOL for x in inc),
        "label": (
            None
            if len(inc) < 2
            else "non-monotone (neither growing nor plateau)"
            if any(x < -TOL for x in inc)
            else "plateau-like (last increment <= 25% of largest)"
            if inc[-1] <= max(inc) / 4
            else "still growing"
        ),
        "label_note": "descriptive convention chosen at analysis time, not registered",
    }
    p4 = completed("p4")
    p4_failed = [r for r in a1.read_jsonl(OUT / "p4.jsonl") if r.get("status") == "failed"]
    a1b = {
        r["params"]["T"]: gap(r)
        for r in a1.read_jsonl(A1B_CELLS)
        if r.get("status") != "failed"
        and "rel_gap" in r
        and r["params"]["alpha"] == "1/5"
        and r["params"]["prior1"] == "1/5"
    }
    if p4:
        g12 = gap(p4[0])
        a1b[12] = g12
        incs = [a1b[T] - a1b[T - 1] for T in (10, 11, 12)]
        cont = g12 >= F(1, 10) or (all(x >= F(1, 200) for x in incs) and g12 >= F(1, 20))
        out["p4"] = {
            "status": "completed",
            "g12": float(g12),
            "g12_exact": str(g12),
            "best_calendar": p4[0]["best_calendar"],
            "solve_seconds": p4[0]["solve_seconds"],
            "joint_nodes": p4[0]["joint_nodes"],
            "last_three_increments": [float(x) for x in incs],
            "meets_A1b_CONTINUE_thresholds": bool(cont),
        }
    elif p4_failed:
        out["p4"] = {"status": "failed", "error": p4_failed[-1]["error"]}
    else:
        out["p4"] = {"status": "not_run"}

    mech = []
    for part in ("p1", "p2", "p3", "p4"):
        for r in completed(part):
            p = r["params"]
            mech.append(
                {
                    "part": part, "prior1": p["prior1"], "alpha": p["alpha"], "T": p["T"],
                    "g": r["rel_gap_float"],
                    "joint_raw_risk": r["joint"]["raw_risk_float"],
                    "joint_activation": r["joint"]["activation_float"],
                    "cal_raw_risk": r["best_calendar_report"]["raw_risk_float"],
                    "cal_activation": r["best_calendar_report"]["activation_float"],
                    "best_calendar": r["best_calendar"],
                }
            )  # fmt: skip
    out["risk_activation_table"] = mech
    return out


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize() -> dict:
    prov = json.loads((OUT / "provenance.json").read_text(encoding="utf-8"))
    p5_path = OUT / "p5_mechanism.json"
    p5 = json.loads(p5_path.read_text(encoding="utf-8")) if p5_path.exists() else None
    failed = {
        part: [r for r in a1.read_jsonl(OUT / f"{part}.jsonl") if r.get("status") == "failed"]
        for part in ("p1", "p2", "p3", "p4")
    }
    summary = {
        "protocol": f"A1c-alpha-mechanism (registered {PROTOCOL_COMMIT}, sha256 {PROTOCOL_SHA256})",
        "generated_utc": datetime.now(UTC).isoformat(),
        "provenance": prov,
        "cells_completed": {part: len(completed(part)) for part in ("p1", "p2", "p3", "p4")},
        "cells_failed": {k: len(v) for k, v in failed.items()},
        "failures": {k: [r["error"] for r in v] for k, v in failed.items() if v},
        "decision": decide(),
        "descriptive": descriptive(),
        "p5": None if p5 is None else {"feasible": p5.get("feasible"), "reason": p5.get("reason")},
        "j_le_cstar_violations": sum(
            not r["j_le_cstar_within_tol"]
            for part in ("p1", "p2", "p3", "p4")
            for r in completed(part)
        ),
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    names = sorted(
        x.name for x in OUT.iterdir() if x.is_file() and x.name not in ("SHA256SUMS.txt",)
    )
    (OUT / "SHA256SUMS.txt").write_text(
        "".join(f"{sha256_file(OUT / n)} *{n}\n" for n in names), encoding="utf-8"
    )
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", required=True, choices=["p123", "p4", "p5", "summary"])
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    assert sha256_file(ROOT / "docs/promising_directions/protocols/A1c-alpha-mechanism.md") == (
        PROTOCOL_SHA256
    ), "protocol file changed"
    prov = a1.verify_solver(Path(a1.DEFAULT_SOLVER_ROOT))
    prov["protocol_sha256"] = PROTOCOL_SHA256
    prov["protocol_commit"] = PROTOCOL_COMMIT
    (OUT / "provenance.json").write_text(json.dumps(prov, indent=2) + "\n", encoding="utf-8")
    start = time.time()
    deadline = start + CAP_SECONDS
    if args.part == "p123":
        a1.load_solver(a1.DEFAULT_SOLVER_ROOT)
        if not sanity():
            sys.exit(1)
        run_parts(["p1", "p2", "p3"], 2, deadline)
    elif args.part == "p4":
        run_parts(["p4"], 1, deadline)
    elif args.part == "p5":
        run_p5()
    else:
        print(json.dumps(summarize(), indent=2))
    print(f"elapsed {time.time() - start:.0f}s", flush=True)


if __name__ == "__main__":
    main()
