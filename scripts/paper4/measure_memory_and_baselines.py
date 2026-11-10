"""Peak memory, wall time and the never-promote baseline for FCG-fast versus the reference.

    uv run --no-sync python scripts/paper4/measure_memory_and_baselines.py

For cells C6, S1, S3 (definitions in ``run_fcg_scale.CELLS``) every measurement runs in its own
process tree:

    orchestrator -> worker (fresh process) -> child (``run_fcg_scale.py --method ref|fast``)

``getrusage(RUSAGE_CHILDREN).ru_maxrss`` is a high-water mark over every waited-for child, so a
worker spawns exactly ONE child and reads it after the wait.  A 1200 s cap applies to each child.
macOS reports ``ru_maxrss`` in bytes and Linux in kilobytes; both the raw value and bytes are
recorded.  The floor includes the worker's pre-exec footprint (a small Python process).

A third, separate child per cell (``breakdown``) re-runs FCG-fast with ``_repair`` wrapped to
capture the final repaired policy, then evaluates it with ``game.expected_metrics`` (cost
breakdown) and a forward recursion for the alternative-law first-promotion probability.  It is
kept apart so that its extra evaluation does not inflate the clean FCG-fast memory figure.

The never-promote cost ``C_0`` is the always-``(0, 0)`` policy under ``game.expected_metrics``
(sum of the first three components), compared to the exact optimum ``V*`` returned by the runs.
The script refuses to overwrite its output.
"""

from __future__ import annotations

import argparse
import json
import platform
import resource
import subprocess
import sys
import time
import traceback
from fractions import Fraction as F
from functools import cache
from pathlib import Path

sys.set_int_max_str_digits(0)  # exact dual bounds exceed the 4300-digit default

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

OUTPUT = ROOT / "docs/paper4/experiments/results/fcg_memory_baselines_v1.json"
CELL_NAMES = ("C6", "S1", "S3")
CAP_SECONDS = 1200
BIG_KEYS = ("L", "gap", "dual_value", "correction_max_times_count", "correction_residual_sum")


def _trim(result: dict) -> dict:
    """Replace huge exact rationals by (float, digit count); the exact U and V stay as strings."""
    out = dict(result)
    for key in BIG_KEYS:
        value = out.get(key)
        if isinstance(value, str) and len(value) > 200:
            out[key] = {"float": float(F(value)), "string_digits": len(value)}
    return out


# --------------------------------------------------------------------------------------
# Child: breakdown of the FCG-fast final policy
# --------------------------------------------------------------------------------------
def first_promotion_probability(game, policy) -> F:
    """Alternative-law probability that the policy ever promotes (forward recursion)."""
    model, horizon = game.model, game.config.horizon

    @cache
    def visit(history, outcomes, posterior):
        time_ = len(history) + 1
        if time_ > horizon:
            return F(0)
        state1 = model.propagate(posterior, 1)
        positive = model.emission(state1)
        total = F(0)
        for (action, query), mass in zip(
            game.choices(history), policy(history, outcomes), strict=True
        ):
            if not mass:
                continue
            if action:
                total += mass
                continue
            following = history + ((action, query),)
            if query:
                for label, probability in ((0, 1 - positive), (1, positive)):
                    likelihood = model.emission1 if label else 1 - model.emission1
                    total += (
                        mass
                        * probability
                        * visit(
                            following,
                            outcomes + ((time_, label),),
                            state1 * likelihood / probability,
                        )
                    )
            else:
                total += mass * visit(following, outcomes, state1)
        return total

    return visit((), (), model.prior1)


def breakdown_child(cell: str) -> dict:
    import shiftlab.paper4.frontier_cuts_fast as fast_module
    from run_fcg_scale import jsonable, make

    config, model = make(cell)
    captured: dict = {}
    original = fast_module._repair

    def spy(game, raw_policy, robust_risk, alpha):
        out = original(game, raw_policy, robust_risk, alpha)
        captured.update(game=game, repaired=out[0], activation=out[2])  # last call wins
        return out

    fast_module._repair = spy
    result = fast_module.frontier_cut_generation_fast(config, model)
    game, policy = captured["game"], captured["repaired"]
    started = time.perf_counter()
    decision, query, switch, queries, switches = game.expected_metrics(policy)
    promotion = first_promotion_probability(game, policy)
    if decision + query + switch != result["U"]:
        raise AssertionError("breakdown does not sum to U")
    return jsonable(
        {
            "U": result["U"],
            "activation": captured["activation"],
            "decision_cost": decision,
            "query_cost": query,
            "switch_cost": switch,
            "expected_queries": queries,
            "expected_switches": switches,
            "expected_promotions_first": promotion,
            "expected_promotions_note": (
                "alternative-law probability of the first promotion (at most one per run); "
                "expected_switches also counts any switch back after promotion"
            ),
            "decision_cost_float": float(decision),
            "query_cost_float": float(query),
            "switch_cost_float": float(switch),
            "expected_queries_float": float(queries),
            "expected_switches_float": float(switches),
            "expected_promotions_first_float": float(promotion),
            "breakdown_eval_seconds": time.perf_counter() - started,
        }
    )


