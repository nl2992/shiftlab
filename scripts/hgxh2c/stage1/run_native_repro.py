"""Idempotent, resumable Stage-1 native reproduction driver (reduced settings; see docs/hgxh2c/02_NATIVE_REPRODUCTION.md).

Usage: python scripts/hgxh2c/stage1/run_native_repro.py [--only NAME ...] [--force] [--list] [--full]
--full runs the PAPER-BUDGET reruns defined in full_jobs.py: chunked (rep/trial chunks, distinct seeds), at most 4 worker
processes, per-job timeouts, markers outputs/hgxh2c/stage1/markers/full_<job>.done, outputs in outputs/hgxh2c/stage1_full/,
then merges chunks into outputs/hgxh2c/stage1_full/full_summary.json (full_merge.py). `--full --list` is a dry run (writes nothing).
Each job is skipped if outputs/hgxh2c/stage1/markers/<job>.done exists (unless --force). Logs go to
outputs/hgxh2c/stage1/<job>.log|.err; jobs run via subprocess with a timeout; the marker is written only on rc==0.
Requires clones in tmp/repro_sources/ (not re-cloned here) and venvs under tmp/repro_sources/venvs:
  risk-monitor: python -m venv --system-site-packages ...; pip install yacs pyyaml
  active-rcps : same + pip install dill multiprocess seaborn; site-packages/pickle5.py = "from pickle import *";
                one-token syntax patch of Predictor.py saved as outputs/hgxh2c/stage1/active_rcps_local.patch
"""

import argparse
import concurrent.futures as cf
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "tmp" / "repro_sources"
OUT = ROOT / "outputs" / "hgxh2c" / "stage1"
MARK = OUT / "markers"
STAGE = ROOT / "scripts" / "hgxh2c" / "stage1"
# forward slashes: exp_uci derives its output subdir from the last '/' component of --cfg_dir
RM_CFG = (STAGE / "risk_monitor_cfg").as_posix()
RM_COMMON = ["--batch_ts=1", "--stop_counter", "5", "25", "0", "--device=cpu", "--save_file"]
H = 3600


def venv(name):
    return str(SRC / "venvs" / name / "Scripts" / "python.exe")


def rm_job(cfg, suffix, tw="0", get_pred="--get_pred"):
    return (
        [
            venv("risk-monitor"),
            "-X",
            "utf8",
            "-I",
            "-u",
            str(SRC / "risk-monitor" / "exp" / "exp_uci.py"),
            f"--cfg_file={cfg}",
            f"--cfg_dir={RM_CFG}",
            f"--exp_suffix={suffix}",
            get_pred,
            "--tracker_window",
            "0",
            tw,
            tw,
        ]
        + RM_COMMON,
        ROOT,
    )


JOBS = {  # name: (cmd, cwd, timeout_s)
    "gambling_cs": (
        [
            sys.executable,
            "-I",
            "-u",
            str(STAGE / "gambling_cs_run.py"),
            str(SRC / "gambling_cs"),
            str(OUT / "gambling_cs" / "result.json"),
            "3000",
            "3",
        ],
        ROOT,
        1 * H,
    ),
    "gambling_cs_multivariate": (
        [
            sys.executable,
            "-I",
            "-u",
            str(STAGE / "gambling_cs_multivariate_run.py"),
            str(SRC / "gambling_cs"),
            str(OUT / "gambling_cs" / "multivariate_result.json"),
        ],
        ROOT,
        1 * H,
    ),
    "pprm_independent": (
        [
            sys.executable,
            "-I",
            "-u",
            str(STAGE / "pprm_independent.py"),
            str(OUT / "pprm_indep" / "result.json"),
            "60",
            "1500",
        ],
        ROOT,
        1 * H,
    ),
    "rm_uci_approx": (*rm_job("cfg_uci_approx", "_approx"), 1 * H),
    # tracker_window 0 = full-history bets (quadratic cost; grid GRAPA needs ~hours/trial here) -> windowed runs for grapa
    "rm_uci_approx_w200": (
        *rm_job("cfg_uci_approx", "_approx_w200", "200", "--no-get_pred"),
        1 * H,
    ),
    "rm_uci_grapa_w200": (*rm_job("cfg_uci_grapa", "_grapa_w200", "200", "--no-get_pred"), 3 * H),
    "bop_label_shift": (
        [
            sys.executable,
            "-u",
            str(STAGE / "bop_run.py"),
            str(SRC / "betting_on_predictions"),
            "mains/main_label_shift.py",
            "3",
            "10",
        ],
        ROOT,
        3 * H,
    ),
    "bop_concept_shift": (
        [
            sys.executable,
            "-u",
            str(STAGE / "bop_run.py"),
            str(SRC / "betting_on_predictions"),
            "mains/main_concept_shift.py",
            "4",
            "4",
        ],
        ROOT,
        2 * H,
    ),
    "active_rcps_sim": (
        [
            venv("active-rcps"),
            "-u",
            "-X",
            "utf8",
            "simulation.py",
            "--processes",
            "1",
            "--label_ct",
            "800",
            "--trials",
            "4",
            "--out_dir",
            str(OUT / "active_rcps_sim"),
        ],
        SRC / "active-rcps",
        3 * H,
    ),
}


