"""wpG: exact certified gamma_cell vs calendar LP at t = 1 (e = 1/10, d = 1, c = k = 0, alpha = 1/20) for growing
T at fixed B: tests whether adaptive query timing lets the causal learner beat the fixed calendar 1..B.
usage: uv run --no-sync python scripts/paper4_continuation/theory_v2/wpG_exact_longT.py OUT.json"""
import hashlib, json, sys, time
from fractions import Fraction as F
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / "theory_C"))
from wpG_lib import gamma
from gamma_lib import gamma_cell
out = Path(sys.argv[1])
if out.exists():
    sys.exit(f"refusing to overwrite {out}")
rows = []; t0 = time.time()
cells = [(T, 2) for T in (4, 6, 8, 10, 12, 14)] + [(T, 3) for T in (5, 7, 9, 10, 11, 12, 13)] + \
        [(T, 4) for T in (6, 8, 10, 11, 12)] + [(9, 6)]
for T, B in cells:
    a = F(1, 20); s = time.time()
    try:
        g = gamma_cell(T, B, 1, 1, 1, F(1, 10), F(9, 10), F(1, 2), 0, 0, a)
    except RuntimeError as err:  # FCG-fast non-termination is recorded, not hidden
        rows.append(dict(T=T, B=B, alpha="1/20", e="1/10", error=str(err), sec=time.time() - s))
        print(T, B, "ERROR", err, flush=True)
        continue
    m = gamma(T, B, 1.0, 0.1, float(a))
    VI = float(F(g["U_IID"]))
    rows.append(dict(T=T, B=B, alpha="1/20", e="1/10", exact_Gamma=[g["Gamma_lo"], g["Gamma_hi"]],
                     exact_Gamma_f=[g["Gamma_lo_f"], g["Gamma_hi_f"]], exact_VOI=T / 2 - VI,
                     exact_rho=g["Gamma_lo_f"] / (T / 2 - VI), cal_Gamma=m["Gamma"], cal_rho=m["rho"],
                     cal_V_IID=m["V_IID"], exact_U_IID=g["U_IID"], src=g["V_causal_source"], sec=time.time() - s))
    r = rows[-1]
    print(T, B, "exactG %.6f rho %.4f | calG %.6f rho %.4f" % (r["exact_Gamma_f"][0], r["exact_rho"], r["cal_Gamma"], r["cal_rho"]), round(r["sec"], 1), flush=True)
    if time.time() - t0 > 2400:
        print("wall cap reached"); break
out.write_text(json.dumps(dict(script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                               elapsed_s=time.time() - t0, rows=rows), indent=1, default=str))
print("wrote", out)
