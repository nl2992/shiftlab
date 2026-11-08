"""All-tier ">= SOTA" analysis (sota_expansion/11_AMENDMENT_ALL_DATA.md section 4).

Usage: python analyze_all.py  (reads the record files listed in TIERS; missing files are skipped)
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
O = ROOT / "outputs/qsg_methods_search/sota_expansion"
TIERS = {
    "F": [O / "batchF/records.jsonl"],
    "S1": [O / "nine/records.jsonl", O / "nine_armR/records.jsonl"],
    "S2": [O / "batch2/records.jsonl"],
    "D": [O / "dev/records.jsonl", O / "dev_eqsdp/records.jsonl", O / "dev_chalgse/records.jsonl"],
}
ARMS = {"B": "EQSDp_l0.9_g0.2", "R": "EQSDp_l0.98_g0.3"}
ADAPTERS = [
    "qiu_delayed_movement",
    "gong_zhang_paid_obs",
    "gongT_w100_m10",
    "gongT_w800_m20",
    "upf_d0.95_m50",
    "upf_d0.8_m50",
    "chalgse_l1.0_g0.2",
    "chalgse_l0.9_g0.3",
    "cams_adapter",
    "model_selector_causal",
    "model_picker_adapter",
    "online_llm_picker",
    "variance_min_ipw",
    "han_arw_label_clock",
]
CONTROLS = [
    "wald_l0.9_g0.2",
    "wald_l0.97_g0.2",
    "hoef_l0.9_g0.45",
    "hoef_l0.97_g0.3",
    "smarg_l0.9_k0.2",
    "smarg_l0.97_k0.2",
    "dwell_l0.9_s5",
    "dwell_l0.97_s3",
    "econF_mo5_m5",
    "econF_mo5_m0",
    "economic_replacement",
]
SOTA = ADAPTERS + CONTROLS
MARGIN = 0.01
NBOOT = 2000


def load():
    frames = []
    for tier, paths in TIERS.items():
        for p in paths:
            if p.exists():
                d = pd.read_json(p, lines=True)[["stream", "ep", "seed", "policy", "net"]]
                d["tier"] = tier
                frames.append(d)
    d = pd.concat(frames)
    d = d.drop_duplicates(["tier", "stream", "ep", "seed", "policy"])
    return d.groupby(["tier", "stream", "ep", "policy"]).net.mean().unstack("policy")


def upper(x, rng):
    idx = rng.integers(0, len(x), (NBOOT, len(x)))
    return np.quantile(x[idx].mean(1), 0.95)


def per_dataset(m):
    rows = []
    for (tier, stream), g in m.groupby(level=[0, 1]):
        for arm, a in ARMS.items():
            if a not in g:
                continue
            for c in SOTA:
                if c not in g:
                    continue
                x = (g[a] - g[c]).dropna().to_numpy()
                rng = np.random.default_rng(0)
                cj = g[c].mean()
                u = upper(x, rng)
                rows.append(
                    {
                        "tier": tier,
                        "stream": stream,
                        "arm": arm,
                        "comp": c,
                        "n": len(x),
                        "delta": x.mean(),
                        "pct": 100 * x.mean() / cj,
                        "U": u,
                        "margin": MARGIN * cj,
                        "sup": u < 0,
                        "noninf": u < MARGIN * cj,
                    }
                )
    return pd.DataFrame(rows)


def main():
    m = load()
    r = per_dataset(m)
    r.to_csv(O / "all_tier_per_dataset.csv", index=False)
    pd.set_option("display.width", 250)
    print("datasets per tier:", r.groupby("tier").stream.nunique().to_dict())
    print(
        "\n=== Datasets supporting 'arm >= SOTA' (non-inferior to EVERY uncertified comparator) ==="
    )
    sup = r.groupby(["tier", "stream", "arm"]).agg(
        all_noninf=("noninf", "all"),
        n_comp=("comp", "size"),
        n_sup=("sup", "sum"),
        n_fail=("noninf", lambda s: (~s).sum()),
    )
    for arm in ARMS:
        s = sup.xs(arm, level="arm")
        for tiers in (["F"], ["F", "S1", "S2"], ["F", "S1", "S2", "D"]):
            ss = s[s.index.get_level_values(0).isin(tiers)]
            print(
                f"arm {arm} tiers {'+'.join(tiers):10s}: {int(ss.all_noninf.sum())}/{len(ss)} datasets"
            )
    print(
        "\nper dataset (n_fail = comparators where non-inferiority fails; failing comparators listed):"
    )
    for (tier, stream, arm), row in sup.iterrows():
        fails = r[
            (r.tier == tier) & (r.stream == stream) & (r.arm == arm) & ~r.noninf
        ].comp.tolist()
        print(
            f"  {tier:3s} {stream:28s} arm {arm}: ok={row.all_noninf!s:5s} superior to {row.n_sup}/{row.n_comp}; fails: {fails}"
        )
    print(
        "\n=== Pooled per tier and comparator: equal-dataset mean delta, dataset-level t 95% CI, sign ==="
    )
    for arm in ARMS:
        for tiers in (["F"], ["S1", "S2"], ["D"], ["F", "S1", "S2"]):
            rr = r[(r.arm == arm) & r.tier.isin(tiers)]
            if rr.empty:
                continue
            print(f"\n-- arm {arm}, tiers {'+'.join(tiers)} --")
            print(
                f"{'comparator':24s} {'K':>3s} {'meanD':>7s} {'%':>6s} {'t-CI':>17s} {'neg':>4s} {'t-p':>7s} {'noninf':>6s}"
            )
            for c in SOTA:
                q = rr[rr.comp == c]
                if len(q) < 2:
                    continue
                k, mu, sd = len(q), q.delta.mean(), q.delta.std(ddof=1)
                h = stats.t.ppf(0.975, k - 1) * sd / np.sqrt(k)
                p = stats.ttest_1samp(q.delta, 0).pvalue
                cj = (q.delta / (q.pct / 100)).mean()
                ni = (mu + h) < MARGIN * cj
                print(
                    f"{c:24s} {k:3d} {mu:7.2f} {q.pct.mean():6.2f} [{mu - h:7.2f},{mu + h:7.2f}] "
                    f"{int((q.delta < 0).sum()):4d} {p:7.4f} {ni!s:>6s}"
                )


if __name__ == "__main__":
    sys.exit(main())
