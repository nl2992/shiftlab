# E1 / E4: RB-DP validation against certified values, and baselines

Date 2026-11-13. d = 1 only. Grid for all runs below: `n_beta = 201`, `w_step_div = 10` (so alpha = 1/20 uses 200 w-cells, 1/10 uses 100, 1/4 uses 40). Float DP; U is the exactly evaluated cost of the extracted policy. Every JSON in `results/` records script sha256, solver sha256, grid, seed and per-cell runtime.

## E1.1 RB-DP vs certified wpM_scaling cells (150 cells)

Selection: 90 cells evenly strided from the 504 `ok`, d=1, T<12 cells (sorted by T,B,t,k,alpha) plus all 60 cells with T>=12. Cell parameters recovered from `wpM_scaling.py`: t01=t10=t, e=(1/10,9/10), prior 1/2, c=0, k in {0,1/50}. `Gamma_f` = interval for V*_causal - V*_IID; `VOI_interval_f` = C0 - V*_IID (IID value, not causal); rho = Gamma / VOI. RB-DP: Gamma = U_causal - U_iid, VOI = C0 - U_iid.

| quantity | max abs dev | median | p90 | cells > 1e-6 |
|---|---|---|---|---|
| Gamma vs interval midpoint | 2.53e-03 | 4.3e-16 | 2.4e-15 | 2 |
| Gamma outside certified interval | 2.53e-03 | 0 | 5.0e-16 | 2 |
| VOI vs certified interval | 2.53e-03 | 1.4e-16 | 7.1e-16 | 2 |
| rho vs midpoint | 3.04e-03 | 1.1e-14 | 9.1e-14 | 2 |
| C0 | 0 | 0 | 0 | 0 |

148 of 150 cells agree to <= 1.1e-14 (float round-off). Coverage: B=1:58, 2:49, 3:23, 4:20; t in {2/3,3/4,9/10} 51/50/49; k=0:107, 1/50:43; alpha 1/20:56, 1/10:65, 1/4:29; T=2..16 (all 60 T>=12 cells included). All 150 have certified Gamma > 0.

Cells exceeding 1e-6 (both t=9/10, B=4, k=0, alpha=1/10, c=0, e=(1/10,9/10), prior 1/2):

| T | RB-DP U_iid | certified V_IID | diff | RB-DP U_causal | certified V_causal | diff |
|---|---|---|---|---|---|---|
| 7 | 3.148517 | 3.145989 | +2.53e-03 | 3.350240 | 3.350240 | +1.6e-14 |
| 12 | 5.449887 | 5.448796 | +1.09e-03 | 5.693343 | 5.693343 | +3.0e-13 |

Both exceedances come from the IID-mode policy being suboptimal on the grid (U_iid above the true optimum); the causal-mode U is exact. U is still a valid upper bound, so these are not sandwich violations. At T=7, B=4 the Gamma error is 1.3% of Gamma and the VOI error 0.7%.

Sandwich checks over all 150 cells: no U below a certified lower value (min U - certified = -1.8e-15 IID, -8.9e-16 causal, i.e. round-off) and no L above a certified upper value (max L - certified U = -1.6e-3 IID, -5.3e-4 causal). Gap U - L (causal mode): median 0.024, p90 0.090, max 0.266; median gap/VOI = 0.43, so L is loose as expected and only U carries information.

## E1.2 Fresh seeded grid vs fresh `gamma_cell` (40 cells, seed 20261113)

Draws: T in 4..8, B in 1..min(3,T), t01,t10 = n/d with d in {4,5,6,8,10,12} in (0.05,0.95), e0 = n/{10,20} in (0.05,0.45), e1 in (0.55,0.95), prior in {0,1/3,1/2}, c in {0,1/100}, k in {0,1/20,1/10}, alpha in {1/20,1/10,1/5}. All 40 reference calls finished (mean 2.3 s, no timeouts); certified intervals have width <= 6.3e-14.

