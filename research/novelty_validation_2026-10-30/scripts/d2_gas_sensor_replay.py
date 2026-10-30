"""D2: UCI Gas Sensor Array Drift -- counterfactual-replay monitoring of a frozen classifier's decision cost.

EXPLORATORY (the dataset's batches 3-10 were already inspected by earlier repository work; see protocol 06).
Pre-declared choices are in 06_REAL_DATA_PROVENANCE_AND_PROTOCOL.md and were committed before this ran.
No timestamps or label delays exist in the source: 'delay=5 events' and 'label rate' are SIMULATED feedback.
"""
import json, sys, hashlib, zipfile, io
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from sklearn.datasets import load_svmlight_file
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, "src")
from shiftlab.sota_search import detectors as det
from shiftlab.sota_search import generators as g

ZIP = Path(sys.argv[1]); OUT = Path(sys.argv[2])
POS_CLASS, FN, FP = 6, g.FN_COST, g.FP_COST         # decision loss: FN 5, FP 1 (repository convention)
TAU = FP / (FP + FN)
ALPHA_T, DELTA_S = 0.04, 0.01                       # alarm budget 0.04 + nominal-risk budget 0.01 = 0.05
THR = float(np.log(1 / ALPHA_T))
EPS = 0.10                                          # economic tolerance per event (primary)
S_SEEDS, DELAY, GAMMA = 300, 5, 0.995
FRACS = (0.05, 0.10, 0.20)
SPLIT_SEED = 20261030

with zipfile.ZipFile(ZIP) as z:
    batches = {}
    for b in range(1, 11):
        X, y = load_svmlight_file(io.BytesIO(z.read(f"Dataset/batch{b}.dat")), n_features=128)
        batches[b] = (X.toarray(), y.astype(int))

sc = StandardScaler().fit(batches[1][0])
clf = LogisticRegression(C=1.0, max_iter=5000).fit(sc.transform(batches[1][0]), (batches[1][1] == POS_CLASS))


def score(b, idx=None):
    X, y = batches[b]
    if idx is not None:
        X, y = X[idx], y[idx]
    p = clf.predict_proba(sc.transform(X))[:, 1]
    yy = (y == POS_CLASS).astype(float)
    act = (p >= TAU).astype(float)
    loss = act * (1 - yy) * FP + (1 - act) * yy * FN
    return p, yy, loss, (p - yy) ** 2


# calibration = fixed random half of batch 2 (nominal risk); the other half is the real-data NULL stream
rng = np.random.default_rng(SPLIT_SEED)
perm2 = rng.permutation(len(batches[2][1])); h = len(perm2) // 2
cal_idx, null_idx = np.sort(perm2[:h]), np.sort(perm2[h:])
pc, yc, lc, bc = score(2, cal_idx)
n_cal = len(lc)
r0_hat = float(lc.mean())
r0_ucb = r0_hat + FN * np.sqrt(np.log(1 / DELTA_S) / (2 * n_cal))      # Hoeffding, range [0, FN]
r0b = float(bc.mean())
det._SOURCE_CACHE["GAS"] = {"loss": (r0_hat, float(lc.std())), "brier": (r0b, float(bc.std()))}


def make_sim(p, y, loss, brier, S, perm_seed=None):
    P, Y, L, B = (np.tile(a, (S, 1)) for a in (p, y, loss, brier))
    if perm_seed is not None:                                     # independent random order per row (null stream)
        r = np.random.default_rng(perm_seed)
        order = np.argsort(r.random(P.shape), axis=1)
        P, Y, L, B = (np.take_along_axis(a, order, 1) for a in (P, Y, L, B))
    return {"y": Y, "p": P, "loss": L, "brier": B, "world": SimpleNamespace(family="GAS"),
            "r0_cost": r0_ucb, "x": np.zeros((S, P.shape[1], 1), np.float32)}


def pr_style(sim, frac, lseed, tol):
    """SOURCE_INSPIRED supervised risk monitor (Podkopaev-Ramdas structure, Hoeffding stitched width, labels only)."""
    obs, avail = det._labeled_obs(sim, frac, DELAY, lseed)
    n = np.cumsum(avail, 1)
    mean = np.cumsum(obs, 1) / np.maximum(n, 1)
    w = FN * np.sqrt(np.log(np.pi**2 * np.maximum(n, 1) ** 2 / (3 * ALPHA_T)) / (2 * np.maximum(n, 1)))
    stat = mean - r0_ucb - tol - w
    return np.where(n > 0, stat, -np.inf)


