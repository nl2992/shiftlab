import importlib.util
import itertools
from pathlib import Path

import numpy as np
import pytest

spec = importlib.util.spec_from_file_location("fixed_block_draft", Path(__file__).with_name("sota_fixed_block_draft.py"))
draft = importlib.util.module_from_spec(spec)
spec.loader.exec_module(draft)


@pytest.mark.parametrize("reliance", [0, 0.25, 1])
def test_exact_design_unbiasedness_over_all_without_replacement_partitions(reliance):
    outcomes = np.array([0.05, 0.2, 0.7, 0.95, 0.1])
    proxy = np.array([0.9, 0.8, 0.2, 0.1, 0.5])
    estimates = []
    for subset in itertools.combinations(range(5), 2):
        estimate = draft.completed_block(proxy, subset, outcomes[list(subset)], reliance=reliance)
        estimates.append(estimate.estimate)
        assert -reliance <= estimate.estimate <= 1 + reliance
    assert np.mean(estimates) == pytest.approx(outcomes.mean())


def test_hard_cap_reserves_complete_blocks_including_pending_labels():
    plan = draft.feasible_complete_blocks(horizon=512, block_size=20, labels_per_block=4, total_labels=101)
    assert plan["labels_reserved"] == 100
    assert plan["events_used"] == 500
    assert plan["unused_event_tail"] == 12
    assert plan["unused_label_budget"] == 1


def test_unqueried_losses_are_not_an_estimator_argument_and_duplicates_refused():
    proxy = np.linspace(0, 1, 10)
    indices = draft.choose_indices(10, 2, seed=4)
    assert len(set(indices)) == 2
    with pytest.raises(ValueError, match="subset"):
        draft.completed_block(proxy, [1, 1], [0.2, 0.3], reliance=1)
    with pytest.raises(ValueError, match="each labeled"):
        draft.completed_block(proxy, indices, np.ones(10), reliance=1)
