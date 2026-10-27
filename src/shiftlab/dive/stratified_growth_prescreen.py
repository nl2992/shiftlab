"""Formula-only G1 growth screen for the frozen stratified-harm protocol.

This module evaluates caller-supplied learner slices. It generates no stream,
queries, labels, seeds, or monitor paths, and it does not select K or interpret
the resulting comparisons.
"""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np
from numpy.typing import NDArray

from .adg_growth_prescreen import (
    LearnerSlice,
    _increments,
    _joint_weights,
    unfavourable_outcome_is_positive,
)
from .stratified_harm_allocation import (
    minimax_support_allocation,
    minimax_uncapped_allocation,
)
from .stratified_harm_design import binary_outcome_probability

EPSILON = 0.10
ALPHA = 0.05
STAKE_GRID = (0.05, 0.1, 0.2, 0.4, 0.8, 1.0)
REGISTERED_BUDGETS = (0.02, 0.05, 0.10, 0.20)
REGISTERED_K = (2, 4, 8)
QUERY_FLOOR = 0.01
QUERY_CEILING = 1.0
BASE_SUPPORT = 5.1
WORKING_MEAN = 0.25


def fixed_tariff_strata(stream: LearnerSlice, K: int) -> NDArray[np.int64]:
    """Map agreement to stratum 0 and disagreement tariffs to fixed equal bins."""
    if K not in REGISTERED_K:
        raise ValueError("K must be one of the registered values 2, 4, or 8")
    deployed = np.asarray(stream.deployed)
    reference = np.asarray(stream.reference)
    tariff = np.asarray(stream.tariff, dtype=float)
    if (
        deployed.ndim != 1
        or reference.shape != deployed.shape
        or tariff.shape != deployed.shape
        or not len(deployed)
        or not np.isfinite(tariff).all()
        or not np.isin(deployed, (0, 1)).all()
        or not np.isin(reference, (0, 1)).all()
    ):
        raise ValueError("slice actions and tariffs must be matching finite vectors")
    if np.any(tariff < 0.5 - 1e-12) or np.any(tariff > 2.5 + 1e-12):
        raise ValueError("tariffs must lie in the frozen interval [0.5, 2.5]")
    boundaries = np.linspace(0.5, 2.5, K)[1:-1]
    # side='right' assigns a boundary to the higher interval; 2.5 clips to K-1.
    tariff_bin = np.searchsorted(boundaries, np.minimum(tariff, 2.5), side="right") + 1
    return np.where(deployed == reference, 0, tariff_bin).astype(np.int64)


def _validate_slice(stream: LearnerSlice) -> tuple[NDArray, ...]:
    fields = (
        np.asarray(stream.deployed),
        np.asarray(stream.reference),
        np.asarray(stream.lower, dtype=float),
        np.asarray(stream.upper, dtype=float),
        np.asarray(stream.ridge_centered, dtype=float),
        np.asarray(stream.tariff, dtype=float),
    )
    size = len(fields[0])
    if size == 0 or any(array.shape != (size,) for array in fields):
        raise ValueError("learner-slice fields must be matching nonempty vectors")
    if any(not np.isfinite(array).all() for array in fields[2:]):
        raise ValueError("support, proxy, and tariff values must be finite")
    if not np.isfinite(stream.fn) or not np.isfinite(stream.fp) or min(stream.fn, stream.fp) < 0:
        raise ValueError("costs must be finite and nonnegative")
    if np.any(fields[2] > fields[3]):
        raise ValueError("lower support must not exceed upper support")
    return fields


