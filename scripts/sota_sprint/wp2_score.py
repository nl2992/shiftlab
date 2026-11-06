"""WP2 scoring: V1/V2, registered first-promotion EI proxy, and all-in excess economic cost.

Input: one or more wp2_run.py output directories (records.jsonl). Output: one row per
(regime, T, delay_mult, policy) cell with cluster-bootstrap 95% CIs, plus any pooled class rows.

Scores (first promotion tau; d_t = l0_t - l1_t; c_s = 5):
  promote   P(ever promote)                  V2 error rate on a marginal null / power on an alternative
  v1_err_H  P(promote and mean d over [tau, tau+H) <= 0), H = 100, 500
  hp        P(first promote and EI), EI = sum_{t>=tau} d_t - c_s <= 0 registered V3 proxy
  hp_path   P(promote and DB <= 0), DB = sum l0 - loss - c_s*switches
  pi_ei     sum EI / sum promote                                 share of promotions that are EI
  adv_rest  mean rest-of-episode d at promotion (among promoted)  conditional advantage estimate
  harm      legacy field: mean J(policy) - J(never-switch)        all-in excess economic cost incl. label spend
  db, labels, delay (first promotion; never = T), net

Clusters: real twin -> (regime, split); other real -> (regime, ep); synthetic -> (regime, seed).
Pooled rows resample clusters within each regime (stratified).

The raw/schema field `harm` is retained for compatibility. It is not application-level
decision harm; it combines predictive loss and accounting costs, and causal utility is
not identified by these records.

    uv run python scripts/sota_sprint/wp2_score.py --runs outputs/sprint2/WP2/run1_twin2 \
        --out outputs/sprint2/WP2/scores_run1.csv
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

CS = 5.0
NBOOT = 2000


CORRECTION_TAG = "_wmaxfix_20261105"


def load(dirs, corrected=False) -> pd.DataFrame:
    source_rows = []
    for d in dirs:
        d = Path(d)
        with open(d / "records.jsonl") as fh:
            for line in fh:
                r = json.loads(line)
                r["_source_dir"] = str(d)
                source_rows.append(r)
    if corrected:
        original = pd.DataFrame(source_rows)
        source_rows = []
        for source, group in original.groupby("_source_dir", sort=False):
            old = group.drop(columns="_source_dir").copy()
            corrected_path = Path(source).with_name(Path(source).name + CORRECTION_TAG) / "records.jsonl"
            if corrected_path.is_file():
                new = pd.read_json(corrected_path, lines=True)
                keys = [k for k in ("kind", "regime", "ep", "seed", "policy")
                        if k in old and k in new]
                if not {"regime", "ep", "seed", "policy"}.issubset(keys):
                    raise ValueError(f"missing exact WP2 correction keys for {source}")
                policies = set(new.policy)
                previous = old[old.policy.isin(policies)]
                if previous.duplicated(keys).any() or new.duplicated(keys).any():
                    raise ValueError(f"duplicate WP2 correction keys for {source}")
                join = previous[keys].merge(new[keys], on=keys, how="outer", indicator=True,
                                            validate="one_to_one")
                if not (join["_merge"] == "both").all():
                    raise ValueError(f"unmatched WP2 corrected rows for {source}")
                old = old[~old.policy.isin(policies)]
                old = pd.concat([old, new], ignore_index=True)
            source_rows.extend(old.to_dict("records"))
    rows = []
    for r in source_rows:
        r.pop("_source_dir", None)
        p = r.pop("promos")
        f = p[0] if p else {}
        r.update({"tau": f.get("t", -1), "ei": f.get("ei", 0),
                  "adv_100": f.get("adv_100", np.nan), "adv_500": f.get("adv_500", np.nan),
                  "adv_rest": f.get("adv_rest", np.nan), "pre_adv": f.get("pre_adv", np.nan),
                  "n_ei_all": sum(x["ei"] for x in p)})
        rows.append(r)
    df = pd.DataFrame(rows)
    return derive(df)


def derive(df: pd.DataFrame) -> pd.DataFrame:
    pr = df.ever_promote.astype(bool)
    df = df.assign(
        cluster=np.where(df.kind == "synthetic", df.regime + "|s" + df.seed.astype(str),
                         np.where(df.split >= 0, df.regime + "|p" + df.split.astype(str),
                                  df.regime + "|e" + df.ep.astype(str))),
        hp=(pr & (df.ei == 1)).astype(float),
        hp_path=(pr & (df.db <= 0)).astype(float),
        v1_err_100=(pr & (df.adv_100 <= 0)).astype(float),
        v1_err_500=(pr & (df.adv_500 <= 0)).astype(float),
        delay_t=np.where(df.first_deploy >= 0, df.first_deploy, df["T"]).astype(float),
        adv_rest_p=np.where(pr, df.adv_rest, 0.0))
    return df


def _cluster_sums(g: pd.DataFrame, cols) -> pd.DataFrame:
    agg = g.groupby("cluster").agg(**{c: (c, "sum") for c in cols}, n=("policy", "size"),
                                   stratum=("regime", "first"))
    return agg


def boot(agg: pd.DataFrame, num: str, den: str | None, n=NBOOT, seed=0):
    """Point and percentile CI. den=None: mean of cluster means of num/n; else ratio sum num / sum den."""
    rng = np.random.default_rng(seed)
    a = agg[num].to_numpy(float)
    b = agg["n"].to_numpy(float) if den is None else agg[den].to_numpy(float)
    strata = agg.stratum.to_numpy()

    def stat(idx):
        if den is None:
            return np.mean(a[idx] / b[idx], axis=-1)
        s = b[idx].sum(axis=-1)
        return np.where(s > 0, a[idx].sum(axis=-1) / np.where(s > 0, s, 1), np.nan)

    full = np.arange(len(a))
    point = float(stat(full))
    idx = np.concatenate([rng.choice(np.flatnonzero(strata == s), (n, int((strata == s).sum())))
                          for s in np.unique(strata)], axis=1)
    bs = stat(idx)
    bs = bs[~np.isnan(bs)]
    if not len(bs):
        return point, np.nan, np.nan
    return point, float(np.quantile(bs, 0.025)), float(np.quantile(bs, 0.975))


RATE = ["ever_promote", "hp", "hp_path", "v1_err_100", "v1_err_500"]
MEAN = ["harm", "db", "labels", "delay_t", "net"]


def score_group(g: pd.DataFrame) -> dict:
    agg = _cluster_sums(g, RATE + MEAN + ["ei", "adv_rest_p"])
    agg["ei_p"] = agg["ei"]  # ei is 0 when not promoted, so sum ei = sum EI among promoted
    out = {"runs": int(len(g)), "clusters": int(len(agg))}
    for c in RATE + MEAN:
        p, lo, hi = boot(agg, c, None)
        out[c] = p
        out[c + "_lo"], out[c + "_hi"] = lo, hi
    for c, num in (("pi_ei", "ei_p"), ("adv_rest", "adv_rest_p")):
        p, lo, hi = boot(agg, num, "ever_promote")
        out[c], out[c + "_lo"], out[c + "_hi"] = p, lo, hi
    out["runtime_max"] = float(g.runtime_s.max())
    return out


def score(df: pd.DataFrame, keys=("regime", "T", "delay_mult", "policy")) -> pd.DataFrame:
    rows = [{**dict(zip(keys, k)), **score_group(g)} for k, g in df.groupby(list(keys))]
    return pd.DataFrame(rows)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", required=True, help="comma-separated wp2_run.py output directories")
    ap.add_argument("--out", required=True, help=".csv path")
    a = ap.parse_args(argv)
    s = score(load(a.runs.split(",")))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    s.to_csv(a.out, index=False)
    with pd.option_context("display.width", 200, "display.max_rows", 500):
        print(s[["regime", "T", "delay_mult", "policy", "ever_promote", "hp", "pi_ei", "adv_rest",
                 "harm"]].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
