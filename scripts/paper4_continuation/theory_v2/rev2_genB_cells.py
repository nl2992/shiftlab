"""rev2 red team: exact certified gamma_cell cells (t = 1, d = 1, c = k = 0, prior 1/2, symmetric emissions)
checked against Prop L (IID side), Theorem A (stated and tight forms + aligned-plan lower bound), Theorem V, and the
independent exact aligned / betting policy evaluators of rev2_genB_lib.

usage: uv run --no-sync python scripts/paper4_continuation/theory_v2/rev2_genB_cells.py OUT.json BLIST EALIST [WALL_S]
  BLIST  e.g. 1,2,3        EALIST 'all' or e.g. 1/10:1/20,1/4:1/2   (T runs over 2B..3B+2)
"""
import hashlib, json, sys, time
from fractions import Fraction as F
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / "theory_C"))
from gamma_lib import gamma_cell  # noqa: E402
from rev2_genB_lib import S_iid, aligned_eval, betting_eval, full_voi_calendar, thmV_constants  # noqa: E402

out = Path(sys.argv[1])
if out.exists():
    sys.exit(f"refusing to overwrite {out}")
Bs = [int(b) for b in sys.argv[2].split(",")]
ES = [F(1, 20), F(1, 10), F(1, 4), F(2, 5)]
AS = [F(1, 20), F(1, 10), F(1, 4), F(1, 2)]
if sys.argv[3] == "all":
    EA = [(e, a) for e in ES for a in AS]
else:
    EA = [tuple(F(x) for x in p.split(":")) for p in sys.argv[3].split(",")]
WALL = float(sys.argv[4]) if len(sys.argv) > 4 else 3000.0

rows, t0 = [], time.time()
viol = {}


def flag(name, cond, row):
    row.setdefault("violations", [])
    if cond:
        row["violations"].append(name)
        viol[name] = viol.get(name, 0) + 1


for B in Bs:
    for T in range(2 * B, 3 * B + 3):
        for e, a in EA:
            if time.time() - t0 > WALL:
                break
            s = time.time()
            row = dict(T=T, B=B, e=str(e), alpha=str(a))
            try:
                g = gamma_cell(T, B, 1, 1, 1, e, 1 - e, F(1, 2), 0, 0, a)
            except RuntimeError as err:
                row["error"] = str(err); rows.append(row); print(T, B, e, a, "ERROR", err, flush=True)
                continue
            LI, UI, LC, UC = (F(g[k]) for k in ("L_IID", "U_IID", "L_causal", "U_causal"))
            Glo, Ghi = F(g["Gamma_lo"]), F(g["Gamma_hi"])
            C0 = F(T, 2)
            voiI = (C0 - UI, C0 - LI)
            voiC = (C0 - UC, C0 - LC)
            S, _ = S_iid(B, a, e)
            h, one = B // 2, 1 - 2 * e
            # Prop L (IID side, via CAL-t1)
            propL_lo = ((T - B) // 2) * S
            propL_hi = one * h + (-(-(T - B) // 2)) * S
            flag("propL_lower", voiI[1] < propL_lo, row)
            flag("propL_upper", voiI[0] > propL_hi, row)
            # Theorem A (T >= 2B)
            A_stated = one * h + S * (F(B, 2) + 1)
            A_tight = one * h + ((-(-(T - B) // 2)) - (T - 2 * B + 1) // 2) * S
            A_aligned = ((T - 2 * B + 1) // 2) * S
            flag("thmA_stated", Glo > A_stated, row)
            flag("thmA_final", Glo > one * (B + 1), row)
            flag("thmA_tight", Glo > A_tight, row)
            flag("thmA_aligned_voi", voiC[1] < A_aligned, row)
            al = aligned_eval(T, B, e, a)
            flag("aligned_unsafe", al["risk_causal"] > a, row)
            flag("aligned_voi_below_claim", al["voi"] < A_aligned, row)
            flag("aligned_beats_certificate", al["voi"] > voiC[1], row)
            # Theorem V
            K, pi = thmV_constants(B, e, a)
            V_bound = float(one) / 2 * (K + T * pi)
            flag("thmV", float(Glo) > V_bound, row)
            bt = betting_eval(T, B, e, a)
            fv = full_voi_calendar(T, B, e)
            flag("betting_unsafe", bt["risk_causal"] > a, row)
            flag("thmV_lost_gain", Glo > fv - bt["voi_test"], row)
            flag("thmV_full_voi", voiI[0] > fv, row)
            flag("thmV_Etau", float(bt["E_tau_le_B"]) > K, row)
            flag("thmV_hoeffding", float(bt["P_tau_gt_B"]) > pi, row)
            flag("thmV_denominator", fv < F(T - 1, 2) * one ** 2, row)
            row.update(Gamma=[str(Glo), str(Ghi)], Gamma_f=[float(Glo), float(Ghi)], S_iid=str(S),
                       VOI_IID_f=[float(voiI[0]), float(voiI[1])], VOI_causal_f=[float(voiC[0]), float(voiC[1])],
                       rho_f=float(Glo / voiI[1]) if voiI[1] > 0 else None,
                       thmA_stated=float(A_stated), thmA_tight=float(A_tight), thmA_aligned=float(A_aligned),
                       aligned=dict(risk_causal=str(al["risk_causal"]), risk_iid=str(al["risk_iid"]),
                                    voi=str(al["voi"])),
                       thmV_bound=V_bound, K=K, pi=pi,
                       betting=dict(risk_causal=str(bt["risk_causal"]), voi_test=str(bt["voi_test"]),
                                    full_voi=str(fv), E_tau=float(bt["E_tau_le_B"]),
                                    P_tau_gt_B=float(bt["P_tau_gt_B"])),
                       src=g["V_causal_source"], sec=time.time() - s)
            rows.append(row)
            print(T, B, e, a, "G=[%.6g,%.6g]" % (float(Glo), float(Ghi)), "A_tight %.4g" % float(A_tight),
                  "viol", row["violations"], round(time.time() - s, 1), flush=True)

out.write_text(json.dumps(dict(script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                               lib_sha256=hashlib.sha256((HERE / "rev2_genB_lib.py").read_bytes()).hexdigest(),
                               argv=sys.argv[1:], elapsed_s=time.time() - t0, n_cells=len(rows),
                               n_certified=sum(1 for r in rows if "error" not in r), violation_counts=viol,
                               rows=rows), indent=1, default=str))
print("wrote", out, "violations", viol)
