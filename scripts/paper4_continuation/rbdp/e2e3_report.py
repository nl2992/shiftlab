"""Generates docs/paper4_continuation/rbdp/E2_E3_SCALING_PREMIUM.md from the JSONL results."""
import json, os, io
from fractions import Fraction as F
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
RES = os.path.join(ROOT, "docs/paper4_continuation/rbdp/results")
rd = lambda f: [json.loads(l) for l in open(os.path.join(RES, f))]
rows = rd("e2e3_fast_cells.jsonl"); old = rd("e2e3_cells.jsonl")
E3 = {(r["t"], r["B"], r["T"]): r for r in rows if r["kind"] == "E3"}
o = io.StringIO()
def P(*a): print(*a, file=o)
rr = lambda t: float(2 * F(t) - 1)
TSEL = [6, 8, 12, 16, 24, 32, 48, 64, 100, 200]
def cell(r):
    w = (r["rho_hi"] - r["rho_lo"]) / 2
    return f"{r['rho_Gamma']:.4f}" + (f"±{w:.4f}" if w >= 5e-5 else "")
P("""# E2 / E3 / E3b: long-horizon causal-safety premium and RB-DP scaling

**Date:** 2026-11-13. Not committed. Solver for all headline numbers: `src/shiftlab/paper4/risk_budget_dp_fast.py` with `lattice_exact=True`
(w lattice Z/(10*2^B), alpha = 1/10, n_beta = 401, delay 1, c = k = 0, emissions (e, 1-e), prior 1/2, C0 = T/2).
The first pass used the old solver `risk_budget_dp.py` (uniform w grid, K = 20, n_beta = 201); those numbers are kept as a cross-check (`e2e3_cells.jsonl`).
Every cell records both L and U for each mode. Point estimate rho = (U_c - U_i)/(C0 - U_i); bracket rho in [(L_c - U_i)/(C0 - L_i), (U_c - L_i)/(C0 - U_i)].
**U is an upper bound on V*, L a lower bound (lattice lemma is derived in the solver docstring, not formally proved in the repo), so rho from U is a point estimate, not a certified bound.**
Tables show rho with a "±half-width" of the bracket when it is at least 5e-5.

## 1. E3: rho_Gamma(T), e = 1/10""")
for t in ("2/3", "3/4", "9/10"):
    P(f"\n### t = {t} (r = {rr(t):.4g})\n")
    Ts = [T for T in TSEL if any((t, B, T) in E3 for B in range(1, 9))]
    P("| B | " + " | ".join(f"T={T}" for T in Ts) + " |"); P("|---|" + "---|" * len(Ts))
    for B in range(1, 9):
        if any((t, B, T) in E3 for T in Ts):
            P(f"| {B} | " + " | ".join(cell(E3[(t, B, T)]) if (t, B, T) in E3 else "-" for T in Ts) + " |")
P("""
Reading: for every (t, B) with B <= 6 and every t, rho_Gamma(T) decreases and then flattens; by T = 48-100 the last values agree to about 3 decimals (t = 9/10 is slowest, mixing factor r^T with r = 0.8; its small remaining drift is of the order of the bracket width). No curve heads to zero. B = 7, 8 exist only at t = 3/4 and only to T = 100 (B = 7) and T = 64 (B = 8); B = 8 (0.4189 at T=32, 0.4018 at T=64) and B = 7 at T=64 to 100 (0.3687, 0.3680) have not fully levelled.

### Level-off summary (last three T per cell, relative change between the last two)
""")
P("| t | B | last 3 T | last 3 rho | rel. change last two | VOI_causal(last T) | VOI_iid(last T) | causal risk of iid-mode policy | of causal-mode policy |"); P("|---|---|---|---|---|---|---|---|---|")
for t in ("2/3", "3/4", "9/10"):
    for B in range(1, 9):
        Ts = sorted(T for (tt, b, T) in E3 if tt == t and b == B)
        if len(Ts) < 3: continue
        L3 = Ts[-3:]; v = [E3[(t, B, T)]["rho_Gamma"] for T in L3]; l = E3[(t, B, L3[-1])]
        P(f"| {t} | {B} | {L3} | {', '.join(f'{x:.4f}' for x in v)} | {(v[-1]-v[-2])/v[-2]:+.2%} | {l['VOI_causal']:.5f} | {l['VOI_iid']:.5f} | {l['iid']['risk_causal']:.4f} | {l['causal']['risk_causal']:.4f} |")
