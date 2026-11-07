"""P2 attribution controls: rerun the unchanged scripts/sota_sprint/screen.py on transformed twin-loss streams.

Conditions (each applied per episode, deterministic seeds; see P2_CONTROLS_REGISTRATION.md):
  ORIG   original l0/l1 (re-run at the current code so all conditions share one code version)
  PERM   one random permutation of time applied jointly to (l0,l1): keeps the split's fixed effect, removes serial dependence
  BSWAP  swap (l0,l1) with a fair coin per block of 100 events: removes the episode fixed effect, keeps within-block dependence
  ESWAP  swap (l0,l1) with a fair coin per event: exact conditional null E[l0_t-l1_t | past] = 0
Usage: p2_controls.py build <outdir>   |   p2_controls.py run <outdir> <cond> <datasets> <policies> <seeds> [workers]
"""
import hashlib, json, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "data/sprint_twin_losses"
DATASETS = ["appliances", "beijing_pm25", "bike_hour", "household_power", "metro"]
BLOCK = 100


def transform(l0, l1, cond, rng):
    l0, l1 = l0.copy(), l1.copy()
    K, T = l0.shape
    for k in range(K):
        if cond == "PERM":
            p = rng.permutation(T); l0[k], l1[k] = l0[k, p], l1[k, p]
        elif cond in ("BSWAP", "ESWAP"):
            if cond == "ESWAP":
                c = rng.random(T) < 0.5
            else:
                c = np.repeat(rng.random(-(-T // BLOCK)) < 0.5, BLOCK)[:T]
            a, b = l0[k].copy(), l1[k].copy()
            l0[k], l1[k] = np.where(c, b, a), np.where(c, a, b)
    return l0, l1


def build(out):
    man = {}
    for cond in ("ORIG", "PERM", "BSWAP", "ESWAP"):
        d = Path(out) / cond; d.mkdir(parents=True, exist_ok=True)
        for name in DATASETS:
            z = np.load(SRC / f"twin_{name}.npz")
            rng = np.random.default_rng([20261107, DATASETS.index(name), ["ORIG", "PERM", "BSWAP", "ESWAP"].index(cond)])
            l0, l1 = (z["l0"], z["l1"]) if cond == "ORIG" else transform(z["l0"], z["l1"], cond, rng)
            f = d / f"twin_{name}.npz"
            np.savez(f, l0=l0, l1=l1, split=z["split"], ep=z["ep"])
            man[f"{cond}/{name}"] = dict(sha256=hashlib.sha256(f.read_bytes()).hexdigest(),
                                         src_sha256=hashlib.sha256((SRC / f"twin_{name}.npz").read_bytes()).hexdigest(),
                                         mean_adv=float((l0.astype(int) - l1).mean()),
                                         disagree=float((l0 != l1).mean()))
    (Path(out) / "build_manifest.json").write_text(json.dumps(man, indent=1))
    print(json.dumps(man, indent=1)[:1500])


def run(out, cond, datasets, policies, seeds, workers):
    sys.path.insert(0, str(ROOT / "scripts/sota_sprint"))
    import screen
    screen.TWIN_DIR = Path(out) / cond          # inherited by forked workers; screen.py itself is unchanged
    screen.main(["--kind", "real", "--regimes", ",".join(f"twin_{d}" for d in datasets.split(",")),
                 "--policies", policies, "--seeds", str(seeds), "--seed-base", "2026110620",
                 "--workers", str(workers), "--out", str(Path(out) / f"run_{cond}")])


if __name__ == "__main__":
    if sys.argv[1] == "build":
        build(sys.argv[2])
    else:
        run(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], int(sys.argv[6]), int(sys.argv[7]) if len(sys.argv) > 7 else 4)
