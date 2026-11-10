"""Run ONE method on ONE FCG-scale cell in this process; print one JSON line.

    uv run --no-sync python scripts/paper4/run_fcg_scale.py --cell C6 --method fast

Methods: ref (FirstPromotionDecomposedGame.solve), fast (FCG-fast), v1 (frontier_cuts.py).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from fractions import Fraction as F
from pathlib import Path

sys.set_int_max_str_digits(0)  # exact dual bounds exceed the 4300-digit default

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

MAX_NODES = 200_000
CELLS = {
    "S1": dict(horizon=10, budget=4, delay=2, trans=F(1, 10), emis=(F(1, 50), F(49, 50))),
    "S2": dict(horizon=10, budget=4, delay=2, trans=F(3, 4), emis=(F(1, 50), F(49, 50))),
    "S3": dict(horizon=10, budget=4, delay=2, trans=F(3, 4), emis=(F(1, 20), F(19, 20))),
    "C6": dict(horizon=8, budget=3, delay=1, trans=F(3, 4), emis=(F(1, 20), F(19, 20))),
}


def jsonable(value):
    if isinstance(value, F):
        return str(value)
    if isinstance(value, dict):
        return {k: jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    return value


def make(cell: str):
    from shiftlab.dive.causal_switching_game import GameConfig
    from shiftlab.dive.delayed_regime_information import RegimeModel

    c = CELLS[cell]
    config = GameConfig(
        horizon=c["horizon"],
        budget=c["budget"],
        delay=c["delay"],
        alpha=F(1, 10),
        query_cost=F(1, 100),
        switch_cost=F(1, 10),
        max_nodes=MAX_NODES,
    )
    model = RegimeModel(
        transition01=c["trans"],
        transition10=c["trans"],
        emission0=c["emis"][0],
        emission1=c["emis"][1],
        prior1=F(1, 2),
    )
    return config, model


def run(cell: str, method: str) -> dict:
    config, model = make(cell)
    started = time.perf_counter()
    if method == "ref":
        from shiftlab.dive.first_promotion_decomposition import FirstPromotionDecomposedGame

        report, _policy, _records = FirstPromotionDecomposedGame(config, model).solve()
        keys = (
            "nodes",
            "learner_sequences",
            "opponent_sequences",
            "raw_recovered_cost",
            "raw_causal_null_risk",
            "activation_probability",
            "calibrated_total_cost",
            "calibrated_risk_bound",
            "solver_objective",
        )
        out = {k: report[k] for k in keys}
        out["V_ref"] = report["calibrated_total_cost"]
        out["end_to_end_seconds"] = time.perf_counter() - started
    elif method == "fast":
        from shiftlab.paper4.frontier_cuts_fast import frontier_cut_generation_fast

        out = frontier_cut_generation_fast(config, model)
    elif method == "v1":
        from shiftlab.paper4.frontier_cuts import frontier_cut_generation

        out = frontier_cut_generation(config, model)
        out.pop("policy")
        out.pop("iid_row")
        out["end_to_end_seconds"] = out["seconds"]
    else:
        raise ValueError(method)
    for key in ("U", "L", "gap"):
        if isinstance(out.get(key), F):
            out[f"{key}_float"] = float(out[key])
    return jsonable(out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cell", required=True, choices=sorted(CELLS))
    parser.add_argument("--method", required=True, choices=("ref", "fast", "v1"))
    args = parser.parse_args()
    started = time.perf_counter()
    try:
        result = {"status": "ok", **run(args.cell, args.method)}
    except Exception as exc:  # recorded verbatim, never skipped
        result = {
            "status": "failed",
            "error": repr(exc),
            "trace": traceback.format_exc(),
            "end_to_end_seconds": time.perf_counter() - started,
        }
    result.update(cell=args.cell, method=args.method)
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
