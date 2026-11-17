"""Analysis of the calibrated-comparator study -> results/riskbudget/calib_{summary.json,tables.md}.

Simulation: outputs/paper3/riskbudget/calib_eval (fresh dev seeds 81000-81999).
Real: first run (outputs/.../real) merged with the new arms (outputs/.../real_calib);
THIRD LOOK at the real streams; comparators calibrated on simulation only.
usage: analyze_calib.py
"""

import json

import analyze_real as AR
import numpy as np

from shiftlab.paper3.riskbudget.harness import ROOT, stress_ids
from shiftlab.paper3.riskbudget.real_streams import CONDITIONS, STREAMS, R_of

OUT = ROOT / "outputs" / "paper3" / "riskbudget"
RES = ROOT / "papers/paper3_cost_aware_adaptation/2026_programme/results/riskbudget"
CFG = ROOT / "configs/paper3/f3_calibrated_comparators_v1.json"
EPS, NB = 1e-9, 10000
wilson = AR.wilson
SIM_R = {
    "f3_pi1": (12, 20, 30),
    "f3v2d": (20, 30),
    "stoploss_cal": (12, 20, 30),
    "cusumrb_cal": (12, 20, 30),
}
H_TO_R = {6: 12, 14: 20, 24: 30}


def md(header, rows):
    return AR.md_table(header, rows)


# ------------------------------------------------------------------ simulation
def sim():
    D = {}
    for f in sorted((OUT / "calib_eval").glob("*.json")):
        d = json.loads(f.read_text())
        D[d["regime"]] = d
    rids = list(D)
    arms = D[rids[0]]["arms"]
    stress = [r for r in rids if r in set(stress_ids())]
    orig = [r for r in rids if r not in set(stress)]
    n_seeds = len(D[rids[0]]["seeds"])

    def arr(a, key):  # (regime, seed)
        return np.array([D[g]["fields"][key][arms.index(a)] for g in rids], float)

    def sel(x, grp):
        return x[[rids.index(g) for g in grp]]

    def delta(a, b, grp):
        d = sel(arr(a, "J") - arr(b, "J"), grp).mean(0)
        rng = np.random.default_rng(0)
        bs = d[rng.integers(0, len(d), (NB, len(d)))].mean(1)
        lo, hi = np.percentile(bs, [2.5, 97.5])
        return {"delta": float(d.mean()), "lo": float(lo), "hi": float(hi)}

    def viol(a, R):
        S = arr(a, "sup_harm")
        per = {}
        for g, row in zip(rids, S, strict=True):
            k = int(np.sum(row > R + EPS))
            lo, hi = wilson(k, len(row))
            per[g] = {"k": k, "n": len(row), "rate": k / len(row), "lo": lo, "hi": hi}
        w = max(per, key=lambda g: per[g]["rate"])
        return {"R": R, "worst": w, "worst_stats": per[w], "pooled": float(np.mean([v["rate"] for v in per.values()])),
                "total_k": sum(v["k"] for v in per.values()), "per_regime": per}  # fmt: skip

    out = {"n_regimes": len(rids), "n_seeds": n_seeds, "stress": stress, "arms": {}}
    for a in arms:
        base = a.rsplit("_R", 1)
        R = int(base[1]) if len(base) == 2 and base[1].isdigit() else None
        e = {
            "J": float(arr(a, "J").mean()),
            "J_stress6": float(sel(arr(a, "J"), stress).mean()),
            "J_orig24": float(sel(arr(a, "J"), orig).mean()),
            "labels": float(arr(a, "n_queries").mean()),
            "deployed": float(arr(a, "frac_time_deployed").mean()),
            "sup_max": float(arr(a, "sup_harm").max()),
            "d_never": {n: delta(a, "never", g) for n, g in (("all", rids), ("stress6", stress), ("orig24", orig))},
        }  # fmt: skip
        if R is not None:
            e["R"] = R
            e["violation"] = viol(a, R)
        else:
            e["exceed"] = {str(r): viol(a, r) for r in (12, 20, 30)}
        if a == "never":
            pass
        out["arms"][a] = e
    for a in arms:
        R = out["arms"][a].get("R")
        if a.startswith(("stoploss_cal", "cusumrb_cal")):
            for ref in (f"f3_pi1_R{R}", f"f3v2d_R{R}"):
                if ref in arms:
                    out["arms"][a][f"d_{ref.split('_R')[0]}"] = {
                        n: delta(a, ref, g) for n, g in (("all", rids), ("stress6", stress), ("orig24", orig))
                    }  # fmt: skip
            out["arms"][a]["d_wald_cut"] = {"all": delta(a, "wald_cut", rids)}
    out["arms"]["wald_cut"]["d_f3_pi1_R20"] = {"all": delta("wald_cut", "f3_pi1_R20", rids)}
    return out


