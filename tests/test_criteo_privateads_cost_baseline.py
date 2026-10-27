from __future__ import annotations

import numpy as np
import pyarrow as pa

from scripts.evaluate_criteo_privateads_cost_baseline import (
    HASH_BUCKETS_PER_FIELD,
    TARGET_CTR,
    _splitmix64,
    feature_contract,
    fit_intercept,
    negative_case_control_weight,
    prepare_batch,
    write_artifact_checksums,
)


def test_feature_contract_keeps_only_publisher_available_groups() -> None:
    fields: list[pa.Field] = []
    groups = (
        ("features_kv_bits_constrained_", 31),
        ("features_kv_not_constrained_", 8),
        ("features_browser_bits_constrained_", 11),
        ("features_ctx_not_constrained_", 8),
    )
    remaining_float = 44
    remaining_integer = 13
    for prefix, count in groups:
        for index in range(count):
            if prefix == "features_ctx_not_constrained_" and index == 2:
                dtype = pa.list_(pa.int64())
            elif remaining_float:
                dtype = pa.float64()
                remaining_float -= 1
            else:
                dtype = pa.int64()
                remaining_integer -= 1
            fields.append(pa.field(f"{prefix}{index}", dtype))
    fields.extend(pa.field(f"features_not_available_{i}", pa.float64()) for i in range(80))

    numeric, categorical, list_field = feature_contract(pa.schema(fields))

    assert len(numeric) == 44
    assert len(categorical) == 13
    assert list_field == "features_ctx_not_constrained_2"


def test_negative_case_control_weight_maps_sample_rate_to_target_ctr() -> None:
    sample_ctr = 0.364
    weight = negative_case_control_weight(sample_ctr, TARGET_CTR)
    adjusted_ctr = sample_ctr / (sample_ctr + (1 - sample_ctr) * weight)
    assert np.isclose(adjusted_ctr, TARGET_CTR)


def test_splitmix_hash_is_stable_and_field_specific() -> None:
    values = np.array([0, 17, 2**32 - 1], dtype=np.uint64)
    first = _splitmix64(values, 0)
    assert np.array_equal(first, _splitmix64(values, 0))
    assert np.all((first > 0) & (first < HASH_BUCKETS_PER_FIELD))
    assert not np.array_equal(first, _splitmix64(values, 1))


def test_prepare_batch_handles_null_numeric_and_multi_value_categories() -> None:
    batch = pa.record_batch(
        [
            pa.array([1.0, None, 3.0], type=pa.float64()),
            pa.array([10, None, 20], type=pa.int64()),
            pa.array([[7, 8], None, []], type=pa.list_(pa.int64())),
            pa.array([0, 1, 0], type=pa.int32()),
        ],
        names=["continuous", "category", "category_list", "is_clicked"],
    )

    numeric, codes, rows, labels = prepare_batch(
        batch,
        ["continuous"],
        ["category"],
        "category_list",
        np.array([2.0]),
        np.array([1.0]),
    )

    assert numeric.shape == (3, 2)
    assert np.allclose(numeric[:, 0], [-1.0, -2.0, 1.0])
    assert np.array_equal(numeric[:, 1], [0.0, 1.0, 0.0])
    assert codes.size == 7
    assert rows.size == codes.size
    assert np.array_equal(labels, [0.0, 1.0, 0.0])
    assert np.count_nonzero(rows == 0) == 3
    assert np.count_nonzero(rows == 1) == 2
    assert np.count_nonzero(rows == 2) == 2


def test_intercept_recalibration_matches_weighted_sample_prevalence() -> None:
    sample_ctr = 0.3
    labels = np.array([1.0] * 30 + [0.0] * 70)
    weights = np.where(
        labels > 0.5,
        1.0,
        negative_case_control_weight(sample_ctr, TARGET_CTR),
    )
    logits = np.linspace(-2.0, 2.0, labels.size)
    offset = fit_intercept(logits, labels, weights)
    prediction = 1.0 / (1.0 + np.exp(-np.clip(logits + offset, -35, 35)))
    weighted_prediction = np.average(prediction, weights=weights)
    weighted_prevalence = np.average(labels, weights=weights)
    assert np.isclose(weighted_prediction, weighted_prevalence, atol=1e-7)


def test_artifact_checksums_cover_aggregate_files_and_avoid_self_reference(tmp_path) -> None:
    artifact = tmp_path / "summary.csv"
    artifact.write_text("n,value\n2,0.5\n", encoding="utf-8")

    result = write_artifact_checksums(tmp_path)

    assert result["files"]["summary.csv"]["bytes"] == artifact.stat().st_size
    assert len(result["files"]["summary.csv"]["sha256"]) == 64
    assert "artifact_checksums.json" not in result["files"]
