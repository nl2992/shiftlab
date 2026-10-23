"""Shared evaluator-label handling for population-null and pathwise harm diagnostics."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..decision_harm_experiment import POPULATION_NULL_CONTROLS


def apply_population_null_classification(metrics: pd.DataFrame) -> pd.DataFrame:
    """Separate finite-stream oracle flags from known population-null outcomes.

    The function returns a copy. In stationary and benign-nuisance controls, a sampled
    covariate path can have mean conditional cost above epsilon without changing the
    population null. Such rows remain visible through ``sample_path_material_harm`` and
    ``sample_path_harm_onset_relative``; every monitor crossing in the control is a false
    escalation, and no control row is counted as a harmful alternative.
    """
    if "scenario" not in metrics or "material_harm" not in metrics:
        raise ValueError("metrics must include scenario and material_harm columns")
    result = metrics.copy()
    if "sample_path_material_harm" not in result:
        result["sample_path_material_harm"] = result.material_harm.astype(bool)
    if "sample_path_harm_onset_relative" not in result:
        result["sample_path_harm_onset_relative"] = result.get("harm_onset_relative", np.nan)
    result["population_null_control"] = result.scenario.isin(POPULATION_NULL_CONTROLS)
    null_rows = result.population_null_control
    if not null_rows.any():
        return result

    result.loc[null_rows, "material_harm"] = False
    if "harm_onset_relative" in result:
        result.loc[null_rows, "harm_onset_relative"] = np.nan
    if "harm_reached_before_budget_stop" in result:
        result.loc[null_rows, "harm_reached_before_budget_stop"] = False

    for prefix in ("single_e", "mixture_e", "multiscale_e", "protected_e"):
        alarm_col = f"{prefix}_alarm"
        alarm_time_col = f"{prefix}_alarm_time"
        if alarm_col in result:
            alarm = result[alarm_col].fillna(False).astype(bool)
        elif alarm_time_col in result:
            alarm = result[alarm_time_col].notna()
        else:
            continue
        false_col = f"{prefix}_false_escalation"
        detected_col = f"{prefix}_detected"
        delay_col = f"{prefix}_delay"
        if false_col in result:
            result.loc[null_rows, false_col] = alarm.loc[null_rows]
        if detected_col in result:
            result.loc[null_rows, detected_col] = False
        if delay_col in result:
            result.loc[null_rows, delay_col] = np.nan
    return result
