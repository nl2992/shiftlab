"""Fresh-process timing and risk check for early promotion pruning."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from fractions import Fraction as F
from pathlib import Path

import psutil

from shiftlab.dive.causal_switching_game import GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel
from shiftlab.dive.early_promotion_pruning import EarlyPromotionPruning
from shiftlab.dive.first_promotion_decomposition import FirstPromotionDecomposedGame

ROOT = Path(__file__).resolve().parents[2]
SAMPLE_SECONDS = 0.02


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def worker(kind, horizon):
    model = RegimeModel(
        transition01=F(1, 4),
        transition10=F(1, 4),
        emission0=F(1, 20),
        emission1=F(19, 20),
        prior1=F(1, 2),
    )
    config = GameConfig(horizon=horizon, budget=3, delay=1, alpha=F(1, 10), max_nodes=200_000)
    game = (EarlyPromotionPruning if kind == "pruned" else FirstPromotionDecomposedGame)(
        config, model
    )
    start = time.perf_counter()
    game.build()
    build_time = time.perf_counter() - start
    cache_at_build = len(game._decision_cache)
    start = time.perf_counter()
    report, policy, _ = game.solve()
    solve_time = time.perf_counter() - start
    start = time.perf_counter()
    risk = game.null_risk(policy)
    metrics = game.expected_metrics(policy)
    eval_time = time.perf_counter() - start
    return {
        "kind": kind,
        "horizon": horizon,
        "build_s": build_time,
        "solve_s": solve_time,
        "evaluation_s": eval_time,
        "cost": str(sum(metrics[:3])),
        "risk": str(risk),
        "solver_objective": report["solver_objective"],
        "equality_residual": report["equality_residual"],
        "inequality_violation": report["inequality_violation"],
        "nodes": game.nodes,
        "learner_sequences": game.learner.count,
        "null_sequences": game.opponent.count,
        "continuation_decisions_at_build": cache_at_build,
        "skipped_calls": getattr(game, "skipped_continuations", 0),
        "marked_information": len(getattr(game, "marked_information", ())),
        "forbidden_columns": len(getattr(game, "forbidden_columns", ())),
    }


def invoke(kind, horizon):
    command = [sys.executable, str(Path(__file__).resolve()), "--worker", kind, str(horizon)]
    proc = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=ROOT
    )
    sampled_rss = 0
    process = psutil.Process(proc.pid)
    while proc.poll() is None:
        try:
            sampled_rss = max(sampled_rss, process.memory_info().rss)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        time.sleep(SAMPLE_SECONDS)
    stdout, stderr = proc.communicate()
    if proc.returncode:
        return {
            "kind": kind,
            "horizon": horizon,
            "failure": stderr,
            "returncode": proc.returncode,
            "sampled_peak_rss": sampled_rss,
        }
    row = json.loads(stdout)
    row["sampled_peak_rss"] = sampled_rss
    return row


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        print(json.dumps(worker(sys.argv[2], int(sys.argv[3]))))
        return
    target = ROOT / "docs/risk_preserving_approx/early_pruning_development_v1.json"
    if target.exists():
        raise FileExistsError(f"Refusing to overwrite {target}")
    rows = []
    for horizon in (5, 6, 7, 8):
        for repeat in range(3):
            kinds = ("reference", "pruned") if repeat % 2 == 0 else ("pruned", "reference")
            for kind in kinds:
                row = invoke(kind, horizon)
                row["repeat"] = repeat
                rows.append(row)
    for horizon in (5, 6, 7, 8):
        cells = [r for r in rows if r["horizon"] == horizon and "failure" not in r]
        for r in cells:
            assert F(r["risk"]) <= F(1, 10), r
            assert abs(float(F(r["cost"])) - r["solver_objective"]) <= 1e-7, r
        if len(cells) == 6:
            assert (
                max(float(F(r["cost"])) for r in cells) - min(float(F(r["cost"])) for r in cells)
                <= 1e-7
            ), cells
        if horizon == 6:
            assert all(F(r["cost"]) == F(461083, 160000) for r in cells), cells
    sources = [
        Path(__file__),
        ROOT / "src/shiftlab/dive/early_promotion_pruning.py",
        ROOT / "src/shiftlab/dive/first_promotion_decomposition.py",
        ROOT / "docs/risk_preserving_approx/EARLY_PRUNING_PROTOCOL_V1.md",
    ]
    payload = {
        "sample_interval_seconds": SAMPLE_SECONDS,
        "python": sys.version,
        "hashes": {p.relative_to(ROOT).as_posix(): sha(p) for p in sources},
        "rows": rows,
    }
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
