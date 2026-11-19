# Delay-2 long-horizon study: rho_Gamma versus horizon T

Date: 2026-11-14. Solver: `src/shiftlab/paper4/risk_budget_dp_d2.py` (label delay 2). Delay-1 comparison values come from
`results/e2e3_fast_cells.jsonl` (kind E3, e = 1/10, n_beta = 401), same t, B, T.

## Setup

- Cells: symmetric chain t01 = t10 = t in {2/3, 3/4, 9/10}; e0 = 1/10, e1 = 9/10; prior P(S_1 = 1) = 1/2; c = k = 0; alpha = 1/10
  (same conventions as `e2e3_fast_run.py`). B in {1, 2, 3}, T in {8, 12, 16, 24, 32, 48, 64, 100}; plus B = 4 at T in {8, 12, 16}.
- Risk grid N = 10 * 2^B (`n_w_override`): 20, 40, 80, 160 cells.
- V_causal and V_IID are U (exact cost of the extracted policy, an upper bound on the optimum) in causal and IID mode.
  Gamma = V_causal - V_IID; rho_Gamma = Gamma / (C0 - V_IID).
- Belief grid: uniform, n_beta = 401 (see sensitivity below). Each (cell, mode) ran in its own subprocess with a 30-minute timeout.
- Important caveat: U equals the certified optimum only where it was checked (T <= 7). For T >= 8 the values are exact costs of
  feasible policies on the stated grids; they are upper bounds, and no lower bound was computed. A reported Gamma is a difference of
  two such upper bounds.

## Sanity checks (T <= 7, same code path `one_solve` as the study)

Reference: `gamma_cell(T, B, 2, ...)`. Differences U - exact: (T=5, B=2, t=3/4) iid 0, causal 0; (T=6, B=3, t=2/3) iid 0, causal 0;
(T=7, B=2, t=9/10) iid 4.4e-16, causal 4.4e-16. All within 1e-9. (`results/d2_longhorizon_sanity.json`; belief grid auto chose "reach" there.)

## rho_Gamma by (t, B, T): delay 2 versus delay 1

n/r = not run.

| t, B | delay | T=8 | T=12 | T=16 | T=24 | T=32 | T=48 | T=64 | T=100 |
|---|---|---|---|---|---|---|---|---|---|
| 2/3, B=1 | 2 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 2/3, B=1 | 1 | 0.3335 | 0.3333 | 0.3333 | 0.3333 | 0.3333 | 0.3333 | 0.3333 | 0.3333 |
| 3/4, B=1 | 2 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 3/4, B=1 | 1 | 0.2529 | 0.2502 | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.2500 |
| 9/10, B=1 | 2 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 9/10, B=1 | 1 | 0.1454 | 0.1166 | 0.1065 | 0.1011 | 0.1002 | 0.1000 | 0.1000 | 0.1000 |
| 2/3, B=2 | 2 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 2/3, B=2 | 1 | 0.2041 | 0.2004 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 |
| 3/4, B=2 | 2 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 3/4, B=2 | 1 | 0.1564 | 0.1458 | 0.1436 | 0.1429 | 0.1429 | 0.1429 | 0.1429 | 0.1429 |
| 9/10, B=2 | 2 | 0.1355 | 0.0753 | 0.0562 | 0.0118 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 9/10, B=2 | 1 | 0.2692 | 0.2101 | 0.1514 | 0.0705 | 0.0543 | 0.0529 | 0.0527 | 0.0526 |
| 2/3, B=3 | 2 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 2/3, B=3 | 1 | 0.1543 | 0.1454 | 0.1434 | 0.1429 | 0.1429 | 0.1429 | 0.1429 | 0.1429 |
| 3/4, B=3 | 2 | 0.0426 | 0.0266 | 0.0120 | 0.0006 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 3/4, B=3 | 1 | 0.1956 | 0.1488 | 0.1188 | 0.1007 | 0.1001 | 0.1000 | 0.1000 | 0.1000 |
| 9/10, B=3 | 2 | 0.2375 | 0.1795 | 0.1495 | 0.0594 | 0.0421 | 0.0402 | 0.0399 | 0.0399 |
| 9/10, B=3 | 1 | 0.4714 | 0.3551 | 0.2713 | 0.1703 | 0.1542 | 0.1496 | 0.1489 | 0.1460 |
| 2/3, B=4 | 2 | 0.0176 | 0.0096 | 0.0000 | n/r | n/r | n/r | n/r | n/r |
| 2/3, B=4 | 1 | 0.1666 | 0.1254 | 0.1130 | n/r | n/r | n/r | n/r | n/r |
| 3/4, B=4 | 2 | 0.1381 | 0.1062 | 0.0678 | n/r | n/r | n/r | n/r | n/r |
| 3/4, B=4 | 1 | 0.2852 | 0.2292 | 0.1832 | n/r | n/r | n/r | n/r | n/r |
| 9/10, B=4 | 2 | 0.4262 | 0.3258 | 0.2435 | n/r | n/r | n/r | n/r | n/r |
| 9/10, B=4 | 1 | 0.5434 | 0.4437 | 0.3498 | n/r | n/r | n/r | n/r | n/r |