def sim_md(S, cfg):
    A = S["arms"]
    L = ["# Calibrated comparators: simulation evaluation (fresh dev seeds 81000-81999)\n\n"]
    L.append(
        f"{S['n_regimes']} regimes (stress-6 = regimes_f3_v1, original-24 = regimes_v1), {S['n_seeds']} seeds per regime, "
        "T = 300, k = 3. J = pooled mean over regimes and seeds (lower is better). Delta J = arm minus reference, "
        "95% seed-cluster bootstrap CI (10,000 resamples; seeds shared across regimes). Violation = P(sup H > own R); "
        "worst regime with Wilson 95% interval.\n\n"
    )
    rows = []
    for a, e in A.items():
        if "violation" in e:
            v = e["violation"]
            w = v["worst_stats"]
            vs = f"{w['rate']:.3f} [{w['lo']:.3f},{w['hi']:.3f}] {v['worst']}"
            pv = f"{v['pooled']:.4f}"
        else:
            x = e["exceed"]["20"]
            w = x["worst_stats"]
            vs = f"(R=20) {w['rate']:.3f} [{w['lo']:.3f},{w['hi']:.3f}] {x['worst']}"
            pv = f"(R=20) {x['pooled']:.4f}"
        dn = e["d_never"]["all"]
        pi = e.get("d_f3_pi1", {}).get("all")
        rows.append([a, f"{e['J']:.2f}", f"{dn['delta']:+.2f} [{dn['lo']:+.2f},{dn['hi']:+.2f}]",
                     "" if pi is None else f"{pi['delta']:+.2f} [{pi['lo']:+.2f},{pi['hi']:+.2f}]",
                     vs, pv, f"{e['labels']:.1f}", f"{e['deployed']:.3f}"])  # fmt: skip
    L.append("## Pooled over 30 regimes\n\n")
    L.append(md(["arm", "J", "dJ vs never", "dJ vs f3_pi1 (same R)", "worst-regime violation [Wilson] regime",
                 "pooled violation", "labels", "deployed"], rows))  # fmt: skip
    for grp, key in (("stress-6", "stress6"), ("original-24", "orig24")):
        rows = []
        for a, e in A.items():
            dn = e["d_never"][key]
            pi = e.get("d_f3_pi1", {}).get(key)
            rows.append([a, f"{e['J_' + ('stress6' if key == 'stress6' else 'orig24')]:.2f}",
                         f"{dn['delta']:+.2f} [{dn['lo']:+.2f},{dn['hi']:+.2f}]",
                         "" if pi is None else f"{pi['delta']:+.2f} [{pi['lo']:+.2f},{pi['hi']:+.2f}]"])  # fmt: skip
        L.append(f"\n## {grp}\n\n")
        L.append(md(["arm", "J", "dJ vs never", "dJ vs f3_pi1 (same R)"], rows))
    L.append("\n## Calibrated comparators vs f3v2d (same R) and vs wald_cut\n\n")
    rows = []
    for a, e in A.items():
        if "d_f3v2d" in e:
            d = e["d_f3v2d"]["all"]
            rows.append([a, f"{d['delta']:+.2f} [{d['lo']:+.2f},{d['hi']:+.2f}]"])
    L.append(md(["arm", "dJ vs f3v2d (same R)"], rows))
    rows = []
    for a, e in A.items():
        if "d_wald_cut" in e:
            d = e["d_wald_cut"]["all"]
            rows.append([a, f"{d['delta']:+.2f} [{d['lo']:+.2f},{d['hi']:+.2f}]"])
    L.append("\n" + md(["arm", "dJ vs wald_cut"], rows))
    L.append(
        "\n## Regimes where a calibrated comparator exceeds 0.05 on the fresh seeds (rate [Wilson])\n\n"
    )
    rows = []
    for a, e in A.items():
        if a.startswith(("stoploss_cal", "cusumrb_cal")):
            bad = sorted(
                ((g, v) for g, v in e["violation"]["per_regime"].items() if v["rate"] > 0.05),
                key=lambda x: -x[1]["rate"],
            )
            rows.append([a, f"{len(bad)}/{S['n_regimes']}",
                         "; ".join(f"{g} {v['rate']:.3f} [{v['lo']:.3f},{v['hi']:.3f}]" for g, v in bad[:8]) or "none"])  # fmt: skip
    L.append(md(["arm", "regimes > .05", "worst regimes"], rows))
    L.append("\n## Calibration (calibration seeds 80000-80199) and its frontier\n\n")
    st = cfg["standard"]
    L.append(f"Standard: violation <= {st['violation_rate_max_every_regime']} in every one of {st['n_regimes']} regimes; "
             f"{st['n_seeds']} calibration seeds.\n\n")  # fmt: skip
    rows = []
    for R, ent in cfg["calibration"].items():
        for kind, x in ent.items():
            fresh = A.get(f"{kind}_{R}")
            fv = fresh["violation"]["worst_stats"]["rate"] if fresh else None
            rows.append([R, kind, x["chosen"], "yes" if x["standard_reached"] else "NO",
                         f"{x['chosen_stats']['worst_viol']:.3f} ({x['chosen_stats']['worst_regime']})",
                         f"{x['chosen_stats']['pooled_J']:.2f}", f"{fv:.3f}"])  # fmt: skip
    L.append(md(["R", "comparator", "chosen (c or h_c)", "standard reached", "calib worst viol (regime)",
                 "calib pooled J", "fresh worst viol"], rows))  # fmt: skip
    for R, ent in cfg["calibration"].items():
        for kind, x in ent.items():
            L.append(f"\n### Frontier {kind} {R}\n\n")
            rows = [[f["value"], f"{f['pooled_J']:.2f}", f"{f['worst_viol']:.3f}", f["worst_regime"],
                     f"{f['pooled_viol']:.4f}", "yes" if f["meets"] else ""] for f in x["frontier"]]  # fmt: skip
            L.append(
                md(
                    [
                        "value",
                        "pooled J",
                        "worst-regime viol",
                        "worst regime",
                        "pooled viol",
                        "meets",
                    ],
                    rows,
                )
            )
    return "".join(L)


