"""Event-driven harness: enforces label release = request time + tau; evaluator-side ledger."""

from __future__ import annotations

import numpy as np

from .config import RARConfig
from .controller import RARController


def run_stream(
    X,
    y,
    cfg: RARConfig,
    factory,
    detector,
    *,
    quality=None,
    label_policy=None,
    gate2=None,
    gate3=None,
    controller_cls=RARController,
):
    """Run one controller on a stream. The first cfg.warmup rows are the offline warm-up prefix.

    Returns dict(U, n_correct, n_eval, acc, counts, log, correct(array), controller).
    The harness alone holds y_t; it passes y_i to the controller only at time i + tau.
    """
    X = np.asarray(X, float)
    y = np.asarray(y).astype(int)
    w = cfg.warmup
    ctl = controller_cls(
        cfg, factory, detector, quality=quality, label_policy=label_policy, gate2=gate2, gate3=gate3
    )
    ctl.start(X[:w], y[:w])
    Xs, ys = X[w:], y[w:]
    T = len(ys)
    release = {}
    correct = np.zeros(T)
    for t in range(T):
        rel = [(i, int(ys[i])) for i in release.pop(t, [])]
        out = ctl.step(t, Xs[t], rel)
        correct[t] = float(out.pred == ys[t])  # evaluator-side only
        if out.request_label:
            release.setdefault(t + cfg.tau, []).append(t)
    nc = float(correct.sum())
    return {
        "U": ctl.objective(nc),
        "n_correct": nc,
        "n_eval": T,
        "acc": nc / T,
        "counts": dict(ctl.counts),
        "log": ctl.log,
        "correct": correct,
        "controller": ctl,
    }


def utility_at_rho(res, rho, cfg: RARConfig):
    """Exact re-pricing of a cost-blind run (U is affine in rho for cost-blind policies)."""
    c = res["counts"]
    return res["n_correct"] - rho * (
        c["retrain"] + cfg.Ca_frac * c["alert"] + cfg.Cb_frac * c["rollback"]
    )
