"""Versioned contracts. Nullable real times mean unknown, never fabricated availability."""

from typing import Literal

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SCHEMA_VERSION = "1.1.0"
TIMES = [
    "event_time",
    "feature_available_time",
    "prediction_time",
    "label_event_time",
    "label_available_time",
]


class SyntheticConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scenario: str = "iid_regression"
    n: int = Field(default=5000, ge=100)
    d: int = Field(default=4, ge=2)
    seed: int = Field(default=42, ge=0)
    change_fraction: float = Field(default=0.5, gt=0, lt=1)
    severity: float = Field(default=1.0, ge=0, le=5)
    noise: float = Field(default=0.3, gt=0)
    delay: int = Field(default=0, ge=0)
    missing: float = Field(default=0.0, ge=0, le=1)
    rho: float = Field(default=0.6, gt=-0.99, lt=0.99)
    pattern: Literal[
        "abrupt",
        "multiple",
        "linear",
        "sigmoid",
        "recurring",
        "hmm",
        "seasonal",
        "temporary",
        "variable_dwell",
        "oblivious_adversarial",
    ] = "abrupt"
    regimes: int = Field(default=2, ge=1, le=20)
    review_period: int = Field(default=100, ge=2)
    transition_fraction: float = Field(default=0.1, gt=0, lt=0.5)
    device: Literal["cpu", "cuda", "auto"] = "auto"
    dtype: Literal["float32", "float64"] = "float64"
    chunk_size: int = Field(default=10000, ge=16)
    memory_mb: int = Field(default=512, ge=16)
    output: str = "data"
    train_fraction: float = Field(default=0.2, gt=0, lt=1)
    validation_fraction: float = Field(default=0.1, gt=0, lt=1)
    calibration_fraction: float = Field(default=0.1, gt=0, lt=1)

    @field_validator(
        "n",
        "d",
        "seed",
        "change_fraction",
        "severity",
        "noise",
        "delay",
        "missing",
        "rho",
        "regimes",
        "review_period",
        "transition_fraction",
        "chunk_size",
        "memory_mb",
        "train_fraction",
        "validation_fraction",
        "calibration_fraction",
        mode="before",
    )
    @classmethod
    def reject_boolean_parameters(cls, value):
        if isinstance(value, (bool, np.bool_)):
            raise ValueError(  # noqa: TRY004 - Pydantic turns this into a consistent ValidationError
                "Boolean values are not valid numeric configuration parameters"
            )
        return value

    @model_validator(mode="after")
    def validate_numeric_and_split_configuration(self):
        numeric_fields = (
            "n",
            "d",
            "seed",
            "change_fraction",
            "severity",
            "noise",
            "delay",
            "missing",
            "rho",
            "regimes",
            "review_period",
            "transition_fraction",
            "chunk_size",
            "memory_mb",
            "train_fraction",
            "validation_fraction",
            "calibration_fraction",
        )
        if any(not np.isfinite(getattr(self, name)) for name in numeric_fields):
            raise ValueError("Numeric configuration parameters must be finite")
        if self.train_fraction + self.validation_fraction + self.calibration_fraction >= 1:
            raise ValueError("Training, validation and calibration fractions must sum below one")
        return self


class DatasetTaskSpec(BaseModel):
    """Machine-checked task contract stored with every newly published dataset."""

    model_config = ConfigDict(extra="forbid")
    task_id: str
    task_kind: str
    target_definition: str
    forecast_horizon: dict | None
    valid_target_mask: str
    evaluation_metrics: list[str]
    label_availability_rule: str
    utility_provenance: str


class Manifest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: str = SCHEMA_VERSION
    dataset: str
    version: str
    publisher: str
    source_url: str
    citation: str
    license: str
    permitted_use: str
    acquired_at: str
    retrieval_parameters: dict = Field(default_factory=dict)
    raw_checksums: dict[str, str] = Field(default_factory=dict)
    processing_config: dict = Field(default_factory=dict)
    task_specs: list[DatasetTaskSpec] = Field(default_factory=list)
    code_commit: str | None = None
    source_hash: str
    n_observations: int
    feature_names: list[str]
    feature_dtype: str = "float64"
    feature_kind: Literal["numeric", "structured_reference"] = "numeric"
    time_coverage: list[str | None]
    domains: list[str]
    missingness: dict[str, float]
    limitations: list[str]
    ground_truth: Literal["synthetic_known", "none", "coarse_domains"]
    files: dict[str, str]
    oracle_file: str | None = None
    environment: dict = Field(default_factory=dict)


