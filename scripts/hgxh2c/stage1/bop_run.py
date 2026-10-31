"""Wrapper to run a betting_on_predictions main with reduced pool size / repetitions.
Usage: python bop_run.py <repo_dir> <main.py relative> <procs> <reps>
Rewrites only `processes=130` and `"num_of_repititions": 500` in memory (repo files untouched).
Stubs the `tabpfn` import (only needed by the health-care experiment, not run here)."""

import os
import re
import sys
import types

repo, mod, procs, reps = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
os.chdir(repo)
sys.path.insert(0, repo)
_t = types.ModuleType("tabpfn")
_t.TabPFNClassifier = object
sys.modules["tabpfn"] = _t
if __name__ == "__main__":
    with open(os.path.join(repo, mod), encoding="utf8") as source_file:
        src = source_file.read()
    src = src.replace("processes=130", f"processes={procs}")
    src = re.sub(r'"num_of_repititions":\s*\d+', f'"num_of_repititions": {reps}', src)
    exec(compile(src, mod, "exec"), {"__name__": "__main__", "__file__": os.path.join(repo, mod)})  # noqa: S102 - Execute the explicitly selected experiment entry point.