Reading of the delay-2 rows (as far as the data go):

- B = 1: rho_Gamma = 0 at every T and every t (Gamma = 0 exactly, V_causal = V_IID). Delay 1 gives 1/3, 1/4, 1/10 at large T.
- B = 2: 0 at every T for t = 2/3 and 3/4. For t = 9/10 it is positive for T <= 24 (0.1355, 0.0753, 0.0562, 0.0118) and 0 from T = 32 to 100.
- B = 3: 0 for t = 2/3. For t = 3/4 it is positive for T <= 24 (0.0426, 0.0266, 0.0120, 0.0006) and 0 from T = 32. For t = 9/10 it decreases and
  is 0.0421, 0.0402, 0.0399, 0.0399 at T = 32, 48, 64, 100 (T=64: 0.039929, T=100: 0.039891). Changes between T = 64 and 100 are about 4e-5,
  so it is flat to that resolution over this range; it is not shown beyond T = 100. This is the only (t, B <= 3) series with a nonzero value at T = 100.
- B = 4 (T <= 16 only): 2/3: 0.0176, 0.0096, 0 ; 3/4: 0.1381, 0.1062, 0.0678 ; 9/10: 0.4262, 0.3258, 0.2435. All still decreasing over T = 8..16;
  nothing can be said about levelling for B = 4.
- Delay 1 over the same cells: the values at T = 100 are 1/3, 1/4, 0.1000 (B=1), 0.2000, 0.1429, 0.0526 (B=2), 0.1429, 0.1000, 0.1460 (B=3); the
  9/10, B = 3 delay-1 series is still moving between T = 64 (0.1489) and T = 100 (0.1460).
- Where delay-2 rho_Gamma is 0, the causal risk of the IID-mode policy is 0.1 = alpha, i.e. the IID-mode solution found is itself causally safe.
  This is a statement about the policy the solver extracted, not about every IID-optimal policy.

## Gamma and the causal risk of the IID-mode policy

Only series with a nonzero entry are shown; all other series have Gamma = 0 and IID-policy causal risk 0.100 at every T.

