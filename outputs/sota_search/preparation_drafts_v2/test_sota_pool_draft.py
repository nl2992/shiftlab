import importlib.util
from pathlib import Path

import numpy as np
import pytest

spec = importlib.util.spec_from_file_location("pool_draft", Path(__file__).with_name("sota_pool_draft.py"))
draft = importlib.util.module_from_spec(spec)
spec.loader.exec_module(draft)


def test_staged_updates_query_only_unique_selected_labels_and_preserve_budget():
    x = np.arange(24, dtype=float)[:, None]
    groups = np.arange(24) % 2
    labels = groups * 0.5 + 0.2
    seen = set()

    def request(indices):
        assert not seen.intersection(indices)
        seen.update(indices)
        return labels[list(indices)]

    model = draft.RunningMeanPredictor()
    result = draft.staged_pool(x, groups, stages=3, labels_per_cell=2,
                              predictor=model, request_labels=request, seed=3)
    assert result["labels_used"] == model.count == len(seen) == 12
    # Residuals are constant within each group, so the correction is exact even
    # while the predictor changes between stages.
    assert result["estimate"] == pytest.approx(labels.mean())
    assert all(row["inclusion_probability"] == 0.5 for row in result["sampling_records"])


def test_infeasible_pool_contract_is_rejected_before_any_label_request():
    def forbidden(indices):
        raise AssertionError("no labels should be requested for an invalid plan")

    with pytest.raises(ValueError, match="unsupported contract"):
        draft.staged_pool(np.zeros((5, 1)), np.arange(5), stages=1, labels_per_cell=2,
                          predictor=draft.RunningMeanPredictor(), request_labels=forbidden, seed=1)
