"""Decision-harm measures for budgeted model switching (EVALUATOR-SIDE scoring only).

Every measure is a ratio of sums over episodes, value = sum_e num_e / sum_e den_e, where num_e and
den_e are seed-averaged per-episode quantities. This lets one paired episode bootstrap cover both
plain means (den = 1 on the relevant episode class) and ratios of totals. Episode classes use the
evaluator-side constant ``mean_gain = mean_t(l0_t - l1_t)`` (positive => challenger, model 1, is
truly better over the episode; model 0 is the incumbent/frozen reference).

See docs/paper1_eqsdp/01_MEASURES.md for definitions and code references.
"""

from __future__ import annotations

import warnings

warnings.filterwarnings("ignore", message="Mean of empty slice")

import numpy as np
import pandas as pd
from scipy import stats

from data import CQ, CS, NEVER, T

NBOOT = 2000
# name -> (description, direction)
MEASURES = {
    "harm_all": ("J(pi) - J(never_switch), all episodes", "cost/episode; <0 = better than incumbent"),
    "harm_C": ("J(pi) - J(never_switch), challenger-better episodes", "cost/episode; <0 better"),
    "harm_N": ("J(pi) - J(never_switch), challenger-not-better episodes", "cost/episode; <0 better"),
    "capture": ("share of hindsight-attainable improvement captured, C episodes", "ratio; 1 = best fixed model"),
    "regret_hind": ("J(pi) - J(best fixed model in hindsight), all episodes", "cost/episode; lower better"),
    "wrong_exposure": ("fraction of rounds on truly worse model, gain != 0", "fraction; lower better"),
    "wrong_exposure_C": ("wrong exposure on challenger-better episodes (time on incumbent)", "fraction; lower better"),
    "wrong_exposure_S": ("wrong exposure on challenger-worse episodes (time on challenger)", "fraction; lower better"),
    "ttc_rmst": ("time to first correct deployment, C episodes, censored at T", "rounds; lower better"),
    "promoted_C": ("share of C episodes in which the challenger is ever deployed", "fraction; higher better"),
    "ttc_given_promoted": ("time to first deployment among promoted C episodes", "rounds; lower better"),
    "false_promo_N": ("ever deploys challenger, challenger-not-better (gain <= 0)", "fraction; lower better"),
    "false_promo_S": ("ever deploys challenger, challenger strictly worse (gain < 0)", "fraction; lower better"),
    "switches": ("deployment switches per episode", "count; lower = less churn"),
    "switch_cost_share": ("cs*switches / net cost", "share of net cost"),
    "label_cost_share": ("cq*labels / net cost", "share of net cost"),
    "label_eff_gross": ("prediction-loss averted vs never_switch per paid label", "loss units/label; higher better"),
    "label_eff_net": ("net cost averted vs never_switch per paid label", "cost units/label; higher better"),
    "terminal_correct": ("final deployed model is the truly better one, gain != 0", "fraction; higher better"),
    "terminal_correct_C": ("final model is the challenger, C episodes", "fraction; higher better"),
    "terminal_correct_S": ("final model is the incumbent, challenger strictly worse", "fraction; higher better"),
}  # fmt: skip


def seed_level(d: pd.DataFrame) -> pd.DataFrame:
    """Add Jnever, Jhind to seed-level records (needs CONTROL_never_switch rows)."""
    jn = d[d.policy == NEVER].groupby(["stream", "ep"]).net.mean().rename("Jnever")
    x = d.join(jn, on=["stream", "ep"])
    x = x.assign(gain=x.mean_gain)
    # best fixed model in hindsight: needs no labels and no switches
    x["Jhind"] = x.Jnever - T * x.gain.clip(lower=0.0)
    return x


def components(x: pd.DataFrame) -> dict[str, tuple[pd.Series, pd.Series]]:
    """Per-row (num, den) for each measure; rows are seed-level."""
    g = x.gain
    C, N, S, nz = g > 0, g <= 0, g < 0, g != 0
    one = pd.Series(1.0, index=x.index)

    def m(mask, v):
        return v.where(mask, 0.0), one.where(mask, 0.0)

    allr = one > 0
    harm = x.net - x.Jnever
    cens = x.first_deploy.where(x.first_deploy >= 0, T).astype(float)
    ok = ((x.final == 1) & C) | ((x.final == 0) & S)
    prom = C & (x.ever_promote == 1)
    return {
        "harm_all": m(allr, harm),
        "harm_C": m(C, harm),
        "harm_N": m(N, harm),
        "capture": ((x.Jnever - x.net).where(C, 0.0), (x.Jnever - x.Jhind).where(C, 0.0)),
        "regret_hind": m(allr, x.net - x.Jhind),
        "wrong_exposure": m(nz, x.frac_on_wrong),
        "wrong_exposure_C": m(C, x.frac_on_wrong),
        "wrong_exposure_S": m(S, x.frac_on_wrong),
        "ttc_rmst": m(C, cens),
        "promoted_C": m(C, x.ever_promote.astype(float)),
        "ttc_given_promoted": (cens.where(prom, 0.0), one.where(prom, 0.0)),
        "false_promo_N": m(N, x.ever_promote.astype(float)),
        "false_promo_S": m(S, x.ever_promote.astype(float)),
        "switches": m(allr, x.switches.astype(float)),
        "switch_cost_share": (CS * x.switches, x.net),
        "label_cost_share": (CQ * x.labels, x.net),
        "label_eff_gross": (x.Jnever - x.loss, x.labels.astype(float)),
        "label_eff_net": (x.Jnever - x.net, x.labels.astype(float)),
        "terminal_correct": m(nz, ok.astype(float)),
        "terminal_correct_C": m(C, (x.final == 1).astype(float)),
        "terminal_correct_S": m(S, (x.final == 0).astype(float)),
    }