| mode | exact inside [L,U] | U - exact: min / median / max | exact - L: median / max |
|---|---|---|---|
| IID | 40/40 | -8.9e-16 / 4.4e-16 / 1.16e-04 | 3.3e-03 / 0.135 |
| causal | 40/40 | -8.9e-16 / 4.4e-16 / 1.16e-04 | 2.5e-03 / 0.135 |

U equals the exact value to round-off in 38 of 40 cells. The two other cells (T=5, B=3, alpha=1/5; one with t=(7/12,3/4), e=(3/10,7/10), prior 1/3, c=k=0 giving +2.5e-06, one with t=(1/6,1/10), e=(7/20,17/20), prior 0, k=1/20 giving +1.16e-04) are small grid suboptimality. Max |Gamma_rbdp - Gamma_exact| = 2.5e-06.

Caveat on power: in this random draw 16 of 40 cells have zero IID VOI and only 2 have Gamma > 0 (and only 2 have an IID-optimal policy that is causal-unsafe). It validates the bracketing and U accuracy, but is weak evidence on the causal premium itself; E1.1 is the strong test of Gamma.

## E4 baselines (alpha = 1/10, e = (1/10, 9/10), prior 1/2)

Table gives VOI = C0 - cost for the RB-DP causal policy (a), fraction of that VOI captured by (c) IID-optimal + root repair and (e) fixed-bet e-process gate, and for (b) its VOI and true worst-case causal risk over alpha. (d) never-promote captures 0 by definition. The first 18 rows are T=8, the next 18 T=32, then the extra asymmetric chain.

