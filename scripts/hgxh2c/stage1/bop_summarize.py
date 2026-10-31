"""Tabulate final-step power (fraction of reps that rejected within nsteps) per statistic from betting_on_predictions result pickles.
Chunk-aware: result pickles with the same <setting>/<file> under several roots are merged by concatenating per-rep rejection lists.
Usage: python bop_summarize.py <results_root> [<results_root> ...] [--json out.json]
  A root is either results/simulations (reduced run) or a results/<chunk> dir; pass all chunk roots of one run to merge them."""

import glob
import json
import os
import pickle
import sys


def load_merged(roots):
    merged = {}
    for root in roots:
        for f in sorted(glob.glob(os.path.join(root, "*", "*.pkl"))):
            key = os.path.relpath(f, root).replace("\\", "/")
            with open(f, "rb") as fh:
                d = pickle.load(fh)
            m = merged.setdefault(
                key,
                {
                    "config": d["config"],
                    "null_corr": d["null_corr"],
                    "alt_corr": d["alt_corr"],
                    "rej": {},
                },
            )
            for stat, lst in d["rejection_lists"].items():
                m["rej"].setdefault(stat, []).extend(list(lst))
    out = {}
    for key, m in merged.items():
        n = len(next(iter(m["rej"].values())))
        out[key] = {
            "reps": n,
            "n_test": m["config"]["n_test"],
            "nsteps": m["config"]["nsteps"],
            "null_corr": m["null_corr"],
            "alt_corr": m["alt_corr"],
            "power": {s: sum(x is not None for x in l) / len(l) for s, l in m["rej"].items()},
        }
    return out


if __name__ == "__main__":
    args = [a for a in sys.argv[1:]]
    jpath = None
    if "--json" in args:
        i = args.index("--json")
        jpath = args[i + 1]
        del args[i : i + 2]
    res = load_merged(args)
    for key, r in res.items():
        print(
            f"## {key} reps={r['reps']} n_test={r['n_test']} nsteps={r['nsteps']} null_corr={r['null_corr']:.2f} alt_corr={r['alt_corr']:.2f}"
        )
        for k, v in r["power"].items():
            print(f"   {k:42s} {v:.2f}")
    if jpath:
        with open(jpath, "w") as fh:
            json.dump(res, fh, indent=1)
