"""Paper-budget (--full) job definitions for run_native_repro.py. Chunked, resumable, at most 4 worker processes at a time.

Budgets (paper or authors' defaults) and chunking, all with distinct seeds per chunk:
  Tenzer (betting_on_predictions): 500 reps per config for main_label_shift (4 configs) and main_concept_shift (2 configs), PPI
      variants included; 10 chunks x 50 reps, seed offset 50*k, one results dir per chunk (merged by bop_summarize.load_merged).
  Timans (risk-monitor exp_uci): 50 trials (cfg default) as 5 chunks x 10 trials with a different PROJECT.SEED per chunk, for
      approx_grapa (tracker window 0 and 200) and grid GRAPA (window 200 only: full-history grid GRAPA is quadratic in time,
      about 6 h per trial). exp_ood / exp_cp need external data and are not run.
  Xu (active-rcps simulation.py): 100 trials, label_ct 2500 (script defaults / paper), 20 chunks x 5 trials via --trial_start.
  Ryu-Wornell: notebook sizes for the scalar classes (T=1e4, 5 seeds, six problems; UP included, LBUP/Hybrid need a C compiler
      -> known limit) and the ICML-2024 Fig.1/Fig.3 sizes for the multivariate classes (Fig.2 WoR has no driver code in the repo).
  PPRM independent reproduction: 200 synthetic streams drift+nominal (4 chunks x 50) and the adaptive-vs-fixed reliance
      sweep over synthetic-label quality (q_pred 0.2/0.1/0.05; 100 drift streams each).
Worker budget: group parallelism x processes per job <= 4 (bop chunks use 4 processes and run one at a time).
"""

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "tmp" / "repro_sources"
STAGE = ROOT / "scripts" / "hgxh2c" / "stage1"
FULL = ROOT / "outputs" / "hgxh2c" / "stage1_full"
H = 3600
RM_COMMON = ["--batch_ts=1", "--stop_counter", "5", "25", "0", "--device=cpu", "--save_file"]


def venv(name):
    return str(SRC / "venvs" / name / "Scripts" / "python.exe")


def rm_yaml(tag, trials, seed, timesteps=15000):
    """Authors' cfg_uci.yaml values; only paths, NR_TRIALS, SEED and BET_TYPE differ."""
    bet = "grapa" if tag.startswith("grapa") else "approx_grapa"
    return f"""PROJECT:
  CONFIG_DIR: "{(FULL / "rm_cfg").as_posix()}"
  OUTPUT_DIR: "{(FULL / "risk_monitor_out").as_posix()}"
  SEED: {seed}
DATASET:
  DIR: "{ROOT.as_posix()}/tmp/repro_sources/risk-monitor/data"
MODEL:
  TYPE: rf
  DIR: none
EXP:
  EPS: 0.1
  DELTA: 0.1
  NR_TRIALS: {trials}
  NR_TIMESTEPS: {timesteps}
  PSI_START: 0.0
  PSI_END: 0.05
  PSI_INIT: 0.0
  PSI_STEP: 0.0005
  RISK: miscover
  BET_TYPE: {bet}
  NR_POINT_RISK_SAMP: 100
  NR_BURNIN: 100
  SPLIT_TIME: 12500
  SET_SCORE: abs_res
"""


