"""wpG: is the upper probability v(E) = sup_{causal nulls} P(E) on {0,1}^B (sequential p_t in [0,1/2]) a
2-alternating (submodular) capacity?  Exhaustive check for B = 2, 3; also verifies the pattern formula
v({y}) = 2^-#ones(y) and the up-set identity v(U) = 2^-B |U|.  Exact rationals.
usage: uv run --no-sync python scripts/paper4_continuation/theory_v2/wpG_capacity.py OUT.json"""
import hashlib, itertools, json, sys
from fractions import Fraction as F
from pathlib import Path

def v(f, B):  # f: dict pattern-tuple -> value; recursion R = max(R0, (R0+R1)/2)
    def R(prefix):
        if len(prefix) == B:
            return f.get(prefix, F(0))
        r0, r1 = R(prefix + (0,)), R(prefix + (1,))
        return max(r0, (r0 + r1) / 2)
    return R(())

def main():
    out = Path(sys.argv[1])
    if out.exists():
        sys.exit(f"refusing to overwrite {out}")
    res = {}
    for B in (2, 3):
        pats = list(itertools.product((0, 1), repeat=B))
        sets = [frozenset(p for i, p in enumerate(pats) if m >> i & 1) for m in range(2 ** len(pats))]
        val = {S: v({p: F(1) for p in S}, B) for S in sets}
        viol = [(sorted(A), sorted(C)) for A in sets for C in sets
                if val[A | C] + val[A & C] > val[A] + val[C]]
        pat_ok = all(val[frozenset([p])] == F(1, 2 ** sum(p)) for p in pats)
        up = [S for S in sets if all(q in S for p in S for q in pats if all(a <= b for a, b in zip(p, q)))]
        up_ok = all(val[S] == F(len(S), 2 ** B) for S in up)
        res[B] = dict(n_sets=len(sets), n_violations=len(viol), first_violations=[list(map(list, x)) for x in viol[:5]],
                      pattern_formula_ok=pat_ok, n_upsets=len(up), upset_identity_ok=up_ok)
        print(B, res[B]["n_violations"], pat_ok, len(up), up_ok, viol[:2])
    out.write_text(json.dumps(dict(script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), results=res), indent=1, default=str))
    print("wrote", out)

main()
