"""BCR follow-up: label-price x budget development grid (directive Task 1).

Runs run.py once per (cq, B) cell on fresh development seeds (base 2026111401, 20 seeds),
all 10 environments, a matched policy set: for (lam, gamma) in {.9,.95} x {.05,.1}, the families
kw_anydis, kw_mp, bcr (z_u {.5,1.5} x rho_mon {.1,.3}) and emp (same grid), plus never and the
Model Picker adapter. Every family gets the same (lam, gamma) grid.
"""

import itertools
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENVS = "E1_persist,E2_late,E3_reversal,E4_specialist,E5_ambiguous,E6_null,E6_worse,E2_late_K5,E5_ambiguous_K5,E6_null_K5"
POL = ["never", "model_picker"]
for lam, g in itertools.product((0.9, 0.95), (0.05, 0.1)):
    POL += [f"kw_anydis_l{lam}_g{g}", f"kw_mp_l{lam}_g{g}"]
    for zu, rm in itertools.product((0.5, 1.5), (0.1, 0.3)):
        POL += [f"bcr_l{lam}_g{g}_zu{zu}_rm{rm}", f"emp_l{lam}_g{g}_zu{zu}_rm{rm}"]

if __name__ == "__main__":
    workers = sys.argv[1] if len(sys.argv) > 1 else "8"
    for cq, B in itertools.product((0.02, 0.05, 0.1, 0.2), (100, 200, 400)):
        out = HERE.parents[1] / f"outputs/multimodel_bcr/frontier/cq{cq}_B{B}"
        if (out / "records.jsonl").exists() and (out / "done").exists():
            continue
        subprocess.run(
            [
                sys.executable,
                str(HERE / "run.py"),
                "--envs",
                ENVS,
                "--seeds",
                "20",
                "--seed-base",
                "2026111401",
                "--policies",
                ",".join(POL),
                "--workers",
                workers,
                "--budget",
                str(B),
                "--cq",
                str(cq),
                "--out",
                str(out),
            ],
            check=True,
        )
        (out / "done").write_text("ok")
        print("cell done", cq, B, flush=True)
