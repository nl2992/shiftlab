"""R1 analysis: stream-cluster bootstrap (10,000 resamples, equal stream weights), decision rule.

usage: analyze_real.py [out_dir]   (reads ep_h50.csv, ep_h100.csv from run_real.py)
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "outputs/paper3/payback/real_r1")
NB, SEED = 10_000, 20261110
CERTS = ["B0a", "B0w", "B0b", "B1", "B2"]
X = ["B0a", "B0w", "B0b"]

df = pd.concat([pd.read_csv(OUT / f"ep_h{h}.csv") for h in (100, 50)], ignore_index=True)
df["net_cq0"] = df["gross"]
df["net_cq05"] = df["gross"] - 0.05 * df["labels"]
df["wrong"] = ((df["certified"] == 1) & (df["gross"] <= 1e-9)).astype(int)
df["truncated"] = ((df["certified"] == 1) & (df["hold"] < df["h"])).astype(int)
df.to_csv(OUT / "per_episode.csv", index=False)

rng = np.random.default_rng(SEED)


def boot(diff: np.ndarray):
    """diff: per-stream contrast. Returns mean, 95% percentile CI, two-sided bootstrap p."""
    n = len(diff)
    idx = rng.integers(0, n, size=(NB, n))
    m = diff[idx].mean(1)
    lo, hi = np.percentile(m, [2.5, 97.5])
    p = 2 * min((np.sum(m <= 0) + 1) / (NB + 1), (np.sum(m >= 0) + 1) / (NB + 1))
    return float(diff.mean()), float(lo), float(hi), float(min(p, 1.0))


def per_stream(h, col):
    g = df[df.h == h].groupby(["stream", "cert"])[col].mean().unstack()
    return g[CERTS]


summary = {
    "n_streams": int(df.stream.nunique()),
    "n_episodes": int(df.groupby("stream").episode.nunique().sum()),
    "bootstrap": {
        "resamples": NB,
        "seed": SEED,
        "ci": "95% percentile, stream-cluster, equal weights",
    },
    "contrasts": {},
    "secondary": {},
}
for h in (100, 50):
    for cq, col in ((0.0, "net_cq0"), (0.05, "net_cq05")):
        ps = per_stream(h, col)
        key = f"h{h}_cq{cq}"
        summary["contrasts"][key] = {}
        for x in X:
            m, lo, hi, p = boot((ps["B2"] - ps[x]).to_numpy())
            summary["contrasts"][key][f"B2-{x}"] = {"mean": m, "lo": lo, "hi": hi, "p": p}
        summary["contrasts"][key]["mean_net_by_cert"] = {c: float(ps[c].mean()) for c in CERTS}
        if (h, cq) == (100, 0.0):  # Holm view of the three primary contrasts
            ks = sorted(X, key=lambda x: summary["contrasts"][key][f"B2-{x}"]["p"])
            run = 0.0
            for i, x in enumerate(ks):
                adj = min(1.0, (len(X) - i) * summary["contrasts"][key][f"B2-{x}"]["p"])
                run = max(run, adj)
                summary["contrasts"][key][f"B2-{x}"]["p_holm"] = run

prim = summary["contrasts"]["h100_cq0.0"]
if any(prim[f"B2-{x}"]["lo"] > 0 for x in ("B0w", "B0b")):
    dec = "R1-SUPPORTED"
elif all(prim[f"B2-{x}"]["hi"] < 0 for x in X):
    dec = "R1-REVERSED"
else:
    dec = "R1-INCONCLUSIVE"
summary["decision"] = dec

rows = []
for h in (100, 50):
    d = df[df.h == h]
    for (s, c), g in d.groupby(["stream", "cert"]):
        cert = g[g.certified == 1]
        rows.append(
            {
                "stream": s,
                "h": h,
                "cert": c,
                "n_episodes": len(g),
                "cert_rate": g.certified.mean(),
                "wrong_frac_of_certs": cert.wrong.mean() if len(cert) else np.nan,
                "mean_delay_certified": cert.t.mean() if len(cert) else np.nan,
                "mean_labels": g.labels.mean(),
                "mean_net_cq0": g.net_cq0.mean(),
                "mean_net_cq05": g.net_cq05.mean(),
                "n_truncated_holds": int(g.truncated.sum()),
            }
        )
st = pd.DataFrame(rows)
st.to_csv(OUT / "per_stream.csv", index=False)

for h in (100, 50):
    sh = st[st.h == h]
    summary["secondary"][f"h{h}"] = {}
    for c in CERTS:
        s = sh[sh.cert == c]
        d = df[(df.h == h) & (df.cert == c)]
        ce = d[d.certified == 1]
        summary["secondary"][f"h{h}"][c] = {
            "cert_rate_stream_mean": float(s.cert_rate.mean()),
            "wrong_frac_stream_mean": float(s.wrong_frac_of_certs.mean()),
            "wrong_frac_pooled": float(ce.wrong.mean()) if len(ce) else None,
            "delay_pooled": float(ce.t.mean()) if len(ce) else None,
            "labels_stream_mean": float(s.mean_labels.mean()),
            "n_cert": len(ce),
            "n_truncated_holds": int(d.truncated.sum()),
        }
summary["excluded"] = json.loads((OUT / "meta_h100.json").read_text())["excluded"]
summary["runtime_seconds"] = {
    h: json.loads((OUT / f"meta_h{h}.json").read_text())["seconds"] for h in (100, 50)
}
(OUT / "summary.json").write_text(json.dumps(summary, indent=1))
print(dec)
print(json.dumps(summary["contrasts"], indent=1))
print(json.dumps(summary["secondary"], indent=1))
