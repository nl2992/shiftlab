"""Draft fixed-count random-partition PPI comparator contract.

This differs from published PPRM's independent disjoint pools and is therefore
a SOURCE_INSPIRED_BASELINE adaptation. It repairs random empty-block and hard-cap
truncation ambiguity without claiming the original method's complete guarantee.
All label selection occurs before any true block label is revealed.
"""

import numpy as np

from shiftlab.dive.pprm_risk_monitor import prediction_powered_batch_risk


def choose_indices(pool_size, labels, *, seed):
    if type(pool_size) is not int or type(labels) is not int or not 0 < labels < pool_size:
        raise ValueError("require a nonempty labeled and unlabeled block partition")
    return tuple(sorted(np.random.default_rng(seed).choice(pool_size, labels, replace=False).tolist()))


def completed_block(proxy_losses, labeled_indices, observed_losses, *, reliance):
    """Estimate pool risk with no unqueried true loss argument.

    Given a simple-random size-n subset L chosen independently of the potential
    outcomes, E[mean_L(Y-eta H)] = mean_pool(Y-eta H), and the complement's proxy
    average has expectation mean_pool(H). Thus this estimate is design-unbiased
    for the finite-pool mean for every fixed/past-predictable eta, even with
    heterogeneous rows. This identity alone is not a sequential validity theorem.
    """
    proxies = np.asarray(proxy_losses, dtype=float)
    observed = np.asarray(observed_losses, dtype=float)
    indices = tuple(labeled_indices)
    if proxies.ndim != 1 or len(proxies) < 2:
        raise ValueError("nonempty one-dimensional proxy pool required")
    if not indices or len(indices) >= len(proxies) or len(set(indices)) != len(indices):
        raise ValueError("labeled indices must form a proper nonempty subset")
    if any(type(i) is not int or not 0 <= i < len(proxies) for i in indices):
        raise ValueError("invalid labeled index")
    if observed.shape != (len(indices),):
        raise ValueError("one observed label loss is required for each labeled index")
    unlabeled = np.ones(len(proxies), dtype=bool)
    unlabeled[list(indices)] = False
    return prediction_powered_batch_risk(
        observed, proxies[list(indices)], proxies[unlabeled], reliance=reliance
    )


def feasible_complete_blocks(*, horizon, block_size, labels_per_block, total_labels):
    values = (horizon, block_size, labels_per_block, total_labels)
    if any(type(x) is not int or x < 0 for x in values):
        raise ValueError("nonnegative integer counts required")
    if block_size < 2 or not 0 < labels_per_block < block_size:
        raise ValueError("proper block partition required")
    count = min(horizon // block_size, total_labels // labels_per_block)
    return {"complete_blocks": count, "events_used": count * block_size,
            "labels_reserved": count * labels_per_block,
            "unused_event_tail": horizon - count * block_size,
            "unused_label_budget": total_labels - count * labels_per_block}
