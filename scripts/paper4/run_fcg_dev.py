"""Run FCG development protocol v1 (cells C1-C6) against the decomposed-game reference."""

from __future__ import annotations

import hashlib
import json
import sys
import time
import traceback
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

PROTOCOL = ROOT / "docs/paper4/experiments/protocols/FCG_DEV_PROTOCOL_V1.md"
MODULE = ROOT / "src/shiftlab/paper4/frontier_cuts.py"
OUTPUT = ROOT / "docs/paper4/experiments/results/fcg_dev_v1.json"
REFERENCE_SECONDS_LIMIT = 600.0
MAX_NODES = 200_000  # GameConfig default, as in the other research_risk_approx runners

CELLS = [
    # id, T, B, d, transition, emissions, role, anti-persistent?, anchor cost (if matched)
    ("C1", 5, 2, 1, F(1, 4), (F(1, 20), F(19, 20)), "persistent control", False, None),
    ("C2", 5, 2, 1, F(9, 10), (F(1, 10), F(9, 10)), "anti-persistent", True, None),
    ("C3", 6, 3, 1, F(3, 4), (F(1, 20), F(19, 20)), "anti-persistent", True, None),
    ("C4", 6, 3, 1, F(1, 4), (F(1, 20), F(19, 20)), "control", False, "461083/160000"),
    ("C5", 8, 3, 1, F(1, 4), (F(1, 20), F(19, 20)), "control", False, "24735833/6400000"),
    ("C6", 8, 3, 1, F(3, 4), (F(1, 20), F(19, 20)), "anti-persistent scale", True, None),
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def jsonable(value):
    if isinstance(value, F):
        return str(value)
    if isinstance(value, dict):
        return {k: jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    return value


def main() -> None:
    from shiftlab.dive.causal_switching_game import GameConfig
    from shiftlab.dive.delayed_regime_information import RegimeModel
    from shiftlab.dive.first_promotion_decomposition import FirstPromotionDecomposedGame
    from shiftlab.paper4.frontier_cuts import frontier_cut_generation

    if OUTPUT.exists():
        raise FileExistsError(f"Refusing to overwrite {OUTPUT}")
    cells_out = []
    for cid, horizon, budget, delay, trans, emis, role, anti, anchor in CELLS:
        config = GameConfig(
            horizon=horizon,
            budget=budget,
            delay=delay,
            alpha=F(1, 10),
            query_cost=F(1, 100),
            switch_cost=F(1, 10),
            max_nodes=MAX_NODES,
        )
        model = RegimeModel(
            transition01=trans,
            transition10=trans,
            emission0=emis[0],
            emission1=emis[1],
            prior1=F(1, 2),
        )
        cell = {
            "id": cid,
            "role": role,
            "anti_persistent": anti,
            "config": {
                "horizon": horizon,
                "budget": budget,
                "delay": delay,
                "alpha": str(config.alpha),
                "query_cost": str(config.query_cost),
                "switch_cost": str(config.switch_cost),
                "max_nodes": MAX_NODES,
                "transition": str(trans),
                "emissions": [str(e) for e in emis],
                "prior1": "1/2",
            },
            "anchor_cost_in_protocol": anchor,
        }
        print(f"[{cid}] FCG ...", flush=True)
        try:
            out = frontier_cut_generation(config, model)
            out.pop("policy")
            out.pop("iid_row")
            cell["fcg"] = jsonable(out)
            cell["fcg"]["status"] = "ok"
        except Exception as exc:  # recorded, never skipped
            cell["fcg"] = {"status": "failed", "error": repr(exc), "trace": traceback.format_exc()}
        print(f"[{cid}] reference ...", flush=True)
        started = time.perf_counter()
        try:
            report, _policy, _records = FirstPromotionDecomposedGame(config, model).solve()
            seconds = time.perf_counter() - started
            ref = {
                "status": "ok" if seconds <= REFERENCE_SECONDS_LIMIT else "failed_time_limit",
                "seconds": seconds,
                "nodes": report["nodes"],
                "learner_sequences": report["learner_sequences"],
                "opponent_sequences": report["opponent_sequences"],
                "raw_recovered_cost": report["raw_recovered_cost"],
                "raw_causal_null_risk": report["raw_causal_null_risk"],
                "iid_boundary_risk": report["iid_boundary_risk"],
                "activation_probability": report["activation_probability"],
                "calibrated_total_cost": report["calibrated_total_cost"],
                "calibrated_risk_bound": report["calibrated_risk_bound"],
                "solver_objective": report["solver_objective"],
                "reference_cost_key_used": "calibrated_total_cost (feasible, root-mixed with continue)",
            }
        except Exception as exc:
            ref = {
                "status": "failed",
                "seconds": time.perf_counter() - started,
                "error": repr(exc),
                "trace": traceback.format_exc(),
            }
        cell["reference"] = ref

        gate = {"g_correct": False, "detail": {}}
        fcg = cell["fcg"]
        if fcg["status"] == "ok" and ref["status"] == "ok":
            u, lo = F(fcg["U"]), F(fcg["L"])
            v_ref = F(ref["calibrated_total_cost"])
            alpha = config.alpha
            detail = {
                "risk_le_alpha": F(fcg["final_robust_risk"]) <= alpha,
                "L_le_U": lo <= u,
                "abs_U_minus_Vref": float(abs(u - v_ref)),
                "U_matches_ref_1e-6": float(abs(u - v_ref)) <= 1e-6,
                "gap": float(u - lo),
                "gap_relative_to_max1_absU": float(u - lo) / max(1.0, abs(float(u))),
                "gap_le_1e-6": float(u - lo) <= 1e-6 * max(1.0, abs(float(u))),
            }
            gate["detail"] = detail
            gate["g_correct"] = all(
                detail[k] for k in ("risk_le_alpha", "L_le_U", "U_matches_ref_1e-6", "gap_le_1e-6")
            )
            unsafe = F(fcg["iid_optimum_robust_risk"]) > alpha
            cuts = fcg["n_rows"] - 1
            strictly_better = u < F(fcg["U0"])
            gate["g_demo_cell"] = bool(unsafe and cuts >= 1 and strictly_better)
            gate["g_demo_parts"] = {
                "iid_optimum_unsafe": unsafe,
                "cuts_generated": cuts,
                "U_strictly_below_U0": strictly_better,
                "U0": fcg["U0"],
                "U": fcg["U"],
            }
            gate["g_compute"] = {
                "risk_rows": fcg["n_rows"],
                "reference_opponent_sequences": ref["opponent_sequences"],
                "fcg_seconds": fcg["seconds"],
                "reference_seconds": ref["seconds"],
                "fcg_faster_measured": fcg["seconds"] < ref["seconds"],
            }
        else:
            gate["detail"] = {"reason": "FCG or reference did not complete; cell fails G-correct"}
            gate["g_demo_cell"] = False
        cell["gates"] = gate
        cells_out.append(cell)
        print(
            json.dumps(
                {
                    "cell": cid,
                    "fcg_status": fcg["status"],
                    "ref_status": ref["status"],
                    "g_correct": gate["g_correct"],
                    "g_demo_cell": gate["g_demo_cell"],
                    "fcg_s": fcg.get("seconds"),
                    "ref_s": ref.get("seconds"),
                }
            ),
            flush=True,
        )

    anti_demo = [c["id"] for c in cells_out if c["anti_persistent"] and c["gates"]["g_demo_cell"]]
    any_demo = [c["id"] for c in cells_out if c["gates"]["g_demo_cell"]]
    summary = {
        "G_correct_all_cells": all(c["gates"]["g_correct"] for c in cells_out),
        "G_correct_by_cell": {c["id"]: c["gates"]["g_correct"] for c in cells_out},
        "G_demo_any_cell": bool(any_demo),
        "G_demo_cells": any_demo,
        "G_demo_anti_persistent_cells": anti_demo,
    }
    result = {
        "protocol_sha256": sha(PROTOCOL),
        "runner_sha256": sha(Path(__file__)),
        "module_sha256": sha(MODULE),
        "cells": cells_out,
        "summary": summary,
    }
    OUTPUT.write_text(json.dumps(jsonable(result), indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