def episode_components(d: pd.DataFrame) -> pd.DataFrame:
    """Seed-averaged (num, den) per (stream, ep, policy): columns '<measure>__num' / '__den'."""
    x = seed_level(d)
    cols = {}
    for k, (n, den) in components(x).items():
        cols[f"{k}__num"] = n
        cols[f"{k}__den"] = den
    c = pd.DataFrame(cols)
    c[["stream", "ep", "policy"]] = x[["stream", "ep", "policy"]]
    return c.groupby(["stream", "ep", "policy"]).mean()


def _ratio(num: np.ndarray, den: np.ndarray) -> np.ndarray:
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(den != 0, num / den, np.nan)


def bootstrap_dataset(
    ec: pd.DataFrame, stream: str, policies: list[str], seed: int = 0, nboot: int = NBOOT
) -> dict[str, dict[str, np.ndarray]]:
    """Point estimates and bootstrap draws for every (measure, policy) on one dataset.

    One set of episode resamples is shared by all policies, so differences are paired.
    """
    sub = ec.loc[stream]
    eps = sorted(sub.index.get_level_values("ep").unique())
    n_ep = len(eps)
    idx = np.random.default_rng([seed, 17]).integers(0, n_ep, (nboot, n_ep))
    by_pol = {p: sub.xs(p, level="policy").reindex(eps) for p in policies}
    out = {}
    for k in MEASURES:
        num = np.stack([by_pol[p][f"{k}__num"].to_numpy() for p in policies])
        den = np.stack([by_pol[p][f"{k}__den"].to_numpy() for p in policies])
        out[k] = {
            "point": _ratio(num.sum(1), den.sum(1)),
            "boot": _ratio(num[:, idx].sum(2), den[:, idx].sum(2)),
        }
    return out


def summarise(point, boot):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        lo = np.nanpercentile(boot, 2.5, axis=-1)
        hi = np.nanpercentile(boot, 97.5, axis=-1)
    return point, lo, hi


def run(d: pd.DataFrame, streams: list[str], policies: list[str], arms: dict[str, str]):
    """Return (values, diffs) long DataFrames, per dataset and POOLED (equal-dataset mean).

    POOLED bootstrap: independent episode resamples within each dataset (same draw index across
    datasets), then the equal-weight mean of dataset values per draw.
    """
    ec = episode_components(d)
    per = {s: bootstrap_dataset(ec, s, policies, seed=i) for i, s in enumerate(streams)}
    pidx = {p: i for i, p in enumerate(policies)}
    vrows, drows = [], []
    for k in MEASURES:
        blocks = {s: (per[s][k]["point"], per[s][k]["boot"]) for s in streams}
        blocks["POOLED"] = (
            np.nanmean([per[s][k]["point"] for s in streams], axis=0),
            np.nanmean([per[s][k]["boot"] for s in streams], axis=0),
        )
        for s, (pt, bt) in blocks.items():
            p_, lo, hi = summarise(pt, bt)
            for p, i in pidx.items():
                vrows.append((k, s, p, p_[i], lo[i], hi[i]))
            for arm, an in arms.items():
                ia = pidx[an]
                for p, i in pidx.items():
                    if p != an:
                        dp, dl, dh = summarise(pt[ia] - pt[i], bt[ia] - bt[i])
                        drows.append((k, s, arm, p, dp, dl, dh))
    values = pd.DataFrame(vrows, columns=["measure", "dataset", "policy", "value", "lo", "hi"])
    diffs = pd.DataFrame(drows, columns=["measure", "dataset", "arm", "comp", "diff", "lo", "hi"])
    t_rows = []
    dd = diffs[diffs.dataset != "POOLED"]
    for (k, arm, comp), g in dd.groupby(["measure", "arm", "comp"]):
        v = g["diff"].dropna().to_numpy()
        if len(v) >= 2:
            h = stats.t.ppf(0.975, len(v) - 1) * v.std(ddof=1) / np.sqrt(len(v))
            t_rows.append((k, arm, comp, v.mean() - h, v.mean() + h, int((v < 0).sum()), len(v)))
        else:
            t_rows.append((k, arm, comp, np.nan, np.nan, 0, len(v)))
    tt = pd.DataFrame(
        t_rows, columns=["measure", "arm", "comp", "t_lo", "t_hi", "n_neg_datasets", "n_datasets"]
    )
    pooled = diffs[diffs.dataset == "POOLED"].merge(tt, on=["measure", "arm", "comp"], how="left")
    perds = diffs[diffs.dataset != "POOLED"]
    return values, pd.concat([perds, pooled], ignore_index=True)


def main():
    import argparse
    from pathlib import Path

    import data

    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="outputs/paper1_eqsdp")
    a = ap.parse_args()
    d = data.load_records()
    print("invariants:", data.check_invariants(d))
    policies = sorted(d.policy.unique())
    values, diffs = run(d, data.DATASETS, policies, data.ARMS)
    values["class"] = values.policy.map(data.policy_class)
    diffs["comp_class"] = diffs.comp.map(data.policy_class)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    values.to_csv(out / "measure_values.csv", index=False, float_format="%.6g")
    diffs.to_csv(out / "measure_diffs.csv", index=False, float_format="%.6g")
    print(f"wrote {len(values)} value rows, {len(diffs)} diff rows to {out}")


if __name__ == "__main__":
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent))
    main()
