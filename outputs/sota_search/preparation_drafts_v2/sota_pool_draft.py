"""SOURCE_INSPIRED_BASELINE staged pool sampling with known inclusion weights.

PAI-inspired, not the published PAI algorithm. Full covariate-pool access is
explicit. Stage partitions are fixed before labels. Within each observed stratum,
labels are simple-random without replacement. Predictor updates use earlier-stage
labels only, so each current-stage residual correction is design-unbiased.
No confidence interval or sequential-monitoring guarantee is claimed.
"""

import numpy as np


class RunningMeanPredictor:
    def __init__(self, initial=0.5):
        self.initial = float(initial)
        self.total, self.count = 0.0, 0

    def predict(self, features):
        return np.full(len(features), self.total / self.count if self.count else self.initial)

    def update(self, features, labels):
        self.total += float(np.asarray(labels).sum())
        self.count += len(labels)


def staged_pool(features, groups, *, stages, labels_per_cell, predictor, request_labels, seed):
    x, group = np.asarray(features, float), np.asarray(groups)
    if x.ndim != 2 or group.shape != (len(x),) or not np.isfinite(x).all():
        raise ValueError("finite feature pool and aligned observed groups required")
    if type(stages) is not int or stages < 1 or type(labels_per_cell) is not int or labels_per_cell < 1:
        raise ValueError("positive stage and within-cell label counts required")
    if stages > len(x):
        raise ValueError("more stages than pool observations")
    rng = np.random.default_rng(seed)
    plan = []
    # Verify all strata and reserve the complete label count before requesting any
    # labels. No outcome-dependent early truncation changes inclusion weights.
    for stage in np.array_split(np.arange(len(x)), stages):
        cells = [stage[group[stage] == value] for value in np.unique(group[stage])]
        if any(len(cell) < labels_per_cell for cell in cells):
            raise ValueError("unsupported contract: a pool cell is smaller than its label quota")
        plan.append((stage, cells))
    estimates, records = [], []
    for stage_number, (stage, cells) in enumerate(plan):
        proxy = np.asarray(predictor.predict(x[stage]), float)
        if proxy.shape != (len(stage),) or not np.isfinite(proxy).all():
            raise ValueError("predictor must return finite current-stage proxy values")
        stage_sum = float(proxy.sum())
        selected_all, labels_all = [], []
        for cell in cells:
            selected = np.sort(rng.choice(cell, labels_per_cell, replace=False))
            observed = np.asarray(request_labels(tuple(int(i) for i in selected)), float)
            if observed.shape != (len(selected),) or not np.isfinite(observed).all():
                raise ValueError("one observed finite label per requested index required")
            propensity = len(selected) / len(cell)
            local = np.searchsorted(stage, selected)
            stage_sum += float(((observed - proxy[local]) / propensity).sum())
            selected_all.extend(selected.tolist())
            labels_all.extend(observed.tolist())
            records.append({
                "stage": stage_number, "stratum_size": len(cell),
                "queried_indices": selected.tolist(), "inclusion_probability": propensity,
            })
        estimates.append(stage_sum)
        # Updating happens only after the entire current-stage estimator is frozen.
        predictor.update(x[selected_all], np.array(labels_all))
    return {
        "estimate": sum(estimates) / len(x),
        "labels_used": sum(len(r["queried_indices"]) for r in records),
        "sampling_records": records, "stage_estimated_sums": estimates,
        "contract": "fixed_stage_stratified_uniform_without_replacement_pool",
        "uncertainty": None,
    }
