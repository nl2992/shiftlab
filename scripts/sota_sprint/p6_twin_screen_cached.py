"""Run the frozen screen job on twin bike with a worker-local cache of its loss archive.

`screen._job` remains the source of all policy and metric behavior. This wrapper only avoids
reopening/decompressing the same NPZ archive for each episode/seed job.
"""

from __future__ import annotations

import hashlib
import json
import multiprocessing as mp
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import screen
from registry import IMPORT_ERRORS

DATA = ROOT / "data/sprint_twin_losses/twin_bike_hour.npz"
OUT = ROOT / "outputs/sprint2/round5/p6_twin_bike_1000"
POLICIES = ["P6_LRMD_U", "M_LRMD_SUI", "A5b", "CONTROL_never_switch"]
SEEDS = 1000
SEED_BASE = 2026110812
WORKERS = 8
ALPHA = 0.05
_ORIGINAL_LOAD = np.load


def _init_worker():
    with _ORIGINAL_LOAD(DATA) as archive:
        cache = {k: archive[k] for k in archive.files}
    data_path = DATA.resolve()
    original = _ORIGINAL_LOAD

    def cached_load(file, *args, **kwargs):
        try:
            if Path(file).resolve() == data_path:
                return cache
        except (TypeError, OSError):
            pass
        return original(file, *args, **kwargs)

    screen.np.load = cached_load


def _sources():
    deps = [
        HERE,
        ROOT / "scripts/failure_atlas_v2_flq",
        ROOT / "scripts/failure_atlas_v2",
        ROOT / "scripts/promising_directions/sota",
        ROOT / "scripts/promising_directions/sota/competitors",
    ]
    paths = {p for d in deps for p in d.glob("*.py")}
    paths.add(Path(__file__))
    return {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()[:16]
        for p in sorted(paths)
    }


def smoke_check():
    names = POLICIES
    job = ("real", "twin_bike_hour", 3, 17, SEED_BASE, names, ALPHA)
    expected = screen._job(job)
    # Apply the same cache initializer in the parent process, then compare full records.
    _init_worker()
    actual = screen._job(job)
    clean = lambda rows: [{k: v for k, v in row.items() if k != "runtime_s"} for row in rows]
    assert clean(actual) == clean(expected), "cached job metrics differ from the frozen screen job"


def main():
    smoke_check()
    names = POLICIES
    with _ORIGINAL_LOAD(DATA) as z:
        K = int(z["l0"].shape[0])
    jobs = [
        ("real", "twin_bike_hour", ep, seed, SEED_BASE, names, ALPHA)
        for ep in range(K)
        for seed in range(SEEDS)
    ]
    OUT.mkdir(parents=True, exist_ok=True)
    start = time.time()
    with open(OUT / "records.jsonl", "w") as f, mp.Pool(WORKERS, initializer=_init_worker) as pool:
        for rows in pool.imap_unordered(screen._job, jobs, chunksize=8):
            f.writelines(json.dumps(row) + "\n" for row in rows)
    sources = _sources()
    sources[str(DATA.relative_to(ROOT))] = hashlib.sha256(DATA.read_bytes()).hexdigest()[:16]
    manifest = {
        "argv": {
            "runner": str(Path(__file__).relative_to(ROOT)),
            "kind": "real",
            "regimes": ["twin_bike_hour"],
            "policies": names,
            "seeds": SEEDS,
            "seed_base": SEED_BASE,
            "workers": WORKERS,
            "alpha": ALPHA,
            "optimization": "worker-local NPZ cache; screen._job unchanged",
        },
        "contract": {**screen.CONTRACT, "alpha": ALPHA},
        "git": screen._git_rev(),
        "sources": sources,
        "import_errors": IMPORT_ERRORS,
        "n_jobs": len(jobs),
        "seconds": round(time.time() - start, 1),
        "cached_vs_uncached_smoke": "exact metric match (excluding wall-clock runtime_s): ep=3, seed=17",
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"done {len(jobs)} jobs in {time.time() - start:.0f}s -> {OUT}")


if __name__ == "__main__":
    main()
