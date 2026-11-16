"""Combined analysis of the SECOND LOOK (frozen v3 on the 14 real streams).
usage: analyze_real_v3.py [REAL_DIR] [REAL_V3_DIR] [OUT_DIR]

Uses the statistics of analyze_real.py (episode-cluster bootstrap, equal-weight pooling over 14 /
harmful2 / beneficial12, significance counts, violations, labels) on the first run's arms plus v3,
and adds paired comparisons of v3 against f3_pi1 and f3v2d at the same h (same episodes and seeds).
"""

import json
import sys
from pathlib import Path

import analyze_real as AR
import numpy as np

from shiftlab.paper3.riskbudget.harness import ROOT
from shiftlab.paper3.riskbudget.real_streams import CONDITIONS, HS, STREAMS

AR.BUDGET_PREFIX = (*AR.BUDGET_PREFIX, "v3_h")
REAL = ROOT / "outputs" / "paper3" / "riskbudget" / "real"
REAL3 = ROOT / "outputs" / "paper3" / "riskbudget" / "real_v3"
RES = ROOT / "papers/paper3_cost_aware_adaptation/2026_programme/results/riskbudget"
ARMS = ["never", "wald_cut"] + [
    f"{t}_h{h}" for h in HS for t in ("stoploss", "f3_pi1", "f3v2d", "v3")
]
GROUPS = AR.GROUPS
LABEL = (
    "SECOND LOOK: the 14 streams were seen once with the earlier arms; v3 was designed after that "
    "run (03F section 7) and selected on simulation only."
)


def merge(d1, d2):
    assert d1["seeds"] == d2["seeds"] and d1["n_episodes"] == d2["n_episodes"], "pairing broken"
    arms = d1["arms"] + d2["arms"]
    fields = {f: d1["fields"][f] + d2["fields"][f] for f in d2["fields"]}
    keep = [i for i, a in enumerate(arms) if a in ARMS]
    return {
        "stream": d1["stream"],
        "n_episodes": d1["n_episodes"],
        "arms": [arms[i] for i in keep],
        "fields": {f: [v[i] for i in keep] for f, v in fields.items()},
    }


def paired(d, a, b, stream):
    Ja, Jb = np.nanmean(AR.arr(d, a, "J"), 1), np.nanmean(AR.arr(d, b, "J"), 1)
    diff = Ja - Jb
    return {"delta": float(diff.mean()), "ci": AR.boot_ci(diff, stream)}


