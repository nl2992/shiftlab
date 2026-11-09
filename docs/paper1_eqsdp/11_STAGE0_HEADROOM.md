# 11 — Stage 0 headroom diagnostic (nine datasets, even episodes)

Run 2026-11-08 on `research/paper1-eqsdp-foundation-2026-11-08`. Evaluator-side diagnostic only: it
uses the hidden full-episode losses to score runs and builds no new method. Development data, so
it is descriptive, not confirmatory. All numbers come from `scripts/paper1_eqsdp/stage0_headroom.py`
(tables in `tables/stage0_*.csv`).

## Commands

```
export OPENBLAS_NUM_THREADS=1
PY="<main checkout>/.venv/Scripts/python.exe"
# phase 1: arm R + Wald grid (5 lambda x 4 gamma), B=200, traced, even episodes, 10 seeds (3,770 jobs)
$PY scripts/paper1_eqsdp/stage0_headroom.py run --out outputs/paper1_eqsdp/stage0/p1 --budget 200 --workers 16 --check-orig
# phase 2: free-label ceiling, B=400, arm R and the reference baseline (launched detached, ~1 min)
$PY scripts/paper1_eqsdp/stage0_headroom.py run --out outputs/paper1_eqsdp/stage0/b400 --budget 400 --policies EQSDp_l0.98_g0.3 wald_l0.97_g0.2
$PY scripts/paper1_eqsdp/stage0_headroom.py analyze     # tables/stage0_*.csv, outputs/.../summary.json
$PY -m pytest scripts/paper1_eqsdp/tests -q
```

Sealed datasets are read from the main checkout's `data/c4_sealed` after verifying the registered
`array_content_sha256` of each (`trace_run.sealed_paths`). Seed bases 2026111201 (batch 1) and
2026111301 (batch 2); `ep % 2 == 0` only (377 episodes, 3,770 episode-seed jobs per policy);
contract B=200, c_q=.05, c_s=5, T=2000. No frozen policy code was edited: extra Wald names are
registered by name parsing in `trace_run.registry()` (`wald_l{lam}_g{gamma}` via `sota_extra._mk`
with `WaldLCB`); the 11 grid cells absent from the old registry are new runs, the other 9 existed.

## Reproduction check (before trusting the traced version)

`trace_run.run_policies` replicates the `sota_nine._job` / `suite.run_metrics` loop (same
`build_suite` seeding, same stream rng, `run_episode(trace=True)`), and each row asserts that its
own per-event bookkeeping equals the simulator's `net_cost`.

- Arm R `EQSDp_l0.98_g0.3`: 3,770 re-run rows vs 3,770 even-episode rows in the existing batch-1
  (`nine_armR`) and batch-2 records. Max |net difference| = **0.0**, 0 mismatches.
- Traced net vs the original untraced `run_metrics` net, arm R, run side by side: max |diff| = 0.0.
- The panel also holds `wald_l0.9_g0.2` and `wald_l0.97_g0.2`: both re-run with max |diff| = 0.0
  (11,310 net values compared in total, 0 mismatches).
- Decomposition identity: max |regret − sum of components| over all 79,170 rows = 9.2e-14.

## Reference baseline (task 1)

Equal-dataset mean J on even episodes over all 63 policies with a value on all nine datasets
(45 panel policies read from the records, not re-run; 18 Wald-grid cells that are not in the
panel come from the re-run; full list `tables/stage0_ranking_even.csv`):

| rank | policy | J (equal-dataset mean) | source |
|---|---|---|---|
| 1 | wald_l0.97_g0.2 | 478.075 | panel_records |
| 2 | EQSDp_l0.98_g0.3 | 478.154 | panel_records |
| 3 | wald_l0.98_g0.3 | 478.168 | rerun |
| 4 | wald_l0.98_g0.2 | 478.252 | rerun |
| 5 | smarg_l0.97_k0.2 | 478.294 | panel_records |
| 6 | wald_l0.95_g0.1 | 478.384 | rerun |
| 7 | wald_l0.97_g0.3 | 478.457 | rerun |
| 8 | EQSDp_l0.95_g0.2 | 478.491 | panel_records |

