"""SAES Phase 1: do unlabeled signals carry information about relative model advantage?

Development (exposed streams, data/saes_dev). Two audits:
  A. per-event: on disagreements, AUC of the confidence gap g = |s1-.5| - |s0-.5| for
     z = 1[challenger correct] (would let unlabeled events act as proxy evidence);
  B. staleness: at checkpoints t, regress future advantage change (mean z on [t, t+H) minus mean
     z on [t-H, t), FULL label history = generous to the label-only baseline) on unlabeled
     signal changes (confidence-gap mean, disagreement rate, drift, score gap), recent vs
     reference window. Report correlation and incremental R^2 with an episode bootstrap.
"""

import sys
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score

D = Path(__file__).resolve().parents[2] / "data/saes_dev"
H, R = 300, 100


def wmean(v, m, a, b):
    mm = m[a:b]
    return v[a:b][mm].mean() if mm.sum() >= 5 else np.nan


def main():
    rng = np.random.default_rng(0)
    allrows = []
    print("A. per-event AUC on disagreements (g predicts challenger correct)")
    for f in sorted(D.glob("*.npz")):
        z = np.load(f)
        l0, l1, s0, s1, dr = z["l0"], z["l1"], z["s0"], z["s1"], z["drift"]
        g = np.abs(s1 - 0.5) - np.abs(s0 - 0.5)
        dis = l0 != l1
        zz = (l0 > l1)[dis].astype(int)
        auc = roc_auc_score(zz, g[dis]) if 0 < zz.mean() < 1 else np.nan
        # calibrated-proxy check: mean predicted challenger-correct prob vs realised
        pc = np.where((s1 >= 0.5), s1, 1 - s1)[dis]  # challenger's confidence in its own label
        print(
            f"  {f.stem:9s} eps={l0.shape[0]:3d} dis_events={dis.sum():6d} AUC={auc:.3f} "
            f"p(z)={zz.mean():.3f} mean chall-conf on dis={pc.mean():.3f}"
        )
        for e in range(l0.shape[0]):
            de, ze = dis[e], (l0[e] > l1[e]).astype(float)
            for t in range(H, 2000 - H + 1, 100):
                pf, pp = wmean(ze, de, t, t + H), wmean(ze, de, t - H, t)
                if np.isnan(pf) or np.isnan(pp):
                    continue
                sig = {
                    "dg": wmean(g[e], de, t - R, t) - wmean(g[e], de, t - H, t - R),
                    "dr": de[t - R : t].mean() - de[t - H : t - R].mean(),
                    "ddrift": dr[e, t - R : t].mean() - dr[e, t - H : t - R].mean(),
                    "dsg": (s1[e] - s0[e])[t - R : t].mean()
                    - (s1[e] - s0[e])[t - H : t - R].mean(),
                    "g_now": wmean(g[e], de, t - R, t),
                }
                allrows.append((f.stem, e, pf - pp, pf, pp, sig))
    print("\nB. staleness: corr(signal, future-minus-past advantage), episode bootstrap 95% CI")
    streams = sorted({r[0] for r in allrows})
    keys = ["dg", "dr", "ddrift", "dsg", "g_now"]
    for s in [*streams, "POOLED"]:
        rows = [r for r in allrows if s == "POOLED" or r[0] == s]
        y = np.array([r[2] for r in rows])
        X = np.array([[r[5][k] for k in keys] for r in rows])
        ok = ~np.isnan(X).any(1)
        y, X = y[ok], X[ok]
        epi = np.array([f"{r[0]}:{r[1]}" for r in rows])[ok]
        out = []
        for j, k in enumerate(keys):
            c = np.corrcoef(X[:, j], y)[0, 1]
            ue = np.unique(epi)
            bs = []
            for _ in range(300):
                pick = rng.choice(ue, len(ue))
                idx = np.concatenate([np.where(epi == p)[0] for p in pick])
                if np.std(X[idx, j]) > 0:
                    bs.append(np.corrcoef(X[idx, j], y[idx])[0, 1])
            lo, hi = np.percentile(bs, [2.5, 97.5])
            out.append(f"{k}={c:+.2f}[{lo:+.2f},{hi:+.2f}]")
        print(f"  {s:9s} n={len(y):5d} sd(dy)={y.std():.3f} " + " ".join(out))


if __name__ == "__main__":
    main(*sys.argv[1:])
