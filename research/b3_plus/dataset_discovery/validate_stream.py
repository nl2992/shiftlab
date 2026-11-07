"""Eligibility checks for a candidate stream (protocol section 3 condition 3 and the goal list).

Principle: row order is NOT assumed to be time. ``resolve_order`` decides from the registry's
declared chronology basis *and verifies it against the data*; a dataset with no defensible event
order is ``USELESS_INELIGIBLE`` and no order is invented. Nothing here reads a locked window's
labels: size checks use row counts only and label checks use the training window [0, 30%).

Returns plain dicts; ``ok`` is False with ``status`` set to the USELESS_* code on failure.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

T_EP = 2000
TRAIN_FRAC, DEV_END_FRAC = 0.30, 0.60
MIN_SPEARMAN = 0.90  # documented-order corroboration threshold
MAX_MISSING_COL = 0.5
LEAK_CORR = 0.99


def _check(name, ok, detail, hard=True):
    return {"check": name, "pass": bool(ok), "detail": detail, "hard": hard}


def take(x, order):
    if isinstance(x, pd.DataFrame):
        return x.iloc[order].reset_index(drop=True)
    return x[order]


# --------------------------------------------------------------------------- chronology
def _inversions(t: np.ndarray) -> int:
    d = np.diff(t)
    return int((d < 0).sum())


def resolve_order(raw, chron: dict) -> tuple[np.ndarray | None, dict]:
    """Return (order, report). ``order is None`` means no defensible order (ineligible)."""
    n = raw.n
    basis = chron.get("declared_basis", "none")
    rep = {"declared_basis": basis, "n": n, "justification": chron.get("justification")}
    idx = np.arange(n)
    if basis == "none" or basis == "n/a":
        rep.update(verdict="no_defensible_order", sorted_by=None)
        if raw.time is not None:
            t = raw.time
            fin = np.isfinite(t)
            rep["time_finite_frac"] = float(fin.mean())
            rep["time_monotone_in_file_order"] = bool(_inversions(t[fin]) == 0)
            rep["time_inversions"] = _inversions(t[fin])
        return None, rep

    if basis == "timestamp_column":
        t = raw.time
        if t is None:
            rep.update(verdict="declared_timestamp_missing")
            return None, rep
        fin = np.isfinite(t)
        rep["time_finite_frac"] = float(fin.mean())
        if fin.mean() < 0.99:
            rep.update(verdict="timestamp_mostly_missing")
            return None, rep
        if not chron.get("time_reliable", False):
            rep.update(verdict="timestamp_declared_unreliable")
            return None, rep
        corr = raw.meta.get("time_corroboration") if raw.meta else None
        if corr is not None:
            rho = float(stats.spearmanr(t[::3], corr[::3])[0])
            rep["time_corroboration_spearman"] = rho
            if rho < 0.99:
                rep.update(verdict="timestamp_not_corroborated_by_second_clock")
                return None, rep
        inv = _inversions(t)
        rep["time_inversions"] = inv
        if inv == 0:
            rep.update(verdict="timestamp_monotone_in_file_order", sorted_by=None)
            return idx, rep
        order = np.lexsort((idx, np.nan_to_num(t, nan=np.inf)))
        rep.update(verdict="sorted_by_timestamp", sorted_by=raw.time_name)
        return order, rep

    if basis == "ordinal_columns":
        o = raw.ordinal
        if o is None:
            rep.update(verdict="declared_ordinal_missing")
            return None, rep
        cols = chron["ordinal_columns"]
        # verification: within each label group the file order must already be chronological
        grp = pd.factorize(raw.y)[0]
        key = o[cols[0]].to_numpy() * 10_000 + o[cols[1]].to_numpy()
        df = pd.DataFrame({"g": grp, "k": key})
        within_ok = float((df.groupby("g")["k"].diff().dropna() >= 0).mean())
        rep["within_group_file_order_monotone_frac"] = within_ok
        rep["file_is_group_major"] = bool((np.diff(grp) != 0).sum() <= len(np.unique(grp)))
        order = np.lexsort((idx, o[cols[1]].to_numpy(), o[cols[0]].to_numpy()))
        rep.update(verdict="sorted_by_ordinal_columns", sorted_by=cols)
        if within_ok < 0.999:
            rep["verdict"] = "ordinal_columns_inconsistent_with_file_order"
            return None, rep
        return order, rep

    if basis == "documented_order":
        rep["sorted_by"] = None
        if raw.time is not None and chron.get("plausible_time_range"):
            lo, hi = (pd.Timestamp(x).timestamp() for x in chron["plausible_time_range"])
            t = raw.time
            m = np.isfinite(t) & (t >= lo) & (t <= hi)
            rep["time_plausible_frac"] = float(m.mean())
            if m.sum() < 1000:
                rep.update(verdict="documented_order_not_corroborated_too_few_dates")
                return None, rep
            rho = float(stats.spearmanr(idx[m][::5], t[m][::5])[0])
            rep["spearman_index_vs_date"] = rho
            rep["time_inversions_plausible"] = _inversions(t[m])
            if rho < MIN_SPEARMAN:
                rep.update(verdict="documented_order_contradicted_by_dates")
                return None, rep
            rep["verdict"] = "documented_order_corroborated_by_dates"
            return idx, rep
        rep["verdict"] = "documented_order_uncorroborated"
        return idx, rep

    rep.update(verdict=f"unknown_basis_{basis}")
    return None, rep


# --------------------------------------------------------------------------- generic checks
def class_sorted_check(y: np.ndarray) -> dict:
    """A file sorted by class has ~n_classes runs; chronology would be an artefact of sorting."""
    codes = pd.factorize(y)[0]
    runs = int((np.diff(codes) != 0).sum() + 1)
    k = len(np.unique(codes))
    p = np.bincount(codes) / len(codes)
    expected_runs = float(1 + (len(codes) - 1) * (1 - (p**2).sum()))
    return {
        "runs": runs,
        "n_classes": k,
        "expected_runs_if_shuffled": expected_runs,
        "class_sorted": bool(k > 1 and runs <= 3 * k),
    }


def exchangeability_diagnostic(y: np.ndarray, x, blocks: int = 10) -> dict:
    """Descriptive only: do class mix / features drift with position? Never a gate."""
    n = len(y)  # callers pass only the first 60% (train + dev); the locked window is never read
    b = np.minimum((np.arange(n) * blocks) // n, blocks - 1)
    tab = pd.crosstab(b, pd.factorize(y)[0])
    chi_p = float(stats.chi2_contingency(tab.to_numpy())[1]) if tab.shape[1] > 1 else None
    shift = None
    if isinstance(x, pd.DataFrame):
        num = x.select_dtypes("number")
        if num.shape[1]:
            a = num.iloc[: int(0.5 * n)]  # first half vs second half of train+dev
            z = num.iloc[int(0.5 * n) :]
            sd = a.std().replace(0, np.nan)
            sh = ((z.mean() - a.mean()).abs() / sd).dropna()
            shift = float(sh.median()) if len(sh) else None
    return {
        "class_mix_by_block_chi2_p": chi_p,
        "median_abs_std_feature_shift_first_vs_second_half_of_train_dev": shift,
    }


def leakage_screen(x, y01_train: np.ndarray, n_train: int) -> dict:
    """Flag a numeric feature that (almost) equals the target in the training window."""
    if not isinstance(x, pd.DataFrame):
        return {"max_abs_corr": None, "column": None}
    num = x.select_dtypes("number").iloc[:n_train]
    if not len(num.columns) or y01_train.std() == 0:
        return {"max_abs_corr": None, "column": None}
    c = num.apply(lambda s: s.corr(pd.Series(y01_train, index=s.index)))
    c = c.abs().dropna()
    if c.empty:
        return {"max_abs_corr": None, "column": None}
    return {"max_abs_corr": float(c.max()), "column": str(c.idxmax())}


# --------------------------------------------------------------------------- main entry
def validate(raw, entry: dict, t_ep: int = T_EP) -> dict:
    """Eligibility report. Does not read the labels of the locked window [60%, end)."""
    n = raw.n
    n15, n30, n60 = int(0.15 * n), int(TRAIN_FRAC * n), int(DEV_END_FRAC * n)
    checks = []
    # exact order -------------------------------------------------------------
    order, order_rep = resolve_order(raw, entry["chronology"])
    checks.append(
        _check(
            "chronological_order_defensible",
            order is not None,
            f"verdict={order_rep['verdict']}; declared_basis={order_rep['declared_basis']}",
        )
    )
    rep = {
        "dataset_id": entry["dataset_id"],
        "n_rows": n,
        "order": order_rep,
        "windows": {
            "train_incumbent": [0, n15],
            "train_challenger": [0, n30],
            "dev": [n30, n60],
            "locked": [n60, n],
        },
        "checks": checks,
        "status": None,
        "ok": False,
    }
    declared_n = entry.get("n_rows")
    checks.append(
        _check(
            "row_count_matches_source",
            declared_n is None or declared_n == n,
            f"declared={declared_n} loaded={n}",
            hard=False,
        )
    )
    checks.append(
        _check(
            "X_y_aligned",
            (len(raw.X) if not hasattr(raw.X, "shape") else raw.X.shape[0]) == n,
            "feature rows equal label rows",
        )
    )
    L = n - n60
    checks.append(_check("locked_window_has_one_episode", L >= t_ep, f"locked rows={L}, T={t_ep}"))
    checks.append(
        _check(
            "train_dev_windows_nonempty",
            min(n15, n30 - n15, n60 - n30) >= 200,
            f"window sizes {n15},{n30 - n15},{n60 - n30}",
        )
    )
    if order is None:
        rep["status"] = "USELESS_INELIGIBLE"
        rep["reason"] = (
            f"no defensible chronological order ({order_rep['verdict']}); no order invented"
        )
        return rep
    y = np.asarray(raw.y)[order]
    x = take(raw.X, order)
    cs = class_sorted_check(y[:n60])
    rep["class_sorted_check"] = cs
    checks.append(
        _check(
            "not_class_sorted",
            not cs["class_sorted"],
            f"runs={cs['runs']} classes={cs['n_classes']}",
        )
    )
    tr = y[:n30]
    checks.append(
        _check(
            "two_classes_in_training_window",
            len(np.unique(tr)) >= 2,
            f"{len(np.unique(tr))} classes in first 30%",
        )
    )
    if isinstance(x, pd.DataFrame):
        miss = x.isna().mean()
        bad = int((miss > MAX_MISSING_COL).sum())
        rep["missing"] = {"max_col_missing_frac": float(miss.max()), "cols_over_half_missing": bad}
        checks.append(_check("columns_not_mostly_missing", bad == 0, f"{bad} columns >50% missing"))
        const = int((x.iloc[:n30].nunique(dropna=False) <= 1).sum())
        rep["constant_columns_in_train"] = const
        checks.append(_check("has_informative_columns", const < x.shape[1], f"{const} const cols"))
    rep["exchangeability_diagnostic"] = exchangeability_diagnostic(
        y[:n60], x.iloc[:n60] if isinstance(x, pd.DataFrame) else x[:n60]
    )
    # leakage screen uses the rule-binarised training target; imported lazily (no cycle)
    import construct_model_pairs as cmp

    bin_info = cmp.binarise_info(y[:n30])
    ytr01 = (tr == bin_info["target_class"]).astype(int)
    lk = leakage_screen(x, ytr01, n30)
    rep["leakage_screen"] = lk
    checks.append(
        _check(
            "no_target_equals_feature",
            lk["max_abs_corr"] is None or lk["max_abs_corr"] < LEAK_CORR,
            f"max |corr(feature, target)|={lk['max_abs_corr']} ({lk['column']})",
        )
    )
    hard_fail = [c for c in checks if c["hard"] and not c["pass"]]
    if hard_fail:
        names = {c["check"] for c in hard_fail}
        quality = {
            "columns_not_mostly_missing",
            "has_informative_columns",
            "no_target_equals_feature",
            "two_classes_in_training_window",
        }
        rep["status"] = "USELESS_DATA_QUALITY" if names <= quality else "USELESS_INELIGIBLE"
        rep["reason"] = "; ".join(f"{c['check']}: {c['detail']}" for c in hard_fail)
        return rep
    rep["ok"] = True
    rep["order_array_length"] = len(order)
    rep["_order"] = order  # stripped before JSON serialisation by the caller
    return rep
