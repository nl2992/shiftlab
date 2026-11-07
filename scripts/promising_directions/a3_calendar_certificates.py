"""A3: check the support (Prop 6) and chain (Thm 7) calendar-optimality certificates.

Executes protocols/A3-calendar-optimality-certificates.md. Theory-verification probe; no method
claim.

Action encoding (solver 2bd2e8e, causal_switching_game.py): a choice is (action, query). action 0
keeps the incumbent, action 1 deploys the challenger; `old` is the previous action, and a switch
is `action != old`. A *promotion* is the first step t at which action == 1. Later actions may
roll back (action 0). The joint planner (FirstPromotionDecomposedGame) is exact before the first
promotion and plays a deterministic optimal continuation afterwards, which may still query.
Labels queried at step s are released to the learner at step s + d (information() keeps
(s, y) with s + d <= t). With d = 1 every label from a strictly earlier step is released at
decision time; only the label queried at the current step is outstanding.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing as mp
import platform
import sys
import time
from datetime import UTC, datetime
from fractions import Fraction as F
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import a1_exact_separation as a1
import a2_binding_alpha_screen as a2

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/promising_directions/results/a3"
PROTOCOL = ROOT / "docs/promising_directions/protocols/A3-calendar-optimality-certificates.md"
PROTOCOL_SHA256 = "5d3fdd0bccb5bf83c906d191de2bf3b6cdcce24d61a6e299991f4d1127f98a12"
PROTOCOL_COMMIT = "e511a48"
A2_SCREEN = ROOT / "docs/promising_directions/results/a2/screen.jsonl"
TIGHT = ["1/20", "1/10"]
EPS = 1e-6  # sensitivity run: ignore choice masses at or below this (LP rounding noise)
GAP_TOL = F(1, 10**9)  # g > 0 means rel gap above this; exact values are also recorded
CAP_SECONDS = 3 * 3600
CELL_SECONDS = 1200
NO_C_STAR = ("prop6", "thm7_pure")  # classes that certify C* = J


# ------------------------------------------------------------------ enumeration


def enumerate_flags(game, policy, deadline: float, eps: float = 0.0) -> dict:
    """Exact enumeration of histories reachable with positive mass (every label outcome).

    With eps > 0, choices whose conditional mass is <= eps are treated as absent (sensitivity
    check against LP rounding noise); eps == 0 is the registered exact support.
    """
    model, T, d, B = game.model, game.config.horizon, game.config.delay, game.config.budget
    queries: set[int] = set()
    promo: dict[tuple[int, int, int], F] = {}
    q_after_promo: dict[int, F] = {}
    chain_nondet: list[dict] = []
    chain_paths: set[tuple[int, ...]] = set()
    chain_query_times: set[int] = set()
    nodes = 0
    total = F(0)
    cache: dict = {}

    def masses_at(history, outcomes):
        key = game.information(history, outcomes)
        if key not in cache:
            cache[key] = policy(history, outcomes)
        return cache[key]

    def visit(history, outcomes, posterior, weight, promoted, qtimes):
        nonlocal nodes, total
        nodes += 1
        if time.time() > deadline:
            raise TimeoutError("A3 enumeration deadline")
        t = len(history) + 1
        if t > T:
            total += weight
            return
        released = [y for s, y in outcomes if s + d <= t]
        all1 = all(released)
        state1 = model.propagate(posterior, 1)
        positive = model.emission(state1)
        pairs = [
            (c, m)
            for c, m in zip(game.choices(history), masses_at(history, outcomes), strict=True)
            if m and m > eps
        ]
        kept = sum((m for _, m in pairs), F(0))
        qmass = sum((m for c, m in pairs if c[1]), F(0)) / kept
        if all1 and qmass not in (0, 1):
            chain_nondet.append({"t": t, "query_mass": float(qmass)})
        if all1 and qmass > 0:
            chain_query_times.add(t)
        for (action, query), m in pairs:
            w = weight * m / kept
            if action and not promoted:
                k = (t, len(released), len(released) - sum(released))
                promo[k] = promo.get(k, F(0)) + w
            if query:
                queries.add(t)
                if promoted:
                    q_after_promo[t] = q_after_promo.get(t, F(0)) + w
            nprom = promoted or bool(action)
            nq = (*qtimes, t) if (query and all1) else qtimes
            if query:
                for y, prob in ((0, 1 - positive), (1, positive)):
                    lik1 = model.emission1 if y else 1 - model.emission1
                    visit(
                        (*history, (action, query)),
                        (*outcomes, (t, y)),
                        state1 * lik1 / prob,
                        w * prob,
                        nprom,
                        nq,
                    )
            else:
                visit((*history, (action, query)), outcomes, state1, w, nprom, nq)

    visit((), (), model.prior1, F(1), False, ())
    assert total == 1, total

    # Chain leaves are recorded by a second light pass over chain nodes only.

    def chain_pass(history, outcomes, posterior, qtimes):
        nonlocal nodes
        nodes += 1
        if time.time() > deadline:
            raise TimeoutError("A3 enumeration deadline")
        t = len(history) + 1
        if t > T:
            chain_paths.add(qtimes)
            return
        released = [y for s, y in outcomes if s + d <= t]
        if not all(released):
            return
        state1 = model.propagate(posterior, 1)
        positive = model.emission(state1)
        for (action, query), m in zip(
            game.choices(history), masses_at(history, outcomes), strict=True
        ):
            if not m or m <= eps:
                continue
            nq = (*qtimes, t) if query else qtimes
            if query:
                for y, prob in ((0, 1 - positive), (1, positive)):
                    lik1 = model.emission1 if y else 1 - model.emission1
                    chain_pass(
                        (*history, (action, query)),
                        (*outcomes, (t, y)),
                        state1 * lik1 / prob,
                        nq,
                    )
            else:
                chain_pass((*history, (action, query)), outcomes, state1, nq)

    chain_pass((), (), model.prior1, ())

    p_viol = {k: v for k, v in promo.items() if not (k[1] == B and k[2] == 0)}
    p_after_zero = {k: v for k, v in promo.items() if k[2] > 0}
    return {
        "query_support": sorted(queries),
        "support_size": len(queries),
        "promotion_mass_by_t_released_zeros": {
            f"{k[0]},{k[1]},{k[2]}": float(v) for k, v in sorted(promo.items())
        },
        "promotion_times": sorted({k[0] for k in promo}),
        "p_promote": float(sum(promo.values(), F(0))),
        "P_holds": not p_viol,
        "P_violations": {f"{k[0]},{k[1]},{k[2]}": float(v) for k, v in sorted(p_viol.items())},
        "Pprime_no_promo_after_zero": not p_after_zero,
        "Pprime_no_query_after_promo": not q_after_promo,
        "queries_after_promo_times": sorted(q_after_promo),
        "Pprime_holds": not p_after_zero and not q_after_promo,
        "chain_query_times": sorted(chain_query_times),
        "chain_paths_query_times": sorted(list(x) for x in chain_paths),
        "chain_nondeterministic_nodes": chain_nondet,
        "chain_deterministic": not chain_nondet and len(chain_paths) <= 1,
        "enum_nodes": nodes,
        "eps": eps,
    }


def classify(flags: dict, budget: int) -> dict:
    """Mechanical certificate classes from enumeration flags."""
    prop6 = flags["support_size"] <= budget
    p = flags["P_holds"]
    pure = p and flags["chain_deterministic"]
    if prop6:
        cls = "prop6"
    elif pure:
        cls = "thm7_pure"
    elif p:
        cls = "thm7_mix"
    else:
        cls = "uncertified"
    return {
        "cert_prop6": prop6,
        "cert_thm7_pure": pure,
        "cert_thm7_mix": p,
        "cert_class": cls,
        "certifies_C_star": prop6 or pure,
    }


# ------------------------------------------------------------------ per-cell work


def a2_j_lookup() -> dict[str, str]:
    out = {}
    for r in a1.read_jsonl(A2_SCREEN):
        if r.get("status") == "completed":
            out[a2.screen_key(r)] = r["J"]
    return out


def key_of(p: dict) -> str:
    return json.dumps(p, sort_keys=True)


def gap_fields(res: dict) -> dict:
    g = F(res["rel_gap"])
    return {
        "J": res["J"],
        "C_star": res["C_star"],
        "abs_gap": res["abs_gap"],
        "rel_gap": res["rel_gap"],
        "rel_gap_float": res["rel_gap_float"],
        "g_positive": g > GAP_TOL,
        "best_calendar": res["best_calendar"],
        "n_calendars": res["n_calendars"],
        "solve_cell_seconds": res["solve_seconds"],
    }


def tight_cell(p: dict, deadline: float) -> dict:
    t0 = time.perf_counter()
    cfg, model = a1.make(p)
    game = a1._SOLVER["Joint"](cfg, model)
    jrep, pol, _ = game.solve()
    j = F(jrep["calibrated_total_cost"])
    cell_deadline = min(deadline, time.time() + CELL_SECONDS)
    flags = enumerate_flags(game, pol, cell_deadline, 0.0)
    flags_eps = enumerate_flags(game, pol, cell_deadline, EPS)
    cls = classify(flags, p["B"])
    cls_eps = classify(flags_eps, p["B"])
    row = {
        "params": p,
        "kind": "tight",
        "J": str(j),
        "joint_nodes": jrep["nodes"],
        "activation": jrep["activation_probability"],
        "raw_risk": jrep["raw_causal_null_risk"],
        "flags": flags,
        "flags_eps": flags_eps,
        **cls,
        "cert_class_eps": cls_eps["cert_class"],
        "class_eps_differs": cls_eps["cert_class"] != cls["cert_class"],
    }
    a2j = A2_J.get(a2.screen_key({"params": p})) if p["B"] == 3 else None
    row["a2_J"] = a2j
    row["j_matches_a2"] = None if a2j is None else a2j == str(j)
    if cls["cert_prop6"]:
        q = tuple(flags["query_support"])
        crep = a1._SOLVER["Calendar"](cfg, model, q).solve()[0]
        cq = F(crep["calibrated_total_cost"])
        row["prop6_calendar"] = list(q)
        row["prop6_calendar_cost"] = str(cq)
        row["prop6_calendar_minus_J"] = str(cq - j)
        row["prop6_calendar_minus_J_float"] = float(cq - j)
    if not cls["certifies_C_star"]:
        res = a1.solve_cell(p)
        row["computed"] = gap_fields(res)
        row["J_matches_solve_cell"] = res["J"] == str(j)
    row["seconds"] = time.perf_counter() - t0
    return row


def reference_cell(p: dict) -> dict:
    t0 = time.perf_counter()
    res = a1.solve_cell(p)
    return {
        "params": p,
        "kind": "reference",
        "computed": gap_fields(res),
        "seconds": time.perf_counter() - t0,
    }


def work(task: tuple[dict, str, float]) -> dict:
    p, kind, deadline = task
    if time.time() > deadline:
        return {"params": p, "status": "not_run_time_cap"}
    try:
        row = tight_cell(p, deadline) if kind == "tight" else reference_cell(p)
        row["status"] = "completed"
    except (MemoryError, RuntimeError, TimeoutError) as exc:
        row = {
            "params": p,
            "kind": kind,
            "status": "failed",
            "error": f"{type(exc).__name__}: {exc}",
        }
    return row


A2_J: dict[str, str] = {}


def init_worker(root: str) -> None:
    a1.load_solver(root)
    A2_J.update(a2_j_lookup())


# ------------------------------------------------------------------ orchestration


def cells_for(part: str) -> list[tuple[dict, str]]:
    if part == "part1":
        return [({**f, "B": 3, "alpha": a}, "tight") for f in a2.families() for a in TIGHT]
    tight = [({**f, "B": 4, "alpha": a}, "tight") for f in a2.families() for a in TIGHT]
    ref = [({**f, "B": 4, "alpha": "1"}, "reference") for f in a2.families()]
    return tight + ref


def run_part(part: str, workers: int, deadline: float) -> None:
    path = OUT / f"{part}.jsonl"
    done = {key_of(r["params"]) for r in a1.read_jsonl(path) if r.get("status") != "not_run"}
    allc = cells_for(part)
    todo = [(p, k, deadline) for p, k in allc if key_of(p) not in done]
    print(f"{part}: {len(allc) - len(todo)} done, {len(todo)} to run", flush=True)
    if not todo:
        return
    with (
        mp.Pool(workers, initializer=init_worker, initargs=(a1.DEFAULT_SOLVER_ROOT,)) as pool,
        path.open("a", encoding="utf-8") as fh,
    ):
        for row in pool.imap_unordered(work, todo, chunksize=1):
            if row["status"] == "not_run_time_cap":
                continue
            fh.write(json.dumps(row) + "\n")
            fh.flush()
            p = row["params"]
            print(
                part, p["B"], p["alpha"], row["status"], row.get("cert_class", row.get("kind")),
                f"{row.get('seconds', 0):.0f}s", row.get("error", ""), flush=True,
            )  # fmt: skip
            if time.time() > deadline:
                pool.terminate()
                break


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_provenance() -> dict:
    assert sha256_file(PROTOCOL) == PROTOCOL_SHA256, "protocol file changed"
    path = OUT / "provenance.json"
    prov = json.loads(path.read_text("utf-8")) if path.exists() else {}
    if "start_epoch" not in prov:
        import scipy

        prov = {
            **a1.verify_solver(Path(a1.DEFAULT_SOLVER_ROOT)),
            "protocol_sha256": PROTOCOL_SHA256,
            "protocol_commit": PROTOCOL_COMMIT,
            "script_sha256": sha256_file(Path(__file__)),
            "python": platform.python_version(),
            "scipy": scipy.__version__,
            "start_epoch": time.time(),
            "start_utc": datetime.now(UTC).isoformat(),
            "cap_seconds": CAP_SECONDS,
            "max_nodes": a1.MAX_NODES,
            "workers": 2,
            "eps_sensitivity": EPS,
            "gap_tolerance": str(GAP_TOL),
        }
    else:
        prov["script_sha256_at_resume"] = sha256_file(Path(__file__))
    path.write_text(json.dumps(prov, indent=2) + "\n", encoding="utf-8")
    return prov


def sanity() -> bool:
    """One A2 B=3 cell: the joint J must equal A2's J exactly."""
    a1.load_solver(a1.DEFAULT_SOLVER_ROOT)
    a2j = a2_j_lookup()
    p = {**a2.families()[0], "B": 3, "alpha": "1/20"}
    cfg, model = a1.make(p)
    j = str(F(a1._SOLVER["Joint"](cfg, model).solve()[0]["calibrated_total_cost"]))
    ok = j == a2j[a2.screen_key({"params": p})]
    (OUT / "sanity.json").write_text(
        json.dumps({"passed": ok, "params": p, "J": j, "a2_J": a2j[a2.screen_key({"params": p})]},
                   indent=2) + "\n",
        encoding="utf-8",
    )  # fmt: skip
    print("sanity", "PASS" if ok else "FAIL", j, flush=True)
    return ok