# ------------------------------------------------------------------ real
OLD_ARMS = ["never", "wald_cut", "stoploss_h6", "stoploss_h14", "stoploss_h24", "f3_pi1_h6",
            "f3_pi1_h14", "f3_pi1_h24", "f3v2d_h14"]  # fmt: skip
NEW_ARMS = [f"{k}_h{h}" for k in ("stoploss_cal", "cusumrb_cal") for h in H_TO_R]


def merged(cond, stream):
    old = json.loads((OUT / "real" / cond / f"{stream}.json").read_text())
    new = json.loads((OUT / "real_calib" / cond / f"{stream}.json").read_text())
    assert old["seeds"] == new["seeds"] and old["n_episodes"] == new["n_episodes"]
    arms = OLD_ARMS + NEW_ARMS
    fields = {}
    for f in old["fields"]:
        if f not in new["fields"]:
            continue
        fields[f] = [
            (old if a in OLD_ARMS else new)["fields"][f][
                (old if a in OLD_ARMS else new)["arms"].index(a)
            ]
            for a in arms
        ]
    chk = np.array(old["fields"]["J"][old["arms"].index("never")], float)
    chk2 = np.array(new["fields"]["J"][new["arms"].index("never")], float)
    assert np.allclose(chk, chk2), "never differs between the two real runs"
    return {"arms": arms, "fields": fields, "n_episodes": old["n_episodes"], "stream": stream}