P("""
Both VOIs converge (M2): e.g. t = 3/4, B = 3: VOI_causal/VOI_iid = 0.09592/0.10659 (T=32), 0.09600/0.10667 (T=48 and beyond, to T = 200). At t = 2/3 they are exactly 0.016 B (causal) and 0.024, 0.040, 0.056, 0.072 (iid, B = 1..4) from T = 48 on. The IID-mode policy, evaluated against the causal null, has worst-case risk 0.2-0.4 against the budget alpha = 0.1 (the causal-mode policy sits at 0.1000), so the IID design is unsafe under the causal null in every cell of the table at large T.
Full VOI series are in `results/e2e3_fast_summary.json` and `results/e2e3_fast_cells.jsonl`.

## 2. Theorem checks

- **M1 (B = 1).** Max |rho - closed form| over all B = 1 cells (T = 4..100/200, three t): 1.3e-12 (t=2/3), 2.3e-12 (t=3/4), 2.0e-14 (t=9/10). Passes.
- **M4 (B = 2, liminf >= (1-r)/(2(3+r)), c = 0).** t=2/3: bound 0.10000, rho(T=100) = 0.20000. t=3/4: bound 0.07143, rho(T=200) = 0.14286. t=9/10: bound 0.02632, rho(T=100) = 0.05263 (min over T >= 16 equals the last value). The proved bound holds with a factor of about 2 to spare; the observed limits are (1-r)/(3+r) = 0.2, 0.1429, 0.0526 to the printed digits, exactly twice the bound (numerical observation only).
- **Certified cells.** 60 cells with d = 1, k = 0, alpha = 1/10, e = 1/10, c = 0 (same e and c as `wpM_scaling.py`; B <= 4, T <= 12 (B=1 to 16), t in {2/3, 3/4, 9/10}) from `wpM_scaling_v1_compact.json`: max |rho diff| = 4.2e-13, max |Gamma diff| = 3.3e-14, max |VOI_iid diff| = 1.5e-13. Agreement to float precision (the certified numbers are rational intervals of width ~1e-12).
- **Contradictions with a proved theorem:** none found.

## 3. E3b: the theorem rectangle (t = 63/125, r = 1/125, e = 3/20, g = 0.49)

U values (12 significant digits) from the lattice solver; L equals U to 12 digits in all these cells (symmetric chain, beliefs stay at 1/2 before the first label, so the beta grid does not matter). Rows at n_beta = 401 and 801 agree to ~1e-11 in rho.
""")
P("| B | T | U_iid | U_causal | VOI_iid | VOI_causal | Gamma | rho_Gamma (12 digits) | proved bound |"); P("|---|---|---|---|---|---|---|---|---|")
r0 = rr("63/125"); bd = {1: (1 - r0) / 2, 2: (1 - r0) / (2 * (3 + r0)), 3: 19 / 101, 4: 13 / 84, 5: 40 / 303, 6: 13 / 118}
for r in sorted([r for r in rows if r["kind"] == "E3b" and r["n_beta"] == 401], key=lambda r: (r["B"], r["T"])):
    P(f"| {r['B']} | {r['T']} | {r['iid']['U']:.12g} | {r['causal']['U']:.12g} | {r['VOI_iid']:.6e} | {r['VOI_causal']:.6e} | {r['Gamma']:.6e} | {r['rho_Gamma']:.12f} | {bd[r['B']]:.5f} |")
P("""
Bounds used: B=1 (1-r)/2 = 0.496; B=2 M4's liminf (1-r)/(2(3+r)); B=3..6: 19/101, 13/84, 40/303, 13/118 (the B = 6 proof needs T >= 20; the T = 16 value 0.140913 is shown anyway). Every cell is at or above its bound (B = 1 equals the closed form 0.496 to 6e-11). Gamma is the same 1.944444e-4 for all B and T: the extra queries raise VOI_iid and VOI_causal by the same amount per query.

**Sensitivity.** (a) Lattice solver, n_beta 401 -> 801: rho unchanged to at least 1e-11 in all 18 cells (table above is for 401; the 801 rows are in the JSONL). (b) Old solver (w_step_div 20 -> 40 and n_beta 401 -> 801) on B = 2 and B = 3 at T = 16: change in rho -8.5e-12 and +1.1e-12; change in U_causal and U_iid below 5e-15 in absolute value. These two cells are on-lattice at both grids, so this shows only that, here, grid doubling changes nothing; it does not test B >= 4 (covered instead by the old-vs-lattice comparison in section 5).

## 4. E2: scaling
""")
P("Lattice-exact fast solver, t = 3/4, e = 1/10, causal mode, n_beta = 401, one CPU thread, other jobs were running on the machine (3 of my workers plus another agent's), so timings are pessimistic by an unknown factor. 'Full' = L and U together (in lattice mode L is the same DP as the upper DP, so full and U-only coincide).\n")
P("| T | B | N_w | full solve s | L-only s | U-only s | L | U |"); P("|---|---|---|---|---|---|---|---|")
for r in sorted([r for r in rows if r["kind"] == "E2"], key=lambda r: (r["B"] != 3, r["B"], r["T"])):
    P(f"| {r['T']} | {r['B']} | {r['full']['n_w']} | {r['full_solve_s']:.1f} | {r['L_only_s']:.1f} | {r['U_only_s']:.1f} | {r['full']['L']:.8f} | {r['full']['U']:.8f} |")
