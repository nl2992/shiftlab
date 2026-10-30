"""S11 amortised approximation of the exact acquisition policy + exact small-instance references (S04/S06/Q3).

Uses the repository's exact solver (src/shiftlab/dive/rpoq_exact.py). Training instances and test instances use
disjoint alternative parameters (p_alt). The cost of the exact oracle is counted (train data generation)."""

import itertools
import json
import sys
import time

import numpy as np
import pandas as pd
from sklearn.neural_network import MLPClassifier
from sklearn.tree import DecisionTreeClassifier

from shiftlab.dive.rpoq_exact import Evaluator, Instance, constant_table, neyman_table

sys.setrecursionlimit(20000)
H, DELAY = 10, 2
GRID = (0.25, 0.5, 0.75, 1.0)


def inst(pa, budget, horizon=H):
    return Instance(horizon=horizon, delay=DELAY, budget=budget, p_alt=pa)


TRAIN_ALT = [(0.65, 0.60), (0.70, 0.60), (0.75, 0.65), (0.80, 0.70), (0.85, 0.70), (0.70, 0.75)]
TEST_ALT = [(0.72, 0.62), (0.78, 0.68), (0.90, 0.75), (0.62, 0.58), (0.68, 0.80)]
BUDGETS = (2, 3, 4)


def feats(inst_, t, ctx, w, buf, b):
    npend = sum(1 for e in buf if e[0] == "p")
    return [t, ctx, b, np.log(max(w, 1e-9)), npend, inst_.p_alt[0], inst_.p_alt[1]]


def collect(pa, budget):
    i = inst(pa, budget)
    ev = Evaluator(i, i.p_alt, i.budget)
    t0 = time.time()
    v = ev.value()
    X, y = [], []
    for t, w, buf, b in list(ev._post):
        if t >= i.horizon or b == 0:
            continue
        for ctx in (0, 1):
            X.append(feats(i, t, ctx, w, buf, b))
            y.append(ev.act(t, ctx, w, buf, b))
    return i, ev, v, np.array(X), np.array(y), time.time() - t0


t_all = time.time()
CACHE = "outputs/gap_closure/e11_oracle_states_subsample.npz"
import os  # noqa: E402

if os.path.exists(
    CACHE
):  # collected by an earlier identical run of this script (398.2 s of exact solving, 4,439,928 states)
    z_ = np.load(CACHE)
    X, y = z_["X"], z_["y"]
    t_oracle, n_all = 398.2, 4_439_928
    cls = np.array([GRID.index(q) for q in y])
else:
    Xs, ys, t_oracle = [], [], 0.0
    for pa, b in itertools.product(TRAIN_ALT, BUDGETS):
        _, _, _, X, y, dt = collect(pa, b)
        Xs.append(X)
        ys.append(y)
        t_oracle += dt
    X, y = np.vstack(Xs), np.concatenate(ys)
    n_all = len(X)
    sub = np.random.default_rng(0).choice(n_all, 200_000, replace=False)
    np.savez_compressed(CACHE, X=X[sub], y=y[sub])
    X, y = X[sub], y[sub]
    cls = np.array([GRID.index(q) for q in y])
print("training states", n_all, "fit on", len(X), "oracle seconds", round(t_oracle, 1), flush=True)

models = {}
t0 = time.time()
models["tree_d6"] = DecisionTreeClassifier(max_depth=6, random_state=0).fit(X, cls)
models["tree_d3"] = DecisionTreeClassifier(max_depth=3, random_state=0).fit(X, cls)
models["mlp_16"] = MLPClassifier((16,), max_iter=60, random_state=0).fit(
    (X - X.mean(0)) / (X.std(0) + 1e-9), cls
)
mu, sd = X.mean(0), X.std(0) + 1e-9
fit_time = time.time() - t0
# finite-state controller: (t, ctx, b) -> majority q (ignores wealth and pending state)
fsc = (
    pd.DataFrame(np.c_[X[:, :3], y], columns=["t", "ctx", "b", "q"])
    .groupby(["t", "ctx", "b"])
    .q.agg(lambda s: s.mode().iloc[0])
    .to_dict()
)
# quantised lookup on (t, ctx, b, wealth bin, pending count, alt bin)
qbins = lambda r: (
    int(r[0]),
    int(r[1]),
    int(r[2]),
    int(np.clip(np.round(r[3] * 2), -6, 6)),
    int(r[4]),
    round(r[5] * 10),
)
lk = (
    pd.DataFrame(
        [qbins(r) + (v,) for r, v in zip(X, y, strict=True)], columns=list("abcdef") + ["q"]
    )
    .groupby(list("abcdef"))
    .q.agg(lambda s: s.mode().iloc[0])
    .to_dict()
)