| t, B | quantity | T=8 | T=12 | T=16 | T=24 | T=32 | T=48 | T=64 | T=100 |
|---|---|---|---|---|---|---|---|---|---|
| 9/10, B=2 | Gamma | 2.05e-02 | 1.38e-02 | 1.10e-02 | 2.39e-03 | 0.00e+00 | 0.00e+00 | 0.00e+00 | 0.00e+00 |
| 9/10, B=2 | causal risk of IID policy | 0.200 | 0.200 | 0.200 | 0.200 | 0.100 | 0.100 | 0.100 | 0.100 |
| 3/4, B=3 | Gamma | 1.92e-03 | 1.36e-03 | 6.34e-04 | 3.34e-05 | 0.00e+00 | 0.00e+00 | 0.00e+00 | 0.00e+00 |
| 3/4, B=3 | causal risk of IID policy | 0.200 | 0.200 | 0.200 | 0.200 | 0.100 | 0.100 | 0.100 | 0.100 |
| 9/10, B=3 | Gamma | 4.71e-02 | 5.02e-02 | 4.68e-02 | 1.97e-02 | 1.46e-02 | 1.44e-02 | 1.43e-02 | 1.43e-02 |
| 9/10, B=3 | causal risk of IID policy | 0.200 | 0.200 | 0.200 | 0.200 | 0.200 | 0.200 | 0.200 | 0.200 |
| 2/3, B=4 | Gamma | 3.51e-04 | 2.19e-04 | 0.00e+00 | n/r | n/r | n/r | n/r | n/r |
| 2/3, B=4 | causal risk of IID policy | 0.200 | 0.200 | 0.100 | n/r | n/r | n/r | n/r | n/r |
| 3/4, B=4 | Gamma | 7.84e-03 | 7.34e-03 | 4.88e-03 | n/r | n/r | n/r | n/r | n/r |
| 3/4, B=4 | causal risk of IID policy | 0.200 | 0.200 | 0.200 | n/r | n/r | n/r | n/r | n/r |
| 9/10, B=4 | Gamma | 1.21e-01 | 1.37e-01 | 1.18e-01 | n/r | n/r | n/r | n/r | n/r |
| 9/10, B=4 | causal risk of IID policy | 0.250 | 0.275 | 0.275 | n/r | n/r | n/r | n/r | n/r |

Causal risk of the causal-mode policy: maximum over all 81 cells = 0.10000000000000005 (alpha + 5.6e-17), always <= alpha + 1e-9.
Maximum causal risk of an IID-mode policy: 0.275 (t = 9/10, B = 4, T = 12 and 16). No cell has V_causal < V_IID - 1e-9. No flags raised.

## Belief-grid sensitivity

Belief grids compared: uniform with n_beta = 201, 401, 801, and `belief_grid="reach"` (exact reachable beliefs, no interpolation).

Reach feasibility. Reach was run on the whole B <= 3 grid (72 cells) with a 600 s per-mode timeout: 49 cells ok, 22 cells raised
`RuntimeError: belief outside the active set (use belief_grid='uniform')`, 1 cell timed out (9/10, B=3, T=64; causal mode hit 600 s).
Pattern of the errors: every error is for t = 2/3 or 3/4 (the 3/4 chain at B = 1 from T = 48, B = 2 from T = 48 (T = 24 fine), B = 3 from T = 32;
2/3 at B = 2 from T = 24 and B = 3 from T = 24, none at B = 1) and for 9/10 at (B=2, T=100) and (B=3, T=100). The error is raised by the solver's lookup of a
belief that is not in the reachable set; I did not investigate the cause (a rounding-key mismatch in the reachable-belief set is a guess, not tested). Reach
cell sizes (belief points): 9/10 B=2: 397 at T=16, 1805 at T=32, 7693 at T=64 (21 s for both modes); 9/10 B=3: 3357 at T=16, 34397 at T=32 (83 s),
125853 at T=48 (about 640 s for both modes), and T=64 timed out. Where reach ran, it is faster than uniform n_beta = 401 for B <= 2 (e.g. 21 s vs 93 s at 9/10, B=2, T=64) and slower for B = 3 beyond T = 32.
Because reach does not work for every chain and horizon, the main grid uses the uniform belief grid; the reach values are a cross-check.

Reach versus the main grid (uniform, n_beta = 401), 49 cells where reach ran: max |V_causal or V_IID difference| by T: 4e-16 (T=8), 9e-16 (12), 1.8e-15 (16),
2.7e-12 (24), 1.5e-12 (32), 9.9e-12 (48), 2.05e-5 (64; one cell, 9/10 B=2, where the uniform V is higher), 4.9e-12 (100). Max |rho_Gamma difference| over all 49 cells: 1.7e-14.

n_beta = 401 minus 201 and minus reach (T = 16 and 32, B in {2, 3}, three chains): at T = 16 all differences <= 1.8e-15 in V and <= 1.7e-14 in rho_Gamma.
At T = 32 differences in V are <= 4.2e-12 except (3/4, B=3, T=32) where V is 7.8e-6 lower at 401 than at 201 (both modes; rho_Gamma 0 in both).
rho_Gamma differences at T = 32 are 0 or <= 5.1e-15.