def main(real=REAL, real3=REAL3, res=RES):
    S, P = {}, {}
    chk = {}
    for c in CONDITIONS:
        per, pairs = {}, {}
        for s in STREAMS:
            d = merge(
                json.loads((Path(real) / c / f"{s}.json").read_text()),
                json.loads((Path(real3) / c / f"{s}.json").read_text()),
            )
            per[s] = AR.stream_stats(d, s)
            pairs[s] = {
                f"v3_h{h}": {
                    "vs_f3_pi1": paired(d, f"v3_h{h}", f"f3_pi1_h{h}", s),
                    "vs_f3v2d": paired(d, f"v3_h{h}", f"f3v2d_h{h}", s),
                }
                for h in HS
            }
            # deterministic claim: v3 runs without a sampled round never violate
            for h in HS:
                n = f"v3_h{h}"
                v = AR.arr(d, n, "sup_harm") > AR.R_LIST[h] + AR.EPS
                ns = AR.arr(d, n, "n_sampled")
                e = chk.setdefault(c, {}).setdefault(
                    n, {"unsampled_runs": 0, "unsampled_viol": 0, "runs": 0, "viol": 0}
                )
                e["unsampled_runs"] += int((ns == 0).sum())
                e["unsampled_viol"] += int((v & (ns == 0)).sum())
                e["runs"] += int(v.size)
                e["viol"] += int(v.sum())
        arms = list(per[next(iter(STREAMS))]["arms"])
        S[c] = {"streams": per, "pooled": {g: AR.pooled(per, ss, arms) for g, ss in GROUPS.items()}}
        P[c] = {"per_stream": pairs, "pooled": {}}
        for g, ss in GROUPS.items():
            P[c]["pooled"][g] = {}
            for n in [f"v3_h{h}" for h in HS]:
                o = {}
                for ref in ("vs_f3_pi1", "vs_f3v2d"):
                    xs = [pairs[s][n][ref] for s in ss]
                    sg = [AR.sig(x["ci"], x["delta"]) for x in xs]
                    o[ref] = {
                        "mean_delta": float(np.mean([x["delta"] for x in xs])),
                        "n_better": int(sum(v == -1 for v in sg)),
                        "n_worse": int(sum(v == 1 for v in sg)),
                        "n_with_ci": int(sum(v is not None for v in sg)),
                    }
                P[c]["pooled"][g][n] = o
    # flags: any v3 stream/condition with Wilson lower bound above .05
    flags = []
    for c in CONDITIONS:
        for s in STREAMS:
            for h in HS:
                v = S[c]["streams"][s]["arms"][f"v3_h{h}"]["violation"]
                if v["lo"] > 0.05:
                    flags.append({"condition": c, "stream": s, "h": h, **v})
    Path(res).mkdir(parents=True, exist_ok=True)
    (Path(res) / "real_v3_summary.json").write_text(
        json.dumps(
            {
                "label": "SECOND_LOOK_EXPOSED_STREAMS",
                "note": LABEL,
                "R_by_h": AR.R_LIST,
                "arms": ARMS,
                "results": S,
                "v3_paired": P,
                "v3_deterministic_check": chk,
                "v3_flags_wilson_lo_gt_.05": flags,
            },
            indent=1,
        )
    )
    (Path(res) / "real_v3_tables.md").write_text(render(S, P, chk, flags))