# ------------------------------------------------------------------ summary


def done_rows(part: str) -> list[dict]:
    return a1.read_jsonl(OUT / f"{part}.jsonl")


def effective_g_positive(r: dict) -> bool | None:
    """True/False if g is determined for a completed tight cell, else None."""
    if r.get("certifies_C_star"):
        return False
    if "computed" in r:
        return r["computed"]["g_positive"]
    return None


def summarize_part(part: str, expected: int) -> dict:
    rows = done_rows(part)
    tight = [r for r in rows if r.get("kind") == "tight" and r["status"] == "completed"]
    classes: dict[str, int] = {}
    for r in tight:
        classes[r["cert_class"]] = classes.get(r["cert_class"], 0) + 1
    multi = {
        "prop6": sum(r["cert_prop6"] for r in tight),
        "thm7_pure": sum(r["cert_thm7_pure"] for r in tight),
        "thm7_mix": sum(r["cert_thm7_mix"] for r in tight),
    }
    by_alpha = {}
    for a in TIGHT:
        sub = [r for r in tight if r["params"]["alpha"] == a]
        by_alpha[a] = {
            "completed": len(sub),
            **{c: sum(r["cert_class"] == c for r in sub) for c in
               ("prop6", "thm7_pure", "thm7_mix", "uncertified")},
        }  # fmt: skip
    unc = [
        {
            "params": r["params"],
            "support": r["flags"]["query_support"],
            "promotion_times": r["flags"]["promotion_times"],
            "promotion_mass_by_t_released_zeros": r["flags"]["promotion_mass_by_t_released_zeros"],
            "P_violations": r["flags"]["P_violations"],
            "Pprime_holds": r["flags"]["Pprime_holds"],
            "chain_query_times": r["flags"]["chain_query_times"],
            "chain_deterministic": r["flags"]["chain_deterministic"],
            "activation": r["activation"],
            "g": r.get("computed", {}).get("rel_gap_float"),
            "g_exact": r.get("computed", {}).get("rel_gap"),
            "best_calendar": r.get("computed", {}).get("best_calendar"),
        }
        for r in tight
        if r["cert_class"] == "uncertified"
    ]
    not_cert_c = [r for r in tight if not r["certifies_C_star"]]
    gpos = [r for r in tight if effective_g_positive(r) is True]
    gunk = [r for r in tight if effective_g_positive(r) is None]
    failed = [r for r in rows if r["status"] == "failed"]
    j_checked = [r for r in tight if r.get("j_matches_a2") is not None]
    p6 = [r for r in tight if "prop6_calendar_minus_J_float" in r]
    return {
        "expected_tight_cells": 108,
        "expected_total_rows": expected,
        "tight_completed": len(tight),
        "failed": [{"params": r["params"], "error": r["error"]} for r in failed],
        "class_counts_primary": classes,
        "class_counts_overlapping_flags": multi,
        "by_alpha": by_alpha,
        "n_class_differs_under_eps": sum(r["class_eps_differs"] for r in tight),
        "n_P_prime_holds": sum(r["flags"]["Pprime_holds"] for r in tight),
        "uncertified_cells": unc,
        "n_cells_needing_computed_g": len(not_cert_c),
        "n_tight_cells_with_g_positive": len(gpos),
        "tight_cells_g_positive": [
            {
                "params": r["params"],
                "g": r["computed"]["rel_gap_float"],
                "g_exact": r["computed"]["rel_gap"],
                "best_calendar": r["computed"]["best_calendar"],
                "cert_class": r["cert_class"],
                "support": r["flags"]["query_support"],
            }
            for r in gpos
        ],
        "n_tight_cells_g_undetermined": len(gunk),
        "a2_J_exact_matches": [sum(r["j_matches_a2"] for r in j_checked), len(j_checked)],
        "prop6_calendar_minus_J_max_abs": max(
            (abs(r["prop6_calendar_minus_J_float"]) for r in p6), default=None
        ),
        "prop6_calendar_cost_exceeds_J_by_gt_1e-9": sum(
            r["prop6_calendar_minus_J_float"] > 1e-9 for r in p6
        ),
        "J_matches_solve_cell": [
            sum(r["J_matches_solve_cell"] for r in tight if "J_matches_solve_cell" in r),
            sum("J_matches_solve_cell" in r for r in tight),
        ],
        "max_support_size": max((r["flags"]["support_size"] for r in tight), default=None),
        "support_size_hist": {
            str(s): sum(r["flags"]["support_size"] == s for r in tight)
            for s in sorted({r["flags"]["support_size"] for r in tight})
        },
        "chain_query_times_hist": {
            json.dumps(t): sum(r["flags"]["chain_query_times"] == t for r in tight)
            for t in sorted({tuple(r["flags"]["chain_query_times"]) for r in tight})
        },
    }


