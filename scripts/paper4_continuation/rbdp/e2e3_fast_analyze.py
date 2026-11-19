"""Analysis of e2e3_fast_cells.jsonl (lattice-exact fast solver) vs old-solver e2e3_cells.jsonl and certified data."""
import json, os, sys, hashlib
from fractions import Fraction as F
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
RES = os.path.join(ROOT, "docs/paper4_continuation/rbdp/results")
rd = lambda f: [json.loads(l) for l in open(os.path.join(RES, f))]
rows = rd("e2e3_fast_cells.jsonl"); old = rd("e2e3_cells.jsonl")
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
E3 = {(r["t"], r["B"], r["T"]): r for r in rows if r["kind"] == "E3"}
OLD = {(r["t"], r["B"], r["T"]): r for r in old if r["kind"] == "E3"}
rr = lambda t: float(2 * F(t) - 1)
def m1(t, T):
    r = rr(t); n = T - 1
    return (1 - r) / 2 if n % 2 == 0 else (1 - r) * (1 + r ** n) / (2 * (1 - r ** (n + 1)))
P = print; out = {"script_sha256": sha(__file__), "solver_sha256": sha(os.path.join(ROOT, "src/shiftlab/paper4/risk_budget_dp_fast.py"))}
P("M1 max dev:", {t: max(abs(r["rho_Gamma"] - m1(t, T)) for (tt, B, T), r in E3.items() if B == 1 and tt == t) for t in ("2/3", "3/4", "9/10")})
P("max (U-L) over E3 cells: causal %.3e iid %.3e; max rho bracket width %.3e" % (
    max(r["causal"]["U"] - r["causal"]["L"] for r in E3.values()), max(r["iid"]["U"] - r["iid"]["L"] for r in E3.values()),
    max(r["rho_hi"] - r["rho_lo"] for r in E3.values())))
curves = {}
for t in ("2/3", "3/4", "9/10"):
    Ts = sorted({k[2] for k in E3 if k[0] == t})
    P(f"\n### t={t} (r={rr(t):.4g}) rho_Gamma(T)  [point from U; bracket half-width in parens if > 1e-4]")
    P("| B | " + " | ".join(f"T={T}" for T in Ts) + " |"); P("|---|" + "---|" * len(Ts))
    for B in range(1, 9):
        if not any((t, B, T) in E3 for T in Ts): continue
        cells = []
        for T in Ts:
            r = E3.get((t, B, T))
            if not r: cells.append("-"); continue
            w = (r["rho_hi"] - r["rho_lo"]) / 2
            cells.append(f"{r['rho_Gamma']:.4f}" + (f" (±{w:.4f})" if w > 1e-4 else ""))
        P(f"| {B} | " + " | ".join(cells) + " |")
        curves[(t, B)] = sorted(T for T in Ts if (t, B, T) in E3)
P("\n### level-off table")
P("| t | B | last 3 T | last 3 rho | rel chg last two | VOI_c(last) | VOI_i(last) | Gamma(last) | iid-pol causal risk | causal-pol causal risk |"); P("|---|---|---|---|---|---|---|---|---|---|")
lev = []
for (t, B), Ts in sorted(curves.items()):
    L3 = Ts[-3:]; v = [E3[(t, B, T)]["rho_Gamma"] for T in L3]; l = E3[(t, B, Ts[-1])]
    rc = (v[-1] - v[-2]) / v[-2] if len(v) > 1 else float('nan')
    lev.append(dict(t=t, B=B, T=L3, rho=v, rel=rc))
    P(f"| {t} | {B} | {L3} | {', '.join(f'{x:.4f}' for x in v)} | {rc:+.2%} | {l['VOI_causal']:.5f} | {l['VOI_iid']:.5f} | {l['Gamma']:.3e} | {l['iid']['risk_causal']:.4f} | {l['causal']['risk_causal']:.4f} |")
out["level_off"] = lev
for t in ("2/3", "3/4", "9/10"):
    P(f"\n### t={t} VOI_causal/VOI_iid")
    for B in range(1, 9):
        Ts = curves.get((t, B), [])
        if Ts: P(f"B={B}: " + "; ".join(f"T={T}: {E3[(t,B,T)]['VOI_causal']:.5f}/{E3[(t,B,T)]['VOI_iid']:.5f}" for T in Ts))
P("\n### M4 (B=2)")
for t in ("2/3", "3/4", "9/10"):
    r = rr(t); Ts = curves[(t, 2)]
    P(f"t={t} bound {(1-r)/(2*(3+r)):.5f}; min rho over T>=16 {min(E3[(t,2,T)]['rho_Gamma'] for T in Ts if T>=16):.5f}; last {E3[(t,2,Ts[-1])]['rho_Gamma']:.5f} at T={Ts[-1]}")