def render(S, P, chk, flags):
    L = [
        "# F3 v3 on the 14 real streams: SECOND LOOK (03F section 7, step 4)\n",
        f"**{LABEL}**\n",
        (
            "Label EXPOSED_STREAMS_FROZEN_CONFIG (second look). v3 = `configs/paper3/f3_v3_frozen.json`, "
            "budgets R = 10 + h, window = declared delay, same episodes, tapes and policy seeds as the first "
            "run, so v3 is paired with the earlier arms (`real_tables.md`). J is mean cost per episode "
            "(T = 2000); Delta J = row minus reference (negative is better); brackets are 95% "
            "episode-cluster bootstrap CIs (seeds averaged within episode, 10,000 resamples), absent for "
            "streams with fewer than 6 episodes. 'sig b/w' = streams whose own CI excludes 0 "
            "(better/worse).\n"
        ),
    ]
    for c in CONDITIONS:
        L.append(f"\n## Condition: {c}\n")
        for g in GROUPS:
            Pg = S[c]["pooled"][g]
            L.append(f"\n### {c} / {g}: pooled (equal weight over streams)\n")
            rows = []
            for a in ARMS:
                p = Pg[a]
                v = p.get("violation")
                vs = (
                    f"{v['k']}/{v['n']}"
                    if v
                    else f"R24:{p['exceed']['24']['k']} R60:{p['exceed']['60']['k']}"
                )
                w, n = p["d_wald_cut"], p["d_never"]
                x1 = x2 = ""
                if a.startswith("v3_h"):
                    q = P[c]["pooled"][g][a]
                    x1 = f"{q['vs_f3_pi1']['mean_delta']:+.2f} ({q['vs_f3_pi1']['n_better']}/{q['vs_f3_pi1']['n_worse']})"
                    x2 = f"{q['vs_f3v2d']['mean_delta']:+.2f} ({q['vs_f3v2d']['n_better']}/{q['vs_f3v2d']['n_worse']})"
                rows.append(
                    [
                        a,
                        AR.f2(p["J"]),
                        f"{w['mean_delta']:+.2f}",
                        f"{w['n_better']}/{w['n_worse']} of {w['n_streams_with_ci']}",
                        f"{n['mean_delta']:+.2f}",
                        f"{n['n_better']}/{n['n_worse']} of {n['n_streams_with_ci']}",
                        x1,
                        x2,
                        f"{p['sup_max']:.0f}",
                        vs,
                        AR.f2(p["labels"]),
                        f"{p['deployed']:.3f}",
                        AR.f2(p["forced_rollbacks"]),
                    ]
                )
            L.append(
                AR.md_table(
                    [
                        "arm",
                        "J",
                        "dJ vs wald_cut",
                        "sig b/w",
                        "dJ vs never",
                        "sig b/w",
                        "v3 minus f3_pi1 same h (b/w)",
                        "v3 minus f3v2d same h (b/w)",
                        "max sup-harm",
                        "violations (own R) / exceed",
                        "labels",
                        "deployed",
                        "forced rb",
                    ],
                    rows,
                )
            )
        # per-stream tables
        st = S[c]["streams"]
        streams = list(st)
        L.append(f"\n### {c}: per stream at h = 50 (R = 60)\n")
        rows = []
        for s in streams:
            a = st[s]["arms"]
            pp = P[c]["per_stream"][s]["v3_h50"]
            v = a["v3_h50"]["violation"]
            rows.append(
                [s, st[s]["n_episodes"]]
                + [
                    AR.f2(a[n]["J"])
                    for n in ("never", "wald_cut", "f3_pi1_h50", "f3v2d_h50", "v3_h50")
                ]
                + [
                    AR.fci(a["v3_h50"]["d_wald_cut"]),
                    AR.fci(a["v3_h50"]["d_never"]),
                    AR.fci(pp["vs_f3_pi1"]),
                    AR.fci(pp["vs_f3v2d"]),
                    f"{v['k']}/{v['n']} ({v['lo']:.3f}-{v['hi']:.3f})",
                    AR.f2(a["v3_h50"]["labels"]),
                    f"{a['v3_h50']['deployed']:.3f}",
                    AR.f2(a["v3_h50"]["forced_rollbacks"]),
                ]
            )
        L.append(
            AR.md_table(
                [
                    "stream",
                    "eps",
                    "never",
                    "wald_cut",
                    "f3_pi1_h50",
                    "f3v2d_h50",
                    "v3_h50",
                    "v3 dJ vs wald_cut",
                    "v3 dJ vs never",
                    "v3 minus f3_pi1",
                    "v3 minus f3v2d",
                    "v3 violations (Wilson)",
                    "v3 labels",
                    "v3 deployed",
                    "v3 forced rb",
                ],
                rows,
            )
        )
        for title, key, fn in (
            ("v3 mean J by h", None, lambda a: AR.f2(a["J"])),
            ("v3 violations of own R: k/n (Wilson 95%)", None, AR.viol_cell),
            ("v3 labels used", None, lambda a: AR.f2(a["labels"])),
            ("v3 Delta J vs wald_cut", None, lambda a: AR.fci(a["d_wald_cut"])),
        ):
            L.append(f"\n### {c}: {title}\n")
            rows = [[s] + [fn(st[s]["arms"][f"v3_h{h}"]) for h in HS] for s in streams]
            L.append(AR.md_table(["stream"] + [f"v3_h{h}" for h in HS], rows))
    L.append("\n## Checks\n")
    rows = [
        [c, n, f"{e['viol']}/{e['runs']}", f"{e['unsampled_viol']}/{e['unsampled_runs']}"]
        for c, d in chk.items()
        for n, e in d.items()
    ]
    L.append(
        AR.md_table(
            [
                "condition",
                "arm",
                "violations / runs",
                "violations in runs with no sampled round (must be 0)",
            ],
            rows,
        )
    )
    L.append(
        "\nStream x condition x h cells with Wilson lower bound above .05 for v3: "
        + (
            "none"
            if not flags
            else "; ".join(
                f"{f['condition']}/{f['stream']}/h{f['h']} {f['k']}/{f['n']}" for f in flags
            )
        )
        + "\n"
    )
    return "".join(L)


if __name__ == "__main__":
    main(*(Path(p) for p in sys.argv[1:4]))
