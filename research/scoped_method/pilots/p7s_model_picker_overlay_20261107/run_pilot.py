"""Run exactly the four-cell, 50-seed frozen P7s / Model Picker overlay screen."""

from __future__ import annotations

import gzip
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
FLQ = ROOT / "scripts/failure_atlas_v2_flq"
SOTA = ROOT / "scripts/promising_directions/sota"
for p in (FLQ, SOTA, SOTA / "competitors", SOTA.parent, ROOT / "scripts/sota_sprint"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from b3_plus_policy import b1
from bench import parse_regime
from p7s_model_picker_overlay import P7sModelPickerOverlay
from registry import EXTRA
from simulator import policy_rng, run_episode
from suite import build_suite, stream_from_losses

OUT = Path(__file__).resolve().parent
CELLS = ("F1_late_800", "F0_better", "F3_reversal_800", "F0_null")
METHODS = (
    "P7s_MP_overlay",
    "P7s_MP_no_settled_throttle",
    "P7s_settled",
    "model_picker_adapter",
    "D1",
    "gated_adaptive_range+front",
    "CONTROL_never_switch",
)
T, B, D, CQ, CS, ALPHA, N, SEED_BASE = 2000, 200, 100, 0.05, 5.0, 0.05, 50, 7110601701


def _h(s: str) -> int:
    return int.from_bytes(hashlib.sha256(s.encode()).digest()[:4], "big")


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def _factory(name, T, budget, cs, cq, alpha, delay, ep, seed):
    def r(key):
        return policy_rng(SEED_BASE + _h(name) % 1000, ep * 100_000 + seed, key)

    extra = dict(EXTRA)

    def make_overlay(throttle):
        return P7sModelPickerOverlay(
            T,
            budget,
            delay,
            cs,
            cq,
            rng=r("P7s"),
            params=b1.Params(T=T, delay=delay, cq=cq, alpha=alpha),
            name=name,
            settled_throttle=throttle,
        )

    extra["P7s_MP_overlay"] = lambda *_args: make_overlay(True)
    extra["P7s_MP_no_settled_throttle"] = lambda *_args: make_overlay(False)
    return build_suite(
        T,
        budget,
        cs,
        cq,
        alpha,
        delay,
        ep * 100_000 + seed,
        SEED_BASE + _h(name) % 1000,
        names=list(METHODS),
        extra=extra,
    )


def _metrics(policy, losses, gain, labels, preds, cell, seed):
    started = time.perf_counter()
    result = run_episode(
        policy,
        model_predictions=preds,
        labels=labels,
        delay=D,
        budget=B,
        label_price=CQ,
        switch_cost=CS,
        trace=True,
    )
    rec = result.records
    dep = np.asarray([x["deployed_model"] for x in rec], dtype=int)
    promotions = np.flatnonzero((dep[1:] == 1) & (dep[:-1] == 0)) + 1
    rollbacks = np.flatnonzero((dep[1:] == 0) & (dep[:-1] == 1)) + 1
    first_prom = int(promotions[0]) if len(promotions) else -1
    row = {
        "cell": cell,
        "seed": seed,
        "policy": policy.name,
        "net_cost": result.net_cost,
        "predictive_loss": result.prediction_loss,
        "label_expenditure": CQ * result.requested_labels,
        "switch_expenditure": CS * result.deployment_switches,
        "labels": result.requested_labels,
        "switches": result.deployment_switches,
        "promotion_count": len(promotions),
        "rollback_count": len(rollbacks),
        "first_promotion_t": first_prom,
        "promotion_times": promotions.tolist(),
        "rollback_times": rollbacks.tolist(),
        "refused_requests": result.refused_requests,
        "elapsed_s": time.perf_counter() - started,
    }
    trace = getattr(policy, "q_parts_trace", None)
    for t, rec_t in enumerate(rec):
        ev = {
            "cell": cell,
            "seed": seed,
            "policy": policy.name,
            **rec_t,
            "label": int(labels[t]),
            "loss0": int(losses[t, 0]),
            "loss1": int(losses[t, 1]),
            "gain_truth": float(gain[t]),
        }
        if trace is not None:
            ev.update({f"overlay_{k}": v for k, v in trace[t].items() if k != "t"})
        yield row, ev


def main():
    raw_path = OUT / "raw_event_records.jsonl.gz"
    summary_path = OUT / "raw_episode_rows.jsonl"
    if any(p.exists() for p in (raw_path, summary_path, OUT / "MANIFEST.json", OUT / "RESULTS.md")):
        raise FileExistsError("pilot output exists; refusing to overwrite registered results")
    with gzip.open(raw_path, "wt", encoding="utf-8") as events, summary_path.open("w") as summaries:
        for cell in CELLS:
            regime, _ = parse_regime(cell)
            for seed in range(N):
                losses = regime.sample(
                    np.random.default_rng(
                        np.random.SeedSequence([SEED_BASE, _h(regime.name), seed])
                    )
                )
                gain, _ = regime.truth_gain(), regime.delay
                for policy in _factory(cell, T, B, CS, CQ, ALPHA, D, seed, seed):
                    preds, labels = stream_from_losses(
                        losses, np.random.default_rng([SEED_BASE, _h(cell), seed, 7])
                    )
                    gen = _metrics(policy, losses, gain, labels, preds, cell, seed)
                    row, first = next(gen)
                    summaries.write(json.dumps(row, sort_keys=True) + "\n")
                    events.write(json.dumps(first, sort_keys=True) + "\n")
                    for _, ev in gen:
                        events.write(json.dumps(ev, sort_keys=True) + "\n")
                    if row["refused_requests"] or row["labels"] > B:
                        raise RuntimeError(f"budget invariant failed: {cell}/{seed}/{policy.name}")
                    if isinstance(policy, P7sModelPickerOverlay) and not np.allclose(
                        policy.cp.tr["q"][:T, 0], [x["combined"] for x in policy.q_parts_trace]
                    ):
                        raise RuntimeError("combined propensity differs from CertPlus issued q")
    files = (raw_path, summary_path)
    manifest = {
        "source_commit": _git("rev-parse", "HEAD"),
        "source_worktree_dirty": bool(_git("status", "--porcelain")),
        "command": "PYTHONPATH=scripts/promising_directions/sota uv run python research/scoped_method/pilots/p7s_model_picker_overlay_20261107/run_pilot.py",
        "cells": list(CELLS),
        "methods": list(METHODS),
        "seeds_per_cell": N,
        "seed_base": SEED_BASE,
        "horizon": T,
        "budget": B,
        "delay": D,
        "label_price": CQ,
        "switch_cost": CS,
        "alpha": ALPHA,
        "python": __import__("platform").python_version(),
        "numpy": np.__version__,
        "source_sha256": {
            str(p): hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
            for p in (
                "scripts/promising_directions/b3_plus_policy.py",
                "scripts/promising_directions/sota/competitors/b3_plus_policy_adapter.py",
                "scripts/promising_directions/sota/competitors/p7s_model_picker_overlay.py",
                "research/scoped_method/pilots/p7s_model_picker_overlay_20261107/run_pilot.py",
                "research/scoped_method/pilots/p7s_model_picker_overlay_20261107/analyze.py",
                "research/scoped_method/pilots/p7s_model_picker_overlay_20261107/PROTOCOL.md",
            )
        },
        "raw_artifacts": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
    }
    (OUT / "MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