def build_full_groups(write_cfgs=True):
    """Return [(group, max_parallel, [(job, cmd, cwd, timeout_s)])]; groups run in order."""
    py = sys.executable
    g = []
    g.append(("gambling", 2, [
        ("full_gambling_scalar", [py, "-I", "-u", str(STAGE / "gambling_cs_run.py"), str(SRC / "gambling_cs"),
                                  str(FULL / "gambling_cs" / "scalar.json"), "10000", "5", "all"], ROOT, 6 * H),
        ("full_gambling_multivariate", [py, "-I", "-u", str(STAGE / "gambling_cs_multivariate_run.py"), str(SRC / "gambling_cs"),
                                        str(FULL / "gambling_cs" / "multivariate.json"), "full"], ROOT, 12 * H),
    ]))  # fmt: skip
    pj = []
    for k in range(4):
        pj.append((f"full_pprm_main_c{k}", [py, "-I", "-u", str(STAGE / "pprm_independent.py"), str(FULL / "pprm" / f"main_c{k}.json"),
                                            "50", "1500", str(100 * k)], ROOT, 4 * H))  # fmt: skip
    for q in ("0.2", "0.1", "0.05"):
        for k in range(2):
            pj.append((f"full_pprm_sweep_q{q}_c{k}", [py, "-I", "-u", str(STAGE / "pprm_independent.py"),
                                                      str(FULL / "pprm" / f"sweep_q{q}_c{k}.json"), "50", "1500", str(100 * k + 5000),
                                                      q, "0.02", "--no-nominal"], ROOT, 4 * H))  # fmt: skip
    g.append(("pprm", 4, pj))
    cfgdir = FULL / "rm_cfg"
    if write_cfgs:
        cfgdir.mkdir(parents=True, exist_ok=True)
        (cfgdir / "cfg_full_prep.yaml").write_text(
            rm_yaml("approx", 1, 1, timesteps=300), encoding="utf-8"
        )
        for tag in ("approx_w0", "approx_w200", "grapa_w200"):
            for k in range(5):
                (cfgdir / f"cfg_full_{tag}_c{k}.yaml").write_text(
                    rm_yaml(tag, 10, 66666666 + 1000 * (k + 1)), encoding="utf-8"
                )

    def rm_cmd(cfg, suffix, tw, get_pred):
        return [venv("risk-monitor"), "-X", "utf8", "-I", "-u", str(SRC / "risk-monitor" / "exp" / "exp_uci.py"),
                f"--cfg_file={cfg}", f"--cfg_dir={cfgdir.as_posix()}", f"--exp_suffix={suffix}", get_pred,
                "--tracker_window", "0", tw, tw] + RM_COMMON  # fmt: skip

    g.append(
        (
            "rm_prep",
            1,
            [
                (
                    "full_rm_prep",
                    rm_cmd("cfg_full_prep", "_full_prep", "0", "--get_pred"),
                    ROOT,
                    1 * H,
                )
            ],
        )
    )
    rj = []
    for tag, tw, to in (
        ("approx_w0", "0", 8 * H),
        ("approx_w200", "200", 4 * H),
        ("grapa_w200", "200", 16 * H),
    ):
        for k in range(5):
            rj.append(
                (
                    f"full_rm_{tag}_c{k}",
                    rm_cmd(f"cfg_full_{tag}_c{k}", f"_full_{tag}_c{k}", tw, "--no-get_pred"),
                    ROOT,
                    to,
                )
            )
    g.append(("rm", 4, rj))
    xj = []
    for k in range(20):
        xj.append((f"full_xu_c{k:02d}", [venv("active-rcps"), "-u", "-X", "utf8", "simulation.py", "--processes", "1", "--trial_start",
                                         str(1 + 5 * k), "--trials", "5", "--label_ct", "2500", "--out_dir", str(FULL / "xu" / f"c{k}")],
                   SRC / "active-rcps", 16 * H))  # fmt: skip
    g.append(("xu", 4, xj))
    bj = []
    for fam, main, to in (
        ("label", "main_label_shift", 10 * H),
        ("concept", "main_concept_shift", 30 * H),
    ):
        for k in range(10):
            bj.append((f"full_bop_{fam}_c{k:02d}", [py, "-u", str(STAGE / "bop_run.py"), str(SRC / "betting_on_predictions"),
                                                    f"mains/{main}.py", "4", "50", str(50 * k), f"full_{fam}_c{k:02d}"], ROOT, to))  # fmt: skip
    g.append(("bop", 1, bj))  # each chunk job already uses 4 worker processes
    return g


def run_job(name, cmd, cwd, to, logdir, markdir):
    t0 = time.time()
    with (
        open(logdir / f"{name}.log", "w", encoding="utf8") as lo,
        open(logdir / f"{name}.err", "w", encoding="utf8") as le,
    ):
        try:
            rc = subprocess.run(
                cmd, cwd=str(cwd), stdout=lo, stderr=le, timeout=to, check=False
            ).returncode
        except subprocess.TimeoutExpired:
            rc = "TIMEOUT"
    st = {"rc": rc, "secs": round(time.time() - t0)}
    if rc == 0:
        (markdir / f"{name}.done").write_text(json.dumps(st))
    print(name, st, flush=True)
    return name, st
