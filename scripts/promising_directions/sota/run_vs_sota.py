"""P7s against the published competitors, on the five real case-study datasets.

This is the comparison the completion gate actually asks for, and the one that had never been
run. Everything previously on the record was ours against ours: the five case studies are P7s
against P3b (both ours), and the decisive run was `EconomicStop` -- a stand-in built on gated
deployment's own confidence sequence -- against gated deployment. Neither compares the method we
claim against a method somebody else published.

What this script does instead: it drives **P7s itself**, through the simulator's
`Policy` interface, over the same event streams as every published competitor, and pairs the
results on (episode, query seed).

Pairing. For a given (episode, seed) every policy is driven by a generator derived from
`(SEED_BASE, episode, seed, policy_name)`, so policies cannot consume one another's randomness
while still facing identical streams. Net cost is the registered one:
`prediction_loss + c_q * requested_labels + c_s * deployment_switches`.

Replay. Cached 0/1 loss streams are replayed so that `pred != label` reproduces the stored loss
event for event. No model is retrained and no raw data is touched. There are two ways to do that
and the difference is not cosmetic:

* `zeros` sets every label to 0, so a model's prediction equals its loss. Simple, but it makes the
  label marginal degenerate, which could change the behaviour of any competitor that conditions on
  the predicted class or estimates a class prior.
* `xor` draws a balanced label stream and sets each model's prediction to `label XOR loss`. The
  per-model loss sequence is bit-for-bit the same, but the label marginal is realistic.

Both are run. If a competitor's cost differs between them, its adapter depends on the label
marginal and the `zeros` number is an artefact; `xor` is then the number to use. This is checked
rather than assumed. The consequence for competitor coverage is recorded in
`FEATURE_DEPENDENT` below: a method whose acquisition needs development-set features or a fitted
nuisance model cannot run on a loss-only stream, and is reported as not-run rather than
approximated by something easier to beat.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

SOTA = Path(__file__).resolve().parent
sys.path.insert(0, str(SOTA))
sys.path.insert(0, str(SOTA / "competitors"))
sys.path.insert(0, str(SOTA.parent))  # scripts/promising_directions, for b3_plus_policy

from b3_plus_policy import b1
from certificate_stops import DiscernStyleStop, GatedDeploymentStop
from controls import FixedModel
from model_picker import ModelPickerDeploymentAdapter
from model_selector import ModelSelectorCausalAdapter
from online_llm_picker import OnlineLLMPicker
from simulator import (
    check_budget_feasible,
    check_no_future_access,
    policy_rng,
    run_episode,
)
from smcs import SMCSDeploymentPolicy
from xu_acquisition import XuAcquisitionPolicy

SEED_BASE = 20261101  # the registered seed base, as in the five case studies
T_EP = 2000

# Registered per-dataset delays (B3_PLUS_PROTOCOL / run_decisive). Overridden by the cache's own
# `delay` field where it carries one.
DELAYS = {"rialto": 100, "spam": 50, "weather": 1, "openml_ldpa": 100, "uci_occupancy": 100}

PRIMARY = ("spam", "rialto", "weather", "openml_ldpa", "uci_occupancy")

# Published methods that CANNOT run on a loss-only replay stream, with the reason. These are not
# wins and not losses; they are not-run, and saying so is the point of recording them here.
FEATURE_DEPENDENT = {
    "CAMS (Zhang et al.)": "needs an advice_fn (kNN correctness policy) fit on development features",
    "variance minimisation (Hara et al.)": "constructor refuses without a development surrogate",
    "Xu prediction_assisted": "needs a nuisance predictor fit on development data",
    "Sawade et al. 2012 (calibrated)": "needs a calibrated posterior over features",
}


def load_losses(name: str, roots: list[Path]) -> tuple[np.ndarray, int | None]:
    """Return (K, T, 2) stacked 0/1 losses, plus the cache's own delay if it carries one."""
    for r in roots:
        p = r / f"{name}.npz"
        if p.exists():
            z = np.load(p)
            d = int(z["delay"]) if "delay" in z else None
            return np.stack([z["l0"], z["l1"]], axis=2), d
    raise FileNotFoundError(f"no cached losses for {name} under {[str(r) for r in roots]}")


def make_p7s(horizon, budget, cs, cq, alpha, delay, rng):
    """Our method, as a simulator Policy. Isolated here so the wiring is reviewable in one place.

    `P7sPolicy` drives a real `CertPlus(n=1, variant="P7s", acq_shape="settled")`; it is verified
    event-for-event against the vectorised class on these same real streams by
    `tests/promising_directions/test_sota_b3_plus_adapter.py`.
    """
    from b3_plus_policy_adapter import P7sPolicy

    return P7sPolicy(
        horizon=horizon, budget=budget, delay=delay, switch_cost=cs, label_price=cq, rng=rng,
        params=b1.Params(T=horizon, delay=delay, cq=cq, alpha=alpha),
    )


