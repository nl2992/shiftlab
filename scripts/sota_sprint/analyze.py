"""Screening analysis: per-regime summaries and paired contrasts against the strongest comparators.

For each candidate and regime it reports mean net cost, promotion rate, rollbacks, labels, delay
and the paired difference (candidate - comparator, 95% t-interval over seeds/episodes) against:
its declared host, the best certified published comparator present (chosen per regime on the same
seeds: conservative for the candidate), the best uncertified published method, and the best
policy of any kind. Null regimes also get the promotion rate against the registered bound.

    uv run python scripts/sota_sprint/analyze.py outputs/sota_sprint/screen/A \
        --candidates A1,A2 --hosts A1=QSG,A2=QSG --out docs/sota_sprint/screen_A.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from bench import CERTIFIED_PUBLISHED, NULL_PROMOTION_BOUND, UNCERTIFIED_PUBLISHED, parse_regime


def load(dirs) -> pd.DataFrame:
    return pd.concat(
        [pd.read_json(Path(d) / "records.jsonl", lines=True) for d in dirs], ignore_index=True
    )


def paired(df: pd.DataFrame, a: str, b: str) -> dict | None:
    piv = df.pivot_table(index=["regime", "ep", "seed"], columns="policy", values="net")
    if a not in piv or b not in piv:
        return None
    d = (piv[a] - piv[b]).dropna().to_numpy()
    if len(d) < 2:
        return None
    se = d.std(ddof=1) / np.sqrt(len(d))
    return {
        "vs": b,
        "mean": round(float(d.mean()), 2),
        "lo": round(float(d.mean() - 1.96 * se), 2),
        "hi": round(float(d.mean() + 1.96 * se), 2),
        "n": len(d),
        "frac_better": round(float((d < 0).mean()), 3),
    }


def summarise(df: pd.DataFrame, candidates, hosts) -> dict:
    out = {}
    for reg, g in df.groupby("regime"):
        try:
            tags = parse_regime(reg)[0].tags
        except KeyError:
            tags = ("real",)
        means = g.groupby("policy")["net"].mean()
        pol = g.groupby("policy").agg(
            net=("net", "mean"),
            promote=("ever_promote", "mean"),
            rollbacks=("n_rollbacks", "mean"),
            labels=("labels", "mean"),
            switches=("switches", "mean"),
            first=("first_deploy", lambda s: float(np.median(s[s >= 0])) if (s >= 0).any() else -1),
            delay=("detect_delay", lambda s: float(np.median(s[s >= 0])) if (s >= 0).any() else -1),
            regret=("regret_expected_oracle", "mean"),
            pending=("max_pending", "mean"),
            runtime=("runtime_s", "mean"),
        )
        cert = [p for p in CERTIFIED_PUBLISHED if p in means]
        unc = [p for p in UNCERTIFIED_PUBLISHED if p in means]
        best_cert = means[cert].idxmin() if cert else None
        best_unc = means[unc].idxmin() if unc else None
        cell = {
            "tags": list(tags),
            "policies": pol.round(3).to_dict(orient="index"),
            "best_certified": best_cert,
            "best_uncertified": best_unc,
            "contrasts": {},
        }
        for c in candidates:
            if c not in means:
                continue
            others = means.drop(c)
            best_any = others.idxmin()
            cc = {
                k: paired(g, c, v)
                for k, v in (
                    ("host", hosts.get(c)),
                    ("best_certified", best_cert),
                    ("best_uncertified", best_unc),
                    ("best_any", best_any),
                )
                if v
            }
            if "null" in tags:
                cc["null_promotion"] = round(float(pol.loc[c, "promote"]), 3)
                cc["null_bound_ok"] = bool(pol.loc[c, "promote"] <= NULL_PROMOTION_BOUND)
            cell["contrasts"][c] = cc
        out[reg] = cell
    return out


def to_markdown(summary: dict, candidates) -> str:
    lines = [
        "| candidate | regime | net | promote | first | labels | rb | vs host | vs best cert | vs best uncert |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]

    def f(x):
        return "" if not x else f"{x['mean']:+.1f} [{x['lo']:+.1f},{x['hi']:+.1f}] ({x['vs']})"

    for c in candidates:
        for reg, cell in summary.items():
            if c not in cell["contrasts"]:
                continue
            p = cell["policies"][c]
            k = cell["contrasts"][c]
            lines.append(
                f"| {c} | {reg} | {p['net']:.1f} | {p['promote']:.2f} | {p['first']:.0f} | "
                f"{p['labels']:.0f} | {p['rollbacks']:.2f} | {f(k.get('host'))} | "
                f"{f(k.get('best_certified'))} | {f(k.get('best_uncertified'))} |"
            )
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dirs", nargs="+")
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--hosts", default="", help="cand=host,...")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    cands = [c for c in a.candidates.split(",") if c]
    hosts = dict(x.split("=", 1) for x in a.hosts.split(",") if x)
    df = load(a.dirs)
    s = summarise(df, cands, hosts)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(s, indent=1, default=float) + "\n")
    Path(a.out).with_suffix(".md").write_text(to_markdown(s, cands))
    print(to_markdown(s, cands))


if __name__ == "__main__":
    main()