# --------------------------------------------------------------------------------------
# Worker: one child, one rusage read
# --------------------------------------------------------------------------------------
def worker(cell: str, method: str) -> dict:
    if method in ("ref", "fast"):
        command = [
            sys.executable,
            str(ROOT / "scripts/paper4/run_fcg_scale.py"),
            "--cell",
            cell,
            "--method",
            method,
        ]
    elif method == "breakdown":
        command = [sys.executable, str(Path(__file__).resolve()), "--breakdown-child", cell]
    else:
        raise ValueError(method)
    started = time.perf_counter()
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=CAP_SECONDS)
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate()
        timed_out = True
    wall = time.perf_counter() - started
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    raw = usage.ru_maxrss
    in_bytes = raw if sys.platform == "darwin" else raw * 1024
    payload = None
    lines = [line for line in stdout.splitlines() if line.strip()]
    if lines:
        try:
            payload = json.loads(lines[-1])
        except json.JSONDecodeError:
            payload = None
    return {
        "cell": cell,
        "method": method,
        "returncode": process.returncode,
        "timed_out": timed_out,
        "cap_seconds": CAP_SECONDS,
        "wall_seconds_measured_by_worker": wall,
        "ru_maxrss_raw": raw,
        "ru_maxrss_units": "bytes (darwin)" if sys.platform == "darwin" else "kilobytes (linux)",
        "peak_rss_bytes": in_bytes,
        "peak_rss_mib": in_bytes / 2**20,
        "child_user_seconds": usage.ru_utime,
        "child_system_seconds": usage.ru_stime,
        "child_result": payload,
        "stderr_tail": stderr[-2000:] if stderr else "",
    }


# --------------------------------------------------------------------------------------
# Orchestrator
# --------------------------------------------------------------------------------------
def never_promote_cost(cell: str) -> dict:
    from run_fcg_scale import make
    from shiftlab.dive.causal_switching_game import CausalSwitchingGame

    config, model = make(cell)
    game = CausalSwitchingGame(config, model)
    metrics = game.expected_metrics(
        lambda history, outcomes: tuple(F(choice == (0, 0)) for choice in game.choices(history))
    )
    return {
        "C0": str(sum(metrics[:3])),
        "C0_float": float(sum(metrics[:3])),
        "decision_cost": str(metrics[0]),
        "query_cost": str(metrics[1]),
        "switch_cost": str(metrics[2]),
        "expected_queries": str(metrics[3]),
        "expected_switches": str(metrics[4]),
    }


def git_head() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout.strip()
    except Exception as exc:  # recorded, not fatal
        return f"unavailable: {exc!r}"


