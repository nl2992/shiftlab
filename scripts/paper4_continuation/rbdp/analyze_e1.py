"""Summaries of E1.1 / E1.2 from JSONL (prints markdown-ish tables)."""
import json, os, sys, numpy as np
from fractions import Fraction as F
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import RES
r1 = [json.loads(l) for l in open(os.path.join(RES, "e1_1_wpM.jsonl"))]
print("E1.1 n =", len(r1))
for name in ("dev_Gamma_interval", "dev_Gamma_mid", "dev_VOI_interval", "dev_VOI_mid", "dev_rho", "dev_C0"):
    v = np.array([r[name] for r in r1 if r[name] is not None])
    print(name, "n=%d max=%.3e median=%.3e p90=%.3e p99=%.3e" % (len(v), v.max(), np.median(v), np.percentile(v, 90), np.percentile(v, 99)),
          "n>1e-6:", int((v > 1e-6).sum()), "n>1e-9:", int((v > 1e-9).sum()))
for r in r1:
    if max(r["dev_Gamma_interval"], r["dev_VOI_interval"], r["dev_Gamma_mid"]) > 1e-6:
        print("EXCEEDS", r["cell"], "Gam", r["Gamma_rbdp"], r["Gamma_cert"], "VOI", r["VOI_rbdp"], r["VOI_cert"])
# bound consistency vs certified V: V_iid cert = C0 - VOI_cert, V_causal = V_iid + Gamma
bad = 0
for r in r1:
    Cc = r["causal"]["C0"]; vi = [Cc - r["VOI_cert"][1], Cc - r["VOI_cert"][0]]
    if r["iid"]["U"] < vi[0] - 1e-9 or r["iid"]["L"] > vi[1] + 1e-9:
        bad += 1; print("IID sandwich violated", r["cell"])
print("iid sandwich violations", bad)
print("gap U-L causal: max %.4f median %.4f ; gap/VOI median %.3f" % (
    max(r["causal"]["U"] - r["causal"]["L"] for r in r1), np.median([r["causal"]["U"] - r["causal"]["L"] for r in r1]),
    np.median([(r["causal"]["U"] - r["causal"]["L"]) / r["VOI_rbdp"] for r in r1 if r["VOI_rbdp"] > 1e-9])))
from collections import Counter
for f in ("T", "B"): print(f, sorted(Counter(r["cell"][f] for r in r1).items()))
for f in ("t01", "k", "alpha"): print(f, Counter(r["cell"][f] for r in r1))
print("sum rbdp wall", sum(r["causal"]["wall_s"] + r["iid"]["wall_s"] for r in r1))
print("positive-Gamma cells", sum(r["Gamma_cert"][0] > 0 for r in r1), "; cells w/ VOI~0", sum(r["VOI_rbdp"] < 1e-9 for r in r1))
print("U<Lcert / L>Ucert for causal: need Lc,Uc; only Gamma/VOI available in compact")

r2 = [json.loads(l) for l in open(os.path.join(RES, "e1_2_fresh.jsonl"))]
print("\nE1.2 n =", len(r2), Counter(r["ref"]["status"] for r in r2))
rows = []
for r in r2:
    if r["ref"]["status"] != "ok": continue
    for m, (lk, uk) in (("iid", ("L_IID", "U_IID")), ("causal", ("L_causal", "U_causal"))):
        Lc, Uc = float(F(r["ref"][lk])), float(F(r["ref"][uk]))
        L, U = r[m]["L"], r[m]["U"]
        inside = L - 1e-9 <= Lc and Uc <= U + 1e-9   # RB-DP bracket contains cert interval
        ex = (Lc + Uc) / 2
        rows.append((m, r["cell"], L, U, Lc, Uc, U - ex, ex - L, inside, r[m]["C0"]))
for m in ("iid", "causal"):
    s = [x for x in rows if x[0] == m]
    d = np.array([x[6] for x in s]); lg = np.array([x[7] for x in s])
    print(m, "n=%d" % len(s), "bracket-contains-exact: %d/%d" % (sum(x[8] for x in s), len(s)),
          "U-exact: min %.3e max %.3e median %.3e" % (d.min(), d.max(), np.median(d)),
          "exact-L: min %.3e max %.3e median %.3e" % (lg.min(), lg.max(), np.median(lg)))
    for x in s:
        if not x[8] or x[6] < -1e-9: print("  VIOL", x[1], "L,U", x[2], x[3], "cert", x[4], x[5])
print("cert widths max", max(x[5] - x[4] for x in rows))
print("cells where VOI(exact iid)~0:", sum(1 for r in r2 if r["ref"]["status"]=="ok" and r["iid"]["C0"]-float(F(r["ref"]["U_IID"]))<1e-9))
print("causal<->iid U equal count", sum(abs(r["causal"]["U"]-r["iid"]["U"])<1e-9 for r in r2))
print("max |risk_causal| iid-opt / alpha", max(r["iid"]["risk_causal"]/float(F(r["cell"]["alpha"])) for r in r2))
print("mean runtime ref", np.mean([r["ref"]["runtime_s"] for r in r2]))
