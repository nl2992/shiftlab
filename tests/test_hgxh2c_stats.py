import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy.stats import beta

from shiftlab.hgxh2c import freeze as fz
from shiftlab.hgxh2c.stats import (
    COLUMNS,
    clopper_pearson,
    frontier,
    holm,
    intersection_union,
    paired_cluster_bootstrap,
    summarise,
)  # fmt: skip

ROOT = Path(__file__).resolve().parents[1]


def test_clopper_pearson():
    lo, hi = clopper_pearson(5, 100)
    assert lo == pytest.approx(beta.ppf(0.025, 5, 96)) and hi == pytest.approx(
        beta.ppf(0.975, 6, 95)
    )
    assert clopper_pearson(0, 10)[0] == 0 and clopper_pearson(0, 10)[1] == pytest.approx(
        0.3085, abs=1e-3
    )
    assert clopper_pearson(10, 10)[1] == 1


def test_bootstrap_known_difference():
    rng = np.random.default_rng(1)
    rows = [(c, s, rng.normal(10 + c, 1)) for c in range(12) for s in range(80)]
    df = pd.DataFrame(rows, columns=["cell_id", "seed", "b"])
    df["a"] = df["b"] - 0.5 + rng.normal(0, 0.5, len(df))  # gain = b - a = 0.5
    r = paired_cluster_bootstrap(df, "a", "b", n_boot=500)
    assert r["lo"] < 0.5 < r["hi"] and r["p_one_sided"] < 0.01
    df["a"] = df["b"] + rng.normal(0, 0.5, len(df))
    assert paired_cluster_bootstrap(df, "a", "b", n_boot=500)["p_one_sided"] > 0.05


def test_holm_and_iu():
    adj = holm({"a": 0.01, "b": 0.04, "c": 0.03, "d": 0.005})
    assert adj == pytest.approx({"d": 0.02, "a": 0.03, "c": 0.06, "b": 0.06})
    assert intersection_union({"x": {"p_one_sided": 0.01}, "y": {"p_one_sided": 0.2}}) == {
        "pass_": False,
        "p": 0.2,
    }


def _tbl():
    rows = []
    for m, jc, pw, far in [("good", 1.0, 1.0, 0.0), ("dom", 2.0, 0.5, 0.0), ("cheap", 0.5, 0.2, 0.0),
                           ("invalid", 0.1, 1.0, 1.0), ("cusum_x", 0.9, 0.9, 0.0)]:  # fmt: skip
        for s in range(40):
            h = s < int(pw * 40)
            rows.append(
                (
                    m,
                    "h",
                    "coshift",
                    s,
                    "dev",
                    50,
                    60 if h else -1,
                    60 if h else -1,
                    60 if h else -1,
                    10,
                    jc,
                    0,
                    False,
                    False,
                    0.0,
                )
            )
            fa = s < int(far * 40)
            rows.append(
                (
                    m,
                    "n",
                    "null_stationary",
                    s,
                    "dev",
                    -1,
                    10 if fa else -1,
                    10 if fa else -1,
                    10 if fa else -1,
                    10,
                    jc,
                    0,
                    True,
                    True,
                    0.0,
                )
            )
    return pd.DataFrame(rows, columns=COLUMNS)


REG = {
    m: {"track": "C", "fidelity": "TASK_ADAPTED", "notes": ""}
    for m in ("good", "dom", "cheap", "invalid", "cusum_x")
}


def test_frontier_track_filter_and_references():
    s = _tbl()
    t = s[s.method_id.isin(["good", "cheap"])].copy()
    t["method_id"] = t.method_id.map({"good": "wrongtrack", "cheap": "tenzer_x"})
    s = summarise(pd.concat([s, t]), T=1000)
    reg = {**REG, "wrongtrack": {"track": "B", "fidelity": "TASK_ADAPTED", "notes": ""},
           "tenzer_x": {"track": "C", "fidelity": "SOURCE_INSPIRED", "notes": "DIFFERENT_NULL: lr"}}  # fmt: skip
    f = frontier(s, registry=reg)
    c = f["frontier"]["C|h"]
    assert "wrongtrack" not in c and "tenzer_x" not in c and f["references"] == ["tenzer_x"]
    assert "wrongtrack" in f["frontier"]["B|h"] and "good" not in f["frontier"]["B|h"]


def test_summarise_frontier():
    s = summarise(_tbl(), T=1000)
    assert s.query("method_id=='good' and cell_id=='h'").power_C.iloc[0] == 1.0
    assert s.query("method_id=='dom' and cell_id=='n'").far_C.iloc[0] == 0.0
    f = frontier(s, registry=REG)
    assert "invalid" in f["excluded"]["C"] and "cusum_x" in f["flagged"]
    ids = f["frontier"]["C|h"]
    assert "dom" not in ids and {"good", "cheap"} <= set(ids) and "invalid" not in ids


def test_freeze(tmp_path):
    fp, art = tmp_path / "F.json", tmp_path / "a.json"
    art.write_text("1")
    with pytest.raises(RuntimeError):
        fz.confirm_seeds_allowed(fp)
    fz.freeze("frontier", art, fp)
    fz.freeze("finalists", art, fp)
    assert fz.confirm_seeds_allowed(fp)
    art.write_text("2")
    with pytest.raises(RuntimeError, match="mismatch"):
        fz.require_frozen(["frontier"], fp)


def test_pipeline_status():
    r = subprocess.run([sys.executable, str(ROOT / "scripts/hgxh2c/pipeline.py"), "--status"], capture_output=True,
                       text=True, cwd=ROOT, check=False, env={**os.environ, "PYTHONPATH": str(ROOT / "src")})  # fmt: skip
    assert r.returncode == 0 and "stage1" in r.stdout
