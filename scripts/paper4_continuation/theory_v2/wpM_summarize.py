"""Summarise wpM scaling results (partial jsonl or compact json) into MIXING_SCALING.md tables. Data only."""
import json, sys, collections
from fractions import Fraction as F

src, out = sys.argv[1], sys.argv[2]
if src.endswith(".jsonl"):
    rows = [json.loads(l) for l in open(src) if l.strip()]
    for r in rows:
        r.setdefault("rho_mid", r.get("rho_mid"))
else:
    rows = json.load(open(src))["cells"]
g = collections.defaultdict(dict)
for r in rows:
    g[(str(F(r["t01"])), r["d"], str(F(r["k"])), r["B"], str(F(r["alpha"])))][r["T"]] = r
st = collections.Counter(r["status"] for r in rows)
L = ["# Mixing-chain scaling: certified rho_Gamma vs horizon T (data only)", "",
     f"Cell statuses: {dict(st)}. rho = Gamma/(C0 - V*_IID), C0 = T/2; entries are midpoint [certified interval low, high]; "
     "Gamma and VOI (= C0 - V*_IID) midpoints shown as G / V. '-' = not ok (timeout / skipped / not run).", ""]
flags = []
fams = sorted({k[:4] for k in g}, key=lambda k: (k[0], k[1], k[2], k[3]))
for fam in fams:
    t, d, k, B = fam
    L.append(f"## t={t}, d={d}, k={k}, B={B}")
    alphas = sorted({a for kk in g if kk[:4] == fam for a in [kk[4]]}, key=F)
    Ts = sorted({T for a in alphas for T in g[fam + (a,)]})
    L.append("| T | " + " | ".join(f"alpha={a}: rho [lo,hi]; G; V" for a in alphas) + " |")
    L.append("|---|" + "---|" * len(alphas))
    for T in Ts:
        cells = []
        for a in alphas:
            r = g[fam + (a,)].get(T)
            if not r or r["status"] != "ok" or r.get("rho_mid") is None:
                cells.append("-" if not r else r["status"])
            else:
                ri = r.get("rho_interval") or [float("nan")] * 2
                cells.append(f"{r['rho_mid']:.4f} [{ri[0]:.4f},{ri[1]:.4f}]; {r['Gamma_mid_f']:.4f}; {r['VOI_mid_f']:.4f}")
        L.append(f"| {T} | " + " | ".join(cells) + " |")
    L.append("")
    for a in alphas:
        ok = {T: r for T, r in g[fam + (a,)].items() if r["status"] == "ok" and r.get("rho_mid") is not None}
        if len(ok) < 2:
            continue
        Tmax = max(ok); Tmin = min(ok)
        r12 = ok.get(12)
        ratio = ok[Tmax]["rho_mid"] / ok[Tmin]["rho_mid"] if ok[Tmin]["rho_mid"] > 0 else None
        beyond = ok[Tmax]["rho_mid"] / r12["rho_mid"] if (r12 and Tmax > 12 and r12["rho_mid"] > 0) else None
        flags.append((fam, a, Tmin, Tmax, ratio, beyond))
L.append("## Ratios rho(T_max)/rho(T_min_ok) and rho(T_max)/rho(12) (only where T_max>12)")
L.append("| t | d | k | B | alpha | T_min | T_max | rho(Tmax)/rho(Tmin) | rho(Tmax)/rho(12) | falls >half beyond 12 |")
L.append("|---|---|---|---|---|---|---|---|---|---|")
for fam, a, tmin, tmax, ratio, beyond in flags:
    f = lambda x: "n/a" if x is None else f"{x:.3f}"
    L.append(f"| {fam[0]} | {fam[1]} | {fam[2]} | {fam[3]} | {a} | {tmin} | {tmax} | {f(ratio)} | {f(beyond)} | "
             f"{'n/a' if beyond is None else ('YES' if beyond < 0.5 else 'no')} |")
open(out, "w").write("\n".join(L) + "\n")
print("wrote", out, len(L), "lines")
