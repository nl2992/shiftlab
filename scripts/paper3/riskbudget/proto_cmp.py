"""VALID sharper width (exact mixture, dense lambda grid) vs frozen; dev seeds only.
(DIAGNOSTIC (dev seeds 5301080000+ only, nothing reported): how much cost could a sharper width buy?
Arms: never, wald_cut, frozen v3 at R=20, and v3 with the width scaled by 0.5 and 0 (INVALID, upper bound on the gain)."""
import copy, sys, time
from pathlib import Path
import numpy as np
from shiftlab.paper3.riskbudget.harness_v3 import (OUT, _frozen_arm, load_frozen_v3, orig30_arms, run_family, load_family, v3_arm)
from shiftlab.paper3.simulation import seeds_for

def main():
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    sh = load_frozen_v3()
    arms = [_frozen_arm("never"), _frozen_arm("wald_cut")]
    for R in (20,):
        arms.append(v3_arm(sh, R, f"v3_R{R}"))
        for sc in ():
            s2 = copy.deepcopy(sh); s2["width_scale"] = sc
            arms.append(v3_arm(s2, R, f"v3_R{R}_w{sc:g}"))
    s4 = copy.deepcopy(sh); s4['deterministic'] = True
    arms.append(v3_arm(s4, 20, 'safe_det_R20'))
    s5 = copy.deepcopy(sh); s5['mix_m'] = 12
    arms.append(v3_arm(s5, 20, 'v3_R20_mix12b'))
    for mm in ():
        s3 = copy.deepcopy(sh); s3['mix_m'] = mm
        arms.append(v3_arm(s3, 20, f'v3_R20_mix{mm}'))
    seeds = seeds_for("dev", N, 80000)
    out = OUT / f"proto_cmp_n{N}"
    t0 = time.time()
    run_family("orig", arms, seeds, out, 300, 6, log=lambda m: None)
    names, regs, sd, A = load_family(out, "orig")
    J = A["J"]  # (arm, regime, seed)
    print("wall", round(time.time() - t0))
    orig = [i for i, r in enumerate(regs)]
    m = J.mean(axis=2).mean(axis=1)
    for n_, v in zip(names, m): print(f"{n_:14s} pooled J = {v:8.3f}")
    never, wald = m[0], m[1]
    for n_, v in zip(names[2:], m[2:]):
        print(f"{n_:14s} keeps {100*(never-v)/(never-wald):5.1f}% of Wald's gain over never")



if __name__ == "__main__":
    main()
