# ruff: noqa
import subprocess
import sys

py = sys.executable
subprocess.run([py, "launch_matched.py", "fresh", "6"])
for pool in ("nine", "fresh"):
    subprocess.run([py, "launch_refgrid.py", pool, "6"])
