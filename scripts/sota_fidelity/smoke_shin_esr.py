"""SMOKE comparison (not evidence): two-sided e-SR on the label clock vs RMM / E_rb / LRMD.

5 paired seeds x 4 regimes, contract T=2000, B=200, c_q=.05, c_s=5, alpha=.05 (bench.CONTRACT).
Uses a seed base that is NOT bench.DEV_SEED_BASE, so no development seeds are consumed. Policies are
built through existing code only: registry.EXTRA (rmm:*, E_rb:*), fidelity_extras.EXTRA, and the RMM
module's own ``FACTORIES["LRMD_k1"]`` (RMM statistic with a never-switch base, alpha split 1.0, k=1
pacer: the closest RMM relative of the two-sided e-SR).

    uv run --extra drift python scripts/sota_fidelity/smoke_shin_esr.py --out <dir>
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT / "scripts/failure_atlas_v2_flq", ROOT / "scripts/sota_sprint",
           ROOT / "scripts/promising_directions/sota/competitors"):
    sys.path.insert(0, str(_p))

import screen
from bench import CONTRACT, parse_regime
from fidelity_extras import EXTRA as FID
from registry import EXTRA as REG
from shin_esr import TwoSidedESRDeploymentAdapter
from suite import build_suite

SEED_BASE = 2026110699  # smoke only; bench.DEV_SEED_BASE is untouched
REGIMES = ["F0_null", "F0_better", "F3_reversal_800", "S_reversal_400"]


def _esr(**kw):
    return lambda T, B, cs, cq, a, d, r: TwoSidedESRDeploymentAdapter(
        T, B, a, rng=r(kw["name"]), **kw)


def build_extra() -> dict:
    mod = sys.modules["atlas_v2_restart_monitor"]
    extra = {**REG, **FID}
    extra["rmm:LRMD_k1"] = lambda T, B, cs, cq, a, d, r: mod.FACTORIES["LRMD_k1"](T, B, cs, cq, a, d, r)
    extra["esr_rmmbets_fullalpha"] = _esr(name="esr_rmmbets_fullalpha", bets="rmm",
                                          side_alpha_fraction=1.0)
    extra["esr_arl"] = _esr(name="esr_arl", calibration="arl")
    return extra


POLICIES = ["CONTROL_never_switch", "two_sided_esr_label_clock", "esr_rmmbets_fullalpha", "esr_arl",
            "rmm:LRMD_k1", "rmm:gated_deployment+RMM", "E_rb:gated_deployment",
            "river_page_hinkley_t3"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--seeds", type=int, default=5)
    a = ap.parse_args()
    extra = build_extra()
    rows = []
    for name in REGIMES:
        R, _ = parse_regime(name)
        for seed in range(a.seeds):
            losses = R.sample(np.random.default_rng(np.random.SeedSequence(
                [SEED_BASE, screen._h(R.name), seed])))
            gain, delay = R.truth_gain(), R.delay
            for pol in build_suite(losses.shape[0], CONTRACT["budget"], CONTRACT["cs"], CONTRACT["cq"],
                                   CONTRACT["alpha"], delay, seed, SEED_BASE + screen._h(name) % 1000,
                                   names=POLICIES, extra=extra):
                m = screen.metrics(pol, losses, gain, delay=delay, budget=CONTRACT["budget"],
                                   cq=CONTRACT["cq"], cs=CONTRACT["cs"],
                                   stream_rng=np.random.default_rng([SEED_BASE, screen._h(name), seed, 7]))
                rows.append({"regime": name, "seed": seed, "policy": pol.name, **m})
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "records.json").write_text(json.dumps(rows, indent=1, default=float))
    import pandas as pd

    df = pd.DataFrame(rows)
    g = df.groupby(["regime", "policy"]).agg(net=("net", "mean"), promote=("ever_promote", "mean"),
                                             rollbacks=("n_rollbacks", "mean"),
                                             switches=("switches", "mean"),
                                             labels=("labels", "mean"))
    g = g.reindex(pd.MultiIndex.from_product([REGIMES, POLICIES]))
    pd.set_option("display.width", 200)
    print(g.round(2).to_string())
    (a.out / "summary.txt").write_text(g.round(2).to_string() + "\n")


if __name__ == "__main__":
    main()
