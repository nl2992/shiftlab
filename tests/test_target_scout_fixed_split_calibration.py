"""Numerical checks for the prespecified familywise null-calibration bound."""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from scipy.stats import binom

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from calibrate_target_scout_fixed_split import upper_cp
from compare_target_scout_fixed_split import (
    BUDGET_RATE,
    _make_config,
    _stream_for_seed,
)
from confirm_target_scout_fixed_split import run as run_confirmation

from shiftlab.dive.budgeted_promotion import (
    _monitor_family,
    _monitor_scout_context_policy,
    _monitor_validation_context_policy,
)


def test_zero_false_promotions_have_simultaneous_upper_bound_below_five_percent() -> None:
    per_stratum_alpha = 0.05 / 27
    upper = upper_cp(0, 1000, per_stratum_alpha)
    assert upper == pytest.approx(0.00628, abs=0.00002)
    assert upper <= 0.05
    assert binom.cdf(0, 1000, upper) == pytest.approx(per_stratum_alpha, rel=1e-9)


def test_exact_upper_bound_uses_observed_false_promotions() -> None:
    alpha = 0.05 / 27
    upper = upper_cp(10, 1000, alpha)
    assert upper > 10 / 1000
    assert binom.cdf(10, 1000, upper) == pytest.approx(alpha, rel=1e-9)


def test_confirmation_refuses_to_run_when_calibration_gate_fails(tmp_path: Path) -> None:
    calibration = tmp_path / "calibration.json"
    calibration.write_text(
        '{"experiment":"target_scout_fixed_split_exact_rule_null_calibration",'
        '"inference":{"pass":false}}',
        encoding="utf-8",
    )
    output = tmp_path / "confirmation"
    with pytest.raises(RuntimeError, match="calibration did not pass"):
        run_confirmation(
            seeds=300,
            seed_offset=99_010_000,
            device="cuda",
            calibration=calibration,
            output=output,
        )
    assert not output.exists()


def test_oracle_truth_cannot_change_selection_or_certification() -> None:
    config = _make_config(
        n=1200,
        d=16,
        seed=441_009,
        prevalence=0.5,
        signal=0.05,
        error=0.1,
        device="cpu",
    )
    scenario = SimpleNamespace(
        name="candidate_context_heterogeneity",
        fn_cost=5.0,
        fp_cost=1.0,
        harmful_adaptation=False,
    )
    family, y, uniforms, _ = _stream_for_seed(
        seed=441_009,
        config=config,
        device="cpu",
        scenario=scenario,
    )
    oracle_corrupted = dict(family)
    oracle_corrupted["h_truth"] = np.full_like(family["h_truth"], 999.0)

    def observable_decisions(candidate_family: dict[str, object]) -> list[tuple[object, ...]]:
        pooled = _monitor_family(
            family=candidate_family,
            y=y,
            scenario=scenario,
            config=config,
            query_name="uniform",
            budget_rate=BUDGET_RATE,
            estimator="direct_ipw",
            query_uniforms=uniforms,
            bound_mode="global",
            monitoring_rule="fixed_mixture",
        )[0]
        fixed = _monitor_validation_context_policy(
            family=candidate_family,
            y=y,
            scenario=scenario,
            config=replace(config, include_validation_context_policy=True).validate(),
            query_name="uniform",
            budget_rate=BUDGET_RATE,
            query_uniforms=uniforms,
        )
        scout = _monitor_scout_context_policy(
            family=candidate_family,
            y=y,
            scenario=scenario,
            config=replace(config, include_scout_context_policy=True).validate(),
            query_name="uniform",
            budget_rate=BUDGET_RATE,
            query_uniforms=uniforms,
        )
        return [
            (
                row["candidate_id"],
                bool(row["promoted"]),
                int(row["labels_queried"]),
                int(row["monitor_events_processed"]),
                row["stop_reason"],
            )
            for row in (pooled, fixed, scout)
        ]

    assert observable_decisions(family) == observable_decisions(oracle_corrupted)


@pytest.mark.parametrize("events,trials,alpha", [(-1, 10, 0.05), (11, 10, 0.05), (0, 0, 0.05)])
def test_invalid_exact_interval_arguments_raise(events: int, trials: int, alpha: float) -> None:
    with pytest.raises(ValueError):
        upper_cp(events, trials, alpha)
