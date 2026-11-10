"""Run ONE method on ONE cell in this process; print one JSON line.

uv run --no-sync python scripts/paper4_continuation/ablation_one.py --method R0 --cell C6
"""

from __future__ import annotations

import argparse
import json
import resource
import sys
import time
import traceback
from fractions import Fraction as F
from pathlib import Path

sys.set_int_max_str_digits(0)
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from shiftlab.paper4_continuation.ablation import CELLS, METHODS, MAX_NODES, run_method  # noqa: E402


def jsonable(value):
    if isinstance(value, F):
        return str(value)
    if isinstance(value, dict):
        return {k: jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    return value


def finish(out: dict) -> dict:
    """Float/size summaries for exact values; very long exact strings are trimmed."""
    res = dict(out)
    for key in ("U", "L", "U0", "final_cost"):
        value = res.get(key)
        if isinstance(value, F):
            res[f"{key}_float"] = float(value)
            text = str(value)
            if len(text) > 300:
                res[f"{key}_digits"] = len(text)
                res[key] = None
    return jsonable(res)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--method", required=True, choices=METHODS)
    parser.add_argument("--cell", required=True, choices=sorted(CELLS))
    parser.add_argument("--max-nodes", type=int, default=MAX_NODES)
    args = parser.parse_args()
    started = time.perf_counter()
    try:
        result = {"status": "ok", **finish(run_method(args.method, args.cell, args.max_nodes))}
    except Exception as exc:  # recorded verbatim, never skipped
        result = {
            "status": "failed",
            "error": repr(exc),
            "trace": traceback.format_exc(),
            "total_seconds": time.perf_counter() - started,
        }
    usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    result["self_ru_maxrss_bytes"] = usage if sys.platform == "darwin" else usage * 1024
    result.update(method=args.method, cell=args.cell)
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
