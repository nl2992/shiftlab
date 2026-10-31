import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_mechanism_check_smoke(tmp_path):
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/run_atlas_mechanism_check_v1.py"),
            "--T",
            "100",
            "--n-seeds",
            "4",
            "--workers",
            "4",
            "--out",
            str(tmp_path),
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=ROOT,
        timeout=300,
    )
    assert r.returncode == 0, r.stderr[-2000:]
    res = json.loads((tmp_path / "results.json").read_text("utf-8"))
    assert res["seeds"] == [280000, 280004]
    for k in (
        "check1_straddle_repair",
        "check2_straddle_delay_prediction",
        "check3_triggered_kelly_neutral_arm",
    ):
        assert isinstance(res[k]["pass"], bool)
    text = (tmp_path / "summary.md").read_text("utf-8")
    assert "PASS" in text or "FAIL" in text