# old vs new
P("\n### old solver (K=20 uniform w grid) vs lattice: |dU|, by B")
dd = {}
for k, r in E3.items():
    o = OLD.get(k)
    if o:
        for m in ("causal", "iid"):
            dd.setdefault((k[1], m), []).append((o[m]["U"] - r[m]["U"], k))
for (B, m), v in sorted(dd.items()):
    mx = max(v, key=lambda x: abs(x[0]))
    P(f"B={B} {m}: max|U_old-U_new|={abs(mx[0]):.3e} (old-new={mx[0]:+.3e}) at {mx[1]}; n={len(v)}")
bigrho = sorted(((abs(OLD[k]['rho_Gamma'] - E3[k]['rho_Gamma']), k) for k in E3 if k in OLD), reverse=True)[:5]
P("largest |rho_old - rho_new|:", bigrho)
# certified
cert = json.load(open(os.path.join(ROOT, "docs/paper4_continuation/theory_v2/results/wpM_scaling_v1_compact.json")))["cells"]
dif = []
for x in cert:
    k = (x["t01"], x["B"], x["T"])
    if x.get("d") == 1 and x["k"] == "0" and x["alpha"] == "1/10" and x["status"] == "ok" and k in E3:
        dif.append((abs(E3[k]["rho_Gamma"] - x["rho_mid"]), abs(E3[k]["Gamma"] - x["Gamma_mid_f"]), abs(E3[k]["VOI_iid"] - x["VOI_mid_f"]), k))
P(f"\ncertified comparison: {len(dif)} cells; max|drho|={max(d[0] for d in dif):.3e} max|dGamma|={max(d[1] for d in dif):.3e} max|dVOI_iid|={max(d[2] for d in dif):.3e}; worst {max(dif)[3]}")
out["cert"] = dict(n=len(dif), max_drho=max(d[0] for d in dif), max_dGamma=max(d[1] for d in dif), max_dVOI_iid=max(d[2] for d in dif))
# rectangle
P("\n### E3b rectangle")
bounds = {3: 19 / 101, 4: 13 / 84, 5: 40 / 303, 6: 13 / 118}
r0 = rr("63/125"); bounds[1] = (1 - r0) / 2; bounds[2] = (1 - r0) / (2 * (3 + r0))
rect = []
for r in sorted([r for r in rows if r["kind"] == "E3b"], key=lambda r: (r["n_beta"], r["B"], r["T"])):
    b = bounds[r["B"]] if (r["B"] != 6 or r["T"] >= 20) or True else None
    rect.append(dict(n_beta=r["n_beta"], B=r["B"], T=r["T"], U_c=r["causal"]["U"], L_c=r["causal"]["L"], U_i=r["iid"]["U"], L_i=r["iid"]["L"], rho=r["rho_Gamma"], rho_lo=r["rho_lo"], rho_hi=r["rho_hi"], bound=b))
    P(f"nb={r['n_beta']} B={r['B']} T={r['T']}: U_iid={r['iid']['U']:.12g} L_iid={r['iid']['L']:.12g} U_c={r['causal']['U']:.12g} L_c={r['causal']['L']:.12g} | VOI_i={r['VOI_iid']:.6e} VOI_c={r['VOI_causal']:.6e} G={r['Gamma']:.6e} rho={r['rho_Gamma']:.6f} [{r['rho_lo']:.6f},{r['rho_hi']:.6f}] bound={b:.5f}")
out["rectangle"] = rect
# E2
P("\n### E2 (lattice-exact fast solver)")
P("| T | B | N_w | full solve s (L and U) | L-only s | U-only s | L | U |"); P("|---|---|---|---|---|---|---|---|")
e2 = [r for r in rows if r["kind"] == "E2"]
for r in sorted(e2, key=lambda r: (r["B"] != 3, r["B"], r["T"])):
    P(f"| {r['T']} | {r['B']} | {r['full']['n_w']} | {r['full_solve_s']:.1f} | {r['L_only_s']:.1f} | {r['U_only_s']:.1f} | {r['full']['L']:.8f} | {r['full']['U']:.8f} |")
out["e2"] = [dict(T=r["T"], B=r["B"], full_s=r["full_solve_s"], L_only_s=r["L_only_s"], U_only_s=r["U_only_s"]) for r in e2]
# old E2
P("\n### old solver E2 (K=20)")
for r in sorted([r for r in old if r["kind"] == "E2"], key=lambda r: (r["B"] != 3, r["B"], r["T"])):
    P(f"T={r['T']} B={r['B']}: full {r['full_solve_s']:.1f}s upper-only {r['upper_only_s']:.1f}s lower {r['lower_dp_s']:.1f}s")
old_sens = [r for r in old if r["kind"] == "E3b_sens"]
P("\nold-solver sensitivity cells:", [(r["B"], r["T"], r["rho_Gamma"]) for r in old_sens])
json.dump(out, open(os.path.join(RES, "e2e3_fast_summary.json"), "w"), indent=1)