P("""
Growth: at B = 3, time doubles when T doubles (0.6, 1.2, 2.2, 4.4, 8.3 s for T = 16..256): linear in T. At T = 32 the time is 0.2, 0.4, 1.2, 2.6, 15.5, 122 s for B = 1, 2, 3, 4, 6, 8: growth in B is exponential (about 6x from B = 4 to 6 and 8x from 6 to 8), because the lattice has N = 10*2^B points. The old uniform-grid solver instead grows about linearly in B because its grid is fixed.
Rough rule: seconds ~ 1.6e-3 * T * B * 2^B per mode.

For comparison the old solver (uniform K = 20 grid, N_w = 200, n_beta 401, run concurrently with load) took:
""")
P("| T | B | full s | upper-only s | lower DP s |"); P("|---|---|---|---|---|")
for r in sorted([r for r in old if r["kind"] == "E2"], key=lambda r: (r["B"] != 3, r["B"], r["T"])):
    P(f"| {r['T']} | {r['B']} | {r['full_solve_s']:.1f} | {r['upper_only_s']:.1f} | {r['lower_dp_s']:.1f} |")
P("""
Old solver: linear in T (30, 61, 121, 272 s for T = 16..128 at B = 3) and about linear in B; T = 256 not run. Exact solver limits from the repo docs (not re-run): T = 16, B = 3, t = 63/125, e = 3/20 timed out at 3,600 s; `docs/paper4/experiments/04_scaling_and_comparators.md` reports 37-71 s at T = 10. The lattice solver does T = 16, B = 3 in 0.6 s (this run, loaded machine); T = 256, B = 3 in 8 s.

## 5. Old uniform-grid solver versus lattice solver (anomaly list)

The lead's note is confirmed. Over the 30 overlapping cells per B (T <= 64, three t), max |U_old - U_new| (old is never below new, as it must be for a restricted grid, except the +/- 1e-12 float noise at B <= 2):
B = 1, 2: <= 1.3e-12. B = 3: causal 6.8e-6, iid 1.4e-5 (t=9/10, T=48). B = 4: causal 1.4e-5. B = 5: iid 2.1e-4 (t=9/10, T=32). B = 6: iid 1.4e-4 (t=9/10, T=32). Largest effect on rho: 1.3e-4 (t=9/10, B=5, T=32). So the first-pass numbers for B >= 5 at t = 9/10 were slightly suboptimal (U not tight on that grid); conclusions do not change, but the first-pass JSONL should not be used for B >= 3 at t = 9/10. At t = 2/3 and 3/4 old and lattice agree to ~1e-13 except noted B = 3 cells.
One further note: the first old-solver driver crashed once (B > T cells, e.g. B = 5 at T = 4) and was restarted with those cells removed; completed cells are unaffected.

## 6. Caveats

- rho values are point estimates from U; they are not certified bounds. The lattice L-U gap is zero for the symmetric-belief cells (rectangle) and reaches 1.1e-3 in V (rho bracket half-width up to 7e-4) at t = 9/10, B = 5, 6, T = 100, because of linear beta interpolation in L (n_beta = 401 not refined).
- n_beta = 201 was used in the first pass (checked: U identical to 1e-12 at two cells); all headline numbers use 401.
- Only t = 3/4 has B = 7 (T = 16, 32, 64, 100), B = 8 (T = 16, 32, 64) and T = 200 (B <= 5). t = 2/3 and 9/10 at B = 7, 8 and T = 200 at B = 6 were not run. The fast pass alone used about 70 CPU-minutes (sum of per-task runtimes) and the old-solver pass more; the 40-minute wall budget was exceeded (about 85 minutes wall in total).
- The M6-M9 tests concern a tiny VOI (1e-4..1e-3); U values near 16 carry ~1e-15 float noise, so rho is trustworthy to about 1e-10 there (B = 4..6 show differences of order 1e-8 in rho between T = 16, 20 and 32; whether these are small finite-T effects or float noise was not resolved).
- Timings were taken under shared load.
- Lattice-exactness (the dyadic-lattice lemma) is derived by the lead in the solver docstring, not proved; evidence is exact agreement with certified values on 60 cells.

## 7. Reproduce

```
uv run --no-sync python scripts/paper4_continuation/rbdp/e2e3_run.py 42            # first pass, old solver -> results/e2e3_cells.jsonl
uv run --no-sync python scripts/paper4_continuation/rbdp/e2e3_fast_run.py 28        # lattice solver -> results/e2e3_fast_cells.jsonl (resumable)
uv run --no-sync python scripts/paper4_continuation/rbdp/e2e3_fast_analyze.py       # tables + results/e2e3_fast_summary.json
uv run --no-sync python scripts/paper4_continuation/rbdp/e2e3_report.py             # regenerates this file
```
Files: `scripts/paper4_continuation/rbdp/e2e3_*.py`, `docs/paper4_continuation/rbdp/results/e2e3_*`. Every JSONL line carries the script and solver sha256.
""")
open(os.path.join(ROOT, "docs/paper4_continuation/rbdp/E2_E3_SCALING_PREMIUM.md"), "w").write(o.getvalue())