n_beta = 801 minus 401 (uniform; B in {2, 3}, T in {32, 64}): V differences at T = 32: <= 1.6e-7 in magnitude (largest: 2/3, B=3: -1.6e-7), all others <= 2.4e-13.
At T = 64: 2/3 B=2 -6.8e-12; 3/4 B=2 -1.4e-10; 9/10 B=2 -1.5e-5; 2/3 B=3 -5.1e-9; 3/4 B=3 -3.0e-8; 9/10 B=3 -2.7e-5 (causal), -3.1e-5 (IID).
rho_Gamma differences at T = 64: 0 in every cell except (9/10, B=3): +7.9e-6 (0.039929 at 401).
All values with rho_Gamma = 0 stayed 0 in every comparison. V decreased with finer grids in every nonzero difference, consistent with U being an upper bound on a coarser belief grid.

Why 401: the earlier comparisons at T = 16, 32 showed 201 vs 401 differing by 7.8e-6 in V for one cell, 401 matches the delay-1 runs, and the cost was affordable. The 801 and
reach comparisons show that main-grid V values at T >= 64 can carry belief-grid errors of up to about 3e-5 and rho_Gamma errors of order 1e-5 for the 9/10, B=3 series;
T = 100 was not re-run at 801.

## Timings and what was run

- 81 main cells (72 grid + 9 for B = 4): all status ok, none timed out, none errored. Longest cell: 714 s (causal + IID wall time; B=3, T=100, t=9/10),
  of which a mode takes roughly 280-360 s. Total solver time (sum of `time_total` over all cells and both modes): 11283 s. B = 1 cells: <= 53 s; B = 2: <= 141 s;
  B = 4 at T = 16: 543-676 s. Four cells ran in parallel; main grid + B = 4 took about 58 minutes wall (cells finished between 06:05 and 07:03 local), the
  sensitivity runs about 100 minutes wall overlapping with these. Solve time grew roughly linearly in T at fixed B; it rose by about 10x from B = 1 to B = 3 at T = 100 (53 s to 714 s per cell).
- Extra cells in `d2_longhorizon_sens.jsonl`: 36 initial (n_beta 201, 401, reach; T in {16, 32}, B in {2, 3}, three t), 12 at n_beta = 801, and the reach re-run of the B <= 3 grid (cells already present were reused; 22 errors and 1 timeout in total over all reach cells, listed in the summary JSON under `sens_not_ok`).
- Not run: reach with a timeout above 600 s; B = 4 at T > 16; B >= 5; T > 100; n_beta = 801 at T = 100; non-symmetric chains; other e or alpha.
- The study did not compute lower bounds, so no statement is made on how close U is to the optimum at T >= 8.

## Reproduce

```
uv run --no-sync python scripts/paper4_continuation/rbdp/d2_longhorizon_run.py sanity
uv run --no-sync python scripts/paper4_continuation/rbdp/d2_longhorizon_run.py sens 60 4 900
uv run --no-sync python scripts/paper4_continuation/rbdp/d2_longhorizon_run.py sens801
uv run --no-sync python scripts/paper4_continuation/rbdp/d2_longhorizon_run.py reachgrid
uv run --no-sync python scripts/paper4_continuation/rbdp/d2_longhorizon_run.py grid uniform 401 170 4
uv run --no-sync python scripts/paper4_continuation/rbdp/d2_longhorizon_run.py grid uniform 401 60 4 b4
uv run --no-sync python scripts/paper4_continuation/rbdp/d2_longhorizon_analyze.py
```

Outputs: `results/d2_longhorizon_cells.jsonl`, `results/d2_longhorizon_sens.jsonl`, `results/d2_longhorizon_sanity.json`, `results/d2_longhorizon_summary.json`.

## Addendum (2026-11-16, lead)

B = 4 has since been run at T = 24, 32, 48, 64, 100 for all three chains (cells appended to
`results/d2_longhorizon_cells.jsonl`); the table and the memory fix that made it possible are in `DELAY2.md` §7.
Reproduce: `D2_TABLES_ON_DISK=1 D2_MEM_CAP_GB=4 uv run --no-sync python scripts/paper4_continuation/rbdp/d2_longhorizon_b4.py 720 1 180`
(one solve at a time; the T = 100 cells need tens of GB of temporary disk).