**Reference baseline = `wald_l0.97_g0.2`, J_ref = 478.075** (pooled; per-dataset J_ref in
`tables/stage0_jref.csv`). It is also the best Wald-grid cell. Arm R is second at 478.154
(+0.078, 0.016% of J_ref): a tie at the resolution of this diagnostic, with neither separated
from the other in the later-ranked cells either (ranks 3-8 lie within 0.42). Both are traced below.
The reference baseline was chosen on these same even episodes, so it carries selection optimism
that arm R (selected earlier on other data) does not.

## Decomposition of regret over the best fixed model (task 2)

Definitions (exact, implemented in `trace_run.decompose`; regret = J − min(L0, L1), L = full-episode
loss of the fixed model, episodes classed by evaluator-side sign of L0 − L1):

| component | definition |
|---|---|
| late adoption | challenger-better episodes (L0 > L1): sum over events with the incumbent deployed of l0 − l1. Events on the challenger contribute exactly 0, so this equals loss − L1 |
| false promotion | not-better episodes (L0 ≤ L1, ties included): sum over events with the challenger deployed of l1 − l0, plus c_s for the first switch (the promotion itself) |
| reversal churn | c_s × (switches − 1) when switches ≥ 1, on both classes (all switches beyond the first). Convention: on not-better episodes the first switch is booked to false promotion and only the rest to churn, so no cost is counted twice |
| label spend | c_q × paid labels |
| residual | the unavoidable adoption switch: c_s × min(switches, 1) on challenger-better episodes, and 0 on not-better episodes. It arises because the oracle best fixed model pays no switch cost while any policy starting on model 0 must switch once to reach the challenger |

The five components sum to the regret exactly (identity above). Late adoption is not purely
recoverable: the sum is net over events and includes periods where the incumbent was locally
better; it is an upper bound on what earlier adoption could save, not an achievable target.
Per episode, seed-means are taken first; CIs resample episodes within dataset (2,000 resamples,
shared across components); pooled = equal-dataset mean, its CI the percentile interval of the
equal-weight mean of independent per-dataset resamples. % of J_ref divides by the (point) J_ref of
the same dataset (pooled: pooled J_ref). Labels actually used average 176 of 200 (label spend
8.82 for both policies).


**EQSDp_l0.98_g0.3: mean per episode (loss units)** (pooled row = equal-dataset mean; brackets = 95% episode-bootstrap CI)

| dataset | late_adoption | false_promotion | reversal_churn | label_spend | residual | regret |
|---|---|---|---|---|---|---|
| sf_311 | 27.92 [22.98, 33.07] | 0.00 [0.00, 0.00] | 0.54 [0.28, 0.86] | 9.87 [9.75, 9.97] | 5.00 [5.00, 5.00] | 43.33 [38.40, 48.42] |
| kc_311 | 3.62 [0.89, 7.94] | 10.56 [4.86, 15.63] | 4.04 [3.17, 4.96] | 9.96 [9.93, 9.99] | 1.25 [0.62, 2.00] | 29.44 [22.54, 35.26] |
| montgomery_traffic | 3.88 [1.87, 6.05] | 2.62 [0.87, 4.79] | 3.46 [2.16, 4.92] | 6.60 [6.14, 7.10] | 3.40 [2.40, 4.20] | 19.96 [17.09, 23.08] |
| dallas_311 | 10.58 [8.22, 12.88] | 2.12 [0.84, 3.62] | 2.91 [1.97, 3.90] | 9.78 [9.67, 9.88] | 4.00 [3.50, 4.50] | 29.39 [26.91, 31.84] |
| dc_311 | 29.79 [27.43, 32.05] | 0.00 [0.00, 0.00] | 0.43 [0.16, 0.75] | 9.99 [9.99, 10.00] | 5.00 [5.00, 5.00] | 45.22 [42.92, 47.45] |
| austin_311 | 5.67 [4.02, 7.32] | 3.99 [2.15, 6.11] | 2.56 [1.82, 3.32] | 7.87 [7.23, 8.50] | 3.00 [2.30, 3.70] | 23.08 [20.71, 25.55] |
| cincinnati_311 | 9.29 [6.73, 11.91] | 3.27 [1.36, 5.35] | 2.06 [1.18, 3.01] | 9.54 [8.89, 9.96] | 3.53 [2.79, 4.26] | 27.68 [25.12, 30.27] |
| oakland_311 | 4.50 [3.33, 5.73] | 1.92 [0.00, 4.43] | 0.66 [0.11, 1.36] | 5.80 [5.33, 6.28] | 4.29 [3.57, 4.82] | 17.16 [14.95, 19.71] |
| sandiego_311 | 5.84 [4.36, 7.49] | 4.98 [2.96, 7.10] | 3.71 [2.79, 4.72] | 9.94 [9.92, 9.97] | 3.10 [2.50, 3.70] | 27.57 [25.37, 29.82] |
| **POOLED** | 11.23 [10.34, 12.14] | 3.27 [2.41, 4.02] | 2.26 [1.98, 2.55] | 8.82 [8.69, 8.93] | 3.62 [3.41, 3.82] | 29.20 [28.04, 30.35] |

