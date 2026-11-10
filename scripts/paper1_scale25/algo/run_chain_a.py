# ruff: noqa
import subprocess
import sys

py = sys.executable
for pool in ("nine", "fresh"):
    subprocess.run([py, "launch_abl.py", pool, "6"])
