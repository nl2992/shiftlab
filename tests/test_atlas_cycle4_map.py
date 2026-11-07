import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_cycle4_map_smoke(tmp_path):
    cmd = [
        sys.executable,
        str(ROOT / "scripts/run_atlas_cycle4_map_v1.py"),
        "--T", "80", "--n-seeds", "3", "--n-f1", "5", "--n-f2", "3",
        "--workers", "4", "--out", str(tmp_path),
    ]  # fmt: skip
    r = subprocess.run(cmd, check=False, capture_output=True, text=True, cwd=ROOT, timeout=120)
    assert r.returncode == 0, r.stderr[-2000:]
    res = json.loads((tmp_path / "results.json").read_text("utf-8"))
    assert res["seeds"] == [100000, 100003]
    for k in ("P1", "P2", "H_TK2"):
        assert isinstance(res[k]["pass"], bool)
    assert set(res["family"]) == {"1", "2"}
    n_lines = len((tmp_path / "checkpoint.jsonl").read_text("utf-8").splitlines())
    # resume: second run does no new work
    r2 = subprocess.run(cmd, check=False, capture_output=True, text=True, cwd=ROOT, timeout=120)
    assert r2.returncode == 0, r2.stderr[-2000:]
    assert len((tmp_path / "checkpoint.jsonl").read_text("utf-8").splitlines()) == n_lines
    assert "todo=0" in (tmp_path / "run.log").read_text("utf-8")
    assert "PASS" in (tmp_path / "summary.md").read_text("utf-8") or "FAIL" in (
        tmp_path / "summary.md"
    ).read_text("utf-8")
