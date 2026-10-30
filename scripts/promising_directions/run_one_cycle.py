"""Run one cycle: pick a pending task, enforce protocol-hash immutability, run, verify, report."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from research_loop import atomic_write, git, ledger_append, now, save_state, sha256_file

CYCLES_DIR = "outputs/promising_directions/cycles"
REPORTS_DIR = "docs/promising_directions/CYCLE_REPORTS"


def run_one_cycle(root: Path, state: dict, task_id: str, limits: dict) -> dict:
    """Mutates and returns state. Completed tasks are never rerun. Caller must hold the lock."""
    task = state["tasks"][task_id]
    if task["status"] == "completed":
        return state
    state["cycle_counter"] += 1
    cycle_id = f"cycle-{state['cycle_counter']:04d}-{task_id}"
    cdir = root / CYCLES_DIR / cycle_id
    cdir.mkdir(parents=True, exist_ok=True)
    rec = {
        "cycle_id": cycle_id,
        "started_at": now(),
        "branch": git(root, "branch", "--show-current"),
        "head": git(root, "rev-parse", "HEAD"),
        "dirty": bool(git(root, "status", "--porcelain")),
        "command": task["command"],
        "protocol_sha256": task["protocol_sha256"],
        "last_verified_checkpoint": state["last_verified_checkpoint"],
    }
    outcome, error, insight = "completed", None, None

    proto = root / task["protocol_path"]
    cur = sha256_file(proto) if proto.exists() else None
    if cur != task["protocol_sha256"]:
        outcome, error = (
            "protocol_changed",
            f"protocol hash {cur} != registered {task['protocol_sha256']}",
        )
    else:
        env = {
            **os.environ,
            "LOOP_CYCLE_DIR": str(cdir),
            "LOOP_INSIGHT_PATH": str(cdir / "insight.json"),
        }
        cmd = task["command"]
        try:
            with open(cdir / "stdout.txt", "w") as so, open(cdir / "stderr.txt", "w") as se:
                p = subprocess.run(
                    cmd,
                    check=False,
                    shell=isinstance(cmd, str),
                    cwd=root,
                    env=env,
                    stdout=so,
                    stderr=se,
                    timeout=limits["per_cycle_timeout_s"],
                )
            if p.returncode != 0:
                outcome, error = "failed", f"exit code {p.returncode}"
        except subprocess.TimeoutExpired:
            outcome, error = "failed", f"timeout after {limits['per_cycle_timeout_s']}s"
        except OSError as e:
            outcome, error = "failed", f"could not launch: {e}"
        missing = [o for o in task["expected_outputs"] if not (root / o).is_file()]
        if outcome == "completed" and missing:
            outcome, error = "failed", f"missing expected outputs: {missing}"

    if outcome == "completed":
        arts = [*task["expected_outputs"], f"{CYCLES_DIR}/{cycle_id}/stdout.txt"]
        ip = cdir / "insight.json"
        if ip.is_file():
            arts.append(f"{CYCLES_DIR}/{cycle_id}/insight.json")
            try:
                insight = json.loads(ip.read_text(encoding="utf-8"))
            except ValueError:
                insight = None
        task["artifacts"] = {a: sha256_file(root / a) for a in arts}
        state["last_verified_checkpoint"] = cycle_id
        state["consecutive_infra_failures"] = 0
        new = bool(insight and insight.get("new_insight") is True)
        state["consecutive_no_insight"] = 0 if new else state["consecutive_no_insight"] + 1
    elif outcome == "failed":
        state["consecutive_infra_failures"] += 1
    task["status"], task["error"] = outcome, error
    rec.update(outcome=outcome, error=error, insight=insight, finished_at=now())
    task["cycles"].append(rec)
    state["next_task"] = next(
        (t for t, v in state["tasks"].items() if v["status"] == "pending"), None
    )
    save_state(root, state)

    atomic_write(
        root / REPORTS_DIR / f"{cycle_id}.md",
        "\n".join(
            [
                f"# {cycle_id}",
                "",
                f"- task: {task_id} (lane {task['lane']})",
                f"- hypothesis: {task['hypothesis']}",
                f"- outcome: {outcome}",
                f"- error: {error}",
                f"- branch/HEAD/dirty: {rec['branch']} / {rec['head']} / {rec['dirty']}",
                f"- protocol sha256: {rec['protocol_sha256']}",
                f"- new_insight: {insight.get('new_insight') if insight else None}",
                f"- summary: {insight.get('summary') if insight else None}",
                f"- artifacts: {json.dumps(task['artifacts'], indent=2)}",
                f"- last verified checkpoint before this cycle: {rec['last_verified_checkpoint']}",
                f"- logs: {CYCLES_DIR}/{cycle_id}/",
                "",
                "Smoke/plumbing outcomes are not scientific evidence.",
                "",
            ]
        ),
    )
    ledger_append(root, f"{cycle_id} task={task_id} outcome={outcome} error={error}")
    return state