**EQSDp_l0.98_g0.3: % of J_ref** (pooled row = equal-dataset mean; brackets = 95% episode-bootstrap CI)

| dataset | late_adoption | false_promotion | reversal_churn | label_spend | residual | regret |
|---|---|---|---|---|---|---|
| sf_311 | 6.22 [5.12, 7.37] | 0.00 [0.00, 0.00] | 0.12 [0.06, 0.19] | 2.20 [2.17, 2.22] | 1.11 [1.11, 1.11] | 9.66 [8.56, 10.79] |
| kc_311 | 0.61 [0.15, 1.34] | 1.78 [0.82, 2.63] | 0.68 [0.54, 0.84] | 1.68 [1.67, 1.68] | 0.21 [0.11, 0.34] | 4.96 [3.80, 5.94] |
| montgomery_traffic | 1.05 [0.51, 1.64] | 0.71 [0.24, 1.30] | 0.94 [0.59, 1.34] | 1.79 [1.67, 1.93] | 0.92 [0.65, 1.14] | 5.42 [4.64, 6.27] |
| dallas_311 | 2.18 [1.69, 2.65] | 0.44 [0.17, 0.74] | 0.60 [0.41, 0.80] | 2.01 [1.99, 2.03] | 0.82 [0.72, 0.93] | 6.05 [5.54, 6.55] |
| dc_311 | 7.41 [6.83, 7.97] | 0.00 [0.00, 0.00] | 0.11 [0.04, 0.19] | 2.49 [2.49, 2.49] | 1.24 [1.24, 1.24] | 11.25 [10.68, 11.81] |
| austin_311 | 0.83 [0.59, 1.07] | 0.58 [0.31, 0.89] | 0.37 [0.27, 0.49] | 1.15 [1.06, 1.24] | 0.44 [0.34, 0.54] | 3.38 [3.03, 3.74] |
| cincinnati_311 | 1.94 [1.41, 2.49] | 0.68 [0.29, 1.12] | 0.43 [0.25, 0.63] | 2.00 [1.86, 2.09] | 0.74 [0.58, 0.89] | 5.79 [5.26, 6.33] |
| oakland_311 | 0.98 [0.72, 1.24] | 0.42 [0.00, 0.96] | 0.14 [0.02, 0.29] | 1.26 [1.16, 1.36] | 0.93 [0.78, 1.05] | 3.73 [3.25, 4.28] |
| sandiego_311 | 1.52 [1.14, 1.95] | 1.30 [0.77, 1.85] | 0.97 [0.73, 1.23] | 2.59 [2.59, 2.60] | 0.81 [0.65, 0.97] | 7.19 [6.62, 7.78] |
| **POOLED** | 2.35 [2.16, 2.54] | 0.68 [0.50, 0.84] | 0.47 [0.42, 0.53] | 1.84 [1.82, 1.87] | 0.76 [0.71, 0.80] | 6.11 [5.86, 6.35] |

**wald_l0.97_g0.2: mean per episode (loss units)** (pooled row = equal-dataset mean; brackets = 95% episode-bootstrap CI)