def build_suite(horizon, budget, cs, cq, alpha, eps, p_min, delay, episode, seed, *,
                with_controls: bool):
    """One entry per policy. Published competitors first, then our method, then any controls."""
    def r(nm):
        # paired on (episode, seed); private per policy so nobody perturbs anybody else
        return policy_rng(SEED_BASE, episode * 10_000 + seed, nm)

    pols = [
        GatedDeploymentStop(horizon, budget, alpha, rng=r("gated_deployment"), p_min=p_min),
        DiscernStyleStop(horizon, budget, alpha, eps, rng=r("discern_style"), p_min=p_min),
        SMCSDeploymentPolicy(2, r("smcs"), alpha=alpha),
        ModelPickerDeploymentAdapter(2, 2, r("model_picker")),
        ModelSelectorCausalAdapter(2, 2, r("model_selector")),
        OnlineLLMPicker(2, 2, rng=r("online_llm_picker")),
        XuAcquisitionPolicy("acquisition_only", r("xu_acquisition_only"), delay=delay),
        make_p7s(horizon, budget, cs, cq, alpha, delay, r("P7s")),
    ]
    if with_controls:
        # Controls, NOT competitors. Reported separately; never counted as a SOTA win.
        pols.append(FixedModel(0, name="CONTROL_never_switch"))
    return pols


def build_stream(ep_losses: np.ndarray, label_mode: str, rng) -> tuple[np.ndarray, np.ndarray]:
    """Turn a (T, 2) 0/1 loss record into (predictions, labels) that reproduce it exactly."""
    T = ep_losses.shape[0]
    if label_mode == "zeros":
        labels = np.zeros(T, dtype=int)
    elif label_mode == "xor":
        labels = rng.integers(0, 2, T)
    else:
        raise ValueError(f"unknown label_mode {label_mode!r}")
    preds = (labels[:, None].astype(int) ^ ep_losses.astype(int))
    assert ((preds != labels[:, None]).astype(int) == ep_losses.astype(int)).all()
    return preds, labels


def run_dataset(name, losses, *, budget, cq, cs, alpha, eps, p_min, n_seeds, delay,
                with_controls, label_mode="zeros"):
    """Returns {policy: (K, n_seeds) net cost}, per-episode diagnostics, and any validation gripes."""
    K, T = losses.shape[0], losses.shape[1]
    cost: dict[str, np.ndarray] = {}
    diag: dict[str, dict[str, np.ndarray]] = {}
    problems: list[str] = []
    for ep in range(K):
        for si in range(n_seeds):
            # the stream is paired across policies within an (episode, seed)
            preds, labels = build_stream(
                losses[ep], label_mode, np.random.default_rng([SEED_BASE, ep, si, 7])
            )
            for pol in build_suite(T, budget, cs, cq, alpha, eps, p_min, delay, ep, si,
                                   with_controls=with_controls):
                res = run_episode(
                    pol, model_predictions=preds, labels=labels, delay=delay, budget=budget,
                    label_price=cq, switch_cost=cs, trace=(ep == 0 and si == 0),
                )
                if ep == 0 and si == 0:
                    problems += [f"{name}/{pol.name}: {m}" for m in
                                 check_budget_feasible(res, budget) + check_no_future_access(res, delay)]
                elif res.requested_labels > budget:
                    problems.append(f"{name}/{pol.name} ep{ep} s{si}: over budget")
                cost.setdefault(pol.name, np.zeros((K, n_seeds)))[ep, si] = res.net_cost
                d = diag.setdefault(pol.name, {})
                for key, val in (("loss", res.prediction_loss), ("labels", res.requested_labels),
                                 ("switches", res.deployment_switches)):
                    d.setdefault(key, np.zeros((K, n_seeds)))[ep, si] = val
    return cost, diag, problems


