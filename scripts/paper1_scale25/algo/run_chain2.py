# ruff: noqa
import subprocess
import sys

py = sys.executable
subprocess.run([py, "launch_matched.py", "nine", "5"])
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
            "5",
            "--workers",
            "6",
        ]
    )