| dataset | late_adoption | false_promotion | reversal_churn | label_spend | residual | regret |
|---|---|---|---|---|---|---|
| sf_311 | 31.01 [25.58, 36.55] | 0.00 [0.00, 0.00] | 0.18 [0.06, 0.32] | 9.87 [9.75, 9.97] | 5.00 [5.00, 5.00] | 46.07 [40.62, 51.56] |
| kc_311 | 3.86 [0.98, 8.42] | 9.55 [2.90, 15.15] | 2.65 [1.94, 3.38] | 9.96 [9.93, 9.99] | 1.25 [0.62, 2.00] | 27.27 [19.67, 33.80] |
| montgomery_traffic | 5.62 [3.14, 8.49] | 2.50 [0.68, 4.82] | 1.80 [0.80, 2.98] | 6.60 [6.14, 7.10] | 3.20 [2.20, 4.00] | 19.72 [16.47, 23.13] |
| dallas_311 | 11.27 [8.87, 13.63] | 1.57 [0.32, 3.09] | 1.90 [1.23, 2.60] | 9.78 [9.67, 9.88] | 4.00 [3.50, 4.50] | 28.53 [25.79, 31.09] |
| dc_311 | 32.67 [30.20, 35.13] | 0.00 [0.00, 0.00] | 0.11 [0.01, 0.25] | 9.99 [9.99, 10.00] | 5.00 [5.00, 5.00] | 47.77 [45.26, 50.27] |
| austin_311 | 6.33 [4.63, 8.09] | 3.82 [1.90, 6.00] | 1.40 [0.85, 2.01] | 7.87 [7.23, 8.50] | 2.97 [2.29, 3.63] | 22.39 [19.91, 24.91] |
| cincinnati_311 | 10.69 [7.89, 13.51] | 2.66 [1.08, 4.43] | 1.24 [0.74, 1.79] | 9.54 [8.89, 9.96] | 3.51 [2.76, 4.25] | 27.64 [24.80, 30.23] |
| oakland_311 | 5.87 [4.41, 7.35] | 1.00 [0.00, 2.58] | 0.30 [0.00, 0.75] | 5.80 [5.33, 6.28] | 4.18 [3.43, 4.79] | 17.15 [15.13, 19.12] |
| sandiego_311 | 6.60 [4.98, 8.30] | 4.22 [2.30, 6.28] | 1.75 [1.18, 2.38] | 9.94 [9.92, 9.97] | 3.09 [2.48, 3.70] | 25.60 [23.60, 27.61] |
| **POOLED** | 12.66 [11.71, 13.63] | 2.81 [1.90, 3.58] | 1.26 [1.08, 1.47] | 8.82 [8.69, 8.93] | 3.58 [3.37, 3.78] | 29.13 [27.90, 30.37] |

**wald_l0.97_g0.2: % of J_ref** (pooled row = equal-dataset mean; brackets = 95% episode-bootstrap CI)

| dataset | late_adoption | false_promotion | reversal_churn | label_spend | residual | regret |
|---|---|---|---|---|---|---|
| sf_311 | 6.91 [5.70, 8.15] | 0.00 [0.00, 0.00] | 0.04 [0.01, 0.07] | 2.20 [2.17, 2.22] | 1.11 [1.11, 1.11] | 10.27 [9.06, 11.50] |
| kc_311 | 0.65 [0.17, 1.42] | 1.61 [0.49, 2.55] | 0.45 [0.33, 0.57] | 1.68 [1.67, 1.68] | 0.21 [0.11, 0.34] | 4.60 [3.31, 5.70] |
| montgomery_traffic | 1.53 [0.85, 2.31] | 0.68 [0.18, 1.31] | 0.49 [0.22, 0.81] | 1.79 [1.67, 1.93] | 0.87 [0.60, 1.09] | 5.36 [4.48, 6.29] |
| dallas_311 | 2.32 [1.83, 2.80] | 0.32 [0.07, 0.64] | 0.39 [0.25, 0.53] | 2.01 [1.99, 2.03] | 0.82 [0.72, 0.93] | 5.87 [5.31, 6.40] |
| dc_311 | 8.13 [7.51, 8.74] | 0.00 [0.00, 0.00] | 0.03 [0.00, 0.06] | 2.49 [2.49, 2.49] | 1.24 [1.24, 1.24] | 11.89 [11.26, 12.51] |
| austin_311 | 0.93 [0.68, 1.18] | 0.56 [0.28, 0.88] | 0.20 [0.12, 0.29] | 1.15 [1.06, 1.24] | 0.43 [0.34, 0.53] | 3.28 [2.91, 3.65] |
| cincinnati_311 | 2.24 [1.65, 2.83] | 0.56 [0.23, 0.93] | 0.26 [0.15, 0.38] | 2.00 [1.86, 2.09] | 0.74 [0.58, 0.89] | 5.78 [5.19, 6.33] |
| oakland_311 | 1.27 [0.96, 1.60] | 0.22 [0.00, 0.56] | 0.07 [0.00, 0.16] | 1.26 [1.16, 1.36] | 0.91 [0.74, 1.04] | 3.72 [3.29, 4.15] |
| sandiego_311 | 1.72 [1.30, 2.17] | 1.10 [0.60, 1.64] | 0.46 [0.31, 0.62] | 2.59 [2.59, 2.60] | 0.81 [0.65, 0.97] | 6.68 [6.16, 7.20] |
| **POOLED** | 2.65 [2.45, 2.85] | 0.59 [0.40, 0.75] | 0.26 [0.23, 0.31] | 1.84 [1.82, 1.87] | 0.75 [0.71, 0.79] | 6.09 [5.84, 6.35] |

