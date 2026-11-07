"""Chronological model-pair construction for B3+ screening (mirrors b3_real_data.build_fetched).

Windows (fractions of the *ordered* stream): incumbent trains on [0, 15%), the challenger on
[0, 30%) (option A: HGB) or [15%, 30%) (option B: LR); dev = [30%, 60%); locked = [60%, end).
Preprocessing is fit on [0, 30%) only. Pair selection receives ONLY rows [0, 60%): the function
signatures make it impossible to use a locked-window loss to pick a pair.

Binarisation (one global rule, applied to every dataset): target = the lowest sorted class label
("class 0") if its rate in the training window [0, 30%) lies in [0.05, 0.95]; otherwise the majority
class of that window. y01 = (y == target). The rule that fired is recorded.
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "scripts/promising_directions"))

import b3_plus_baselines as base  # noqa: E402  (loads the pinned b1 and frozen b3_real_data)

b3 = base._b3

T_EP = 2000
RATE_LO, RATE_HI = 0.05, 0.95
# Headroom precheck (protocol section 4)
MIN_DISAGREE = 0.02
TFIDF_MAX_FEATURES = 5000


def windows(n: int) -> dict:
    return {"n15": int(0.15 * n), "n30": int(0.30 * n), "n60": int(0.60 * n), "n": n}


# --------------------------------------------------------------------------- binarisation
def _py(v):
    return v.item() if hasattr(v, "item") else v


def binarise_info(y_train: np.ndarray) -> dict:
    """Apply the single global rule on the training-window labels only."""
    vals, cnt = np.unique(np.asarray(y_train), return_counts=True)  # sorted ascending
    if len(vals) < 2:
        return {
            "rule": "degenerate_single_class",
            "target_class": _py(vals[0]),
            "classes": [_py(v) for v in vals],
            "class0_rate_train": 1.0,
            "target_rate_train": 1.0,
            "n_classes_train": 1,
        }
    c0, r0 = vals[0], float(cnt[0] / cnt.sum())
    if RATE_LO <= r0 <= RATE_HI:
        tgt, j, rule = c0, 0, "class0_vs_rest"
    else:
        j = int(np.argmax(cnt))  # np.argmax breaks ties by the lowest sorted label
        tgt, rule = vals[j], "majority_vs_rest"
    return {
        "rule": rule,
        "target_class": _py(tgt),
        "classes": [_py(v) for v in vals],
        "class0_rate_train": r0,
        "target_rate_train": float(cnt[j] / cnt.sum()),
        "n_classes_train": int(len(vals)),
    }


def binarise(y: np.ndarray, n30: int) -> tuple[np.ndarray, dict]:
    """y01 for the whole stream; the rule is decided from y[:n30] alone."""
    info = binarise_info(y[:n30])
    return (np.asarray(y) == info["target_class"]).astype(np.int8), info


# --------------------------------------------------------------------------- features
class Featurizer:
    """Train-only preprocessing fit on [0, n30). Dense: b3.prep + median imputation; text: TF-IDF."""

    def __init__(self, x_train):
        self.kind = "dense"
        if isinstance(x_train, np.ndarray) and x_train.dtype == object:
            self.kind = "text"
            self.vec = TfidfVectorizer(
                max_features=TFIDF_MAX_FEATURES,
                min_df=5,
                sublinear_tf=True,
                dtype=np.float32,
                strip_accents="unicode",
            ).fit(x_train)
            self.f = lambda a: self.vec.transform(a)
            return
        self.obj_cols = [
            c
            for c in x_train.columns
            if (not pd.api.types.is_numeric_dtype(x_train[c])) or pd.api.types.is_bool_dtype(x_train[c])
        ]
        x = self._fix(x_train)
        self.f0 = b3.prep(x)
        self.imp = SimpleImputer(strategy="median").fit(self.f0(x))
        self.f = lambda a: self.imp.transform(self.f0(self._fix(a)))

    def _fix(self, a):
        a = a.copy()
        for c in self.obj_cols:  # categorical / bool -> str so prep() one-hot encodes them
            a[c] = a[c].astype(str)
        return a

    def slice(self, x, a, b):
        return x[a:b] if self.kind == "text" else x.iloc[a:b]

    def __call__(self, x, a, b):
        return self.f(self.slice(x, a, b))


def fit_or_constant(kind: str, feats, y):
    if len(np.unique(y)) < 2:
        return int(y[0])
    return b3.mk_fetched(kind).fit(feats, y)


def predict_loss(m, feats, y) -> np.ndarray:
    pr = np.full(feats.shape[0], m) if isinstance(m, int) else m.predict(feats)
    return (pr != y).astype(np.int8)


# --------------------------------------------------------------------------- headroom precheck
def headroom_precheck(l0_dev: np.ndarray, l1_dev: np.ndarray, t_ep: int = T_EP, cs: float = 5.0):
    """Protocol section 4, on DEV-window per-event 0/1 losses only."""
    l0 = np.asarray(l0_dev, dtype=float)
    l1 = np.asarray(l1_dev, dtype=float)
    dis = float((l0 != l1).mean())
    inc, chal = float(l0.mean()), float(l1.mean())
    adv = inc - chal
    res = {
        "dev_rows": int(len(l0)),
        "disagree": dis,
        "inc_err_dev": inc,
        "chal_err_dev": chal,
        "adv_per_event": adv,
        "adv_times_T": round(adv * t_ep, 9),  # rounded so an exact break-even is not a float artefact
        "cs": cs,
        "T": t_ep,
        "cond_disagree_ge_0.02": bool(dis >= MIN_DISAGREE),
        "cond_challenger_better": bool(chal < inc),
        "cond_adv_T_gt_cs": bool(round(adv * t_ep, 9) > cs),
    }
    res["passes"] = bool(
        res["cond_disagree_ge_0.02"] and res["cond_challenger_better"] and res["cond_adv_T_gt_cs"]
    )
    return res


# --------------------------------------------------------------------------- pair selection
def pair_options(featurizer_kind: str) -> list[dict]:
    """A = HGB on [0, 30%) (not feasible on sparse text); B = LR on [15%, 30%)."""
    opts = []
    if featurizer_kind == "dense":
        opts.append({"name": "A", "challenger": "HGB", "train": "0-30%"})
    opts.append({"name": "B", "challenger": "LR", "train": "15-30%"})
    return opts


def _train_challenger(opt, F, y01, x, w):
    a, b = (0, w["n30"]) if opt["name"] == "A" else (w["n15"], w["n30"])
    return fit_or_constant(opt["challenger"], F(x, a, b), y01[a:b])


def select_pair(x60, y01_60: np.ndarray, w: dict, t_ep: int = T_EP, cs: float = 5.0) -> dict:
    """Fit and select a pair using rows [0, n60) only (``x60``/``y01_60`` are already truncated).

    Option B is tried only if option A fails the dev headroom precheck. The locked window is not
    an argument, so no locked loss can influence the choice.
    """
    if len(y01_60) != w["n60"]:
        raise ValueError("select_pair must receive exactly the first n60 rows (no locked data)")
    n15, n30, n60 = w["n15"], w["n30"], w["n60"]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        F = Featurizer(x60[:n30] if isinstance(x60, np.ndarray) else x60.iloc[:n30])
        inc = fit_or_constant("LR", F(x60, 0, n15), y01_60[:n15])
        l0_dev = predict_loss(inc, F(x60, n30, n60), y01_60[n30:n60])
        tried, chosen, chal_model = [], None, None
        for opt in pair_options(F.kind):
            m = _train_challenger(opt, F, y01_60, x60, w)
            l1_dev = predict_loss(m, F(x60, n30, n60), y01_60[n30:n60])
            hr = headroom_precheck(l0_dev, l1_dev, t_ep, cs)
            tried.append({**opt, "dev": hr})
            if hr["passes"]:
                chosen, chal_model = opt, m
                break
    return {
        "featurizer": F,
        "incumbent": inc,
        "challenger": chal_model,
        "chosen": chosen,
        "tried": tried,
        "inc_err_dev": float(l0_dev.mean()),
        "featurizer_kind": F.kind,
        "passes_headroom": chosen is not None,
    }


def locked_episode_losses(sel: dict, x_full, y01_full: np.ndarray, starts: list[int], t_ep=T_EP):
    """Per-episode (l0, l1) on locked rows. Only callable on a pair that already passed headroom."""
    if not sel["passes_headroom"]:
        raise RuntimeError("refusing to compute locked losses for a pair that failed the precheck")
    F = sel["featurizer"]
    eps = []
    for s in starts:
        xs = F(x_full, s, s + t_ep)
        ys = y01_full[s : s + t_ep]
        eps.append(
            (s, predict_loss(sel["incumbent"], xs, ys), predict_loss(sel["challenger"], xs, ys))
        )
    return eps


def episode_starts(n: int) -> list[int]:
    w = windows(n)
    return b3.episode_plan(w["n60"], n - w["n60"])
