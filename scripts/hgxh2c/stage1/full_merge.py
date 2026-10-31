"""Merge reduced or full (paper-budget) Stage-1 results into one machine-readable JSON consumed by scripts/hgxh2c/make_report.py.
Usage: python full_merge.py reduced|full   -> outputs/hgxh2c/stage1/reduced_summary.json | outputs/hgxh2c/stage1_full/full_summary.json
Missing pieces are skipped (the summary lists what it found), so it can be run on partial results."""

import glob
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
BOP = ROOT / "tmp/repro_sources/betting_on_predictions/results"
RED = ROOT / "outputs/hgxh2c/stage1"
FULL = ROOT / "outputs/hgxh2c/stage1_full"
RM_RED = RED / "risk_monitor_out/risk_monitor_cfg/uci_cbm_abs_res_12500"
RM_FULL = FULL / "risk_monitor_out/rm_cfg/uci_cbm_abs_res_12500"


def jl(p):
    try:
        return json.loads(Path(p).read_text("utf-8"))
    except (OSError, ValueError):
        return None


def bop(roots):
    import bop_summarize

    roots = [r for r in roots if r.exists()]
    return bop_summarize.load_merged([str(r) for r in roots]) if roots else None


def rm(groups):
    import rm_summarize

    out = {}
    for name, dirs in groups.items():
        dirs = [
            str(d) for d in dirs if Path(d).exists() and (Path(d) / "pmeb_eprocess.pt").exists()
        ]
        if dirs:
            out[name] = rm_summarize.summarize_dirs(dirs, merge=True)["merged"]
    return out or None


def xu(csvs):
    import csv
    import statistics

    rows = []
    for c in csvs:
        if Path(c).exists():
            with open(c, encoding="utf-8") as fh:
                rows += list(csv.reader(fh))[1:]
    if not rows:
        return None
    by = {}
    for r in rows:  # columns: index, Method, beta-hat
        by.setdefault(r[1], []).append(float(r[-1]))
    return {
        "n_trials": min(len(v) for v in by.values()),
        "beta_hat": {
            m: {
                "mean": statistics.mean(v),
                "sd": statistics.stdev(v) if len(v) > 1 else None,
                "n": len(v),
            }
            for m, v in by.items()
        },
    }


def pprm(files):
    import numpy as np

    out = {}
    for sc in ("drift", "nominal"):
        runs = []
        for f in files:
            r = jl(f)
            if r and r.get(sc, {}).get("raw_runs"):
                runs += r[sc]["raw_runs"]
        if not runs:
            continue
        s = {"streams": len(runs)}
        for k in ("srm", "pp_fixed", "pp_adapt"):
            t = [x[k] for x in runs if x[k] is not None]
            s[k] = {
                "alarm_rate": len(t) / len(runs),
                "mean_alarm_t": float(np.mean(t)) if t else None,
                "sd": float(np.std(t)) if t else None,
            }
        for a, b in (("pp_adapt", "pp_fixed"), ("pp_adapt", "srm")):
            d = [x[a] - x[b] for x in runs if x[a] is not None and x[b] is not None]
            s[f"paired_{a}_minus_{b}"] = (
                {
                    "mean": float(np.mean(d)),
                    "se": float(np.std(d, ddof=1) / len(d) ** 0.5) if len(d) > 1 else None,
                    "n": len(d),
                }
                if d
                else None
            )
        out[sc] = s
    return out or None


def reduced():
    s = {"kind": "reduced"}
    s["tenzer_label_shift"] = bop([BOP / "simulations"]) and {
        k: v for k, v in bop([BOP / "simulations"]).items() if k.startswith("label_shift")
    }
    s["tenzer_concept_shift"] = bop([BOP / "simulations"]) and {
        k: v for k, v in bop([BOP / "simulations"]).items() if k.startswith("concept_shift")
    }
    s["timans"] = rm(
        {
            "approx_w0": [RM_RED / "erc_0.1_0.1_miscover_ts15000_bts1_tw0_approx"],
            "approx_w200": [RM_RED / "erc_0.1_0.1_miscover_ts15000_bts1_tw200_approx_w200"],
            "grapa_w200": [RM_RED / "erc_0.1_0.1_miscover_ts15000_bts1_tw200_grapa_w200"],
        }
    )
    s["ryu_scalar"] = jl(RED / "gambling_cs/result.json")
    s["ryu_multivariate"] = jl(RED / "gambling_cs/multivariate_result.json")
    s["xu"] = xu([RED / "active_rcps_sim/last_beta_dist.csv"])
    r = jl(RED / "pprm_indep/result.json")
    s["pprm"] = (
        pprm([RED / "pprm_indep/result.json"])
        if r and r.get("drift", {}).get("raw_runs")
        else (
            {sc: {k: v for k, v in r[sc].items()} for sc in ("drift", "nominal") if sc in r}
            if r
            else None
        )
    )
    return s, RED / "reduced_summary.json"


def full():
    s = {"kind": "full"}
    bop(sorted(BOP.glob("full_label_c*")) + sorted(BOP.glob("full_concept_c*")))
    # chunk dirs are separate roots per main, so merge per family
    s["tenzer_label_shift"] = bop(sorted(BOP.glob("full_label_c*")))
    s["tenzer_concept_shift"] = bop(sorted(BOP.glob("full_concept_c*")))
    groups = {}
    for tag, nm in (
        ("approx_w0", "approx_w0"),
        ("approx_w200", "approx_w200"),
        ("grapa_w200", "grapa_w200"),
    ):
        groups[nm] = sorted(RM_FULL.glob(f"erc_*_full_{tag}_c*"))
    s["timans"] = rm(groups)
    s["ryu_scalar"] = jl(FULL / "gambling_cs/scalar.json")
    s["ryu_multivariate"] = jl(FULL / "gambling_cs/multivariate.json")
    s["xu"] = xu(sorted(glob.glob(str(FULL / "xu/c*/last_beta_dist.csv"))))
    s["pprm"] = pprm(sorted(glob.glob(str(FULL / "pprm/main_c*.json"))))
    sweep = {}
    for q in ("0.2", "0.1", "0.05", "0.03"):
        v = pprm(
            sorted(glob.glob(str(FULL / f"pprm/sweep_q{q}_c*.json")))
            if q != "0.03"
            else sorted(glob.glob(str(FULL / "pprm/main_c*.json")))
        )
        if v:
            sweep[q] = v["drift"]
    s["pprm_reliance_sweep"] = sweep or None
    return s, FULL / "full_summary.json"


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "full"
    s, path = reduced() if mode == "reduced" else full()
    path.parent.mkdir(parents=True, exist_ok=True)
    s["found"] = sorted(k for k, v in s.items() if v and k not in ("kind",))
    with open(path, "w") as fh:
        json.dump(s, fh, indent=1)
    print("wrote", path, "found:", s["found"])