def boot_group(Jep, streams, a, b, rng):
    """hierarchical bootstrap: resample episodes within streams, equal-weight mean over streams."""
    d = {s: Jep[s][a] - Jep[s][b] for s in streams}
    pt = float(np.mean([x.mean() for x in d.values()]))
    bs = np.zeros(NB // 2)
    for x in d.values():
        bs += x[rng.integers(0, len(x), (NB // 2, len(x)))].mean(1)
    bs /= len(d)
    lo, hi = np.percentile(bs, [2.5, 97.5])
    return {"delta": pt, "lo": float(lo), "hi": float(hi)}


def real():
    AR.BUDGET_PREFIX = (*AR.BUDGET_PREFIX, "stoploss_cal_h", "cusumrb_cal_h")
    S = {}
    for c in CONDITIONS:
        per, Jep = {}, {}
        for s in STREAMS:
            d = merged(c, s)
            per[s] = AR.stream_stats(d, s)
            Jep[s] = {a: np.nanmean(AR.arr(d, a, "J"), 1) for a in d["arms"]}
        arms = OLD_ARMS + NEW_ARMS
        pooled = {g: AR.pooled(per, ss, arms) for g, ss in AR.GROUPS.items()}
        rng = np.random.default_rng(1)
        boots = {}
        for g, ss in AR.GROUPS.items():
            boots[g] = {}
            for a in NEW_ARMS:
                h = a.rsplit("_h", 1)[1]
                refs = {"never": "never", "wald_cut": "wald_cut", "f3_pi1": f"f3_pi1_h{h}"}
                boots[g][a] = {k: boot_group(Jep, ss, a, r, rng) for k, r in refs.items()}
            for h in H_TO_R:
                boots[g][f"f3_pi1_h{h}"] = {"never": boot_group(Jep, ss, f"f3_pi1_h{h}", "never", rng),
                                            "wald_cut": boot_group(Jep, ss, f"f3_pi1_h{h}", "wald_cut", rng)}  # fmt: skip
        S[c] = {"streams": per, "pooled": pooled, "boot": boots}
    return S


def real_md(S):
    L = [
        "\n# Calibrated comparators: real streams (THIRD LOOK; comparators calibrated on simulation only)\n\n"
    ]
    L.append("14 cached streams, 230 episodes, T = 2000, B = 200, k = 5, 20 policy seeds (60000-60019) as in the first run. "
             "Budget R = 10 + h; calibrated margin / threshold transferred by headroom (h6 -> R12, h14 -> R20, h24 -> R30 "
             "calibration). Violation = sup-harm > 10 + h, counted over runs (Wilson 95%; optimistic because runs share "
             "tapes). Delta J: equal-weight mean over streams of the per-stream difference; 95% CI by episode-within-stream "
             "bootstrap (5,000 resamples). 'stoploss_hX' is the uncalibrated first-run stop-loss.\n")  # fmt: skip
    for c in CONDITIONS:
        P, B = S[c]["pooled"], S[c]["boot"]
        L.append(f"\n## Condition: {c}\n")
        for g in AR.GROUPS:
            rows = []
            for a in OLD_ARMS + NEW_ARMS:
                p = P[g][a]
                v = p.get("violation")
                vs = (
                    f"{v['k']}/{v['n']} ({v['ci'][0]:.3f}-{v['ci'][1]:.3f})"
                    if v
                    else f"R24:{p['exceed']['24']['k']}"
                )
                b = B[g].get(a)
                dn = dw = dp = ""
                if b:
                    f_ = lambda x: f"{x['delta']:+.1f} [{x['lo']:+.1f},{x['hi']:+.1f}]"
                    dn, dw = f_(b["never"]), f_(b["wald_cut"])
                    dp = f_(b["f3_pi1"]) if "f3_pi1" in b else ""
                rows.append([a, f"{p['J']:.1f}", dn, dw, dp, f"{p['sup_max']:.0f}", vs, f"{p['labels']:.1f}",
                             f"{p['deployed']:.3f}", AR.f2(p["forced_rollbacks"])])  # fmt: skip
            L.append(f"\n#### {g}\n\n")
            L.append(md(["arm", "J", "dJ vs never", "dJ vs wald_cut", "dJ vs f3_pi1 (same h)", "max sup-harm",
                         "violations (own R) k/n (Wilson)", "labels", "deployed", "forced rb"], rows))  # fmt: skip
        st = S[c]["streams"]
        for title, fn in (
            ("Mean J", lambda s: AR.f2(s["J"])),
            ("Violations of own R at h=14 (k/n)", lambda s: f"{s['violation']['k']}/{s['violation']['n']}" if "violation" in s else f"R24:{s['exceed']['24']['k']}"),
            ("Delta J vs never", lambda s: AR.fci(s["d_never"])),
        ):  # fmt: skip
            L.append(f"\n### {c}, per stream at h=14: {title}\n\n")
            arms14 = [
                "never",
                "wald_cut",
                "stoploss_h14",
                "f3_pi1_h14",
                "f3v2d_h14",
                "stoploss_cal_h14",
                "cusumrb_cal_h14",
            ]
            L.append(
                md(
                    ["arm", *STREAMS],
                    [[a, *[fn(st[s]["arms"][a]) for s in STREAMS]] for a in arms14],
                )
            )
    return "".join(L)


def main():
    cfg = json.loads(CFG.read_text())
    S = sim()
    text = sim_md(S, cfg)
    summ = {
        "label_sim": "fresh dev seeds 81000-81999; calibration seeds 80000-80199",
        "calibration": cfg,
        "sim": S,
    }
    if (OUT / "real_calib").exists():
        R = real()
        summ["real"] = {"label": "THIRD LOOK at the real streams; comparators calibrated on simulation only",
                        "results": R, "R_by_h": {str(h): R_of(h) for h in H_TO_R}}  # fmt: skip
        text += real_md(R)
    RES.mkdir(parents=True, exist_ok=True)
    (RES / "calib_summary.json").write_text(json.dumps(summ, indent=1))
    (RES / "calib_tables.md").write_text(text)
    print("wrote", RES / "calib_tables.md")


if __name__ == "__main__":
    main()