def validate_frame(frame: pd.DataFrame) -> dict:
    """Validate standardized rows without inferring missing real-world timestamps."""
    required = [
        "sample_id",
        "entity_id",
        *TIMES,
        "features",
        "target",
        "domain_id",
        "regime_id",
        "decision_context",
        "sample_weight",
        "split",
        "metadata",
    ]
    absent = set(required) - set(frame.columns)
    if absent:
        raise ValueError(f"Missing columns: {sorted(absent)}")
    if frame.sample_id.isna().any() or frame.sample_id.duplicated().any():
        raise ValueError("sample_id must be unique and present")
    if (
        "feature_reference" in frame
        and frame.feature_reference.notna().any()
        and frame.feature_reference.isna().any()
    ):
        raise ValueError("Structured-reference datasets require one reference per observation")
    if not frame.split.isin(["train", "validation", "calibration", "test", "unassigned"]).all():
        raise ValueError("Invalid split")
    numeric_times = {}
    for column in TIMES:
        values = pd.to_numeric(frame[column], errors="coerce")
        malformed = frame[column].notna() & values.isna()
        if malformed.any():
            raise ValueError(f"{column} must be numeric when known")
        known = values.notna()
        if (~np.isfinite(values.loc[known].to_numpy(dtype=float))).any():
            raise ValueError(f"{column} must be finite when known")
        numeric_times[column] = values
    for early, late in [
        ("event_time", "feature_available_time"),
        ("feature_available_time", "prediction_time"),
        ("label_event_time", "label_available_time"),
    ]:
        mask = numeric_times[early].notna() & numeric_times[late].notna()
        if (numeric_times[early].loc[mask] > numeric_times[late].loc[mask]).any():
            raise ValueError(f"Invalid ordering: {early} > {late}")
    target = pd.to_numeric(frame.target, errors="coerce")
    if (frame.target.notna() & target.isna()).any():
        raise ValueError("target must be numeric when known")
    if np.isinf(target.dropna().to_numpy(dtype=float)).any():
        raise ValueError("target must be finite when known")
    feature_rows = [np.asarray(value, dtype=float) for value in frame.features]
    if feature_rows:
        if any(row.ndim != 1 for row in feature_rows):
            raise ValueError("features must be one-dimensional numeric vectors")
        if any(row.shape != feature_rows[0].shape for row in feature_rows[1:]):
            raise ValueError("feature vectors must have a consistent dimension")
        if any(np.isinf(row).any() for row in feature_rows):
            raise ValueError("features must be finite or missing")
    weights_numeric = pd.to_numeric(frame.sample_weight, errors="coerce")
    if (frame.sample_weight.notna() & weights_numeric.isna()).any():
        raise ValueError("sample_weight must be numeric when known")
    if np.isinf(weights_numeric.dropna().to_numpy(dtype=float)).any():
        raise ValueError("sample_weight must be finite when known")
    weights = weights_numeric.dropna()
    if (weights < 0).any():
        raise ValueError("negative sample weights")
    order = ["train", "validation", "calibration", "test"]
    previous_end = None
    for split in order:
        times = frame.loc[frame.split == split, "prediction_time"].dropna()
        if len(times):
            if previous_end is not None and times.min() <= previous_end:
                raise ValueError("Chronological splits overlap or are reversed")
            previous_end = times.max()
    return {
        "rows": len(frame),
        "unknown_prediction_times": int(frame.prediction_time.isna().sum()),
        "unknown_label_availability": int(frame.label_available_time.isna().sum()),
        "missing_targets": int(frame.target.isna().sum()),
    }