ARMS = {
    "C0_cost_parent": lambda s, f, ls, tol: det.pp_cost_tight(s, frac=f, delay=DELAY, lseed=ls, tol=tol),
    "C1_cost_disc_Kelly": lambda s, f, ls, tol: det.fix_cost(s, frac=f, delay=DELAY, lseed=ls, tol=tol, gamma=GAMMA, uniform_cap=True),
    "C2_cost_ONS": lambda s, f, ls, tol: det.pp_cost_guided(s, frac=f, delay=DELAY, lseed=ls, tol=tol, mode="cost_ons"),
    "H2c_guided_disc": lambda s, f, ls, tol: det.pp_cost_guided(s, frac=f, delay=DELAY, lseed=ls, tol=tol, mode="guided_disc", gamma=GAMMA),
    "PR_style_Hoeffding_CS": lambda s, f, ls, tol: pr_style(s, f, ls, tol),
}


PER_SEED = {}  # added after the first run (output only; computations unchanged)


def run_stream(sim, tag, seed0):
    rows = []
    T = sim["y"].shape[1]
    for frac in FRACS:
        for tol in (EPS, 0.0):
            for k, (name, fn) in enumerate(ARMS.items()):
                stat = fn(sim, frac, seed0 + k * 0 + int(frac * 1000), tol)    # same label mask for every arm
                thr = 0.0 if name.startswith("PR_") else THR
                al = det.first_cross(stat, thr)
                alarmed = al < T
                PER_SEED[f"{tag}|{frac}|{tol}|{name}"] = al
                # evaluator-side realised excess cost before alarm (uses all labels; never visible to monitors)
                excess = np.cumsum(sim["loss"] - r0_hat, 1)
                pre = np.where(alarmed, excess[np.arange(len(al)), np.minimum(al, T - 1)], excess[:, -1])
                rows.append(dict(stream=tag, frac=frac, tol=tol, arm=name, T=T, S=len(al),
                                 alarm_rate=float(alarmed.mean()),
                                 median_alarm_idx=float(np.median(al[alarmed])) if alarmed.any() else None,
                                 labels_at_alarm=float(np.mean(np.where(alarmed, al, T)) * frac),
                                 mean_prealarm_excess_cost=float(pre.mean())))
    return rows


# ---- stream A: real-data NULL (held-out half of batch 2, random order per row; exchangeable by construction)
pn, yn, ln, bn = score(2, null_idx)
simA = make_sim(pn, yn, ln, bn, S_SEEDS, perm_seed=7)
rowsA = run_stream(simA, "A_null_batch2_heldout_half_permuted", 5000)
# ---- stream B: documented batch order 3..10, file order within batch
parts = [score(b) for b in range(3, 11)]
cat = [np.concatenate([x[i] for x in parts]) for i in range(4)]
bounds = np.cumsum([0] + [len(x[0]) for x in parts])
simB = make_sim(*cat, S_SEEDS)
rowsB = run_stream(simB, "B_batches3to10_documented_order", 6000)

desc = [dict(batch=b, n=int(len(batches[b][1])), pos_rate=float((batches[b][1] == POS_CLASS).mean()),
             mean_cost=float(score(b)[2].mean()), excess_vs_cal=float(score(b)[2].mean() - r0_hat),
             brier=float(score(b)[3].mean())) for b in range(1, 11)]
meta = dict(zip_sha256=hashlib.sha256(ZIP.read_bytes()).hexdigest(), n_cal=n_cal, r0_hat=r0_hat, r0_ucb=r0_ucb,
            r0_brier=r0b, THR=THR, EPS=EPS, TAU=TAU, T_null=simA["y"].shape[1], T_drift=simB["y"].shape[1],
            batch_bounds=bounds.tolist(), n_train=int(len(batches[1][1])),
            train_pos=int((batches[1][1] == POS_CLASS).sum()), sklearn_C=1.0)
OUT.mkdir(parents=True, exist_ok=True)
json.dump(dict(meta=meta, per_batch=desc, results=rowsA + rowsB), open(OUT / "d2_gas_sensor_replay.json", "w"), indent=1)
np.savez_compressed(OUT / "d2_gas_sensor_per_seed_alarm_idx.npz", **PER_SEED)
import pandas as pd
d = pd.DataFrame(rowsA + rowsB)
pd.set_option("display.width", 250)
print(json.dumps(meta, indent=0)[:900]); print(pd.DataFrame(desc).round(3))
print(d[d.tol == EPS].round(3).to_string(index=False))
