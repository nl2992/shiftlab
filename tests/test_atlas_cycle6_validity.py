"""Smoke test for the cycle-6 validity script (tiny T and seeds; no scientific content)."""

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location(
        "cycle6", ROOT / "scripts" / "run_atlas_cycle6_validity_v1.py"
    )
    m = importlib.util.module_from_spec(spec)
    sys.modules["cycle6"] = m
    spec.loader.exec_module(m)
    return m


def test_cycle6_smoke_resume_and_summary(tmp_path):
    m = _load()
    T, n = 100, 2
    cfgs = m.config_list(T)
    assert len(cfgs) == 32 + 4
    keep = {"dep_rho0.8_bt0.5_d10", "rel_bt0.25_fav_first", "rel_bt0.25_control"}
    cfgs = [c for c in cfgs if c["id"] in keep]
    sd = m.fa.seeds("development", n, offset=m.SEED_OFFSET)
    assert sd == (150000, 150001)
    m.run(tmp_path, T, sd, 1, cfgs)
    done = m.load_done(tmp_path / "configs.jsonl")
    assert set(done) == keep
    for r in done.values():
        assert set(r["fp"]) == set(m.ALL_COLS) and all(len(v) == n for v in r["fp"].values())
    size = (tmp_path / "configs.jsonl").stat().st_size
    m.run(tmp_path, T, sd, 1, cfgs)  # resume: nothing re-run
    assert (tmp_path / "configs.jsonl").stat().st_size == size
    m.write_summary(tmp_path, T, done)
    txt = (tmp_path / "summary.md").read_text("utf-8")
    for s in ("V1:", "V2:", "V3:", "V4", "git head", "Interpretation"):
        assert s in txt
    json.loads((tmp_path / "analysis.json").read_text("utf-8"))
    rel = next(c for c in cfgs if c["id"] == "rel_bt0.25_fav_first")
    c = m.build_null_cell("rel", rel, T)
    assert c.null and c.delays == (4, 40)
