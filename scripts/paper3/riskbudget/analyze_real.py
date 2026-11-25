"""Analysis of the F3 real-stream check: everything in the 'Reported' section of
2026_programme/05F_F3_REAL_STREAM_PROTOCOL.md.  usage: analyze_real.py [REAL_DIR] [OUT_DIR]

Runs within an episode share a tape, so Wilson intervals over runs are optimistic for comparators
(the effective sample size is the number of episodes).
"""

import json
import sys
import zlib
from pathlib import Path

import numpy as np

from shiftlab.paper3.riskbudget.harness import ROOT
from shiftlab.paper3.riskbudget.real_streams import BENEFICIAL, CONDITIONS, HARMFUL, STREAMS

REAL = ROOT / "outputs" / "paper3" / "riskbudget" / "real"
RES = ROOT / "papers/paper3_cost_aware_adaptation/2026_programme/results/riskbudget"
EPS, N_BOOT, MIN_EP = 1e-9, 10000, 6
GROUPS = {f"all{len(STREAMS)}": tuple(STREAMS), "harmful2": HARMFUL, f"beneficial{len(BENEFICIAL)}": BENEFICIAL}
HEAD_ARMS = [
    *["never", "wald_cut", "cusum", "gate_wald", "cusum_rb_h4", "cusum_rb_h8"],
    *["stoploss_h14", "stoploss_h50", "f3_pi1_h6", "f3_pi1_h14", "f3_pi1_h24"],
    *["f3_pi1_h50", "f3_pi1_h100", "f3v2d_h14", "f3v2d_h50", "f3v2d_h100", "f3v2_blind8_h14"],
]
R_LIST = {6: 16, 14: 24, 24: 34, 50: 60, 100: 110}
BUDGET_PREFIX = ("stoploss_h", "f3_pi1_h", "f3v2d_h", "f3v2_blind8_h")


