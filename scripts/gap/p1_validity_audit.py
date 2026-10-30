"""Phase 1 validity audit: exact finite-support check of the covariate-dependent bet cap, heterogeneous-risk
null simulation, outcome-dependent delay (naive vs prefix release), AR/cluster dependence. Synthetic only."""

import json
import time

from shiftlab.gap import audit
from shiftlab.gap import engine as E
from shiftlab.gap import worlds as W
from shiftlab.sota_search import harness as h

OUT = "outputs/gap_closure/p1"


def wilson(k, n):
    lo, hi = h.wilson(int(k), int(n))
    return [round(lo, 4), round(hi, 4)]


def sim_null(label, stream_fn, cfgs, S=1000, seeds=(1,), delay=5, truth_kind="none"):
    out = []
    for name, cfg, dl in cfgs:
        k = n = 0
        t0 = time.time()
        for sd in seeds:
            st = stream_fn(sd)
            d = dl(st) if callable(dl) else dl
            res = E.run(st, cfg, delay=d, qseed=sd)
            k += int((res["alarm"] < st["loss"].shape[1]).sum())
            n += S
        out.append(
            {
                "scenario": label,
                "arm": name,
                "fa": k / n,
                "fa_ci": wilson(k, n),
                "n": n,
                "s": round(time.time() - t0, 1),
            }
        )
        print(out[-1], flush=True)
    return out


def main():
    res = {"exact": audit.exact_cap_check()}
    print("exact done", flush=True)
    S = 1000
    # (A) heterogeneous risk, marginal unchanged: legacy x-cap vs sup-cap; plug-in Kelly and forced max bet
    hn = W.HeteroNull()
    base = {"risk": "brier", "frac": 0.1, "release": "prefix"}
    cf = [
        ("kelly_x_cap", E.Cfg(cap_mode="x", **base), 5),
        ("kelly_sup_cap", E.Cfg(cap_mode="sup", **base), 5),
        ("forced_x_cap", E.Cfg(cap_mode="x", force_bet=True, **base), 5),
        ("forced_sup_cap", E.Cfg(cap_mode="sup", force_bet=True, **base), 5),
    ]
    res["hetero"] = []
    for shifted in (False, True):
        res["hetero"] += sim_null(
            f"hetero_shifted={shifted}",
            lambda sd, shifted=shifted: W.make_hetero_stream(hn, S, 5000 + sd, shifted),
            cf,
            S=S,
        )
    # (B) outcome-dependent delay on a G1 null: naive arrived-subset vs in-order prefix release
    w0 = W.LogitWorld(regimes=(W.Regime(),), name="null")
    mk = lambda sd: W.make_stream(w0, S, 6000 + sd)
    res["delay"] = []
    for kind in ("fixed", "uniform", "outcome", "outcome_rev", "heavy", "burst"):
        cfgs = []
        for rel in ("arrived", "prefix"):
            cfgs.append(
                (
                    f"HG_{rel}",
                    E.Cfg(risk="brier", frac=0.2, gamma=0.99, gate_w=100, release=rel),
                    lambda st, kind=kind: W.delays(
                        kind, S, st["loss"].shape[1], st["loss"], d=5, seed=1
                    ),
                )
            )
        res["delay"] += sim_null(f"G1_null_delay={kind}", mk, cfgs, S=S)
    # (C) dependence: AR / cluster latent logit noise (unchanged marginal law)
    res["dependence"] = []
    for nm, kw in (
        ("iid", {}),
        ("ar0.9_s1", {"ar_rho": 0.9, "ar_sigma": 1.0}),
        ("ar0.98_s1.5", {"ar_rho": 0.98, "ar_sigma": 1.5}),
        ("cluster100_s1.5", {"cluster_len": 100, "cluster_sigma": 1.5}),
    ):
        wd = W.LogitWorld(regimes=(W.Regime(),), name=nm, **kw)
        mkd = lambda sd, wd=wd: W.make_stream(wd, S, 7000 + sd)
        cfgs = [
            ("pprm_sup", E.Cfg(risk="brier", frac=0.2), 5),
            ("HG_sup", E.Cfg(risk="brier", frac=0.2, gamma=0.99, gate_w=100), 5),
        ]
        res["dependence"] += sim_null(f"dep_{nm}", mkd, cfgs, S=S)
    with open(f"{OUT}/validity_audit.json", "w") as fh:
        json.dump(res, fh, indent=1)


if __name__ == "__main__":
    main()
