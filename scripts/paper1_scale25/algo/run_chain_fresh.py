# ruff: noqa
import subprocess
import sys

subprocess.run([sys.executable, "launch_abl.py", "fresh", "6"])
subprocess.run([sys.executable, "launch_matched.py", "fresh", "6"])
