"""Fixed-horizon policy selection for aggregate randomized headline experiments."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.sparse import vstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold

RISK_START = pd.Timestamp("2013-06-24")
RISK_END = pd.Timestamp("2014-01-11")
RESPONSE_FIELDS = ("clicks", "impressions")


@dataclass
class FittedCTRPolicy:
    vectorizer: TfidfVectorizer
    model: LogisticRegression
    c_value: float

    def predict(self, texts: Iterable[str]) -> np.ndarray:
        matrix = self.vectorizer.transform(list(texts))
        return self.model.predict_proba(matrix)[:, 1]


def package_text(frame: pd.DataFrame) -> list[str]:
    """Use only headline and excerpt, which are displayed before package selection."""
    headline = frame["headline"].fillna("").astype(str)
    excerpt = frame["excerpt"].fillna("").astype(str)
    return [f"headline {h} excerpt {e}" for h, e in zip(headline, excerpt, strict=True)]


def filter_eligible_tests(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """Exclude risk-window tests and malformed arms without splitting a test."""
    required = {
        "created_at",
        "clickability_test_id",
        "headline",
        "excerpt",
        "impressions",
        "clicks",
    }
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"Missing policy-evaluation columns: {missing}")
    data = frame.copy()
    if data["clickability_test_id"].isna().any():
        raise ValueError("Missing experiment IDs are not permitted")
    created = pd.to_datetime(data["created_at"], format="mixed", errors="coerce")
    if created.isna().any():
        raise ValueError("Unparseable created_at value")
    risk_arm = created.dt.normalize().between(RISK_START, RISK_END, inclusive="both")
    if "Problem" in data.columns:
        raw_problem = data["Problem"]
        if pd.api.types.is_bool_dtype(raw_problem):
            problem = raw_problem.fillna(False)
        else:
            problem = (
                raw_problem.astype("string").str.strip().str.lower().isin({"1", "true", "yes", "y"})
            )
        risk_arm |= problem
    risk_tests = set(data.loc[risk_arm, "clickability_test_id"].unique())
    eligible = data.loc[~data["clickability_test_id"].isin(risk_tests)].copy()

    impressions = pd.to_numeric(eligible["impressions"], errors="coerce")
    clicks = pd.to_numeric(eligible["clicks"], errors="coerce")
    valid_arm = (
        impressions.notna()
        & clicks.notna()
        & (impressions > 0)
        & (clicks >= 0)
        & (clicks <= impressions)
        & (impressions % 1 == 0)
        & (clicks % 1 == 0)
    )
    invalid_tests = set(eligible.loc[~valid_arm, "clickability_test_id"].unique())
    eligible = eligible.loc[~eligible["clickability_test_id"].isin(invalid_tests)].copy()
    eligible["impressions"] = impressions.loc[eligible.index].astype("int64")
    eligible["clicks"] = clicks.loc[eligible.index].astype("int64")
    arm_counts = eligible.groupby("clickability_test_id", sort=False).size()
    singleton_tests = set(arm_counts.index[arm_counts < 2])
    eligible = eligible.loc[~eligible["clickability_test_id"].isin(singleton_tests)].copy()
    counts = {
        "input_tests": int(data["clickability_test_id"].nunique()),
        "risk_window_tests": len(risk_tests),
        "invalid_count_tests": len(invalid_tests),
        "singleton_tests": len(singleton_tests),
        "eligible_tests": int(eligible["clickability_test_id"].nunique()),
        "eligible_arms": len(eligible),
    }
    return eligible.reset_index(drop=True), counts


def _fit_vectorizer(texts: list[str]) -> tuple[TfidfVectorizer, object]:
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2), min_df=3, max_features=50_000, sublinear_tf=True
    )
    matrix = vectorizer.fit_transform(texts)
    if matrix.shape[1] == 0:
        raise ValueError("No usable text vocabulary in training data")
    return vectorizer, matrix


def _fit_model(
    matrix: object, clicks: np.ndarray, impressions: np.ndarray, c_value: float
) -> LogisticRegression:
    positives = clicks.astype(np.float64)
    negatives = (impressions - clicks).astype(np.float64)
    response = np.concatenate(
        [np.ones(len(clicks), dtype=np.int8), np.zeros(len(clicks), dtype=np.int8)]
    )
    weights = np.concatenate([positives, negatives])
    expanded = vstack([matrix, matrix], format="csr")
    model = LogisticRegression(C=c_value, solver="liblinear", max_iter=1000, random_state=20261026)
    model.fit(expanded, response, sample_weight=weights)
    return model


def select_package_indices(frame: pd.DataFrame, predictions: np.ndarray) -> np.ndarray:
    """Choose the highest predicted CTR per test; deterministic text tie break."""
    if len(frame) != len(predictions):
        raise ValueError("Prediction and package counts differ")
    chosen: list[int] = []
    texts = package_text(frame)
    for indices in frame.groupby("clickability_test_id", sort=False).indices.values():
        index_array = np.asarray(indices, dtype=np.int64)
        scores = predictions[index_array]
        best = np.flatnonzero(scores == scores.max())
        winner = min(
            (int(index_array[position]) for position in best),
            key=lambda idx: (texts[idx], idx),
        )
        chosen.append(winner)
    return np.asarray(chosen, dtype=np.int64)


def equal_test_contrasts(frame: pd.DataFrame, predictions: np.ndarray) -> pd.DataFrame:
    """Return aggregate-only per-test selected-minus-uniform CTR contrasts."""
    data = frame.reset_index(drop=True).copy()
    data["ctr"] = data["clicks"] / data["impressions"]
    selected = select_package_indices(data, predictions)
    groups = data.groupby("clickability_test_id", sort=False)
    if len(selected) != groups.ngroups:
        raise ValueError("Policy did not select exactly one package per test")
    records: list[dict[str, float | int | str]] = []
    if "test_week" in data:
        weeks = data.groupby("clickability_test_id", sort=False)["test_week"].first()
    else:
        weeks = pd.Series(-1, index=groups.size().index)
    for test_id, group in groups:
        group_indices = group.index.to_numpy(dtype=np.int64)
        chosen_index = int(selected[len(records)])
        chosen_ctr = float(data.loc[chosen_index, "ctr"])
        ref_ctr = float(group["ctr"].mean())
        total_impressions = int(group["impressions"].sum())
        records.append(
            {
                "clickability_test_id": str(test_id),
                "test_week": int(weeks.loc[test_id]),
                "selected_ctr": chosen_ctr,
                "uniform_reference_ctr": ref_ctr,
                "delta_ctr": chosen_ctr - ref_ctr,
                "total_impressions": total_impressions,
                "selected_impressions": int(data.loc[chosen_index, "impressions"]),
                "n_arms": len(group_indices),
                "best_arm_ctr_evaluator_only": float(group["ctr"].max()),
            }
        )
    return pd.DataFrame.from_records(records)


def tune_and_fit(
    frame: pd.DataFrame, *, c_grid: tuple[float, ...] = (0.01, 0.1, 1.0, 10.0)
) -> tuple[FittedCTRPolicy, dict[str, float]]:
    """Select C by grouped CV policy value, then fit one frozen development policy."""
    groups = frame["clickability_test_id"].to_numpy()
    if np.unique(groups).size < 5:
        raise ValueError("At least five training experiments are required for grouped CV")
    splitter = GroupKFold(n_splits=5)
    cv_values: dict[float, list[float]] = {c: [] for c in c_grid}
    for train_idx, validation_idx in splitter.split(frame, groups=groups):
        train = frame.iloc[train_idx].reset_index(drop=True)
        validation = frame.iloc[validation_idx].reset_index(drop=True)
        vectorizer, train_matrix = _fit_vectorizer(package_text(train))
        validation_matrix = vectorizer.transform(package_text(validation))
        for c_value in c_grid:
            model = _fit_model(
                train_matrix,
                train["clicks"].to_numpy(),
                train["impressions"].to_numpy(),
                c_value,
            )
            prediction = model.predict_proba(validation_matrix)[:, 1]
            contrasts = equal_test_contrasts(validation, prediction)
            cv_values[c_value].extend(contrasts["delta_ctr"].tolist())
    cv_means = {c: float(np.mean(values)) for c, values in cv_values.items()}
    selected_c = max(c_grid, key=lambda c: (cv_means[c], -c))
    vectorizer, train_matrix = _fit_vectorizer(package_text(frame))
    model = _fit_model(
        train_matrix,
        frame["clicks"].to_numpy(),
        frame["impressions"].to_numpy(),
        selected_c,
    )
    return FittedCTRPolicy(vectorizer, model, selected_c), {str(c): cv_means[c] for c in c_grid}


def week_cluster_bootstrap(
    contrasts: pd.DataFrame, *, n_bootstrap: int = 10_000, seed: int = 20261026
) -> dict[str, float | int]:
    """Paired percentile intervals from week-cluster resampling."""
    if n_bootstrap < 100 or contrasts.empty:
        raise ValueError("Need at least 100 replicates and nonempty contrasts")
    grouped = contrasts.groupby("test_week", sort=False)
    weeks = list(grouped.indices)
    if len(weeks) < 2:
        raise ValueError("At least two week clusters are required")
    delta_sum = grouped["delta_ctr"].sum().reindex(weeks).to_numpy(dtype=np.float64)
    selected_sum = grouped["selected_ctr"].sum().reindex(weeks).to_numpy(dtype=np.float64)
    reference_sum = grouped["uniform_reference_ctr"].sum().reindex(weeks).to_numpy(dtype=np.float64)
    counts = grouped.size().reindex(weeks).to_numpy(dtype=np.float64)
    rng = np.random.default_rng(seed)
    choices = rng.integers(0, len(weeks), size=(n_bootstrap, len(weeks)))
    multiplicity = np.zeros((n_bootstrap, len(weeks)), dtype=np.float64)
    rows = np.arange(n_bootstrap)[:, None]
    np.add.at(multiplicity, (np.broadcast_to(rows, choices.shape), choices), 1.0)
    denom = multiplicity @ counts
    boot_delta = multiplicity @ delta_sum / denom
    boot_selected = multiplicity @ selected_sum / denom
    boot_reference = multiplicity @ reference_sum / denom
    return {
        "week_clusters": len(weeks),
        "bootstrap_replicates": n_bootstrap,
        "seed": seed,
        "delta_ci_95": [
            float(np.quantile(boot_delta, 0.025)),
            float(np.quantile(boot_delta, 0.975)),
        ],
        "delta_one_sided_lower_95": float(np.quantile(boot_delta, 0.05)),
        "selected_ctr_ci_95": [
            float(np.quantile(boot_selected, 0.025)),
            float(np.quantile(boot_selected, 0.975)),
        ],
        "uniform_ctr_ci_95": [
            float(np.quantile(boot_reference, 0.025)),
            float(np.quantile(boot_reference, 0.975)),
        ],
    }
