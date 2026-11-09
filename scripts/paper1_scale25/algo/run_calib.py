# ruff: noqa
import subprocess
import sys

for p in ("fresh", "nine"):
    subprocess.run([sys.executable, "calibrate.py", "--pool", p, "--workers", "8"])