**Free-label ceiling, B=400 minus B=200 (negative = improvement)**

| policy | quantity | dataset | delta J | % of J_ref |
|---|---|---|---|---|
| EQSDp_l0.98_g0.3 | excl_label_fees | sf_311 | -2.72 [-3.71, -1.83] | -0.607 [-0.827, -0.407] |
| EQSDp_l0.98_g0.3 | excl_label_fees | kc_311 | -3.79 [-8.88, 0.84] | -0.639 [-1.496, 0.142] |
| EQSDp_l0.98_g0.3 | excl_label_fees | montgomery_traffic | 1.44 [-0.00, 3.06] | 0.390 [-0.000, 0.832] |
| EQSDp_l0.98_g0.3 | excl_label_fees | dallas_311 | -1.25 [-3.77, 1.43] | -0.258 [-0.776, 0.293] |
| EQSDp_l0.98_g0.3 | excl_label_fees | dc_311 | -2.87 [-4.29, -1.75] | -0.714 [-1.067, -0.436] |
| EQSDp_l0.98_g0.3 | excl_label_fees | austin_311 | -0.04 [-1.16, 1.38] | -0.006 [-0.169, 0.203] |
| EQSDp_l0.98_g0.3 | excl_label_fees | cincinnati_311 | -1.43 [-2.99, 0.16] | -0.299 [-0.625, 0.033] |
| EQSDp_l0.98_g0.3 | excl_label_fees | oakland_311 | -0.20 [-1.16, 0.81] | -0.044 [-0.252, 0.175] |
| EQSDp_l0.98_g0.3 | excl_label_fees | sandiego_311 | 1.04 [-1.72, 4.02] | 0.271 [-0.449, 1.050] |
| EQSDp_l0.98_g0.3 | excl_label_fees | POOLED | -1.09 [-1.91, -0.31] | -0.229 [-0.400, -0.065] |
| EQSDp_l0.98_g0.3 | incl_label_fees | POOLED | 4.69 [3.89, 5.50] | 0.982 [0.813, 1.150] |
| EQSDp_l0.98_g0.3 | label_fees_only | POOLED | 5.79 [5.58, 5.98] | 1.211 [1.168, 1.251] |
| wald_l0.97_g0.2 | excl_label_fees | sf_311 | -4.48 [-5.79, -3.32] | -0.998 [-1.290, -0.740] |
| wald_l0.97_g0.2 | excl_label_fees | kc_311 | -3.49 [-8.04, 0.69] | -0.588 [-1.354, 0.116] |
| wald_l0.97_g0.2 | excl_label_fees | montgomery_traffic | 0.68 [-0.73, 2.74] | 0.184 [-0.199, 0.745] |
| wald_l0.97_g0.2 | excl_label_fees | dallas_311 | -1.55 [-4.25, 1.43] | -0.319 [-0.874, 0.294] |
| wald_l0.97_g0.2 | excl_label_fees | dc_311 | -4.30 [-6.02, -3.03] | -1.069 [-1.499, -0.755] |
| wald_l0.97_g0.2 | excl_label_fees | austin_311 | 0.73 [-0.34, 1.97] | 0.107 [-0.050, 0.289] |
| wald_l0.97_g0.2 | excl_label_fees | cincinnati_311 | -1.68 [-3.86, 0.84] | -0.351 [-0.808, 0.175] |
| wald_l0.97_g0.2 | excl_label_fees | oakland_311 | -0.76 [-1.93, 0.06] | -0.165 [-0.419, 0.014] |
| wald_l0.97_g0.2 | excl_label_fees | sandiego_311 | 1.05 [-1.78, 3.98] | 0.273 [-0.465, 1.038] |
| wald_l0.97_g0.2 | excl_label_fees | POOLED | -1.53 [-2.30, -0.73] | -0.321 [-0.481, -0.154] |
| wald_l0.97_g0.2 | incl_label_fees | POOLED | 4.25 [3.46, 5.07] | 0.890 [0.724, 1.060] |
| wald_l0.97_g0.2 | label_fees_only | POOLED | 5.79 [5.58, 5.98] | 1.211 [1.168, 1.251] |

