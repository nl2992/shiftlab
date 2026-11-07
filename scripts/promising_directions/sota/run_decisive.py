"""The decisive experiment: economic stopping trigger vs certificate stopping trigger.

Pre-registered in `docs/promising_directions/sota/SOTA_NARROWED_PROTOCOL.md`, including the
stop/continue rule and the amendment naming `GatedDeploymentStop` as the bar. This script does
not decide anything; it produces the numbers the pre-registered rule is applied to.

Cached 0/1 loss streams are replayed exactly: with every label set to 0, a model's prediction
equals its loss, so `pred != label` reproduces the stored loss event for event. No model is
retrained and no raw data is touched.

Policies are paired on episodes *and* on seeds: for a given (episode, seed) every policy is
driven by a generator seeded from the same `(seed_base, episode, seed)`, so they see the same
randomness where their behaviour coincides.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

SOTA = Path(__file__).resolve().parent
sys.path.insert(0, str(SOTA))
sys.path.insert(0, str(SOTA / "competitors"))

from certificate_stops import DiscernStyleStop, GatedDeploymentStop
from economic_stop import EconomicStop
from simulator import check_budget_feasible, run_episode

T_EP = 2000
SEED_BASE = 20261101

SOURCES = {
    "rialto": Path("docs/promising_directions/results/b3/losses/rialto.npz"),
    "spam": Path("docs/promising_directions/results/b3/losses/spam.npz"),
    "weather": Path("docs/promising_directions/results/b3/losses/weather.npz"),
}
DELAYS = {"rialto": 100, "spam": 50, "weather": 1, "openml_ldpa": 100, "uci_occupancy": 100}
POWERED = ("rialto", "openml_ldpa")  # only these can decide, per the protocol


def load_losses(name: str, extra_root: Path | None) -> np.ndarray:
    """Return (K, T, 2) stacked 0/1 losses for a dataset."""
    p = SOURCES.get(name)
    if p is None or not p.exists():
        if extra_root is None:
            raise FileNotFoundError(f"no cached losses for {name}")
        p = extra_root / f"{name}.npz"
    z = np.load(p)
    return np.stack([z["l0"], z["l1"]], axis=2)


def make_policies(horizon, budget, cs, alpha, eps, p_min, rng_factory):
    """One entry per policy. Every policy gets its own generator from the same seed."""
    return [
        EconomicStop(horizon, budget, alpha, switch_cost=cs, rng=rng_factory(), p_min=p_min),
        GatedDeploymentStop(horizon, budget, alpha, rng=rng_factory(), p_min=p_min),
        DiscernStyleStop(horizon, budget, alpha, eps, rng=rng_factory(), p_min=p_min),
    ]


def run_dataset(name, losses, *, budget, cq, cs, alpha, eps, p_min, n_seeds, delay):
    """Returns {policy: (K, n_seeds) net cost} plus per-episode diagnostics."""
    K = losses.shape[0]
    out: dict[str, np.ndarray] = {}
    diag: dict[str, dict[str, np.ndarray]] = {}
    for ep in range(K):
        preds = losses[ep]  # (T, 2) 0/1 losses == predictions when every label is 0
        labels = np.zeros(preds.shape[0], dtype=int)
        for si in range(n_seeds):
            seed = np.random.SeedSequence([SEED_BASE, ep, si])

            def factory(_s=seed):
                return np.random.default_rng(_s)

            for pol in make_policies(preds.shape[0], budget, cs, alpha, eps, p_min, factory):
                res = run_episode(
                    pol, model_predictions=preds, labels=labels, delay=delay, budget=budget,
                    label_price=cq, switch_cost=cs, trace=False,
                )
                if check_budget_feasible(res, budget):
                    raise AssertionError(f"{pol.name} violated the budget on {name} ep {ep}")
                out.setdefault(pol.name, np.zeros((K, n_seeds)))[ep, si] = res.net_cost
                d = diag.setdefault(pol.name, {})
                for key, val in (("loss", res.prediction_loss), ("labels", res.requested_labels),
                                 ("switches", res.deployment_switches)):
                    d.setdefault(key, np.zeros((K, n_seeds)))[ep, si] = val
    return out, diag


def paired_ci(diff_per_episode: np.ndarray, rng, n_boot=4000):
    idx = rng.integers(0, len(diff_per_episode), (n_boot, len(diff_per_episode)))
    m = diff_per_episode[idx].mean(1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--datasets", default="rialto,openml_ldpa")
    ap.add_argument("--extra-root", default=None, help="dir with additional <name>.npz losses")
    ap.add_argument("--budget", type=int, default=200)
    ap.add_argument("--cq", type=float, default=0.05)
    ap.add_argument("--cs", type=float, default=5.0)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--eps", type=float, default=0.0)
    ap.add_argument("--p-min", type=float, default=0.05)
    ap.add_argument("--n-seeds", type=int, default=100)
    ap.add_argument("--out", default="docs/promising_directions/results/b3_plus/decisive")
    a = ap.parse_args(argv)

    extra = Path(a.extra_root) if a.extra_root else None
    outdir = Path(a.out)
    outdir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(991)
    report: dict[str, dict] = {}

    for name in a.datasets.split(","):
        losses = load_losses(name, extra)
        delay = DELAYS.get(name, 100)
        costs, diag = run_dataset(
            name, losses, budget=a.budget, cq=a.cq, cs=a.cs, alpha=a.alpha, eps=a.eps,
            p_min=a.p_min, n_seeds=a.n_seeds, delay=delay,
        )
        per_ep = {k: v.mean(axis=1) for k, v in costs.items()}  # average seeds within an episode
        ours = per_ep["economic_stop"]
        entry = {
            "episodes": len(ours), "delay": delay, "powered": name in POWERED,
            "mean_cost": {k: float(v.mean()) for k, v in per_ep.items()},
            "mean_labels": {k: float(d["labels"].mean()) for k, d in diag.items()},
            "mean_switches": {k: float(d["switches"].mean()) for k, d in diag.items()},
            "mean_loss": {k: float(d["loss"].mean()) for k, d in diag.items()},
            "paired_vs_economic": {},
        }
        for k, v in per_ep.items():
            if k == "economic_stop":
                continue
            d = ours - v  # negative => ours cheaper
            lo, hi = paired_ci(d, rng)
            entry["paired_vs_economic"][k] = {
                "mean": float(d.mean()), "lo": lo, "hi": hi,
                "episodes_ours_cheaper": int((d < 0).sum()),
                "episodes_ours_worse": int((d > 0).sum()),
                "verdict": "ours better" if hi < 0 else ("ours worse" if lo > 0 else "tie"),
            }
        report[name] = entry
        print(f"\n==== {name} (K={entry['episodes']}, delay={delay}, "
              f"{'POWERED' if entry['powered'] else 'low power'})")
        for k in sorted(per_ep):
            print(f"  {k:20s} cost={entry['mean_cost'][k]:8.3f} "
                  f"labels={entry['mean_labels'][k]:6.1f} "
                  f"switches={entry['mean_switches'][k]:.3f} loss={entry['mean_loss'][k]:8.2f}")
        for k, c in entry["paired_vs_economic"].items():
            print(f"  ours - {k:18s} {c['mean']:+8.3f} [{c['lo']:+7.3f},{c['hi']:+7.3f}] "
                  f"{c['verdict']:11s} (better in {c['episodes_ours_cheaper']}/"
                  f"{entry['episodes']})")

    cfg = {"budget": a.budget, "cq": a.cq, "cs": a.cs, "alpha": a.alpha, "eps": a.eps,
           "p_min": a.p_min, "n_seeds": a.n_seeds, "seed_base": SEED_BASE}
    (outdir / "decisive_results.json").write_text(
        json.dumps({"config": cfg, "datasets": report}, indent=2) + "\n"
    )
    print(f"\nwrote {outdir / 'decisive_results.json'}")
    return report


if __name__ == "__main__":
    main()
