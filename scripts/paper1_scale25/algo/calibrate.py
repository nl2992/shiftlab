# ruff: noqa
"""Label-count calibration of the matched acquisition controls (UNI, UNC) per dataset.

Target = mean labels per episode of the matched pair arm (EQ+pair for EQ parent, W+pair for Wald parent),
over ALL episodes of the pool (labels are a budget quantity, not an outcome). The calibration runs use a
every-5th-episode, seeds 0-1 subsample and use only label counts (never costs).

    python calibrate.py --pool nine|fresh
Writes OUT/calib_<pool>.json and OUT/specs_matched_<pool>.json.
"""

from __future__ import annotations

import argparse
import json

import numpy as np
import s25_common as sc
import s25_runner as rn

C_GRID = [0.03, 0.06, 0.12, 0.25, 0.5, 1.0, 2.0, 4.0]
PARENTS = {"EQ": (None, sc.EQ_PAIR), "W": (sc.WALD_PARENT, sc.W_PAIR)}


def targets(pool):
    if pool == "nine":
        d = sc.load_nine_search60([sc.EQ_PAIR, sc.W_PAIR])
    else:
        d = sc.load_fresh()
        d = d[d.config_id.isin([sc.EQ_PAIR, sc.W_PAIR])]
    return d.groupby(["config_id", "stream"]).labels.mean()


def spec(name, ds, parent, mod, params):
    s = {"name": name, "datasets": [ds], "modules": [{"id": mod, "params": params}]}
    if parent:
        s["parent"] = parent
    return s


def sub_eps(pool):
    sl = sc.sealed(pool)
    import numpy as np

    return {ds: list(range(0, int(np.load(p)["l0"].shape[0]), 5)) for ds, (p, _, _) in sl.items()}


def labels_of(out):
    import pandas as pd

    d = pd.read_json(out / "records.jsonl", lines=True)
    return d.groupby(["config_id", "stream"]).labels.mean()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pool", required=True)
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    tg = targets(a.pool)
    sl = sc.sealed(a.pool)
    eps = sub_eps(a.pool)
    calib = {}
    # --- UNC: grid in c, then log-log interpolation, then one verification run
    specs = [
        spec(f"cal_UNC_{pk}_{ds}_{c}", ds, par, "UNC", {"c": c})
        for pk, (par, _) in PARENTS.items()
        for ds in sl
        for c in C_GRID
    ]
    # --- UNI: start at the target and rescale twice
    n_uni = {(pk, ds): float(tg[(pn, ds)]) for pk, (_, pn) in PARENTS.items() for ds in sl}
    out = sc.OUT / f"calib_{a.pool}"
    rn.run(specs, out / "unc_grid", a.pool, seeds=(0, 1), episodes=eps, workers=a.workers)
    lab = labels_of(out / "unc_grid")
    c_star = {}
    for pk, (par, pn) in PARENTS.items():
        for ds in sl:
            ys = np.array([lab[f"cal_UNC_{pk}_{ds}_{c}"][ds] for c in C_GRID])
            tgt = float(tg[(pn, ds)])
            ys = np.maximum.accumulate(ys)
            c_star[(pk, ds)] = float(
                np.exp(np.interp(np.log(tgt), np.log(np.maximum(ys, 1e-6)), np.log(C_GRID)))
            )
    for it in range(2):  # UNI rescale (and UNC check) rounds
        specs = [
            spec(f"cal_UNI_{pk}_{ds}", ds, par, "UNI", {"n_target": n_uni[(pk, ds)]})
            for pk, (par, _) in PARENTS.items()
            for ds in sl
        ]
        specs += [
            spec(f"cal_UNCc_{pk}_{ds}", ds, par, "UNC", {"c": c_star[(pk, ds)]})
            for pk, (par, _) in PARENTS.items()
            for ds in sl
        ]
        rn.run(specs, out / f"round{it}", a.pool, seeds=(0, 1), episodes=eps, workers=a.workers)
        lab = labels_of(out / f"round{it}")
        for pk, (par, pn) in PARENTS.items():
            for ds in sl:
                tgt = float(tg[(pn, ds)])
                n_uni[(pk, ds)] *= tgt / max(lab[f"cal_UNI_{pk}_{ds}"][ds], 1e-6)
                c_star[(pk, ds)] *= (tgt / max(lab[f"cal_UNCc_{pk}_{ds}"][ds], 1e-6)) ** 1.5
    final = []
    for pk, (par, pn) in PARENTS.items():
        for ds in sl:
            tgt = float(tg[(pn, ds)])
            calib[f"{pk}|{ds}"] = {
                "target_labels": tgt,
                "n_target_uni": n_uni[(pk, ds)],
                "c_unc": c_star[(pk, ds)],
            }
            final.append(spec(f"UNI_{pk}__{ds}", ds, par, "UNI", {"n_target": n_uni[(pk, ds)]}))
            final.append(spec(f"UNC_{pk}__{ds}", ds, par, "UNC", {"c": c_star[(pk, ds)]}))
    (sc.OUT / f"calib_{a.pool}.json").write_text(json.dumps(calib, indent=1))
    (sc.OUT / f"specs_matched_{a.pool}.json").write_text(json.dumps(final, indent=1))
    print("done")


if __name__ == "__main__":
    main()
