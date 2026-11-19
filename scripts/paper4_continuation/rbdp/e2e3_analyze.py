"""Analysis: reads e2e3_cells.jsonl, writes e2e3_summary.json and prints markdown tables."""
import json, os, sys
from fractions import Fraction as F
sys.path.insert(0, os.path.dirname(__file__))
from e2e3_common import RES, sha, SOLVER
rows = [json.loads(l) for l in open(os.path.join(RES, "e2e3_cells.jsonl"))]
E3 = {}
for r in rows:
    if r["kind"] == "E3": E3[(r["t"], r["B"], r["T"])] = r
def r_of(t): return float(2 * F(t) - 1)
def m1(t, T):
    r = r_of(t); n = T - 1
    return (1 - r) / 2 if n % 2 == 0 else (1 - r) * (1 + r ** n) / (2 * (1 - r ** (n + 1)))
out = {"script_sha256": sha(__file__), "solver_sha256": sha(SOLVER)}
P = lambda *a: print(*a)
# M1 check
dev = {}
for (t, B, T), r in sorted(E3.items()):
    if B == 1: dev.setdefault(t, []).append((abs(r["rho_Gamma"] - m1(t, T)), T))
out["m1_max_abs_dev"] = {t: max(d)[0] for t, d in dev.items()}
out["m1_max_dev_T"] = {t: max(d)[1] for t, d in dev.items()}
P("M1 max |rho - closed form|:", out["m1_max_abs_dev"])
# tables
curves = {}
for t in ["2/3", "3/4", "9/10"]:
    P(f"\n### t={t}  (r={r_of(t):.4g})  rho_Gamma(T)")
    Ts = sorted({k[2] for k in E3 if k[0] == t})
    P("| B | " + " | ".join(f"T={T}" for T in Ts) + " |"); P("|---|" + "---|" * len(Ts))
    for B in range(1, 9):
        if not any((t, B, T) in E3 for T in Ts): continue
        P(f"| {B} | " + " | ".join(f"{E3[(t,B,T)]['rho_Gamma']:.4f}" if (t, B, T) in E3 else "-" for T in Ts) + " |")
        curves[(t, B)] = sorted(T for T in Ts if (t, B, T) in E3)
P("\n### level-off: last three rho, rel change last two, VOI_causal, VOI_iid, Gamma at last T, causal risk of iid policy")
P("| t | B | last 3 T | last 3 rho | rel chg | VOI_c(last) | VOI_i(last) | Gamma(last) | iid-policy causal risk | causal-policy causal risk |"); P("|---|---|---|---|---|---|---|---|---|---|")
lev = []
for (t, B), Ts in sorted(curves.items()):
    L3 = Ts[-3:]; v = [E3[(t, B, T)]["rho_Gamma"] for T in L3]; last = E3[(t, B, Ts[-1])]
    rc = (v[-1] - v[-2]) / v[-2] if len(v) > 1 else None
    lev.append(dict(t=t, B=B, T=L3, rho=v, rel_change_last_two=rc, VOI_causal=last["VOI_causal"], VOI_iid=last["VOI_iid"], Gamma=last["Gamma"],
                    iid_policy_causal_risk=last["iid"]["risk_causal"], causal_policy_causal_risk=last["causal"]["risk_causal"]))
    P(f"| {t} | {B} | {L3} | {', '.join(f'{x:.4f}' for x in v)} | {rc:+.2%} | {last['VOI_causal']:.5f} | {last['VOI_iid']:.5f} | {last['Gamma']:.3e} | {last['iid']['risk_causal']:.4f} | {last['causal']['risk_causal']:.4f} |")
out["level_off"] = lev
# VOI tables
for t in ["2/3", "3/4", "9/10"]:
    P(f"\n### t={t}  VOI_causal / VOI_iid by T")
    for B in range(1, 9):
        Ts = curves.get((t, B), [])
        if Ts: P(f"B={B}: " + "; ".join(f"T={T}: {E3[(t,B,T)]['VOI_causal']:.5f}/{E3[(t,B,T)]['VOI_iid']:.5f}" for T in Ts))
# M4 check, B=2
P("\n### B=2 vs M4 liminf bound (1-r)/(2(3+r))")
for t in ["2/3", "3/4", "9/10"]:
    r = r_of(t); lb = (1 - r) / (2 * (3 + r)); Ts = curves.get((t, 2), [])
    P(f"t={t}: bound={lb:.5f}; min over T>=16 of rho = {min([E3[(t,2,T)]['rho_Gamma'] for T in Ts if T>=16], default=float('nan')):.5f}; last={E3[(t,2,Ts[-1])]['rho_Gamma']:.5f} at T={Ts[-1]}")
    out.setdefault("m4", {})[t] = dict(bound=lb, last_T=Ts[-1], last_rho=E3[(t, 2, Ts[-1])]["rho_Gamma"])
