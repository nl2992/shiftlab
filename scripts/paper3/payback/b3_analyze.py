"""B3 odd-episode analysis: stream-cluster bootstrap (10,000, equal stream weights, seed 20261110)."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path("outputs/paper3/payback/b3")
R1 = pd.read_csv("outputs/paper3/payback/real_r1/per_episode.csv")
R1 = R1[R1.episode % 2 == 1]
NB, SEED = 10_000, 20261110
rng = np.random.default_rng(SEED)


def prep(df):
    df = df.copy()
    df["cq0"] = df["gross"]
    df["cq05"] = df["gross"] - 0.05 * df["labels"]
    df["wrong"] = ((df["certified"] == 1) & (df["gross"] <= 1e-9)).astype(int)
    return df


def boot(diff):
    idx = rng.integers(0, len(diff), size=(NB, len(diff)))
    m = diff[idx].mean(1)
    lo, hi = np.percentile(m, [2.5, 97.5])
    p = 2 * min((np.sum(m <= 0) + 1) / (NB + 1), (np.sum(m >= 0) + 1) / (NB + 1))
    return [float(diff.mean()), float(lo), float(hi), float(min(p, 1))]


def stream_means(df, cert, col):
    return df[df.cert == cert].groupby("stream")[col].mean()


def descr(df, cert):
    d = df[df.cert == cert]
    c = d[d.certified == 1]
    return {
        "n_episodes": len(d),
        "n_cert": len(c),
        "cert_rate_stream_mean": float(d.groupby("stream").certified.mean().mean()),
        "wrong_pooled": (float(c.wrong.mean()) if len(c) else None),
        "n_wrong": int(c.wrong.sum()),
        "delay_t": (float(c.t.mean()) if len(c) else None),
        "labels": float(d.labels.mean()),
        "net_cq0": float(d.groupby("stream").cq0.mean().mean()),
        "net_cq05": float(d.groupby("stream").cq05.mean().mean()),
    }


res = {"streams": None, "settings": {}}
for tag, h, v in (
    ("v002_h100", 100, 0.002),
    ("v002_h50", 50, 0.002),
    ("v0.001_h100", 100, 0.001),
    ("v0.0005_h100", 100, 0.0005),
):
    f = OUT / f"odd_{tag}.csv"
    b = prep(pd.read_csv(f))
    r1 = prep(R1[R1.h == h].rename(columns={}))
    r1 = r1[["stream", "episode", "cert", "certified", "t", "labels", "gross"]].copy()
    r1 = prep(r1)
    b3 = b[b.cert == "C3"].copy()
    b3["cert"] = "B3"
    b2 = b[b.cert == "B2"].copy()
    b2["cert"] = "B2mine"
    allc = pd.concat(
        [
            b3[
                [
                    "stream",
                    "episode",
                    "cert",
                    "certified",
                    "t",
                    "labels",
                    "gross",
                    "cq0",
                    "cq05",
                    "wrong",
                ]
            ],
            b2[
                [
                    "stream",
                    "episode",
                    "cert",
                    "certified",
                    "t",
                    "labels",
                    "gross",
                    "cq0",
                    "cq05",
                    "wrong",
                ]
            ],
            r1[r1.cert.isin(["B0a", "B0w", "B0b", "B2"])][
                [
                    "stream",
                    "episode",
                    "cert",
                    "certified",
                    "t",
                    "labels",
                    "gross",
                    "cq0",
                    "cq05",
                    "wrong",
                ]
            ],
        ]
    )
    res["streams"] = int(allc.stream.nunique())
    S = {
        "descr": {c: descr(allc, c) for c in ["B3", "B2mine", "B2", "B0a", "B0w", "B0b"]},
        "contrasts": {},
    }
    # driver check: my B2 equals R1 B2 episode by episode
    m = b2.merge(r1[r1.cert == "B2"], on=["stream", "episode"], suffixes=("", "_r1"))
    S["b2_matches_R1"] = (
        bool(
            len(m) > 0
            and (m.certified == m.certified_r1).all()
            and np.allclose(m.gross, m.gross_r1)
        )
        if v == 0.002
        else None
    )
    for col in ("cq0", "cq05"):
        for x in ("B0a", "B0w", "B0b", "B2" if v == 0.002 else "B2mine"):
            d = (stream_means(allc, "B3", col) - stream_means(allc, x, col)).to_numpy()
            S["contrasts"][f"B3-{x}_{col}"] = boot(d)
    res["settings"][tag] = S
json.dump(res, open(OUT / "odd_summary.json", "w"), indent=1)  # noqa: SIM115
for tag, S in res["settings"].items():
    print("==", tag, "B2 matches R1:", S["b2_matches_R1"])
    for c, d in S["descr"].items():
        print(" ", c, {k: (round(x, 4) if isinstance(x, float) else x) for k, x in d.items()})
    for k, c in S["contrasts"].items():
        print("   ", k, [round(x, 3) for x in c])