def decide_part1(s: dict) -> str:
    if s["tight_completed"] == 0:
        return "NO_DATA"
    return "THEOREM EXPLAINS" if not s["uncertified_cells"] else "PARTIAL"


def decide_part2(s: dict) -> str:
    if s["tight_completed"] == 0:
        return "NO_DATA"
    if s["n_tight_cells_with_g_positive"]:
        return "GAP AT B=4"
    if s["n_tight_cells_g_undetermined"]:
        return "INCOMPLETE (g undetermined for some completed tight cells)"
    return "CALENDAR-OPTIMAL AT B=4"


def summarize() -> dict:
    s1 = summarize_part("part1", 108)
    s2 = summarize_part("part2", 162)
    ref = [
        r for r in done_rows("part2") if r.get("kind") == "reference" and r["status"] == "completed"
    ]
    refg = [(r["computed"]["rel_gap_float"], r) for r in ref]
    mx = max(refg, key=lambda x: x[0], default=None)
    prov = json.loads((OUT / "provenance.json").read_text("utf-8"))
    summary = {
        "protocol": f"A3 (registered {PROTOCOL_COMMIT}, sha256 {PROTOCOL_SHA256})",
        "generated_utc": datetime.now(UTC).isoformat(),
        "provenance": prov,
        "part1_B3": {"decision": decide_part1(s1), **s1},
        "part2_B4": {
            "decision": decide_part2(s2),
            **s2,
            "alpha1_reference": {
                "completed": len(ref),
                "expected": 54,
                "n_g_positive": sum(r["computed"]["g_positive"] for r in ref),
                "max_g": None if mx is None else mx[0],
                "max_g_exact": None if mx is None else mx[1]["computed"]["rel_gap"],
                "max_g_params": None if mx is None else mx[1]["params"],
            },
        },
        "wall_clock_seconds": time.time() - prov["start_epoch"],
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    names = sorted(x.name for x in OUT.iterdir() if x.is_file() and x.name != "SHA256SUMS.txt")
    (OUT / "SHA256SUMS.txt").write_text(
        "".join(f"{sha256_file(OUT / n)} *{n}\n" for n in names), encoding="utf-8"
    )
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", required=True, choices=["sanity", "part1", "part2", "all", "summary"])
    ap.add_argument("--workers", type=int, default=2)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    prov = write_provenance()
    if args.part == "sanity":
        sys.exit(0 if sanity() else 1)
    if args.part == "summary":
        print(json.dumps(summarize(), indent=2))
        return
    deadline = prov["start_epoch"] + CAP_SECONDS
    workers = min(args.workers, 2)
    if not sanity():
        sys.exit(1)
    for part in ("part1", "part2") if args.part == "all" else (args.part,):
        run_part(part, workers, deadline)


if __name__ == "__main__":
    main()