def orchestrate() -> None:
    if OUTPUT.exists():
        sys.exit(f"refusing to overwrite {OUTPUT}")
    from run_fcg_scale import CELLS, MAX_NODES

    runs, summary = [], {}
    for cell in CELL_NAMES:
        for method in ("ref", "fast", "breakdown"):
            print(f"[{time.strftime('%H:%M:%S')}] {cell} {method}", flush=True)
            completed = subprocess.run(
                [sys.executable, str(Path(__file__).resolve()), "--worker", cell, method],
                capture_output=True,
                text=True,
            )
            try:
                record = json.loads(completed.stdout.strip().splitlines()[-1])
            except Exception:
                record = {
                    "cell": cell,
                    "method": method,
                    "status": "worker_failed",
                    "worker_returncode": completed.returncode,
                    "worker_stdout_tail": completed.stdout[-2000:],
                    "worker_stderr_tail": completed.stderr[-2000:],
                }
            if record.get("child_result"):
                record["child_result"] = _trim(record["child_result"])
            runs.append(record)
            print(
                f"    rc={record.get('returncode')} peak_rss_mib={record.get('peak_rss_mib')} "
                f"wall={record.get('wall_seconds_measured_by_worker')}",
                flush=True,
            )

    for cell in CELL_NAMES:
        by_method = {r["method"]: r for r in runs if r["cell"] == cell}
        baseline = never_promote_cost(cell)
        ref = (by_method.get("ref") or {}).get("child_result") or {}
        fast = (by_method.get("fast") or {}).get("child_result") or {}
        v_ref = F(ref["V_ref"]) if ref.get("status") == "ok" else None
        v_fast = F(fast["U"]) if fast.get("status") == "ok" else None
        c0 = F(baseline["C0"])
        v_star = v_fast if v_fast is not None else v_ref
        summary[cell] = {
            "never_promote": baseline,
            "V_ref": str(v_ref) if v_ref is not None else None,
            "U_fast": str(v_fast) if v_fast is not None else None,
            "ref_equals_fast_exactly": (v_ref == v_fast) if None not in (v_ref, v_fast) else None,
            "C0_minus_Vstar": str(c0 - v_star) if v_star is not None else None,
            "C0_minus_Vstar_float": float(c0 - v_star) if v_star is not None else None,
            "relative_saving_over_never_promote": (
                float((c0 - v_star) / c0) if v_star is not None else None
            ),
            "never_promote_is_optimal": (c0 == v_star) if v_star is not None else None,
            "peak_rss_mib": {
                m: (by_method[m].get("peak_rss_mib") if m in by_method else None)
                for m in ("ref", "fast", "breakdown")
            },
            "end_to_end_seconds": {
                "ref": ref.get("end_to_end_seconds"),
                "fast": fast.get("end_to_end_seconds"),
            },
            "wall_seconds_measured_by_worker": {
                m: (by_method[m].get("wall_seconds_measured_by_worker") if m in by_method else None)
                for m in ("ref", "fast")
            },
        }
        reference_rss = summary[cell]["peak_rss_mib"]["ref"]
        fast_rss = summary[cell]["peak_rss_mib"]["fast"]
        summary[cell]["rss_ratio_ref_over_fast"] = (
            reference_rss / fast_rss if reference_rss and fast_rss else None
        )

    payload = {
        "schema": "fcg_memory_baselines_v1",
        "created_unix": time.time(),
        "git_head": git_head(),
        "platform": platform.platform(),
        "python": sys.version,
        "command": "uv run --no-sync python scripts/paper4/measure_memory_and_baselines.py",
        "cap_seconds_per_child": CAP_SECONDS,
        "cells": {
            c: {
                k: (
                    str(v)
                    if isinstance(v, F)
                    else [str(x) for x in v]
                    if isinstance(v, tuple)
                    else v
                )
                for k, v in CELLS[c].items()
            }
            for c in CELL_NAMES
        },
        "max_nodes": MAX_NODES,
        "alpha": "1/10",
        "query_cost": "1/100",
        "switch_cost": "1/10",
        "measurement_notes": [
            "one fresh worker process per (cell, method); the worker spawns exactly one child",
            "ru_maxrss from getrusage(RUSAGE_CHILDREN) read by the worker after the single child",
            "single repetition per measurement; timing noise of ~20% was seen on the reference",
            "'breakdown' re-runs FCG-fast with _repair wrapped; its RSS is NOT the clean FCG-fast figure",
        ],
        "summary": summary,
        "runs": runs,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("x") as handle:  # 'x' also refuses to overwrite
        json.dump(payload, handle, indent=2, sort_keys=True)
    print(f"wrote {OUTPUT}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", nargs=2, metavar=("CELL", "METHOD"))
    parser.add_argument("--breakdown-child", metavar="CELL")
    args = parser.parse_args()
    if args.breakdown_child:
        try:
            result = {"status": "ok", **breakdown_child(args.breakdown_child)}
        except Exception as exc:
            result = {"status": "failed", "error": repr(exc), "trace": traceback.format_exc()}
        result.update(cell=args.breakdown_child, method="breakdown")
        print(json.dumps(result), flush=True)
    elif args.worker:
        print(json.dumps(worker(*args.worker)), flush=True)
    else:
        orchestrate()


if __name__ == "__main__":
    main()
