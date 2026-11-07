"""Retrospective Giacomini-Rossi one-time-reversal diagnostic on WP1 real loss episodes.

Implements the two-model loss-difference statistic from Giacomini & Rossi (2010), Proposition 3,
for a fixed pair of models in each episode. The episode-level outputs are exploratory: the theorem's
mixing/FCLT and variance conditions are not established for these streams, and no multiplicity or
source-cluster correction is applied across episodes.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from late_real import streams

ROOT = Path(__file__).resolve().parents[2]
Q_CRIT = {0.01: 13.4811, 0.05: 9.8257, 0.10: 8.1379}
COMPONENT_CRIT = {0.01: (6.63, 12.35), 0.05: (3.84, 8.85), 0.10: (2.71, 7.17)}


def gr_one_time_reversal(d, alpha: float = 0.05) -> dict:
    """Return the GR statistic, trimmed break estimate, and component diagnostics.

    ``d[t] = loss_incumbent[t] - loss_challenger[t]`` (positive means challenger has lower loss).
    Uses the paper's conventional 15%-85% trimming, tabulated asymptotic critical values, and
    raw-product HAC estimator under the zero-mean null. Bartlett/Newey-West lag is
    floor(4*(n/100)^(2/9)).
    """
    if alpha not in Q_CRIT:
        raise ValueError(f"alpha must be one of {sorted(Q_CRIT)}")
    x = np.asarray(d, dtype=float)
    n = len(x)
    if n < 20 or not np.isfinite(x).all():
        raise ValueError("d must contain at least 20 finite observations")
    lag = min(n - 1, int(math.floor(4 * (n / 100.0) ** (2 / 9))))
    # Proposition 3's HAC estimator uses raw loss-difference cross-products under H0:E[d_t]=0.
    lrv = float(x @ x) / n
    for k in range(1, lag + 1):
        gamma = float(x[k:] @ x[:-k]) / n
        lrv += 2.0 * (1.0 - k / (lag + 1)) * gamma
    if not math.isfinite(lrv) or lrv <= 0:
        return {"n": n, "lag": lag, "lrv": lrv, "valid": False,
                "reason": "nonpositive_or_nonfinite_HAC_variance"}

    total = float(x.sum())
    lm1 = total * total / (n * lrv)
    lo, hi = int(math.ceil(0.15 * n)), int(math.floor(0.85 * n))
    t = np.arange(lo, hi + 1)
    frac = t / n
    bridge = np.cumsum(x)[t - 1] - frac * total
    lm2_path = bridge * bridge / (n * lrv * frac * (1.0 - frac))
    idx = int(np.argmax(lm2_path))
    lm2 = float(lm2_path[idx])
    q_stat = float(lm1 + lm2)
    c1, c2 = COMPONENT_CRIT[alpha]
    reject = q_stat > Q_CRIT[alpha]
    lm1_reject, lm2_reject = lm1 > c1, lm2 > c2
    if not reject:
        interpretation = "no_rejection"
    elif lm1_reject and lm2_reject:
        interpretation = "constant_advantage_and_instability_components_both_reject"
    elif lm1_reject:
        interpretation = "constant_relative_advantage_component_only"
    elif lm2_reject:
        interpretation = "instability_component_only"
    else:
        interpretation = "joint_statistic_rejects_components_do_not_individually_reject"
    return {
        "n": n, "lag": lag, "lrv": lrv, "valid": True, "alpha": alpha,
        "Q": q_stat, "Q_critical": Q_CRIT[alpha], "reject": bool(reject),
        "LM1": float(lm1), "LM1_critical": c1, "LM1_reject": bool(lm1_reject),
        "LM2_max": lm2, "LM2_critical": c2, "LM2_reject": bool(lm2_reject),
        "break_index_0based": int(t[idx]), "pre_break_mean": float(x[:t[idx]].mean()),
        "post_break_mean": float(x[t[idx]:].mean()), "full_mean": float(x.mean()),
        "interpretation": interpretation,
    }


def analyze(alpha: float = 0.05) -> dict:
    class_path = ROOT / "outputs/sprint2/WP1/classes.json"
    classes = json.loads(class_path.read_text())
    lookup = {(r["stream"], int(r["ep"])): r for r in classes}
    rows = []
    for name, info in sorted(streams().items()):
        if info["family"] not in ("cached", "fresh") and not info["family"].startswith("late_"):
            continue
        z = np.load(info["file"])
        for ep in info["rows"]:
            d = z["l0"][ep].astype(float) - z["l1"][ep].astype(float)
            stat = gr_one_time_reversal(d, alpha)
            cls = lookup.get((name, int(ep)), {})
            rows.append({"stream": name, "episode": int(ep), "cluster": info["cluster"],
                         "family": info["family"], "wp1_class": cls.get("class", "unclassified"),
                         **stat})
    summary = {}
    for cls in sorted({r["wp1_class"] for r in rows}):
        group = [r for r in rows if r["wp1_class"] == cls and r["valid"]]
        summary[cls] = {"episodes": len(group), "clusters": len({r["cluster"] for r in group}),
                        "GR_rejections": sum(r["reject"] for r in group),
                        "LM2_rejections": sum(r["LM2_reject"] for r in group)}
    return {"method": "Giacomini-Rossi one-time reversal, Proposition 3",
            "paper": "Giacomini and Rossi (2010), Journal of Applied Econometrics 25(4), 595-620",
            "scope": "all cached, fresh, and constructed-late WP1 non-twin loss episodes; retrospective full-episode diagnostic",
            "loss_difference": "l0-l1 (positive means challenger lower loss)", "alpha": alpha,
            "critical_values": {"Q": Q_CRIT[alpha], "components": COMPONENT_CRIT[alpha]},
            "hac": "Bartlett/Newey-West; lag floor(4*(n/100)^(2/9))",
            "rows": rows, "summary_by_frozen_WP1_class": summary,
            "limitations": [
                "asymptotic validity requires paper assumptions including a functional CLT and consistent positive HAC long-run variance; these are not established here",
                "one-time permanent reversal alternative is a diagnostic model, not a causal change label",
                "uses all outcomes in each episode retrospectively and is not an online detector",
            "WP1 classes were derived from these same loss sequences, so class-stratified rejection frequencies are circular descriptive summaries, not independent validation",
                "no multiplicity adjustment across episodes and no source-cluster inference",
                "real cache rows are event-time ordered; exact real elapsed-time stamps and label-publication times are not used",
            ]}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--alpha", type=float, choices=sorted(Q_CRIT), default=0.05)
    ap.add_argument("--out", type=Path, default=Path("docs/sprint2/wp1/gr_one_time_reversal.json"))
    a = ap.parse_args(argv)
    result = analyze(a.alpha)
    out = a.out if a.out.is_absolute() else ROOT / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n")
    lines = ["# Giacomini–Rossi one-time reversal diagnostic", "",
             f"Retrospective diagnostic; alpha={a.alpha}; {len(result['rows'])} episodes.", "",
             "| Frozen WP1 class | episodes | source clusters | Q rejections | LM2 instability component |",
             "|---|---:|---:|---:|---:|"]
    for cls, vals in result["summary_by_frozen_WP1_class"].items():
        lines.append(f"| {cls} | {vals['episodes']} | {vals['clusters']} | {vals['GR_rejections']} | {vals['LM2_rejections']} |")
    lines += ["", "This is a retrospective, unadjusted, asymptotic diagnostic; see the JSON limitations.", ""]
    out.with_suffix(".md").write_text("\n".join(lines))
    print(f"wrote {out} and {out.with_suffix('.md')} ({len(result['rows'])} episodes)")


if __name__ == "__main__":
    main()