def make_policy(kind, i):
    def pol(t, ctx, w, buf, b):
        f = np.array([feats(i, t, ctx, w, buf, b)])
        if kind in ("tree_d6", "tree_d3"):
            return float(GRID[int(models[kind].predict(f)[0])])
        if kind == "mlp_16":
            return float(GRID[int(models[kind].predict((f - mu) / sd)[0])])
        if kind == "fsc":
            return float(fsc.get((t, ctx, b), 0.5))
        if kind == "lookup":
            return float(lk.get(qbins(f[0]), fsc.get((t, ctx, b), 0.5)))
        if (
            kind == "remaining"
        ):  # pacing: spend the remaining budget evenly over the remaining horizon
            rem = max(i.horizon - t, 1)
            return min(GRID, key=lambda g: abs(g - min(b / rem * 2, 1.0)))
        if kind == "const_0.5":
            return 0.5
        if kind == "always_1":
            return 1.0
        raise ValueError(kind)

    return pol


rows = []
for pa, b in itertools.product(TEST_ALT, BUDGETS):
    i = inst(pa, b)
    t0 = time.time()
    ev = Evaluator(i, i.p_alt, i.budget)
    v_opt = ev.value()
    t_solve = time.time() - t0
    null_opt = Evaluator(i, i.p_null, i.budget, policy=ev.act).value()
    states = [(t, w, buf, bb) for (t, w, buf, bb) in ev._post if t < i.horizon and bb > 0]
    ney = constant_table(neyman_table(i))
    kinds = ["tree_d6", "tree_d3", "mlp_16", "fsc", "lookup", "remaining", "const_0.5", "always_1"]
    pols = {k: make_policy(k, i) for k in kinds}
    pols["neyman"] = ney
    for k, pol in pols.items():
        t0 = time.time()
        v = Evaluator(i, i.p_alt, i.budget, policy=pol).value()
        nul = Evaluator(i, i.p_null, i.budget, policy=pol).value()
        # decision error on optimal-policy states + per-decision latency
        errs, t0d = 0, time.time()
        sample = states[:400]
        for t, w, buf, bb in sample:
            errs += pol(t, 0, w, buf, bb) != ev.act(t, 0, w, buf, bb)
        lat = (time.time() - t0d) / max(len(sample), 1)
        rows.append(
            {
                "alt": str(pa),
                "budget": b,
                "policy": k,
                "power": v,
                "v_opt": v_opt,
                "gap": v_opt - v,
                "null_alarm": nul,
                "null_alarm_opt": null_opt,
                "decision_error": errs / max(len(sample), 1),
                "latency_ms_per_decision": 1e3 * lat,
                "exact_solve_s": t_solve,
                "n_states": len(ev._post),
            }
        )
df = pd.DataFrame(rows)
df.to_csv("outputs/gap_closure/e11_s11_amortized_test.csv", index=False)
summ = (
    df.groupby("policy")
    .agg(
        gap=("gap", "mean"),
        gap_max=("gap", "max"),
        rel_gap=("gap", lambda s: float(np.mean(s / df.loc[s.index, "v_opt"]))),
        null_alarm=("null_alarm", "mean"),
        null_alarm_max=("null_alarm", "max"),
        err=("decision_error", "mean"),
        lat_ms=("latency_ms_per_decision", "mean"),
    )
    .round(4)
)
print(summ.to_string())
# scaling of the exact solver with horizon and budget
sc = []
for hz, bb in itertools.product((6, 8, 10, 12), (2, 4, 6)):
    t0 = time.time()
    i = inst((0.8, 0.7), bb, hz)
    ev = Evaluator(i, i.p_alt, i.budget)
    v = ev.value()
    sc.append(
        {
            "horizon": hz,
            "budget": bb,
            "seconds": time.time() - t0,
            "states": len(ev._post),
            "power_opt": v,
        }
    )
    print(sc[-1], flush=True)
pd.DataFrame(sc).to_csv("outputs/gap_closure/e11_exact_scaling.csv", index=False)
# Q3 first-promotion value of information (exact): net benefit of labelling budget b under cost c
voi = []
for pa in ((0.8, 0.7), (0.65, 0.6)):
    for b in range(7):
        i = inst(pa, b)
        ev = Evaluator(i, i.p_alt, b)
        pw = ev.value() if b > 0 else 0.0
        nl = Evaluator(i, i.p_null, b, policy=ev.act).value() if b > 0 else 0.0
        voi.append({"p_alt": str(pa), "budget": b, "power": pw, "null_alarm": nl})
pd.DataFrame(voi).to_csv("outputs/gap_closure/e11_exact_voi.csv", index=False)
print(
    "S11 total seconds",
    round(time.time() - t_all),
    "oracle data seconds",
    round(t_oracle, 1),
    "fit seconds",
    round(fit_time, 2),
)
json.dump(
    {
        "train_states": len(X),
        "oracle_data_seconds": t_oracle,
        "fit_seconds": fit_time,
        "total_seconds": time.time() - t_all,
    },
    open("outputs/gap_closure/e11_s11_meta.json", "w"),
)