| T | chain | B | c/k | VOI (a) RB-DP causal | (c) repair frac | (e) e-gate frac (best theta) | (b) IID-opt VOI | (b) risk/alpha |
|---|---|---|---|---|---|---|---|---|
| 8 | anti2/3 | 2 | 0/0 | 0.03121 | 0.628 | 0.744 | 0.03921 | 2.00 |
| 8 | anti2/3 | 3 | 0/0 | 0.04388 | 0.591 | 0.818 | 0.05188 | 2.00 |
| 8 | anti3/4 | 2 | 0/0 | 0.05800 | 0.593 | 0.815 | 0.06875 | 2.00 |
| 8 | anti3/4 | 3 | 0/0 | 0.07618 | 0.622 | 0.859 | 0.09471 | 2.00 |
| 8 | anti9/10 | 2 | 0/0 | 0.13804 | 0.684 | 0.875 | 0.18889 | 2.00 |
| 8 | anti9/10 | 3 | 0/0 | 0.16374 | 0.473 | 0.852 | 0.30978 | 4.00 |
| 8 | pers1/10 | 2 | 0/0 | 0.34000 | 1.000 | 1.000 | 0.34000 | 1.00 |
| 8 | pers1/10 | 3 | 0/0 | 0.50808 | 1.000 | 1.000 | 0.50808 | 1.00 |
| 8 | pers1/4 | 2 | 0/0 | 0.09450 | 1.000 | 1.000 | 0.09450 | 1.00 |
| 8 | pers1/4 | 3 | 0/0 | 0.12834 | 1.000 | 1.000 | 0.12834 | 1.00 |
| 8 | asym(1/4,3/4) | 2 | 0/0 | -0.00000 | n/a (VOI=0) | n/a (VOI=0) | -0.00000 | 0.00 |
| 8 | asym(1/4,3/4) | 3 | 0/0 | -0.00000 | n/a (VOI=0) | n/a (VOI=0) | -0.00000 | 0.00 |
| 8 | anti3/4 | 2 | 1/100, 1/20 | 0.03060 | 0.918 | 0.722 | 0.03747 | 1.33 |
| 8 | anti3/4 | 3 | 1/100, 1/20 | 0.04570 | 0.888 | 0.803 | 0.05409 | 1.33 |
| 8 | pers1/4 | 2 | 1/100, 1/20 | 0.08190 | 1.000 | 1.000 | 0.08190 | 1.00 |
| 8 | pers1/4 | 3 | 1/100, 1/20 | 0.10929 | 1.000 | 1.000 | 0.10929 | 1.00 |
| 8 | asym(1/4,3/4) | 2 | 1/100, 1/20 | -0.00000 | n/a (VOI=0) | n/a (VOI=0) | -0.00000 | 0.00 |
| 8 | asym(1/4,3/4) | 3 | 1/100, 1/20 | -0.00000 | n/a (VOI=0) | n/a (VOI=0) | -0.00000 | 0.00 |
| 32 | anti2/3 | 2 | 0/0 | 0.03200 | 0.625 | 0.750 | 0.04000 | 2.00 |
| 32 | anti2/3 | 3 | 0/0 | 0.04800 | 0.583 | 0.833 | 0.05600 | 2.00 |
| 32 | anti3/4 | 2 | 0/0 | 0.06400 | 0.583 | 0.833 | 0.07467 | 2.00 |
| 32 | anti3/4 | 3 | 0/0 | 0.09592 | 0.556 | 0.889 | 0.10659 | 2.00 |
| 32 | anti9/10 | 2 | 0/0 | 0.24789 | 0.529 | 0.943 | 0.26213 | 2.00 |
| 32 | anti9/10 | 3 | 0/0 | 0.36756 | 0.591 | 0.957 | 0.43459 | 2.00 |
| 32 | pers1/10 | 2 | 0/0 | 0.46023 | 1.000 | 1.000 | 0.46023 | 1.00 |
| 32 | pers1/10 | 3 | 0/0 | 0.75454 | 1.000 | 1.000 | 0.75454 | 1.00 |
| 32 | pers1/4 | 2 | 0/0 | 0.09600 | 1.000 | 1.000 | 0.09600 | 1.00 |
| 32 | pers1/4 | 3 | 0/0 | 0.13824 | 1.000 | 1.000 | 0.13824 | 1.00 |
| 32 | asym(1/4,3/4) | 2 | 0/0 | -0.00000 | n/a (VOI=0) | n/a (VOI=0) | -0.00000 | 0.00 |
| 32 | asym(1/4,3/4) | 3 | 0/0 | -0.00000 | n/a (VOI=0) | n/a (VOI=0) | -0.00000 | 0.00 |
| 32 | anti3/4 | 2 | 1/100, 1/20 | 0.03060 | 0.918 | 0.722 | 0.03747 | 1.33 |
| 32 | anti3/4 | 3 | 1/100, 1/20 | 0.04570 | 0.888 | 0.803 | 0.05409 | 1.33 |
| 32 | pers1/4 | 2 | 1/100, 1/20 | 0.08550 | 1.000 | 1.000 | 0.08550 | 1.00 |
| 32 | pers1/4 | 3 | 1/100, 1/20 | 0.12102 | 1.000 | 1.000 | 0.12102 | 1.00 |
| 32 | asym(1/4,3/4) | 2 | 1/100, 1/20 | -0.00000 | n/a (VOI=0) | n/a (VOI=0) | -0.00000 | 0.00 |
| 32 | asym(1/4,3/4) | 3 | 1/100, 1/20 | -0.00000 | n/a (VOI=0) | n/a (VOI=0) | -0.00000 | 0.00 |
| 8 | asym(9/10,2/3) | 2 | 0/0 | 0.13290 | 0.618 | 0.894 | 0.16438 | 2.00 |
| 8 | asym(9/10,2/3) | 3 | 0/0 | 0.14956 | 0.631 | 0.929 | 0.18862 | 2.00 |
| 32 | asym(9/10,2/3) | 2 | 0/0 | 0.53567 | 0.537 | 1.000 | 0.57574 | 2.00 |
| 32 | asym(9/10,2/3) | 3 | 0/0 | 0.65517 | 0.602 | 1.000 | 0.78824 | 2.00 |

