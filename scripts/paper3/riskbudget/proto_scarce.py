"""DIAGNOSTIC on the label-scarce simulation family (dev seeds 81000+, not registered): frozen v3 vs exact-mixture
width vs the deterministic matched comparator, at h = 14 and 50."""
import copy, sys, time
import numpy as np
from shiftlab.paper3.riskbudget.harness_v3 import OUT, R_of, T_SC, _frozen_arm, load_family, load_frozen_v3, run_family, v3_arm
from shiftlab.paper3.simulation import seeds_for


def main():
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    sh = load_frozen_v3()
    arms = [_frozen_arm("never"), _frozen_arm("wald_cut")]
    for h in (14, 50):
        arms.append(v3_arm(sh, R_of(h), f"v3_h{h}"))
        s = copy.deepcopy(sh); s["mix_m"] = 12; arms.append(v3_arm(s, R_of(h), f"mix12_h{h}"))
        s = copy.deepcopy(sh); s["deterministic"] = True; arms.append(v3_arm(s, R_of(h), f"det_h{h}"))
    out = OUT / f"proto_scarce_n{N}"
    t0 = time.time()
    run_family("scarce", arms, seeds_for("dev", N, 81000), out, T_SC, 6, log=lambda m: None)
    names, regs, sd, A = load_family(out, "scarce")
    J = A["J"].mean(axis=2).mean(axis=1)
    print("wall", round(time.time() - t0), "regimes", len(regs))
    never, wald = J[0], J[1]
    viol = A["sup_harm"]
    for i, n in enumerate(names):
        R = {"n": None}
        h = int(n.split("_h")[1]) if "_h" in n else None
        v = (viol[i] > R_of(h) + 1e-9).mean(axis=1) if h else (viol[i] > R_of(14) + 1e-9).mean(axis=1)
        keep = f"keeps {100*(never-J[i])/(never-wald):6.1f}%" if i >= 2 else ""
        print(f"{n:12s} J {J[i]:8.2f} {keep}  viol(pooled) {100*v.mean():.2f}% worst {100*v.max():.1f}%")


if __name__ == "__main__":
    main()