def _working_design_moments(
    stream: LearnerSlice, strata: NDArray[np.int64], K: int
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """Pilot A_k,C_k and frequencies under the registered centered-mean-0.25 law."""
    _, _, _, _, ridge_centered, _ = _validate_slice(stream)
    disagreement = strata != 0
    h = ridge_centered + EPSILON
    p = np.zeros(len(strata), dtype=float)
    if np.any(disagreement):
        p[disagreement] = binary_outcome_probability(
            stream.deployed[disagreement],
            stream.reference[disagreement],
            stream.fn,
            stream.fp,
            EPSILON,
            WORKING_MEAN,
        )
    z0 = stream.fp * (stream.deployed - stream.reference)
    z1 = stream.fn * (stream.reference - stream.deployed)
    z2_mean = (1 - p) * (z0 - EPSILON) ** 2 + p * (z1 - EPSILON) ** 2
    residual_mean = (1 - p) * (z0 - h) ** 2 + p * (z1 - h) ** 2
    frequencies = np.bincount(strata, minlength=K).astype(float) / len(strata)
    A = np.zeros(K, dtype=float)
    C = np.zeros(K, dtype=float)
    for k in range(1, K):
        mask = strata == k
        if np.any(mask):
            A[k] = float(np.mean(z2_mean[mask] - residual_mean[mask]))
            C[k] = float(np.mean(residual_mean[mask]))
    return A[1:], C[1:], frequencies[1:]


def _allocation_vectors(
    stream: LearnerSlice,
    strata: NDArray[np.int64],
    budget: float,
    K: int,
) -> dict[str, dict[str, NDArray[np.float64] | float]]:
    tariff = np.asarray(stream.tariff, dtype=float)
    target_spend = budget * float(np.mean(tariff))
    means = np.array(
        [float(np.mean(tariff[strata == k])) if np.any(strata == k) else 1.5 for k in range(1, K)]
    )
    frequencies = np.bincount(strata, minlength=K).astype(float)[1:] / len(strata)
    moment_A, moment_C, _ = _working_design_moments(stream, strata, K)
    L = float(np.log(K / ALPHA))
    moment_u = np.divide(
        2 * L * moment_A,
        frequencies * 0.25**2,
        out=np.zeros_like(moment_A),
        where=frequencies > 0,
    )
    moment_v = np.divide(
        2 * L * moment_C,
        frequencies * 0.25**2,
        out=np.zeros_like(moment_C),
        where=frequencies > 0,
    )
    active = frequencies > 0
    q_allocations: dict[str, NDArray[np.float64]] = {}
    for name in ("range_limited", "cap_dominated", "uncapped"):
        q = np.full(K - 1, QUERY_FLOOR, dtype=float)
        if np.any(active):
            w = frequencies[active]
            c = means[active]
            floors = np.full(np.count_nonzero(active), QUERY_FLOOR)
            caps = np.full(np.count_nonzero(active), QUERY_CEILING)
            L = float(np.log(K / ALPHA))
            if name == "range_limited":
                coefficient = BASE_SUPPORT**2 * L / 0.25**2
                solved, _ = minimax_support_allocation(
                    np.full(len(w), coefficient),
                    w,
                    c,
                    target_spend,
                    power=2,
                    floors=floors,
                    caps=caps,
                )
            elif name == "cap_dominated":
                coefficient = BASE_SUPPORT * L / (0.8 * 0.25)
                solved, _ = minimax_support_allocation(
                    np.full(len(w), coefficient),
                    w,
                    c,
                    target_spend,
                    power=1,
                    floors=floors,
                    caps=caps,
                )
            else:
                A, C, _ = _working_design_moments(stream, strata, K)
                active_A = A[active]
                active_C = C[active]
                if np.any(active_C <= 0):
                    raise ValueError("uncapped working residual moments must be positive")
                u = 2 * L * active_A / (w * 0.25**2)
                v = 2 * L * active_C / (w * 0.25**2)
                solved, _ = minimax_uncapped_allocation(
                    u,
                    v,
                    w,
                    c,
                    target_spend,
                    floors=floors,
                    caps=caps,
                )
            q[active] = solved
        q_allocations[name] = q

    result: dict[str, dict[str, NDArray[np.float64] | float]] = {}
    for name, q_disagreement in q_allocations.items():
        q = np.zeros(K, dtype=float)
        q[1:] = q_disagreement
        bounds = np.full(K, EPSILON, dtype=float)
        bounds[1:] = BASE_SUPPORT * (2.0 / q_disagreement - 1.0)
        spend = float(np.mean(np.where(strata == 0, 0.0, q[strata] * tariff)))
        result[name] = {
            "q": q,
            "bounds": bounds,
            "spend": spend,
            "target_spend": target_spend,
            "mean_tariff_by_stratum": means,
            "frequency_by_stratum": frequencies,
            "working_moment_A": moment_A,
            "working_moment_C": moment_C,
            "uncapped_u": moment_u,
            "uncapped_v": moment_v,
        }
    return result


def _working_laws(
    stream: LearnerSlice, strata: NDArray[np.int64], K: int
) -> dict[str, dict[str, object]]:
    _, _, lower, upper, _, _ = _validate_slice(stream)
    disagreement = strata != 0
    bin_count = K - 1
    positive_bins = int(np.ceil(bin_count / 3))
    positive = (strata > 0) & (strata <= positive_bins)
    rest_disagreement = disagreement & ~positive
    p_homogeneous = np.full(len(strata), 0.5, dtype=float)
    p_localized = np.full(len(strata), 0.5, dtype=float)
    p_mixed = np.full(len(strata), 0.5, dtype=float)
    y1_is_upper = unfavourable_outcome_is_positive(stream.deployed, stream.reference)
    p_homogeneous[disagreement] = 0.90
    p_localized[positive] = 0.90
    if np.any(rest_disagreement):
        p_y1_rest = binary_outcome_probability(
            stream.deployed[rest_disagreement],
            stream.reference[rest_disagreement],
            stream.fn,
            stream.fp,
            EPSILON,
            -EPSILON,
        )
        p_localized[rest_disagreement] = np.where(
            y1_is_upper[rest_disagreement], p_y1_rest, 1.0 - p_y1_rest
        )

    w_positive = float(np.mean(positive))
    w_rest = float(np.mean(rest_disagreement))
    if w_positive <= 0:
        positive_gross_mean = 0.0
    elif w_rest > 0:
        positive_gross_mean = min(4.4, (EPSILON + 0.5 * w_rest) / w_positive)
    else:
        positive_gross_mean = EPSILON / w_positive
    if w_rest > 0:
        rest_gross_mean = (EPSILON - w_positive * positive_gross_mean) / w_rest
    else:
        rest_gross_mean = np.nan
    if np.any(positive):
        z0 = stream.fp * (stream.deployed[positive] - stream.reference[positive])
        z1 = stream.fn * (stream.reference[positive] - stream.deployed[positive])
        p_y1_positive = (positive_gross_mean - z0) / (z1 - z0)
        p_mixed[positive] = np.where(y1_is_upper[positive], p_y1_positive, 1.0 - p_y1_positive)
    if np.any(rest_disagreement):
        z0 = stream.fp * (stream.deployed[rest_disagreement] - stream.reference[rest_disagreement])
        z1 = stream.fn * (stream.reference[rest_disagreement] - stream.deployed[rest_disagreement])
        p_y1_rest = (rest_gross_mean - z0) / (z1 - z0)
        p_mixed[rest_disagreement] = np.where(
            y1_is_upper[rest_disagreement], p_y1_rest, 1.0 - p_y1_rest
        )

    laws: dict[str, dict[str, object]] = {}
    for name, probability in (
        ("homogeneous_harm", p_homogeneous),
        ("localized_harm", p_localized),
        ("mixed_sign", p_mixed),
    ):
        probabilities_feasible = bool(
            np.all(np.isfinite(probability[disagreement]))
            and np.all((probability[disagreement] >= 0) & (probability[disagreement] <= 1))
        )
        expected_gross = np.where(
            disagreement,
            (1.0 - probability) * lower + probability * upper,
            0.0,
        )
        centered = expected_gross - EPSILON
        frequencies = np.bincount(strata, minlength=K).astype(float) / len(strata)
        mean_by_stratum: list[float | None] = []
        for k in range(K):
            mask = strata == k
            mean_by_stratum.append(float(np.mean(centered[mask])) if np.any(mask) else None)
        pooled_mean = float(np.mean(centered))
        feasible = probabilities_feasible
        laws[name] = {
            "probability_unfavourable": probability,
            "feasible": bool(feasible),
            "pooled_centered_mean": pooled_mean,
            "pooled_null_check": bool(pooled_mean <= 1e-12),
            "pooled_zero_mean_check": bool(abs(pooled_mean) <= 1e-12),
            "centered_mean_by_stratum": mean_by_stratum,
            "frequency_by_stratum": frequencies,
            "positive_bin_count": positive_bins,
            "positive_gross_mean": positive_gross_mean if name == "mixed_sign" else None,
            "remaining_disagreement_gross_mean": rest_gross_mean if name == "mixed_sign" else None,
        }
    return laws


def _exact_stake_growth(
    *,
    lower: NDArray,
    upper: NDArray,
    probability: NDArray,
    q: NDArray,
    anchor: NDArray,
    gated: bool,
    disagreement: NDArray,
    bound: float,
) -> tuple[NDArray[np.float64], NDArray[np.int64]]:
    """Exact event-averaged log factors; reachable zero factors remain -inf."""
    if not np.isfinite(bound) or bound <= 0:
        raise ValueError("bound must be finite and positive")
    values, q_effective = _increments(
        lower=lower,
        upper=upper,
        propensity=q,
        anchor=anchor,
        gated=gated,
        disagreement=disagreement,
        epsilon=EPSILON,
    )
    weights = _joint_weights(probability, q_effective)
    reachable = weights > 0
    rates: list[float] = []
    zeros: list[int] = []
    for stake in STAKE_GRID:
        factors = 1.0 + stake * values / bound
        if np.any(reachable & (factors < -1e-12)):
            raise ValueError("bound does not cover a reachable increment")
        factors = np.where((factors < 0) & (factors >= -1e-12), 0.0, factors)
        zero_factors = reachable & (factors == 0.0)
        zeros.append(int(np.count_nonzero(zero_factors)))
        with np.errstate(divide="ignore", invalid="ignore"):
            logs = np.log(factors)
        terms = np.zeros_like(weights, dtype=float)
        np.multiply(weights, logs, out=terms, where=reachable)
        rates.append(float(np.mean(np.sum(terms, axis=(1, 2)))))
    return np.asarray(rates), np.asarray(zeros, dtype=np.int64)


def _as_jsonable_per_stratum(
    *,
    stream: LearnerSlice,
    strata: NDArray[np.int64],
    law: dict[str, object],
    q_by_stratum: NDArray[np.float64],
    bounds_by_stratum: NDArray[np.float64],
    alpha_L: NDArray[np.float64],
) -> tuple[list[dict[str, object]], NDArray[np.float64], NDArray[np.float64]]:
    probability = np.asarray(law["probability_unfavourable"], dtype=float)
    anchor = np.asarray(stream.ridge_centered, dtype=float) + EPSILON
    frequencies = np.bincount(strata, minlength=len(q_by_stratum)).astype(float) / len(strata)
    rows: list[dict[str, object]] = []
    calendar_by_stake = np.zeros((len(q_by_stratum), len(STAKE_GRID)), dtype=float)
    zero_counts_by_stratum = np.zeros((len(q_by_stratum), len(STAKE_GRID)), dtype=np.int64)
    for k in range(len(q_by_stratum)):
        mask = strata == k
        if not np.any(mask):
            conditional = np.zeros(len(STAKE_GRID), dtype=float)
            zeros = np.zeros(len(STAKE_GRID), dtype=np.int64)
        elif k == 0:
            conditional, zeros = _exact_stake_growth(
                lower=np.zeros(np.count_nonzero(mask)),
                upper=np.zeros(np.count_nonzero(mask)),
                probability=np.full(np.count_nonzero(mask), 0.5),
                q=np.zeros(np.count_nonzero(mask)),
                anchor=np.zeros(np.count_nonzero(mask)),
                gated=True,
                disagreement=np.zeros(np.count_nonzero(mask), dtype=bool),
                bound=float(bounds_by_stratum[k]),
            )
        else:
            conditional, zeros = _exact_stake_growth(
                lower=np.asarray(stream.lower)[mask],
                upper=np.asarray(stream.upper)[mask],
                probability=probability[mask],
                q=np.full(np.count_nonzero(mask), q_by_stratum[k]),
                anchor=anchor[mask],
                gated=False,
                disagreement=np.ones(np.count_nonzero(mask), dtype=bool),
                bound=float(bounds_by_stratum[k]),
            )
        calendar = frequencies[k] * conditional
        calendar_by_stake[k] = calendar
        zero_counts_by_stratum[k] = zeros
        best = int(np.argmax(calendar))
        rows.append(
            {
                "stratum": k,
                "frequency": float(frequencies[k]),
                "q": float(q_by_stratum[k]),
                "bound": float(bounds_by_stratum[k]),
                "alpha_L": float(alpha_L[k]),
                "conditional_stake_growths": calendar_to_list(conditional),
                "calendar_stake_growths": calendar_to_list(calendar),
                "best_stake": float(STAKE_GRID[best]),
                "best_calendar_growth": float(calendar[best]),
                "reachable_zero_factors_by_stake": zeros.tolist(),
            }
        )
    return rows, calendar_by_stake, zero_counts_by_stratum


def calendar_to_list(values: Iterable[float]) -> list[float]:
    """Convert numeric rates to plain Python floats while preserving infinities."""
    return [float(value) for value in values]


def _pooled_growth(
    *,
    stream: LearnerSlice,
    strata: NDArray[np.int64],
    law: dict[str, object],
    q_by_stratum: NDArray[np.float64],
    bound: float,
    anchor_mode: str,
    gated: bool,
) -> tuple[NDArray[np.float64], NDArray[np.int64], NDArray[np.float64]]:
    probability = np.asarray(law["probability_unfavourable"], dtype=float)
    disagreement = strata != 0
    q = q_by_stratum[strata]
    if anchor_mode == "ridge":
        anchor = np.asarray(stream.ridge_centered, dtype=float) + EPSILON
    elif anchor_mode == "zero":
        anchor = np.zeros(len(strata), dtype=float)
    else:
        raise ValueError("unknown anchor mode")
    rates, zeros = _exact_stake_growth(
        lower=np.asarray(stream.lower, dtype=float),
        upper=np.asarray(stream.upper, dtype=float),
        probability=probability,
        q=q,
        anchor=anchor,
        gated=gated,
        disagreement=disagreement,
        bound=bound,
    )
    strata_rates = np.zeros((len(q_by_stratum), len(STAKE_GRID)), dtype=float)
    for k in range(len(q_by_stratum)):
        mask = strata == k
        if np.any(mask):
            local, _ = _exact_stake_growth(
                lower=np.asarray(stream.lower)[mask],
                upper=np.asarray(stream.upper)[mask],
                probability=probability[mask],
                q=q[mask],
                anchor=anchor[mask],
                gated=gated,
                disagreement=disagreement[mask],
                bound=bound,
            )
            weight = float(np.mean(mask))
            strata_rates[k] = weight * local
    return rates, zeros, strata_rates


def _row(
    *,
    budget: float,
    K: int,
    allocation: str,
    law_name: str,
    arm: str,
    q: NDArray[np.float64],
    bounds: NDArray[np.float64],
    spend: float,
    target_spend: float,
    alpha_L: NDArray[np.float64],
    per_stratum: list[dict[str, object]],
    calendar_by_stake: NDArray[np.float64],
    zeros_by_stratum: NDArray[np.int64],
    law: dict[str, object],
    extra: dict[str, object] | None = None,
) -> dict[str, object]:
    flat_rates = calendar_by_stake.reshape(-1)
    finite_rates = flat_rates[np.isfinite(flat_rates)]
    max_component_growth = float(np.max(finite_rates)) if len(finite_rates) else float("-inf")
    best_index = int(np.argmax(np.max(calendar_by_stake, axis=0)))
    row = {
        "budget_rate": float(budget),
        "K": int(K),
        "allocation": allocation,
        "working_law": law_name,
        "arm": arm,
        "feasible": bool(law["feasible"]),
        "pooled_centered_mean": float(law["pooled_centered_mean"]),
        "pooled_null_check": bool(law["pooled_null_check"]),
        "pooled_zero_mean_check": bool(law["pooled_zero_mean_check"]),
        "expected_spend": float(spend),
        "target_spend": float(target_spend),
        "spend_within_target": bool(spend <= target_spend + 1e-12),
        "q_by_stratum": q.tolist(),
        "bound_by_stratum": bounds.tolist(),
        "alpha_L_by_stratum": alpha_L.tolist(),
        "finite_alpha_penalty_by_stratum": alpha_L.tolist(),
        "stakes": list(STAKE_GRID),
        "stake_mixture_weights": [1.0 / len(STAKE_GRID)] * len(STAKE_GRID),
        "stake_calendar_rates": calendar_by_stake.tolist(),
        "selected_stake": float(STAKE_GRID[best_index]),
        "max_component_growth": max_component_growth,
        "per_stratum": per_stratum,
        "reachable_zero_factors_by_stratum": zeros_by_stratum.tolist(),
    }
    if extra:
        row.update(extra)
    return row


def evaluate_slice(stream: LearnerSlice, budget: float, K: int) -> list[dict[str, object]]:
    """Return exact expected-growth rows for one supplied learner slice.

    ``budget`` is the frozen rate ``r``; expected dollar target is
    ``r * mean(validation tariff)``. The routine evaluates only G1 working laws
    and fixed formulas. It does not draw data or choose among K, allocations,
    laws, or arms.
    """
    if budget not in REGISTERED_BUDGETS:
        raise ValueError("budget must be one of the registered rates 0.02, 0.05, 0.10, 0.20")
    _, _, lower, upper, _, tariff = _validate_slice(stream)
    strata = fixed_tariff_strata(stream, K)
    disagreement = strata != 0
    laws = _working_laws(stream, strata, K)
    allocations = _allocation_vectors(stream, strata, budget, K)
    target_spend = budget * float(np.mean(tariff))
    alpha_L = np.full(K, np.log(K / ALPHA), dtype=float)
    rows: list[dict[str, object]] = []
    frequencies = np.bincount(strata, minlength=K).astype(float) / len(strata)
    disagreement_tariff_spend = float(np.mean(np.where(disagreement, tariff, 0.0)))
    q_d_gated = (
        1.0
        if disagreement_tariff_spend <= 0
        else min(1.0, target_spend / disagreement_tariff_spend)
    )
    q_d_gated = max(QUERY_FLOOR, q_d_gated) if np.any(disagreement) else QUERY_FLOOR
    q_d_proportional = q_d_gated

    for allocation_name, design in allocations.items():
        q = np.asarray(design["q"], dtype=float)
        bounds = np.asarray(design["bounds"], dtype=float)
        spend = float(design["spend"])
        common_bound = float(np.max(bounds))
        common_bounds = np.full(K, common_bound, dtype=float)
        q_proportional = np.zeros(K, dtype=float)
        q_proportional[1:] = q_d_proportional
        bounds_proportional = np.full(K, EPSILON, dtype=float)
        bounds_proportional[1:] = BASE_SUPPORT * (2.0 / q_d_proportional - 1.0)
        spend_proportional = float(
            np.mean(np.where(disagreement, q_proportional[strata] * tariff, 0.0))
        )

        q_gated = np.zeros(K, dtype=float)
        q_gated[1:] = q_d_gated
        bound_gated = 5.0 / q_d_gated + EPSILON
        bound_uniform = BASE_SUPPORT * (2.0 / budget - 1.0)
        q_uniform = np.full(K, budget, dtype=float)
        bounds_uniform = np.full(K, bound_uniform, dtype=float)
        q_full = np.zeros(K, dtype=float)
        q_full[1:] = 1.0
        bounds_full = np.full(K, BASE_SUPPORT, dtype=float)
        bounds_full[0] = EPSILON
        pooled_alpha_L = np.full(K, np.log(1.0 / ALPHA), dtype=float)

        for law_name, law in laws.items():
            probability = np.asarray(law["probability_unfavourable"], dtype=float)
            feasible = bool(law["feasible"])
            if not feasible:
                # Preserve the infeasible target probabilities in the report; do not clip them.
                for arm_name in (
                    "stratified_candidate",
                    "chugg_subgroup_composition",
                    "stratified_common_bound",
                    "stratified_proportional_query",
                    "pooled_same_query_global_bound",
                    "pooled_uniform_correct_bound_U1",
                    "gated_pooled_HT_G1f",
                    "full_feedback",
                    "oracle_strata_upper",
                ):
                    rows.append(
                        {
                            "budget_rate": float(budget),
                            "K": int(K),
                            "allocation": allocation_name,
                            "working_law": law_name,
                            "arm": arm_name,
                            "feasible": False,
                            "pooled_centered_mean": float(law["pooled_centered_mean"]),
                            "pooled_null_check": bool(law["pooled_null_check"]),
                            "pooled_zero_mean_check": bool(law["pooled_zero_mean_check"]),
                            "expected_spend": float(spend),
                            "target_spend": float(target_spend),
                            "spend_within_target": bool(spend <= target_spend + 1e-12),
                            "q_by_stratum": q.tolist(),
                            "bound_by_stratum": bounds.tolist(),
                            "alpha_L_by_stratum": alpha_L.tolist(),
                            "working_moment_A": np.asarray(design["working_moment_A"]).tolist(),
                            "working_moment_C": np.asarray(design["working_moment_C"]).tolist(),
                            "uncapped_u": np.asarray(design["uncapped_u"]).tolist(),
                            "uncapped_v": np.asarray(design["uncapped_v"]).tolist(),
                            "infeasible_probability_values": probability[disagreement].tolist(),
                        }
                    )
                continue

            base_per_stratum, base_calendar, base_zeros = _as_jsonable_per_stratum(
                stream=stream,
                strata=strata,
                law=law,
                q_by_stratum=q,
                bounds_by_stratum=bounds,
                alpha_L=alpha_L,
            )
            # Independent same-q, same-score, same-bound subgroup betting calculation.
            chugg_per_stratum: list[dict[str, object]] = []
            chugg_calendar = np.zeros_like(base_calendar)
            chugg_zeros = np.zeros_like(base_zeros)
            for k in range(K):
                mask = strata == k
                if not np.any(mask):
                    conditional = np.zeros(len(STAKE_GRID), dtype=float)
                    zeros = np.zeros(len(STAKE_GRID), dtype=np.int64)
                elif k == 0:
                    conditional = np.asarray(
                        [np.log1p(-stake) if stake < 1.0 else float("-inf") for stake in STAKE_GRID]
                    )
                    zeros = np.asarray(
                        [2 * np.count_nonzero(mask) if stake == 1.0 else 0 for stake in STAKE_GRID],
                        dtype=np.int64,
                    )
                else:
                    # Independent formula: construct the query/outcome atoms directly.
                    atom_logs: list[float] = []
                    zeros_list: list[int] = []
                    for stake in STAKE_GRID:
                        mass = np.count_nonzero(mask)
                        local_logs = np.zeros(mass, dtype=float)
                        zero_count = 0
                        for i, event in enumerate(np.flatnonzero(mask)):
                            p = float(probability[event])
                            qi = float(q[k])
                            d0 = float(lower[event])
                            d1 = float(upper[event])
                            h = float(stream.ridge_centered[event] + EPSILON)
                            atoms = (
                                ((1 - p) * (1 - qi), h - EPSILON),
                                (p * (1 - qi), h - EPSILON),
                                ((1 - p) * qi, h + (d0 - h) / qi - EPSILON),
                                (p * qi, h + (d1 - h) / qi - EPSILON),
                            )
                            expected = 0.0
                            for mass_atom, value in atoms:
                                if mass_atom <= 0:
                                    continue
                                factor = 1 + stake * value / float(bounds[k])
                                if factor < -1e-12:
                                    raise ValueError(
                                        "Chugg bound does not cover a reachable increment"
                                    )
                                factor = max(0.0, factor)
                                if factor == 0.0:
                                    zero_count += 1
                                    expected = float("-inf")
                                    break
                                expected += mass_atom * float(np.log(factor))
                            local_logs[i] = expected
                        atom_logs.append(float(np.mean(local_logs)))
                        zeros_list.append(zero_count)
                    conditional = np.asarray(atom_logs)
                    zeros = np.asarray(zeros_list, dtype=np.int64)
                calendar = frequencies[k] * conditional
                chugg_calendar[k] = calendar
                chugg_zeros[k] = zeros
                best = int(np.argmax(calendar))
                chugg_per_stratum.append(
                    {
                        "stratum": k,
                        "frequency": float(frequencies[k]),
                        "q": float(q[k]),
                        "bound": float(bounds[k]),
                        "alpha_L": float(alpha_L[k]),
                        "conditional_stake_growths": calendar_to_list(conditional),
                        "calendar_stake_growths": calendar_to_list(calendar),
                        "best_stake": float(STAKE_GRID[best]),
                        "best_calendar_growth": float(calendar[best]),
                        "reachable_zero_factors_by_stake": zeros.tolist(),
                    }
                )
            finite_pair = np.isfinite(base_calendar) & np.isfinite(chugg_calendar)
            same_infinity = (
                np.isinf(base_calendar)
                & np.isinf(chugg_calendar)
                & (np.signbit(base_calendar) == np.signbit(chugg_calendar))
            )
            if not np.all(finite_pair | same_infinity):
                identity_error = float("inf")
            else:
                identity_error = float(
                    np.max(np.abs(base_calendar[finite_pair] - chugg_calendar[finite_pair]))
                    if np.any(finite_pair)
                    else 0.0
                )
            if identity_error > 1e-12:
                raise RuntimeError("stratified candidate and Chugg composition rates differ")
            rows.append(
                _row(
                    budget=budget,
                    K=K,
                    allocation=allocation_name,
                    law_name=law_name,
                    arm="stratified_candidate",
                    q=q,
                    bounds=bounds,
                    spend=spend,
                    target_spend=target_spend,
                    alpha_L=alpha_L,
                    per_stratum=base_per_stratum,
                    calendar_by_stake=base_calendar,
                    zeros_by_stratum=base_zeros,
                    law=law,
                    extra={"stratum_ids": strata.tolist(), "identity_error": identity_error},
                )
            )
            rows.append(
                _row(
                    budget=budget,
                    K=K,
                    allocation=allocation_name,
                    law_name=law_name,
                    arm="chugg_subgroup_composition",
                    q=q,
                    bounds=bounds,
                    spend=spend,
                    target_spend=target_spend,
                    alpha_L=alpha_L,
                    per_stratum=chugg_per_stratum,
                    calendar_by_stake=chugg_calendar,
                    zeros_by_stratum=chugg_zeros,
                    law=law,
                    extra={"identity_error": identity_error},
                )
            )

            for arm_name, arm_q, arm_bounds, arm_spend in (
                ("stratified_common_bound", q, common_bounds, spend),
                (
                    "stratified_proportional_query",
                    q_proportional,
                    bounds_proportional,
                    spend_proportional,
                ),
            ):
                per_stratum, calendar, zeros = _as_jsonable_per_stratum(
                    stream=stream,
                    strata=strata,
                    law=law,
                    q_by_stratum=arm_q,
                    bounds_by_stratum=arm_bounds,
                    alpha_L=alpha_L,
                )
                rows.append(
                    _row(
                        budget=budget,
                        K=K,
                        allocation=allocation_name,
                        law_name=law_name,
                        arm=arm_name,
                        q=arm_q,
                        bounds=arm_bounds,
                        spend=arm_spend,
                        target_spend=target_spend,
                        alpha_L=alpha_L,
                        per_stratum=per_stratum,
                        calendar_by_stake=calendar,
                        zeros_by_stratum=zeros,
                        law=law,
                    )
                )

            pooled_specs = (
                (
                    "pooled_same_query_global_bound",
                    q,
                    np.full(K, common_bound),
                    spend,
                    common_bound,
                    "ridge",
                    True,
                ),
                (
                    "pooled_uniform_correct_bound_U1",
                    q_uniform,
                    bounds_uniform,
                    float(np.mean(q_uniform[strata] * tariff)),
                    bound_uniform,
                    "ridge",
                    False,
                ),
                (
                    "gated_pooled_HT_G1f",
                    q_gated,
                    np.full(K, bound_gated),
                    float(np.mean(np.where(disagreement, q_gated[strata] * tariff, 0.0))),
                    bound_gated,
                    "zero",
                    True,
                ),
                (
                    "full_feedback",
                    q_full,
                    bounds_full,
                    float(np.mean(np.where(disagreement, tariff, 0.0))),
                    BASE_SUPPORT,
                    "ridge",
                    True,
                ),
            )
            full_feedback_per_stratum = None
            for (
                arm_name,
                arm_q,
                arm_bounds,
                arm_spend,
                global_bound,
                anchor_mode,
                gated,
            ) in pooled_specs:
                pooled_rates, pooled_zeros, per_stratum_rates = _pooled_growth(
                    stream=stream,
                    strata=strata,
                    law=law,
                    q_by_stratum=arm_q,
                    bound=global_bound,
                    anchor_mode=anchor_mode,
                    gated=gated,
                )
                per_stratum = [
                    {
                        "stratum": k,
                        "frequency": float(frequencies[k]),
                        "q": float(arm_q[k]),
                        "bound": float(arm_bounds[k]),
                        "alpha_L": float(pooled_alpha_L[k]),
                        "calendar_stake_growths": calendar_to_list(per_stratum_rates[k]),
                        "best_calendar_growth": float(np.max(per_stratum_rates[k])),
                    }
                    for k in range(K)
                ]
                calendar = np.tile(pooled_rates, (K, 1)) / K
                for k in range(K):
                    calendar[k] = per_stratum_rates[k]
                zeros_by_stratum = np.zeros((K, len(STAKE_GRID)), dtype=np.int64)
                zeros_by_stratum[-1] = pooled_zeros
                if arm_name == "full_feedback":
                    full_feedback_per_stratum = per_stratum_rates.copy()
                rows.append(
                    _row(
                        budget=budget,
                        K=K,
                        allocation=allocation_name,
                        law_name=law_name,
                        arm=arm_name,
                        q=arm_q,
                        bounds=arm_bounds,
                        spend=arm_spend,
                        target_spend=target_spend,
                        alpha_L=pooled_alpha_L,
                        per_stratum=per_stratum,
                        calendar_by_stake=calendar,
                        zeros_by_stratum=zeros_by_stratum,
                        law=law,
                        extra={
                            "pooled_global_stake_rates": pooled_rates.tolist(),
                            "pooled_global_bound": float(global_bound),
                            "pooled_zero_factor_count_by_stake": pooled_zeros.tolist(),
                            "selected_stake": float(STAKE_GRID[int(np.argmax(pooled_rates))]),
                            "max_component_growth": float(np.max(pooled_rates)),
                            "label_matched": arm_name != "full_feedback",
                        },
                    )
                )

            if full_feedback_per_stratum is None:
                raise RuntimeError("full-feedback reference was not evaluated")
            harm_indices = [
                k
                for k, mean in enumerate(law["centered_mean_by_stratum"])
                if mean is not None and mean > 0
            ]
            if harm_indices:
                oracle_rates = np.max(full_feedback_per_stratum[harm_indices], axis=0)
                oracle_per_stratum = [
                    {
                        "strata_known_harmful_to_oracle": harm_indices,
                        "full_feedback_component_calendar_rates_by_stake": oracle_rates.tolist(),
                    }
                ]
                oracle_q = q_full
                oracle_bounds = bounds_full
            else:
                oracle_rates = np.zeros(len(STAKE_GRID), dtype=float)
                oracle_per_stratum = [{"strata_known_harmful_to_oracle": []}]
                oracle_q = q_full
                oracle_bounds = bounds_full
            oracle_calendar = np.zeros((K, len(STAKE_GRID)), dtype=float)
            oracle_calendar[0] = oracle_rates
            rows.append(
                _row(
                    budget=budget,
                    K=K,
                    allocation=allocation_name,
                    law_name=law_name,
                    arm="oracle_strata_upper",
                    q=oracle_q,
                    bounds=oracle_bounds,
                    spend=float(np.mean(np.where(disagreement, tariff, 0.0))),
                    target_spend=target_spend,
                    alpha_L=alpha_L,
                    per_stratum=oracle_per_stratum,
                    calendar_by_stake=oracle_calendar,
                    zeros_by_stratum=np.zeros((K, len(STAKE_GRID)), dtype=np.int64),
                    law=law,
                    extra={
                        "oracle_harmful_strata": harm_indices,
                        "label_matched": False,
                        "alpha_L_by_stratum": alpha_L.tolist(),
                    },
                )
            )
    return rows
