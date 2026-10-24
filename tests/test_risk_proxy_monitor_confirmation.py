import hashlib
import json

from shiftlab.dive.risk_proxy_monitor_confirmation import (
    METHODS,
    run_risk_proxy_monitor_confirmation,
)


def test_independent_monitor_confirmation_cpu_smoke_writes_verified_outputs(tmp_path):
    metrics, manifest = run_risk_proxy_monitor_confirmation(
        tmp_path,
        null_seeds=2,
        alternative_seeds=2,
        seed_offset=20405024,
        n=1200,
        device="cpu",
    )

    assert set(metrics.method.unique()) == set(METHODS)
    assert len(metrics) == (2 * 2 + 2 * 2) * len(METHODS)
    assert metrics.groupby(["scenario", "seed"]).labels_queried.nunique().max() == 1
    assert metrics.groupby(["scenario", "seed"]).realized_label_spend.nunique().max() == 1
    saved_manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    saved_digest = hashlib.sha256((tmp_path / "metrics.parquet").read_bytes()).hexdigest()
    assert saved_manifest["metrics_sha256"] == saved_digest
    assert manifest["independent_of_development_seed_blocks"]
    assert saved_manifest["decision"]["null_calibration_pass"] is False
