import json
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "promising_directions"))
import research_loop as rl
import verify_artifacts

PY = sys.executable
OK = (
    "import json,os;os.makedirs('out',exist_ok=True);json.dump({},open('out/r.json','w'));"
    "json.dump({'new_insight':%s,'summary':'s'},open(os.environ['LOOP_INSIGHT_PATH'],'w'))"
)


def make_root(tmp_path, tasks):
    (tmp_path / "docs/promising_directions/CYCLE_REPORTS").mkdir(parents=True)
    (tmp_path / "configs/promising_directions").mkdir(parents=True)
    (tmp_path / rl.LEDGER).write_text("# ledger\n")
    (tmp_path / "proto.md").write_text("protocol v1")
    lim = {
        "max_cycles_per_session": 20,
        "max_workers": 1,
        "max_consecutive_no_insight": 3,
        "max_consecutive_infra_failures": 2,
        "per_cycle_timeout_s": 30,
    }
    full = [
        {
            "lane": "C",
            "hypothesis": "h",
            "expected_outputs": ["out/r.json"],
            "protocol_path": "proto.md",
            **t,
        }
        for t in tasks
    ]
    cfg = {"limits": lim, "lanes": {"C": {"status": "active"}}, "tasks": full}
    (tmp_path / rl.CONFIG).write_text(yaml.safe_dump(cfg))
    return tmp_path


def ok_task(tid, insight=True):
    return {"id": tid, "command": [PY, "-c", OK % insight]}


def state_of(root):
    return json.loads((root / rl.STATE).read_text())


def test_lock_exclusive_and_stale(tmp_path):
    p = tmp_path / "l.lock"
    with rl.Lock(p), pytest.raises(RuntimeError):
        rl.Lock(p).acquire()
    assert not p.exists()
    p.write_text(json.dumps({"pid": 2**30, "ts": 0}))  # dead pid -> stale
    with rl.Lock(p):
        pass


def test_atomic_write_leaves_no_temp(tmp_path):
    p = tmp_path / "s.json"
    rl.atomic_write(p, "a")
    rl.atomic_write(p, "b")
    assert p.read_text() == "b" and [x.name for x in tmp_path.iterdir()] == ["s.json"]


def test_idempotent_resume(tmp_path):
    root = make_root(tmp_path, [ok_task("t1")])
    rl.run_session(root, 1)
    s = state_of(root)
    assert s["tasks"]["t1"]["status"] == "completed" and len(s["tasks"]["t1"]["cycles"]) == 1
    rl.run_session(root, 5, resume=True)
    s = state_of(root)
    assert len(s["tasks"]["t1"]["cycles"]) == 1 and s["cycle_counter"] == 1
    assert s["stop_reason"] == "queue_empty"
    assert verify_artifacts.verify(root) == []
    (root / "out/r.json").write_text("tampered")
    assert verify_artifacts.verify(root)


def test_protocol_hash_immutable(tmp_path):
    root = make_root(tmp_path, [ok_task("t1")])
    rl.ensure_state(root, rl.load_config(root))
    (root / "proto.md").write_text("protocol v2")
    rl.run_session(root, 1)
    t = state_of(root)["tasks"]["t1"]
    assert t["status"] == "protocol_changed" and not (root / "out/r.json").exists()


def test_failure_preserved(tmp_path):
    bad = {"id": "bad", "command": [PY, "-c", "import sys;print('boom');sys.exit(3)"]}
    root = make_root(tmp_path, [ok_task("t1"), bad])
    rl.run_session(root, 5)
    s = state_of(root)
    t = s["tasks"]["bad"]
    assert t["status"] == "failed" and "exit code 3" in t["error"]
    assert t["cycles"][0]["command"] == bad["command"]
    assert (
        t["cycles"][0]["last_verified_checkpoint"]
        == s["last_verified_checkpoint"]
        == "cycle-0001-t1"
    )
    log = root / "outputs/promising_directions/cycles/cycle-0002-bad/stdout.txt"
    assert log.read_text().strip() == "boom"


def test_infra_failure_stop(tmp_path):
    fail = [PY, "-c", "import sys;sys.exit(1)"]
    root = make_root(tmp_path, [{"id": f"b{i}", "command": fail} for i in range(3)])
    rl.run_session(root, 10)
    assert state_of(root)["stop_reason"] == "infra_failures"


def test_no_insight_stop_after_three(tmp_path):
    root = make_root(tmp_path, [ok_task(f"t{i}", insight=False) for i in range(5)])
    rl.run_session(root, 10)
    s = state_of(root)
    assert s["stop_reason"] == "no_insight" and s["cycle_counter"] == 3 and s["next_task"] == "t3"