# certified comparison
cert = json.load(open(os.path.join(os.path.dirname(RES), "..", "theory_v2", "results", "wpM_scaling_v1_compact.json")))["cells"]
cc = {}
for x in cert:
    if x.get("d") == 1 and x["k"] == "0" and x["alpha"] == "1/10" and x["status"] == "ok":
        cc[(x["t01"], x["B"], x["T"])] = x
dd = []
for k, x in cc.items():
    if k in E3 and k[2] <= 12:
        lo, hi = x["rho_interval"]; mine = E3[k]["rho_Gamma"]
        dd.append(dict(t=k[0], B=k[1], T=k[2], cert_rho_mid=x["rho_mid"], cert_lo=lo, cert_hi=hi, mine=mine, diff=mine - x["rho_mid"],
                       voi_c_diff=E3[k]["VOI_causal"] - (x["VOI_mid_f"] - x["Gamma_mid_f"]) if False else None,
                       gamma_diff=E3[k]["Gamma"] - x["Gamma_mid_f"], voi_iid_diff=E3[k]["VOI_iid"] - x["VOI_mid_f"]))
out["cert_compare"] = dd
P(f"\n### certified comparison: {len(dd)} cells; max|rho diff|={max(abs(d['diff']) for d in dd):.3e}; max|Gamma diff|={max(abs(d['gamma_diff']) for d in dd):.3e}; max|VOI_iid diff|={max(abs(d['voi_iid_diff']) for d in dd):.3e}")
worst = sorted(dd, key=lambda d: -abs(d["diff"]))[:5]
for d in worst: P(d)
# E3b
bounds = {1: None, 2: None, 3: 19 / 101, 4: 13 / 84, 5: 40 / 303, 6: 13 / 118}
E3b = {(r["B"], r["T"]): r for r in rows if r["kind"] == "E3b"}
P("\n### E3b rectangle t=63/125 e=3/20")
P("| B | T | U_iid | U_causal | VOI_iid | VOI_causal | Gamma | rho | bound | iid-policy causal risk |"); P("|---|---|---|---|---|---|---|---|---|---|")
rect = []
for (B, T), r in sorted(E3b.items()):
    rr = r_of("63/125"); b = (1 - rr) / 2 if B == 1 else (( (1 - rr) / (2 * (3 + rr))) if B == 2 else bounds[B])
    rect.append(dict(B=B, T=T, U_iid=r["iid"]["U"], U_causal=r["causal"]["U"], rho=r["rho_Gamma"], bound=b, ok=r["rho_Gamma"] >= b - 1e-9, Gamma=r["Gamma"], VOI_iid=r["VOI_iid"], VOI_causal=r["VOI_causal"]))
    P(f"| {B} | {T} | {r['iid']['U']:.12g} | {r['causal']['U']:.12g} | {r['VOI_iid']:.6e} | {r['VOI_causal']:.6e} | {r['Gamma']:.6e} | {r['rho_Gamma']:.6f} | {b:.5f} | {r['iid']['risk_causal']:.4f} |")
out["rectangle"] = rect
P("\nsensitivity (n_beta 801, wdiv 40):")
sens = []
for r in rows:
    if r["kind"] == "E3b_sens":
        b = E3b.get((r["B"], r["T"]))
        if b:
            sens.append(dict(B=r["B"], T=r["T"], rho_base=b["rho_Gamma"], rho_fine=r["rho_Gamma"], d_rho=r["rho_Gamma"] - b["rho_Gamma"],
                             dU_causal=r["causal"]["U"] - b["causal"]["U"], dU_iid=r["iid"]["U"] - b["iid"]["U"]))
            P(sens[-1])
out["sensitivity"] = sens
# E2
P("\n### E2")
e2 = [r for r in rows if r["kind"] == "E2"]
P("| T | B | full solve s | upper-only s | lower DP s |"); P("|---|---|---|---|---|")
for r in sorted(e2, key=lambda r: (r["B"] != 3, r["B"], r["T"])):
    P(f"| {r['T']} | {r['B']} | {r['full_solve_s']:.1f} | {r['upper_only_s']:.1f} | {r['lower_dp_s']:.1f} | L={r['L']:.6f} U={r['U']:.6f}")
out["e2"] = [{k: r[k] for k in ("T", "B", "full_solve_s", "upper_only_s", "lower_dp_s", "L", "U", "time_breakdown")} for r in e2]
json.dump(out, open(os.path.join(RES, "e2e3_summary.json"), "w"), indent=1)
