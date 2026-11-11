"""Tabulate wpC2 results: max over alpha<=1/2 of Gamma_mid and rho_mid by (family,T,B)."""
import json, sys, collections
J = "docs/paper4_continuation/theory_v2/results/wpC2_relative_premium_v1_compact.json"
D = json.load(open(J))
cells = D["cells"]
st = collections.Counter(c["status"] for c in cells)
print("status", dict(st))
ok = [c for c in cells if c["status"] == "ok"]
fams = ["F_persist", "F_anti", "F_coin"]
def tab(key, fmt):
    for f in fams:
        rows = [c for c in ok if c["family"] == f and c.get(key) is not None]
        Ts = sorted({c["T"] for c in rows}); Bs = sorted({c["B"] for c in rows})
        print(f"\n{f}: max over alpha and configs of {key}  (rows T, cols B)")
        print("| T \\ B | " + " | ".join(map(str, Bs)) + " |"); print("|---" * (len(Bs) + 1) + "|")
        for T in Ts:
            line = []
            for B in Bs:
                v = [c[key] for c in rows if c["T"] == T and c["B"] == B]
                line.append(fmt % max(v) if v else "-")
            print(f"| {T} | " + " | ".join(line) + " |")
tab("Gamma_mid_f", "%.4f"); tab("rho_mid", "%.4f")
best = max((c for c in ok if c.get("rho_mid") is not None), key=lambda c: c["rho_mid"])
print("\nlargest rho", best["rho_mid"], {k: best[k] for k in ("family","T","B","d","t01","t10","e0","e1","k","alpha","Gamma_f","rho_interval")})
over = [c for c in ok if c.get("rho_mid") is not None and c["rho_mid"] > 0.5]
print("B>=2 cells rho_mid>1/2:", len([c for c in over if c["B"] >= 2]), " B=1:", len([c for c in over if c["B"] == 1]))
hi = [c for c in ok if c.get("rho_interval") and c["rho_interval"][1] > 0.5 and c["B"] >= 2]
print("B>=2 cells with rho upper endpoint >1/2:", len(hi))
# per-config trend: for each (cfg, alpha) rho along T at fixed B and along B at fixed T
import itertools
def key(c): return (c["cfg_id"], c["alpha"])
g = collections.defaultdict(dict)
for c in ok:
    if c["rho_mid"] is not None: g[key(c)][(c["T"], c["B"])] = c["rho_mid"]
for name, sel in (("T", lambda a, b: (b, a)), ("B", lambda a, b: (a, b))):
    cnt = collections.Counter()
    for k, d in g.items():
        series = collections.defaultdict(list)
        for (T, B), v in d.items():
            fixed, var = (B, T) if name == "T" else (T, B)
            series[fixed].append((var, v))
        for fx, s in series.items():
            s.sort()
            for (x0, v0), (x1, v1) in zip(s, s[1:]):
                if x1 != x0 + 1: continue
                f = next(c["family"] for c in ok if key(c) == k)
                cnt[(f, "up" if v1 > v0 + 1e-9 else "down" if v1 < v0 - 1e-9 else "flat")] += 1
    print(f"\nrho step-changes in {name} (adjacent steps, fixed other axis):", dict(sorted(cnt.items())))