Fractions: the safe methods are always <= 1 as they must be. Repair (c) captures 0.47-0.68 in the anti-persistent c=k=0 cells (activation 1/2 or 1/4 because the IID optimum has causal risk 2x or 4x alpha); the e-gate (e) captures 0.74-0.96 there, and equals RB-DP exactly (1.000, to 1e-14) on the two T=32 asym(9/10,2/3) cells. With c=1/100, k=1/20 the ordering flips (repair 0.89-0.92 vs e-gate 0.72-0.80). In persistent chains the IID optimum is already causal-safe (risk/alpha = 1.00), so (b)=(a)=(c)=(e) and no premium exists. (b), the IID design, has higher VOI than RB-DP but violates the causal constraint by 2x (4x in one cell: anti 9/10, B=3, T=8) in every anti-persistent cell, 1.33x with c,k>0, so it is not usable as a safe policy. The chain asym(1/4,3/4) has exactly zero VOI (certified exact too), so it is uninformative; asym(9/10,2/3) was added after the first run to have a non-degenerate asymmetric chain (c=k=0 only, B in {2,3}).

At T=8 the certified exact causal VOI (`gamma_cell`, run for every T=8 row, all finished) equals the RB-DP VOI to the printed 5 digits in all 20 rows; at T=32 no exact reference exists (not attempted).

### (e) e-process gate: how it was wired
`EProcessGatedPlanner` with stake 1, supports d=1, c, k; run in exact Fractions in a subprocess with a 120 s cap (all runs finished, T=32 included). A gate with threshold theta has worst-case causal risk <= 1/theta by Ville (stake-1 wealth is a supermartingale for any queried-label mean <= 1/2). Thresholds theta in {2,4,8} with theta <= 2^B (higher is unreachable), each root-mixed with never-promote at activation min(1, alpha*theta) so the risk bound is <= alpha; the best theta per cell is reported. The risk is the Ville bound, not an exactly computed worst case, so (e) is safe by theory and possibly conservative. A threshold of 1/alpha = 10 is unreachable with B<=3 at stake 1, hence the repair.

## Caveats
- L is loose (median gap/VOI 0.43); only U is informative. RB-DP quality here means U accuracy.
- IID-mode U can be above optimum on the grid (E1.1: two B=4, t=9/10 cells by up to 2.5e-3), which feeds directly into Gamma and VOI. Grid 201/10 was chosen for speed; finer grids were not run.
- E1.1 compares with `Gamma_f`/`VOI_interval_f` from the compact JSON; causal and IID certified values individually were recovered as C0 - VOI and that plus Gamma.
- E1.1 was run in two sessions (wall 1100 s, then resumed with 500 s); the `wall_budget_s` field in `e1_1_wpM.json` reflects only the last session. Total runtime exceeded the nominal 30 min (roughly 50+ min wall; the machine was shared with another RB-DP job and was contended).
- E4 was restarted twice (once by me by mistake while it was running; it resumes by key and no row was duplicated or altered). Script sha in `e4_baselines.json` is the final version (which adds the asym(9/10,2/3) chain).
- E4 reports the e-gate with the bound-based repair, not an exact worst-case risk. T=32 cells have no exact reference.
- Single seed for E1.2; synthetic cells only.

## Reproduce
```
uv run --no-sync python scripts/paper4_continuation/rbdp/e1_1_wpM.py     # resumes from results/e1_1_wpM.jsonl; env E11_WALL_S sets wall (used 1100 then 500)
uv run --no-sync python scripts/paper4_continuation/rbdp/e1_2_fresh.py    # seed 20261113
uv run --no-sync python scripts/paper4_continuation/rbdp/e4_baselines.py
uv run --no-sync python scripts/paper4_continuation/rbdp/analyze_e1.py    # prints E1 statistics
uv run --no-sync python scripts/paper4_continuation/rbdp/analyze_e4.py    # prints E4 table with exact-reference column
```
Files: `scripts/paper4_continuation/rbdp/{common,e1_1_wpM,e1_2_fresh,e4_baselines,analyze_e1,analyze_e4}.py`; results `docs/paper4_continuation/rbdp/results/{e1_1_wpM,e1_2_fresh,e4_baselines}.{json,jsonl}`.