def paired_ci(diff: np.ndarray, rng, n_boot=4000):
    """Episode-level bootstrap. With K < 5 this is reported but cannot support a claim."""
    if len(diff) < 2:
        return float("nan"), float("nan")
    idx = rng.integers(0, len(diff), (n_boot, len(diff)))
    m = diff[idx].mean(1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--datasets", default=",".join(PRIMARY))
    ap.add_argument("--loss-roots", default="docs/promising_directions/results/b3/losses")
    ap.add_argument("--budget", type=int, default=200)
    ap.add_argument("--cq", type=float, default=0.05)
    ap.add_argument("--cs", type=float, default=5.0)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--eps", type=float, default=0.0)
    ap.add_argument("--p-min", type=float, default=0.05)
    ap.add_argument("--n-seeds", type=int, default=100)
    ap.add_argument("--controls", action="store_true", help="also run the never-switch control")
    ap.add_argument("--label-mode", default="zeros", choices=("zeros", "xor"),
                    help="how the cached losses are replayed; see the module docstring")
    ap.add_argument("--out", default="docs/promising_directions/results/b3_plus/vs_sota")
    a = ap.parse_args(argv)

    roots = [Path(x) for x in a.loss_roots.split(",")]
    outdir = Path(a.out)
    outdir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(991)
    report: dict[str, dict] = {}

    for name in a.datasets.split(","):
        losses, cache_delay = load_losses(name, roots)
        delay = cache_delay if cache_delay is not None else DELAYS.get(name, 100)
        t0 = time.time()
        cost, diag, problems = run_dataset(
            name, losses, budget=a.budget, cq=a.cq, cs=a.cs, alpha=a.alpha, eps=a.eps,
            p_min=a.p_min, n_seeds=a.n_seeds, delay=delay, with_controls=a.controls,
            label_mode=a.label_mode,
        )
        per_ep = {k: v.mean(axis=1) for k, v in cost.items()}  # average seeds within an episode
        ours = per_ep["P7s_settled"]
        K = len(ours)
        entry = {
            "episodes": K, "delay": delay, "seconds": round(time.time() - t0, 1),
            "low_power": K < 5,
            "validation_problems": problems,
            "mean_cost": {k: float(v.mean()) for k, v in per_ep.items()},
            "mean_labels": {k: float(d["labels"].mean()) for k, d in diag.items()},
            "mean_switches": {k: float(d["switches"].mean()) for k, d in diag.items()},
            "mean_loss": {k: float(d["loss"].mean()) for k, d in diag.items()},
            "ours_minus_competitor": {},
        }
        for k, v in per_ep.items():
            if k == "P7s_settled":
                continue
            d = ours - v  # negative => P7s cheaper
            lo, hi = paired_ci(d, rng)
            entry["ours_minus_competitor"][k] = {
                "mean": float(d.mean()), "lo": lo, "hi": hi,
                "episodes_ours_cheaper": int((d < 0).sum()),
                "episodes_ours_worse": int((d > 0).sum()),
                "verdict": ("ours better" if hi < 0 else "ours worse" if lo > 0 else "tie"),
            }
        report[name] = entry

        tag = "LOW POWER (K<5)" if entry["low_power"] else f"K={K}"
        print(f"\n==== {name} ({tag}, delay={delay}, {entry['seconds']}s)")
        for k in sorted(per_ep, key=lambda x: entry["mean_cost"][x]):
            star = " <== OURS" if k == "P7s_settled" else ""
            print(f"  {k:26s} cost={entry['mean_cost'][k]:9.3f} "
                  f"labels={entry['mean_labels'][k]:6.1f} "
                  f"sw={entry['mean_switches'][k]:5.2f} loss={entry['mean_loss'][k]:8.2f}{star}")
        for k, c in entry["ours_minus_competitor"].items():
            print(f"  ours - {k:24s} {c['mean']:+9.3f} [{c['lo']:+8.3f},{c['hi']:+8.3f}] "
                  f"{c['verdict']:11s} (cheaper in {c['episodes_ours_cheaper']}/{K})")
        for m in problems:
            print(f"  !! {m}")

    cfg = {"budget": a.budget, "cq": a.cq, "cs": a.cs, "alpha": a.alpha, "eps": a.eps,
           "p_min": a.p_min, "n_seeds": a.n_seeds, "seed_base": SEED_BASE,
           "loss_roots": [str(r) for r in roots], "label_mode": a.label_mode}
    payload = {"config": cfg, "not_run_feature_dependent": FEATURE_DEPENDENT,
               "datasets": report}
    (outdir / f"vs_sota_results_{a.label_mode}.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(f"\nwrote {outdir / f'vs_sota_results_{a.label_mode}.json'}")

    # A compact scoreboard: for each competitor, on how many datasets is P7s cheaper on the mean?
    comps = sorted({c for e in report.values() for c in e["ours_minus_competitor"]})
    print("\n==== scoreboard (mean net cost, powered datasets only)")
    for c in comps:
        w = [n for n, e in report.items()
             if not e["low_power"] and c in e["ours_minus_competitor"]
             and e["ours_minus_competitor"][c]["mean"] < 0]
        l = [n for n, e in report.items()
             if not e["low_power"] and c in e["ours_minus_competitor"]
             and e["ours_minus_competitor"][c]["mean"] > 0]
        print(f"  vs {c:24s} ours cheaper on {len(w)} / lost on {len(l)}  "
              f"(won: {w or '-'}; lost: {l or '-'})")
    return report


if __name__ == "__main__":
    main()
