"""Fresh-worker resource comparison for registered pre-promotion cap screen."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from fractions import Fraction as F
from pathlib import Path

import psutil
import scipy
from verify_cut_certificate import verify as verify_cut
from verify_full_t7_certificate import verify as verify_full

from shiftlab.dive.causal_switching_game import GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel
from shiftlab.dive.first_promotion_decomposition import FirstPromotionDecomposedGame
from shiftlab.dive.prepromotion_cap import PrePromotionCapGame

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/risk_preserving_approx"
TARGET = OUT / "precap_resource_comparison_v1.json"


def worker(kind, horizon):
    config = GameConfig(horizon=horizon, budget=3, delay=1, alpha=F(1, 10), max_nodes=200_000)
    model = RegimeModel(
        transition01=F(1, 4),
        transition10=F(1, 4),
        emission0=F(1, 20),
        emission1=F(19, 20),
        prior1=F(1, 2),
    )
    game = (
        FirstPromotionDecomposedGame(config, model)
        if kind == "reference"
        else PrePromotionCapGame(config, model, pre_cap=2)
    )
    begin = time.perf_counter()
    game.build()
    build_s = time.perf_counter() - begin
    cache = len(game._decision_cache)
    begin = time.perf_counter()
    report, policy, _ = game.solve()
    solve_s = time.perf_counter() - begin
    begin = time.perf_counter()
    risk = game.null_risk(policy)
    raw = sum(game.expected_metrics(policy)[:3])
    noquery = lambda history, outcomes: tuple(
        F(choice == (0, 0)) for choice in game.choices(history)
    )
    safe = sum(game.expected_metrics(noquery)[:3])
    activation = min(F(1), config.alpha / risk) if risk else F(1)
    upper = activation * raw + (1 - activation) * safe
    eval_s = time.perf_counter() - begin
    memory = psutil.Process().memory_info()
    peak = getattr(memory, "peak_wset", None)
    return {
        "kind": kind,
        "horizon": horizon,
        "pid": os.getpid(),
        "memory_method": "worker psutil.Process().memory_info().peak_wset"
        if peak is not None
        else "unavailable",
        "worker_peak_wset_bytes": peak,
        "build_s": build_s,
        "solve_s": solve_s,
        "eval_s": eval_s,
        "raw_cost": str(raw),
        "raw_risk": str(risk),
        "activation": str(activation),
        "safe_cost": str(upper),
        "safe_risk_bound": str(activation * risk),
        "numeric_objective": report["solver_objective"],
        "equality_residual": report["equality_residual"],
        "inequality_violation": report["inequality_violation"],
        "builder_nodes": game.nodes,
        "learner_sequences": game.learner.count,
        "null_sequences": game.opponent.count,
        "continuation_cache": cache,
    }


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        print(json.dumps(worker(sys.argv[2], int(sys.argv[3]))))
        return
    if TARGET.exists():
        raise FileExistsError(f"Refusing to overwrite {TARGET}")
    t6path = OUT / "causal_cut_certificate_t6_v1.json"
    verify_cut(t6path)
    lower6 = F(json.loads(t6path.read_text(encoding="utf-8"))["certificate"]["lower"])
    lower7 = F(verify_full()["lower"])
    paths = [
        Path(__file__),
        ROOT / "src/shiftlab/dive/prepromotion_cap.py",
        ROOT / "src/shiftlab/dive/first_promotion_decomposition.py",
        OUT / "PRECAP_RESOURCE_PROTOCOL_V1.md",
    ]
    payload = {
        "python": sys.version,
        "scipy": scipy.__version__,
        "psutil": psutil.__version__,
        "hashes": {p.relative_to(ROOT).as_posix(): sha(p) for p in paths},
        "rows": [],
    }
    for horizon in (6, 7, 8):
        for repeat in range(5):
            kinds = ("reference", "cap2") if repeat % 2 == 0 else ("cap2", "reference")
            for kind in kinds:
                command = [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    "--worker",
                    kind,
                    str(horizon),
                ]
                try:
                    result = subprocess.run(
                        command, cwd=ROOT, capture_output=True, text=True, timeout=120, check=False
                    )
                    if result.returncode:
                        row = {
                            "kind": kind,
                            "horizon": horizon,
                            "status": "failed",
                            "returncode": result.returncode,
                            "stderr": result.stderr,
                        }
                    else:
                        row = json.loads(result.stdout)
                        row["status"] = "completed"
                        if F(row["safe_risk_bound"]) > F(1, 10):
                            raise ValueError("Risk bound failed")
                        if abs(float(F(row["raw_cost"])) - row["numeric_objective"]) > 1e-7:
                            raise ValueError("Recovered objective mismatch")
                        if horizon in (6, 7):
                            lower = lower6 if horizon == 6 else lower7
                            row["certified_gap_upper"] = str(F(row["safe_cost"]) - lower)
                            if F(row["certified_gap_upper"]) < 0:
                                raise ValueError("Safe cost below verified lower bound")
                except Exception as exc:  # noqa: BLE001 - Record failures of registered worker cells.
                    row = {
                        "kind": kind,
                        "horizon": horizon,
                        "status": "failed",
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                row["repeat"] = repeat
                payload["rows"].append(row)
                TARGET.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
                print(
                    json.dumps(
                        {
                            "horizon": horizon,
                            "kind": kind,
                            "repeat": repeat,
                            "status": row["status"],
                        }
                    ),
                    flush=True,
                )


if __name__ == "__main__":
    main()
