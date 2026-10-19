"""Native torch group reduction for WILDS platforms lacking compiled torch_scatter wheels.

Only the arithmetic group mean is adapted. WILDS' own metric definitions, grouping,
empty-group handling, metric names and evaluation code remain authoritative. No package
globals or installed dependency files are modified.
"""

from types import FunctionType


def native_group_average(values, groups, n_groups):
    import torch

    if values.numel() != groups.numel() or values.device != groups.device:
        raise ValueError("WILDS group values and indices must match")
    sums = values.new_zeros(n_groups).scatter_add_(0, groups, values.reshape(-1))
    counts = torch.bincount(groups, minlength=n_groups).float()
    averages = sums / counts.to(values.dtype).clamp_min(1)
    return averages, counts


def evaluate_without_scatter(dataset, predictions, targets, metadata):
    from wilds.common.metrics.metric import ElementwiseMetric

    evaluator = dataset.eval.__func__
    namespace = dict(evaluator.__globals__)
    replacements = 0
    for name, klass in list(namespace.items()):
        if not isinstance(klass, type) or not issubclass(klass, ElementwiseMetric):
            continue
        method = klass._compute_group_wise
        if "avg_over_groups" not in method.__code__.co_names:
            continue
        group_method = FunctionType(
            method.__code__,
            {**method.__globals__, "avg_over_groups": native_group_average},
            method.__name__,
            method.__defaults__,
            method.__closure__,
        )
        namespace[name] = type(
            f"NativeGrouped{klass.__name__}", (klass,), {"_compute_group_wise": group_method}
        )
        replacements += 1
    if replacements == 0:
        # A metric without arithmetic group reduction needs no compatibility adaptation.
        return dataset.eval(predictions, targets, metadata)
    function = FunctionType(
        evaluator.__code__,
        namespace,
        evaluator.__name__,
        evaluator.__defaults__,
        evaluator.__closure__,
    )
    function.__kwdefaults__ = evaluator.__kwdefaults__
    result, description = function(dataset, predictions, targets, metadata)
    return (
        result,
        description
        + "\nGroup means used torch-native scatter_add (equivalent arithmetic; compiled torch_scatter unavailable).",
    )
