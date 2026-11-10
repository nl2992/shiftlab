# ruff: noqa
import subprocess
import sys

py = sys.executable
for pool in ("nine", "fresh"):
    subprocess.run(
        [
            py,
            "s25_runner.py",
            "--pool",
            pool,
            "--specs",
            "../../../outputs/paper1_scale25/algo/specs_v2.json",
            "--out",
            f"../../../outputs/paper1_scale25/algo/v2_even_{pool}",
            "--split",
            "even",
            "--seeds",
            "3",
            "--workers",
            "6",
        ]
    )
