"""wpG: alpha-scaling of Gamma and rho at t = 1, d = 1, c = k = 0 (calendar LP, float), plus the causal-safe
betting policy of Theorem V (its causal risk must be <= alpha).  Descriptive.
usage: uv run --no-sync python scripts/paper4_continuation/theory_v2/wpG_alpha.py OUT.json"""
import hashlib, json, sys, time
from fractions import Fraction as F
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from wpG_lib import gamma, test_policy

out = Path(sys.argv[1])
if out.exists():
    sys.exit(f"refusing to overwrite {out}")
t0 = time.time(); rows = []
for e in (F(1, 50), F(1, 10)):
    for B in (4, 8, 12):
        for dT in (1, 2, 20, 21):
            for k in range(1, 11):
                a = 2.0 ** -k
                T = B + dT
                g = gamma(T, B, 1.0, float(e), a)
                tp = test_policy(T, B, float(e), a)
                g.update(e=str(e), alpha=f"2^-{k}", alpha_f=a, test=tp)
                rows.append(g)
            print(e, B, dT, "done", round(time.time() - t0), flush=True)
out.write_text(json.dumps(dict(script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                               lib_sha256=hashlib.sha256((HERE / "wpG_lib.py").read_bytes()).hexdigest(),
                               elapsed_s=time.time() - t0, rows=rows), indent=1, default=str))
print("wrote", out)