def wilson(k, n, z=1.959964):
    p = k / n
    c = p + z * z / (2 * n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    d = 1 + z * z / n
    return max(0.0, (c - h) / d), min(1.0, (c + h) / d)


def arr(d, name, key):  # (E, S)
    v = d["fields"][key][d["arms"].index(name)]
    return np.array([[np.nan if x is None else x for x in row] for row in v], float)


def boot_ci(diff_ep, stream):
    """diff_ep: (E,) episode means (seeds averaged first). Cluster bootstrap over episodes."""
    e = len(diff_ep)
    if e < MIN_EP:
        return None
    rng = np.random.default_rng([0, zlib.crc32(stream.encode())])
    bs = diff_ep[rng.integers(0, e, (N_BOOT, e))].mean(1)
    lo, hi = np.percentile(bs, [2.5, 97.5])
    return float(lo), float(hi)


def own_R(name):
    if name.startswith(BUDGET_PREFIX):
        return R_LIST[int(name.rsplit("_h", 1)[1])]
    return None


def exceed(sup, R):
    k, n = int(np.sum(sup > R + EPS)), sup.size
    lo, hi = wilson(k, n)
    return {"k": k, "n": n, "rate": k / n, "lo": lo, "hi": hi}


def stream_stats(d, stream):
    arms = d["arms"]
    J = {a: arr(d, a, "J") for a in arms}
    Jep = {a: np.nanmean(J[a], 1) for a in arms}
    out = {"n_episodes": d["n_episodes"], "arms": {}}
    for a in arms:
        sup = arr(d, a, "sup_harm").ravel()
        s = {
            "J": float(np.mean(J[a])),
            "labels": float(np.mean(arr(d, a, "n_queries"))),
            "deployed": float(np.mean(arr(d, a, "frac_time_deployed"))),
            "switches": float(np.mean(arr(d, a, "n_switches"))),
            "sup_q95": float(np.quantile(sup, 0.95)),
            "sup_q99": float(np.quantile(sup, 0.99)),
            "sup_max": float(sup.max()),
        }
        fr = arr(d, a, "n_forced_rollbacks")
        s["forced_rollbacks"] = None if np.isnan(fr).all() else float(np.nanmean(fr))
        for ref in ("wald_cut", "never"):
            diff = Jep[a] - Jep[ref]
            s[f"d_{ref}"] = {"delta": float(diff.mean()), "ci": boot_ci(diff, stream)}
        r = own_R(a)
        if r is not None:
            s["R"] = r
            s["violation"] = exceed(sup, r)
        else:
            s["exceed"] = {str(R): exceed(sup, R) for R in R_LIST.values()}
        out["arms"][a] = s
    return out


def sig(ci, delta):
    """+1 if CI excludes 0 from above (worse), -1 if from below (better), 0 else/None."""
    if ci is None:
        return None
    return 1 if ci[0] > 0 else (-1 if ci[1] < 0 else 0)


def pooled(per_stream, streams, arms):
    out = {}
    for a in arms:
        ss = [per_stream[s]["arms"][a] for s in streams]
        p = {
            "J": float(np.mean([x["J"] for x in ss])),
            "labels": float(np.mean([x["labels"] for x in ss])),
            "deployed": float(np.mean([x["deployed"] for x in ss])),
            "sup_max": float(max(x["sup_max"] for x in ss)),
        }
        fr = [x["forced_rollbacks"] for x in ss if x["forced_rollbacks"] is not None]
        p["forced_rollbacks"] = float(np.mean(fr)) if fr else None
        for ref in ("wald_cut", "never"):
            k = f"d_{ref}"
            sg = [sig(x[k]["ci"], x[k]["delta"]) for x in ss]
            p[k] = {
                "mean_delta": float(np.mean([x[k]["delta"] for x in ss])),
                "n_streams_with_ci": int(sum(v is not None for v in sg)),
                "n_better": int(sum(v == -1 for v in sg)),
                "n_worse": int(sum(v == 1 for v in sg)),
            }
        if "violation" in ss[0]:
            kk, nn = sum(x["violation"]["k"] for x in ss), sum(x["violation"]["n"] for x in ss)
            p["violation"] = {"k": kk, "n": nn, "rate": kk / nn, "ci": wilson(kk, nn)}
        else:
            p["exceed"] = {}
            for R in R_LIST.values():
                kk = sum(x["exceed"][str(R)]["k"] for x in ss)
                nn = sum(x["exceed"][str(R)]["n"] for x in ss)
                p["exceed"][str(R)] = {"k": kk, "n": nn, "rate": kk / nn, "ci": wilson(kk, nn)}
        out[a] = p
    return out


# ------------------------------------------------------------------------------ markdown
def f2(x):
    return "n/a" if x is None else f"{x:.2f}"


def fci(s):
    d, ci = s["delta"], s["ci"]
    return f"{d:+.2f}" if ci is None else f"{d:+.2f} [{ci[0]:+.2f},{ci[1]:+.2f}]"


def md_table(header, rows):
    return (
        "| "
        + " | ".join(header)
        + " |\n|"
        + "|".join("---" for _ in header)
        + "|\n"
        + "\n".join("| " + " | ".join(map(str, r)) + " |" for r in rows)
        + "\n"
    )


def viol_cell(s):
    if "violation" in s:
        v = s["violation"]
        return f"{v['k']}/{v['n']} ({v['lo']:.3f}-{v['hi']:.3f})"
    return "; ".join(f"R{R}:{s['exceed'][str(R)]['k']}" for R in R_LIST.values())


def render(S, arms):
    L = [
        "# F3 real-stream check: tables (protocol 05F)\n",
        (
            "Label EXPOSED_STREAMS_FROZEN_CONFIG. J is the mean cost per episode (T=2000), mean over the "
            "20 policy seeds and the stream's episodes. Delta J = arm minus reference (negative is "
            "better); brackets are 95% episode-cluster bootstrap CIs (seeds averaged within episode, "
            "10,000 resamples), absent for streams with fewer than 6 episodes. Runs within an episode "
            "share a tape, so the Wilson intervals are optimistic, most of all for comparators.\n"
        ),
        (
            "Budgets: arm suffix h means R = 10 + h (h6: 16, h14: 24, h24: 34, h50: 60, h100: 110). "
            "Violation = sup-harm > own R (budget arms); comparator cells list the number of runs with "
            "sup-harm above each R.\n"
        ),
    ]
    for c in CONDITIONS:
        P = S[c]["pooled"]
        L.append(f"\n## Condition: {c}\n")
        L.append(
            "### Headline (pooled over streams with equal weight; 'sig' = streams whose own CI "
            "excludes 0, better/worse; streams with <6 episodes have no CI)\n"
        )
        for g in GROUPS:
            rows = []
            for a in HEAD_ARMS:
                p = P[g][a]
                v = p.get("violation")
                vs = (
                    f"{v['k']}/{v['n']}"
                    if v
                    else f"R24:{p['exceed']['24']['k']} R60:{p['exceed']['60']['k']}"
                )
                w, n = p["d_wald_cut"], p["d_never"]
                rows.append(
                    [
                        a,
                        f2(p["J"]),
                        f"{w['mean_delta']:+.2f}",
                        f"{w['n_better']}/{w['n_worse']} of {w['n_streams_with_ci']}",
                        f"{n['mean_delta']:+.2f}",
                        f"{n['n_better']}/{n['n_worse']} of {n['n_streams_with_ci']}",
                        f"{p['sup_max']:.0f}",
                        vs,
                        f2(p["labels"]),
                        f"{p['deployed']:.3f}",
                        f2(p["forced_rollbacks"]),
                    ]
                )
            L.append(f"\n#### {g}\n")
            L.append(
                md_table(
                    [
                        "arm",
                        "J",
                        "dJ vs wald_cut",
                        "sig b/w",
                        "dJ vs never",
                        "sig b/w",
                        "max sup-harm",
                        "violations (own R) or exceed",
                        "labels",
                        "deployed",
                        "forced rb",
                    ],
                    rows,
                )
            )
        streams = list(S[c]["streams"])
        st = S[c]["streams"]
        sections = [
            ("Mean J", lambda s: f2(s["J"])),
            ("Delta J vs wald_cut", lambda s: fci(s["d_wald_cut"])),
            ("Delta J vs never", lambda s: fci(s["d_never"])),
            ("Sup-harm q95/q99/max", lambda s: f"{s['sup_q95']:.0f}/{s['sup_q99']:.0f}/{s['sup_max']:.0f}"),
            ("Violations of own R: k/n (Wilson 95%); comparators: runs above R16/24/34/60/110", viol_cell),
            ("Labels used", lambda s: f2(s["labels"])),
            ("Deployed fraction", lambda s: f"{s['deployed']:.3f}"),
            ("Forced rollbacks (mean)", lambda s: f2(s["forced_rollbacks"])),
        ]  # fmt: skip
        for title, fn in sections:
            L.append(f"\n### {c}: {title}\n")
            rows = [[a] + [fn(st[s]["arms"][a]) for s in streams] for a in arms]
            L.append(md_table(["arm"] + streams, rows))
    return "".join(L)


def main(real=REAL, res=RES):
    S = {}
    for c in CONDITIONS:
        per = {}
        for s in STREAMS:
            d = json.loads((Path(real) / c / f"{s}.json").read_text())
            per[s] = stream_stats(d, s)
            arms = d["arms"]
        S[c] = {
            "streams": per,
            "pooled": {g: pooled(per, ss, arms) for g, ss in GROUPS.items()},
        }
    Path(res).mkdir(parents=True, exist_ok=True)
    (Path(res) / "real_summary.json").write_text(
        json.dumps(
            {
                "label": "EXPOSED_STREAMS_FROZEN_CONFIG",
                "arms": arms,
                "R_by_h": R_LIST,
                "results": S,
            },
            indent=1,
        )
    )
    (Path(res) / "real_tables.md").write_text(render(S, arms))


if __name__ == "__main__":
    main(*sys.argv[1:3])
