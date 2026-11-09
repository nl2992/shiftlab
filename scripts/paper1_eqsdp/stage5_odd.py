"""Stage 5 odd-episode check, once, plus the kc_311 ep 37/39 starvation diagnostic.

  python stage5_odd.py
Refuses to start unless docs/paper1_eqsdp/16_RECOVERY_FREEZE.json is tracked, unmodified, and its
introducing commit is contained in origin/<branch>. Writes outputs/paper1_eqsdp/stage5/odd/run and
.../odd/starvation.csv.
"""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stage2_policies as sp2
import stage5_eval as e5
import stage5_policies as sp5
import trace_run as tr

ROOT = tr.ROOT
FREEZE = ROOT / "docs/paper1_eqsdp/16_RECOVERY_FREEZE.json"
OUT = ROOT / "outputs/paper1_eqsdp/stage5/odd"


def git(*a):
    return subprocess.run(
        ["git", *a], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


def guard() -> str:
    rel = FREEZE.relative_to(ROOT).as_posix()
    assert rel in git("ls-files").splitlines(), "freeze file not tracked"
    assert git("status", "--porcelain", "--", rel) == "", "freeze file modified since commit"
    commit = git("log", "--diff-filter=A", "--format=%H", "--", rel).splitlines()[-1]
    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    git("fetch", "origin", branch)
    git("merge-base", "--is-ancestor", commit, f"origin/{branch}")  # raises if not pushed
    return commit


def trace_requests(dataset, ep, seed, name, spec, path, delay, sb):
    """Purchase event indices of one policy on one episode (same rng derivation as run_policies)."""
    import c4_pilot
    from suite import build_suite, run_episode, stream_from_losses

    z = np.load(path)
    losses = np.stack([z["l0"][ep], z["l1"][ep]], axis=1).astype(np.int8)
    h = int.from_bytes(hashlib.sha256(dataset.encode()).digest()[:4], "big")
    if spec is not None:
        sp2.DYN[name] = sp5.make_factory(spec, name)
    reg = tr.registry()
    rng = np.random.default_rng([sb, h, ep, seed, 7])
    preds, labels = stream_from_losses(losses, rng)
    cfg = c4_pilot.CFG
    (pol,) = build_suite(
        len(losses), 200, 5.0, 0.05, cfg["alpha"], delay, ep * 100_000 + seed,
        sb + h % 1000, names=[name], extra=reg,
    )  # fmt: skip
    res = run_episode(
        pol, model_predictions=preds, labels=labels, delay=delay, budget=200,
        label_price=0.05, switch_cost=5.0, trace=True,
    )  # fmt: skip
    buys = [r["event_id"] for r in res.records if r["requested"]]
    return buys, res.net_cost, res.requested_labels


def starvation(fz):
    path, delay, sb = tr.sealed_paths()["kc_311"]
    rows = []
    roles = fz["roles"]
    pols = {
        "R2": roles["R2"], "R2_roll": roles["R2_roll"], "R3": roles["R3"], "R1": roles["R1"],
        "reference_eqsdp_cutoff": fz["references"]["eqsdp_cutoff"], "arm_R": tr.ARM_R,
    }  # fmt: skip
    for ep in (37, 39):
        for seed in range(10):
            for role, name in pols.items():
                spec = fz["specs"].get(name)
                buys, net, n = trace_requests("kc_311", ep, seed, name, spec, path, delay, sb)
                b = np.array(buys)
                rows.append({
                    "ep": ep, "seed": seed, "role": role, "policy": name, "net": net, "labels": n,
                    "n_0_200": int((b <= 200).sum()),
                    "n_200_800": int(((b > 200) & (b <= 800)).sum()),
                    "n_800_end": int((b > 800).sum()),
                })  # fmt: skip
    with open(OUT / "starvation.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main():
    commit = guard()
    fz = json.loads(FREEZE.read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "start.json").write_text(
        json.dumps({"freeze_commit": commit, "started": time.strftime("%Y-%m-%d %H:%M:%S %z"),
                    "epoch": time.time()})
    )  # fmt: skip
    refs = list(fz["references"].values())
    names = list(dict.fromkeys([*refs, *fz["also_run"]]))
    e5.run_specs(names, fz["specs"], "odd", OUT / "run")
    starvation(fz)
    (OUT / "done.json").write_text(json.dumps({"finished": time.strftime("%Y-%m-%d %H:%M:%S %z")}))


if __name__ == "__main__":
    main()