## Free-label ceiling (task 3)

Same policies, same seeds, B=400 (double the contract budget), c_q unchanged. Table at the end
of the previous section. Pooled, B=400 minus B=200 (negative = better):

| policy | excluding label fees (loss + switches) | including label fees |
|---|---|---|
| `wald_l0.97_g0.2` | −1.53 [−2.30, −0.73] = −0.32% of J_ref [−0.48, −0.15] | +4.25 [3.46, 5.07] = +0.89% |
| `EQSDp_l0.98_g0.3` | −1.09 [−1.91, −0.31] = −0.23% of J_ref [−0.40, −0.07] | +4.69 [3.89, 5.50] = +0.98% |

Doubling the budget at zero fee would buy 0.23-0.32% of J_ref; at the contract price the extra
labels are net losses (extra fees +5.79 = +1.21% of J_ref). Per dataset the loss-and-switch gain
is significant (CI excludes 0) only on sf_311 and dc_311 for both policies (and oakland_311 is
borderline for Wald); it is positive (worse) on montgomery_traffic and sandiego_311.

## Stop rule (plan §4, threshold 0.5% of J_ref)

Pooled point estimates (% of J_ref; 95% CI):

| component | arm R | reference Wald | module it bounds |
|---|---|---|---|
| late adoption | 2.35 [2.16, 2.54] | 2.65 [2.45, 2.85] | C5 early adoption |
| false promotion | 0.68 [0.50, 0.84] | 0.59 [0.40, 0.75] | C2 |
| reversal churn | 0.47 [0.42, 0.53] | 0.26 [0.23, 0.31] | C2 |
| false promotion + churn | 1.16 | 0.85 | C2 |
| label spend (fee) | 1.84 [1.82, 1.87] | 1.84 [1.82, 1.87] | C1 (fee side) |
| free-label ceiling, decisions only | 0.23 [0.07, 0.40] | 0.32 [0.15, 0.48] | C1 (decision side) |
| residual (adoption switch) | 0.76 | 0.75 | none (unavoidable by construction) |

- **C5 (early adoption): passes.** Late adoption is 2.3-2.6% of J_ref, CI lower bounds far above
  0.5%. It is concentrated on sf_311 and dc_311 (6.2-8.1% of J_ref); on the other seven datasets it
  is 0.6-2.3%, and 0.6% on kc_311 and 0.8-0.9% on austin_311 for arm R. Caveat: an upper bound
  on recoverable gain (see above).
- **C2 (false promotion / reversal): passes on the combined target** (0.85-1.16%). False
  promotion alone clears 0.5% for arm R (0.68, CI lower 0.50, borderline) and for Wald (0.59, CI
  lower 0.40); churn alone is below 0.5% for both (0.47 and 0.26). It is
  concentrated in kc_311, sandiego_311, austin_311, montgomery_traffic and cincinnati_311, and is zero
  on sf_311 and dc_311, which have no (or one) not-better episode.
- **C1 (label timing): fails on the decision side, and its fee side is not recoverable by
  timing alone.** What extra labels are worth to decisions is 0.23-0.32% of J_ref, below 0.5%
  (CI upper bounds 0.40 and 0.48 are also below it). The label fee itself is 1.84% of J_ref, which
  exceeds 0.5%, but 176 labels is the spend of policies that need them to decide; saving fees is
  only available if decisions are kept, and the ceiling above says extra information has little
  decision value, not that fewer labels cost nothing. The plan's own criterion (C1 must win
  through decisions, not fees) therefore fails the 0.5% test.

## Limits

- Even episodes of the nine datasets only; these were used to pick the reference baseline, so
  the ranking is development-selection optimistic for the Wald cell.
- Class labels (challenger better or not) are the episode-level realised loss difference; the
  hindsight reference is the best fixed model, not a within-episode switching oracle, so a policy
  that switches usefully mid-episode can have negative late adoption in a sub-interval.
- The B=400 run covers arm R and the reference Wald only. 10 policy seeds are averaged, not
  resampled.
- Nothing here is confirmatory evidence or a claim about a method that has not been built.