def main_full(a):
    sys.path.insert(0, str(STAGE))
    import full_jobs

    groups = full_jobs.build_full_groups(write_cfgs=not a.list)
    logdir = full_jobs.FULL / "logs"
    MARK.mkdir(parents=True, exist_ok=True)
    if not a.list:
        logdir.mkdir(parents=True, exist_ok=True)
        (SRC / "betting_on_predictions" / "logs").mkdir(parents=True, exist_ok=True)
    status = {}
    rm_failed = False
    for gname, par, jobs in groups:
        if gname == "rm" and rm_failed:
            print("skipping risk-monitor chunks: rm_prep failed")
            continue
        todo = []
        for name, cmd, cwd, to in jobs:
            if a.only and not any(o in name for o in a.only):
                continue
            done = (MARK / f"{name}.done").exists()
            if a.list:
                print(
                    f"{name:34s} {'DONE' if done else 'PENDING':8s} timeout={to // H}h group={gname} parallel={par}"
                )
            elif done and not a.force:
                status[name] = "skipped(done)"
            else:
                todo.append((name, cmd, cwd, to))
        if a.list or not todo:
            continue
        with cf.ThreadPoolExecutor(
            max_workers=par
        ) as ex:  # parallelism x processes-per-job <= 4 by construction
            for name, st in ex.map(lambda j: full_jobs.run_job(*j, logdir, MARK), todo):
                status[name] = st
        prep = status.get("full_rm_prep")
        if gname == "rm_prep" and isinstance(prep, dict) and prep["rc"] != 0:
            rm_failed = True
    if a.list:
        print("dry run only (--list): nothing launched")
        return
    (full_jobs.FULL / "driver_last_status.json").write_text(json.dumps(status, indent=1))
    subprocess.run(
        [sys.executable, "-X", "utf8", "-I", str(STAGE / "full_merge.py"), "full"],
        cwd=str(ROOT),
        check=False,
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument(
        "--full", action="store_true", help="paper-budget chunked reruns (full_jobs.py)"
    )
    a = ap.parse_args()
    if a.full:
        return main_full(a)
    MARK.mkdir(parents=True, exist_ok=True)
    (SRC / "betting_on_predictions" / "logs").mkdir(
        parents=True, exist_ok=True
    )  # repo mains write logs here
    status = {}
    for name, (cmd, cwd, to) in JOBS.items():
        if a.only and name not in a.only:
            continue
        marker = MARK / f"{name}.done"
        if a.list:
            print(name, "DONE" if marker.exists() else "PENDING")
            continue
        if marker.exists() and not a.force:
            status[name] = "skipped(done)"
            print(name, status[name])
            continue
        t0 = time.time()
        with (
            open(OUT / f"{name}.log", "w", encoding="utf8") as lo,
            open(OUT / f"{name}.err", "w", encoding="utf8") as le,
        ):
            try:
                rc = subprocess.run(
                    cmd, cwd=str(cwd), stdout=lo, stderr=le, timeout=to, check=False
                ).returncode
            except subprocess.TimeoutExpired:
                rc = "TIMEOUT"
        status[name] = {"rc": rc, "secs": round(time.time() - t0)}
        if rc == 0:
            marker.write_text(json.dumps(status[name]))
        print(name, status[name], flush=True)
    (OUT / "driver_last_status.json").write_text(json.dumps(status, indent=1))


if __name__ == "__main__":
    main()
