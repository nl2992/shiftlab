"""Offline domain summaries and train-only classification evidence, not drift attribution."""

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


def group_summaries(frame, feature_names):
    X = np.stack(frame.features.to_numpy())
    if X.shape[1] != len(feature_names):
        raise ValueError("Feature names do not match observations")
    feature_rows, label_rows = [], []
    for domain in frame.domain_id.drop_duplicates():
        mask = (frame.domain_id == domain).to_numpy()
        for j, name in enumerate(feature_names):
            values = X[mask, j]
            finite = values[np.isfinite(values)]
            feature_rows.append(
                {
                    "domain": domain,
                    "feature": name,
                    "rows": int(mask.sum()),
                    "missing_rate": float(np.isnan(values).mean()),
                    "infinite_count": int(np.isinf(values).sum()),
                    "mean": float(finite.mean()) if len(finite) else None,
                    "std_population": float(finite.std()) if len(finite) else None,
                    "min": float(finite.min()) if len(finite) else None,
                    "max": float(finite.max()) if len(finite) else None,
                }
            )
        labels = frame.loc[mask, "target"]
        for value, count in labels.value_counts(dropna=False).items():
            label_rows.append(
                {
                    "domain": domain,
                    "label": value,
                    "count": int(count),
                    "fraction": float(count / len(labels)),
                    "rows": len(labels),
                }
            )
    return pd.DataFrame(feature_rows), pd.DataFrame(label_rows)


def fit_offline_classifier(frame):
    """Only training rows fit imputation, scaling and regularized multinomial logits.

    No domain ID or batch index enters the feature matrix. This retrospective model
    does not assume that historical availability times were observed in real time.
    """
    X = np.stack(frame.features.to_numpy())
    y = frame.target.to_numpy(dtype=float)
    train = (frame.split == "train").to_numpy() & np.isfinite(y)
    if train.sum() < 20 or len(np.unique(y[train])) < 2:
        raise ValueError("Need at least 20 labeled training rows and two training classes")
    if np.isinf(X).any():
        raise ValueError("Infinite features require an explicit source cleaning policy")
    model = make_pipeline(
        SimpleImputer(keep_empty_features=True),
        StandardScaler(),
        LogisticRegression(C=1.0, max_iter=2000, random_state=42),
    )
    model.fit(X[train], y[train])
    return model.predict_proba(X), model.classes_


def classification_group_evidence(frame, probabilities, classes, cost_matrix=None):
    """Group metrics for fixed predictions; costs are explicitly research-imposed.

    The cost matrix is indexed action,true class. No confidence interval is claimed
    when within-domain dependence and ordering are unknown. SE below is descriptive
    under an IID working assumption, which may be inappropriate for sensor batches.
    """
    p, classes = np.asarray(probabilities), np.asarray(classes)
    if p.shape != (len(frame), len(classes)) or not len(classes):
        raise ValueError("Probability shape disagrees with frame/classes")
    if len(np.unique(classes)) != len(classes):
        raise ValueError("Classes must be unique")
    if not np.isfinite(p).all() or (p < 0).any() or not np.allclose(p.sum(axis=1), 1):
        raise ValueError("Require finite probability vectors")
    k = len(classes)
    costs = np.ones((k, k)) - np.eye(k) if cost_matrix is None else np.asarray(cost_matrix)
    if costs.shape != (k, k) or not np.isfinite(costs).all() or (costs < 0).any():
        raise ValueError("Require finite nonnegative action-by-class costs")
    prediction = classes[p.argmax(axis=1)]
    action = (p @ costs.T).argmin(axis=1)
    rows = []
    y = frame.target.to_numpy()
    for (domain, split), group in frame.groupby(["domain_id", "split"], sort=False):
        # Use stable row positions rather than relying on a caller's DataFrame index.
        mask = ((frame.domain_id == domain) & (frame.split == split)).to_numpy() & np.isfinite(y)
        pos = np.flatnonzero(mask)
        if not len(pos):
            continue
        known = np.isin(y[pos], classes)
        correct = prediction[pos] == y[pos]
        brier, decision_loss, log_losses = [], [], []
        for row in pos:
            matches = np.flatnonzero(classes == y[row])
            if not len(matches):
                continue  # Unknown-class probability/loss must not be invented.
            index = matches[0]
            onehot = (np.arange(k) == index).astype(float)
            brier.append(np.sum((p[row] - onehot) ** 2))
            decision_loss.append(costs[action[row], index])
            log_losses.append(-np.log(max(p[row, index], np.finfo(float).tiny)))
        accuracy = float(correct.mean())
        rows.append(
            {
                "domain": domain,
                "split": split,
                "n": len(pos),
                "accuracy": accuracy,
                "accuracy_iid_descriptive_se": float(np.sqrt(accuracy * (1 - accuracy) / len(pos))),
                "unseen_training_class_count": int((~known).sum()),
                "multiclass_brier_known_classes": float(np.mean(brier)) if brier else None,
                "log_loss_known_classes": float(np.mean(log_losses)) if log_losses else None,
                "decision_loss_known_classes": float(np.mean(decision_loss))
                if decision_loss
                else None,
                "utility_origin": "synthetically imposed action-by-class matrix",
                "evaluation": "training apparent fit"
                if split == "train"
                else "held-out domain diagnostic",
                "uncertainty": "IID descriptive SE only; unknown within-domain dependence, no CI guarantee",
                "attribution": "inconclusive: class mix, selection and domain effects may confound",
            }
        )
    return pd.DataFrame(rows)
