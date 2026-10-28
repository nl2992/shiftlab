# B1 numerical check of Claims 1-2 (Bernoulli-type instance)

**Status: Monte Carlo development evidence only (registry block `lane_b_toy_development`). Not a
theorem, not confirmatory.** Code: `scripts/lane_b/separation_check.py` (re-run: `... separation_check.py 1000 1000`,
about 3.5 min on 6 workers). Tests: `tests/test_lane_b_separation.py` (25 pass; ruff clean).
Full grids: `B1_numerical_check_grid.csv` (every rule x cell x alpha, with null counts and exact
upper bounds) and `B1_numerical_check_restart_diag.csv`.

## Setup as run (and deviations from the brief)

- T=2000, burst of L=300 disagreements on [500,800), sparse disagreements at rho afterwards,
  **D=0 before s=500** (the brief leaves pre-s unspecified). Z = +-1 with mean mu: H 0.5 from s; N -0.2 in
  the burst then 0.5; eps=0.1, C=1. Seeds: 1000 H/N pairs (D, Z-uniforms and sampling-uniforms shared
  between H and N and across all rules in a cell) and 1000 independent null seeds.
- Seed map: `seed = 100600000 + k*10000 + i`, `k = (variant_idx*2 + delay_idx)*4 + budget_idx`
  (k<24), `i in [0,1000)` for H/N rows, `i in [5000,6000)` for null rows; K_alpha reference runs use
  `100690000 + 1000*variant_idx`. All inside 100600000-100699999.
- E-process: the row-vectorised mean-mixture of the five default stakes, identical to
  `PredictableBoundMeanEProcess` (a test checks equality to 1e-9). V = G*Z/q - eps, bound C/q+eps.
  A disagreement with q_t=0 is a predictable skip (factor 1); using bound eps there gave a spurious
  1-stake loss per skipped event (bug found and fixed in development). Alarm at event t is
  recorded at t+d (event-ordered e-process, label arrives d later); a hard budget is charged at
  request (pending labels count).
- Rules. Oblivious: (a) fixed q in {0.05,0.1,0.25,0.5,1}; (b) burst cap, q=1 for the first b
  burst-type disagreements (run of >=3 consecutive D), b in {0,B/4,B/2,B}, then q_sparse in
  {0.25,0.5,1} on other disagreements (burst events after b get q=0); (c) paced
  q=remaining/(past-200-window rate x remaining events). Responsive: r1 = q=1 on burst until a
  Wald SPRT (H0 mean=eps vs H1 mean=0.5, delta=0.2, **alternative known**, past labels only) accepts H0,
  then q=0 on burst-type events, q=1 on sparse; r2 = DE-CuSum-style statistic W (+= Z-eps on arrived
  labels; sample at q=1 iff W>=0; each skipped disagreement adds 1/h), h in {3,10,30,100}.
  Best oblivious / best r2 are picked from their grids on the same seeds (optimistic for both,
  more so for the 18-config oblivious grid, so this is conservative against the separation claim).
- **Deviation 1 (variant A vs B).** Variant A is the literal brief: agreements contribute -eps to
  the e-process. With rho=0.05 that is about 19 agreements per disagreement, and the drag
  dominates: even with an unconstrained budget the best case needs median 225 labels for alpha=0.05
  (P_detect 0.93) and 261 for 0.001 (P 0.54), and **no rule in any cell detects in N, and nothing
  detects in H (max P_H = 0.001 under any budget cap).** The instance is also inconsistent with an
  unconditional charter null (rho*mu - eps < 0 after onset). Variant B (the headline) updates the e-process only on
  disagreement events (null conditional on D_t=1; note this is a conditional-on-current-context
  null, the caveat in the `PredictableBoundMeanEProcess` docstring, which I did not verify).
- **Deviation 2 (B2, supplementary).** With rho=0.05 the sparse phase offers only about 60
  disagreements, below the conjecture's regime for alpha=0.001 (K_alpha(sparse) median 46, only 14% reach it
  at unlimited q=1). B2 repeats variant B with rho=0.2 (about 240 sparse disagreements). Beyond the brief's grid;
  labelled supplementary.

## Results (auto-generated; P standard error <= 0.016 at 1000 seeds)

### Empirical K_alpha (unconstrained budget, d=0)

| variant | scenario | alpha | P_detect | median labels | p90 labels |
|---|---|---|---|---|---|
| A_agree_in_eprocess | H_burst_q1 | 0.05 | 0.927 | 225 | 278 |
| A_agree_in_eprocess | H_burst_q1 | 0.001 | 0.536 | 261 | 293 |
| A_agree_in_eprocess | N_sparse_only_q1 | 0.05 | 0.000 | nan | nan |
| A_agree_in_eprocess | N_sparse_only_q1 | 0.001 | 0.000 | nan | nan |
| B_disagree_only | H_burst_q1 | 0.05 | 1.000 | 41 | 90 |
| B_disagree_only | H_burst_q1 | 0.001 | 1.000 | 92 | 159 |
| B_disagree_only | N_sparse_only_q1 | 0.05 | 0.658 | 38 | 58 |
| B_disagree_only | N_sparse_only_q1 | 0.001 | 0.139 | 46 | 67 |
| B2_disagree_only_rho0.2 | H_burst_q1 | 0.05 | 1.000 | 41 | 82 |
| B2_disagree_only_rho0.2 | H_burst_q1 | 0.001 | 1.000 | 92 | 156 |
| B2_disagree_only_rho0.2 | N_sparse_only_q1 | 0.05 | 1.000 | 49 | 93 |
| B2_disagree_only_rho0.2 | N_sparse_only_q1 | 0.001 | 0.987 | 100 | 162 |

### Null control (mean = eps everywhere)

- alpha=0.05: max false-alarm count over 552 (cell, rule) null runs = 29/1000 (rate 0.0290; B_disagree_only, d=20, B=80, fixed(q=0.5)); largest exact 95% upper bound = 0.0393; mean rate = 0.01045
- alpha=0.001: max false-alarm count over 552 (cell, rule) null runs = 2/1000 (rate 0.0020; B_disagree_only, d=0, B=80, r2(h=30)); largest exact 95% upper bound = 0.0063; mean rate = 0.00013

### Main tables

#### variant A_agree_in_eprocess, d=0, alpha=0.05

| B | choice  rule | P_H | P_N | delay_H | delay_N | labels_H | labels_N |
|---|---|---|---|---|---|---|---|---|
| 40 | obl max-min | fixed(q=0.05) | 0.000 | 0.000 | 1500 | 1200 | 18 | 18 |
| 40 | obl min-delay | fixed(q=0.05) | 0.000 | 0.000 | 1500 | 1200 | 18 | 18 |
| 40 | r1 SPRT | r1 | 0.000 | 0.000 | 1500 | 1200 | 40 | 40 |
| 40 | r2 DE-CuSum best | r2(h=3) | 0.000 | 0.000 | 1500 | 1200 | 40 | 40 |
| 60 | obl max-min | fixed(q=0.05) | 0.000 | 0.000 | 1500 | 1200 | 18 | 18 |
| 60 | obl min-delay | fixed(q=0.05) | 0.000 | 0.000 | 1500 | 1200 | 18 | 18 |
| 60 | r1 SPRT | r1 | 0.000 | 0.000 | 1500 | 1200 | 60 | 59 |
| 60 | r2 DE-CuSum best | r2(h=3) | 0.000 | 0.000 | 1500 | 1200 | 60 | 60 |
| 80 | obl max-min | fixed(q=0.05) | 0.000 | 0.000 | 1500 | 1200 | 18 | 18 |
| 80 | obl min-delay | fixed(q=0.05) | 0.000 | 0.000 | 1500 | 1200 | 18 | 18 |
| 80 | r1 SPRT | r1 | 0.000 | 0.000 | 1500 | 1200 | 78 | 68 |
| 80 | r2 DE-CuSum best | r2(h=3) | 0.000 | 0.000 | 1500 | 1200 | 80 | 80 |
| 120 | obl max-min | fixed(q=1.0) | 0.001 | 0.000 | 1499 | 1200 | 120 | 120 |
| 120 | obl min-delay | fixed(q=1.0) | 0.001 | 0.000 | 1499 | 1200 | 120 | 120 |
| 120 | r1 SPRT | r1 | 0.001 | 0.000 | 1499 | 1200 | 111 | 69 |
| 120 | r2 DE-CuSum best | r2(h=3) | 0.001 | 0.000 | 1499 | 1200 | 120 | 120 |

#### variant A_agree_in_eprocess, d=0, alpha=0.001

| B | choice  rule | P_H | P_N | delay_H | delay_N | labels_H | labels_N |
|---|---|---|---|---|---|---|---|---|
| 40 | obl max-min | fixed(q=0.05) | 0.000 | 0.000 | 1500 | 1200 | 18 | 18 |
| 40 | obl min-delay | fixed(q=0.05) | 0.000 | 0.000 | 1500 | 1200 | 18 | 18 |
| 40 | r1 SPRT | r1 | 0.000 | 0.000 | 1500 | 1200 | 40 | 40 |
| 40 | r2 DE-CuSum best | r2(h=3) | 0.000 | 0.000 | 1500 | 1200 | 40 | 40 |
| 60 | obl max-min | fixed(q=0.05) | 0.000 | 0.000 | 1500 | 1200 | 18 | 18 |
| 60 | obl min-delay | fixed(q=0.05) | 0.000 | 0.000 | 1500 | 1200 | 18 | 18 |
| 60 | r1 SPRT | r1 | 0.000 | 0.000 | 1500 | 1200 | 60 | 59 |
| 60 | r2 DE-CuSum best | r2(h=3) | 0.000 | 0.000 | 1500 | 1200 | 60 | 60 |
| 80 | obl max-min | fixed(q=0.05) | 0.000 | 0.000 | 1500 | 1200 | 18 | 18 |
| 80 | obl min-delay | fixed(q=0.05) | 0.000 | 0.000 | 1500 | 1200 | 18 | 18 |
| 80 | r1 SPRT | r1 | 0.000 | 0.000 | 1500 | 1200 | 78 | 68 |
| 80 | r2 DE-CuSum best | r2(h=3) | 0.000 | 0.000 | 1500 | 1200 | 80 | 80 |
| 120 | obl max-min | fixed(q=0.05) | 0.000 | 0.000 | 1500 | 1200 | 18 | 18 |
| 120 | obl min-delay | fixed(q=0.05) | 0.000 | 0.000 | 1500 | 1200 | 18 | 18 |
| 120 | r1 SPRT | r1 | 0.000 | 0.000 | 1500 | 1200 | 111 | 69 |
| 120 | r2 DE-CuSum best | r2(h=3) | 0.000 | 0.000 | 1500 | 1200 | 120 | 120 |

#### variant A_agree_in_eprocess, d=20, alpha=0.05

| B | choice  rule | P_H | P_N | delay_H | delay_N | labels_H | labels_N |
|---|---|---|---|---|---|---|---|---|
| 40 | obl max-min | fixed(q=0.05) | 0.000 | 0.000 | 1500 | 1200 | 18 | 18 |
| 40 | obl min-delay | fixed(q=0.05) | 0.000 | 0.000 | 1500 | 1200 | 18 | 18 |
| 40 | r1 SPRT | r1 | 0.000 | 0.000 | 1500 | 1200 | 40 | 40 |
| 40 | r2 DE-CuSum best | r2(h=3) | 0.000 | 0.000 | 1500 | 1200 | 40 | 40 |
| 60 | obl max-min | fixed(q=0.05) | 0.000 | 0.000 | 1500 | 1200 | 18 | 18 |
| 60 | obl min-delay | fixed(q=0.05) | 0.000 | 0.000 | 1500 | 1200 | 18 | 18 |
| 60 | r1 SPRT | r1 | 0.000 | 0.000 | 1500 | 1200 | 60 | 60 |
| 60 | r2 DE-CuSum best | r2(h=3) | 0.000 | 0.000 | 1500 | 1200 | 60 | 60 |
| 80 | obl max-min | fixed(q=0.05) | 0.000 | 0.000 | 1500 | 1200 | 18 | 18 |
| 80 | obl min-delay | fixed(q=0.05) | 0.000 | 0.000 | 1500 | 1200 | 18 | 18 |
| 80 | r1 SPRT | r1 | 0.000 | 0.000 | 1500 | 1200 | 80 | 79 |
| 80 | r2 DE-CuSum best | r2(h=3) | 0.000 | 0.000 | 1500 | 1200 | 80 | 80 |
| 120 | obl max-min | fixed(q=0.5) | 0.001 | 0.000 | 1499 | 1200 | 120 | 120 |
| 120 | obl min-delay | fixed(q=0.5) | 0.001 | 0.000 | 1499 | 1200 | 120 | 120 |
| 120 | r1 SPRT | r1 | 0.000 | 0.000 | 1500 | 1200 | 115 | 89 |
| 120 | r2 DE-CuSum best | r2(h=3) | 0.000 | 0.000 | 1500 | 1200 | 120 | 120 |

#### variant A_agree_in_eprocess, d=20, alpha=0.001

| B | choice  rule | P_H | P_N | delay_H | delay_N | labels_H | labels_N |
|---|---|---|---|---|---|---|---|---|
| 40 | obl max-min | fixed(q=0.05) | 0.000 | 0.000 | 1500 | 1200 | 18 | 18 |
| 40 | obl min-delay | fixed(q=0.05) | 0.000 | 0.000 | 1500 | 1200 | 18 | 18 |
| 40 | r1 SPRT | r1 | 0.000 | 0.000 | 1500 | 1200 | 40 | 40 |
| 40 | r2 DE-CuSum best | r2(h=3) | 0.000 | 0.000 | 1500 | 1200 | 40 | 40 |
| 60 | obl max-min | fixed(q=0.05) | 0.000 | 0.000 | 1500 | 1200 | 18 | 18 |
| 60 | obl min-delay | fixed(q=0.05) | 0.000 | 0.000 | 1500 | 1200 | 18 | 18 |
| 60 | r1 SPRT | r1 | 0.000 | 0.000 | 1500 | 1200 | 60 | 60 |
| 60 | r2 DE-CuSum best | r2(h=3) | 0.000 | 0.000 | 1500 | 1200 | 60 | 60 |
| 80 | obl max-min | fixed(q=0.05) | 0.000 | 0.000 | 1500 | 1200 | 18 | 18 |
| 80 | obl min-delay | fixed(q=0.05) | 0.000 | 0.000 | 1500 | 1200 | 18 | 18 |
| 80 | r1 SPRT | r1 | 0.000 | 0.000 | 1500 | 1200 | 80 | 79 |
| 80 | r2 DE-CuSum best | r2(h=3) | 0.000 | 0.000 | 1500 | 1200 | 80 | 80 |
| 120 | obl max-min | fixed(q=0.05) | 0.000 | 0.000 | 1500 | 1200 | 18 | 18 |
| 120 | obl min-delay | fixed(q=0.05) | 0.000 | 0.000 | 1500 | 1200 | 18 | 18 |
| 120 | r1 SPRT | r1 | 0.000 | 0.000 | 1500 | 1200 | 115 | 89 |
| 120 | r2 DE-CuSum best | r2(h=3) | 0.000 | 0.000 | 1500 | 1200 | 120 | 120 |

#### variant B_disagree_only, d=0, alpha=0.05

| B | choice  rule | P_H | P_N | delay_H | delay_N | labels_H | labels_N |
|---|---|---|---|---|---|---|---|---|
| 40 | obl max-min | burstcap(b=0,qs=1.0) | 0.468 | 0.333 | 1129 | 952 | 32 | 35 |
| 40 | obl min-delay | burstcap(b=40,qs=0.5) | 0.474 | 0.001 | 799 | 1199 | 31 | 40 |
| 40 | r1 SPRT | r1 | 0.468 | 0.057 | 814 | 1161 | 32 | 40 |
| 40 | r2 DE-CuSum best | r2(h=100) | 0.473 | 0.011 | 816 | 1196 | 31 | 19 |
| 60 | obl max-min | burstcap(b=0,qs=1.0) | 0.684 | 0.567 | 1077 | 894 | 40 | 45 |
| 60 | obl min-delay | burstcap(b=60,qs=0.25) | 0.762 | 0.000 | 382 | 1200 | 39 | 60 |
| 60 | r1 SPRT | r1 | 0.726 | 0.309 | 490 | 1076 | 40 | 56 |
| 60 | r2 DE-CuSum best | r2(h=100) | 0.721 | 0.027 | 478 | 1193 | 37 | 20 |
| 80 | obl max-min | burstcap(b=0,qs=1.0) | 0.729 | 0.648 | 1065 | 883 | 40 | 46 |
| 80 | obl min-delay | burstcap(b=80,qs=0.25) | 0.887 | 0.001 | 204 | 1199 | 43 | 80 |
| 80 | r1 SPRT | r1 | 0.841 | 0.430 | 361 | 1061 | 42 | 61 |
| 80 | r2 DE-CuSum best | r2(h=100) | 0.851 | 0.037 | 307 | 1191 | 41 | 22 |
| 120 | obl max-min | burstcap(b=0,qs=1.0) | 0.726 | 0.644 | 1049 | 861 | 39 | 45 |
| 120 | obl min-delay | burstcap(b=120,qs=0.5) | 0.979 | 0.000 | 75 | 1200 | 46 | 120 |
| 120 | r1 SPRT | r1 | 0.907 | 0.431 | 300 | 1061 | 44 | 62 |
| 120 | r2 DE-CuSum best | r2(h=100) | 0.926 | 0.037 | 213 | 1191 | 42 | 22 |

#### variant B_disagree_only, d=0, alpha=0.001

| B | choice  rule | P_H | P_N | delay_H | delay_N | labels_H | labels_N |
|---|---|---|---|---|---|---|---|---|
| 40 | obl max-min | burstcap(b=0,qs=1.0) | 0.076 | 0.047 | 1451 | 1171 | 39 | 40 |
| 40 | obl min-delay | burstcap(b=40,qs=0.25) | 0.090 | 0.000 | 1368 | 1200 | 39 | 40 |
| 40 | r1 SPRT | r1 | 0.086 | 0.000 | 1374 | 1200 | 39 | 40 |
| 40 | r2 DE-CuSum best | r2(h=100) | 0.099 | 0.000 | 1357 | 1200 | 38 | 19 |
| 60 | obl max-min | burstcap(b=0,qs=1.0) | 0.179 | 0.115 | 1421 | 1153 | 55 | 56 |
| 60 | obl min-delay | fixed(q=1.0) | 0.196 | 0.000 | 1214 | 1200 | 56 | 60 |
| 60 | r1 SPRT | r1 | 0.196 | 0.012 | 1218 | 1196 | 56 | 59 |
| 60 | r2 DE-CuSum best | r2(h=30) | 0.206 | 0.000 | 1202 | 1200 | 56 | 51 |
| 80 | obl max-min | burstcap(b=0,qs=1.0) | 0.203 | 0.131 | 1423 | 1159 | 58 | 60 |
| 80 | obl min-delay | fixed(q=0.5) | 0.372 | 0.000 | 983 | 1200 | 71 | 80 |
| 80 | r1 SPRT | r1 | 0.348 | 0.033 | 1009 | 1195 | 70 | 68 |
| 80 | r2 DE-CuSum best | r2(h=100) | 0.350 | 0.003 | 1011 | 1200 | 68 | 22 |
| 120 | obl max-min | burstcap(b=0,qs=1.0) | 0.199 | 0.139 | 1416 | 1153 | 57 | 59 |
| 120 | obl min-delay | fixed(q=1.0) | 0.760 | 0.000 | 419 | 1200 | 89 | 120 |
| 120 | r1 SPRT | r1 | 0.667 | 0.038 | 568 | 1191 | 82 | 68 |
| 120 | r2 DE-CuSum best | r2(h=100) | 0.702 | 0.006 | 550 | 1199 | 84 | 22 |

#### variant B_disagree_only, d=20, alpha=0.05

| B | choice  rule | P_H | P_N | delay_H | delay_N | labels_H | labels_N |
|---|---|---|---|---|---|---|---|---|
| 40 | obl max-min | burstcap(b=0,qs=1.0) | 0.449 | 0.334 | 1140 | 955 | 31 | 35 |
| 40 | obl min-delay | fixed(q=0.25) | 0.493 | 0.000 | 815 | 1200 | 32 | 40 |
| 40 | r1 SPRT | r1 | 0.454 | 0.000 | 843 | 1200 | 32 | 40 |
| 40 | r2 DE-CuSum best | r2(h=10) | 0.458 | 0.000 | 832 | 1200 | 32 | 40 |
| 60 | obl max-min | burstcap(b=0,qs=1.0) | 0.696 | 0.621 | 1084 | 893 | 39 | 44 |
| 60 | obl min-delay | burstcap(b=60,qs=0.25) | 0.768 | 0.000 | 389 | 1200 | 39 | 60 |
| 60 | r1 SPRT | r1 | 0.774 | 0.004 | 426 | 1197 | 39 | 60 |
| 60 | r2 DE-CuSum best | r2(h=30) | 0.760 | 0.000 | 400 | 1200 | 39 | 44 |
| 80 | obl max-min | burstcap(b=0,qs=1.0) | 0.751 | 0.662 | 1057 | 873 | 39 | 45 |
| 80 | obl min-delay | fixed(q=1.0) | 0.858 | 0.000 | 262 | 1200 | 44 | 80 |
| 80 | r1 SPRT | r1 | 0.853 | 0.054 | 353 | 1182 | 44 | 79 |
| 80 | r2 DE-CuSum best | r2(h=100) | 0.855 | 0.003 | 268 | 1200 | 44 | 29 |
| 120 | obl max-min | burstcap(b=0,qs=1.0) | 0.725 | 0.633 | 1074 | 897 | 40 | 46 |
| 120 | obl min-delay | burstcap(b=120,qs=0.5) | 0.986 | 0.001 | 83 | 1199 | 44 | 120 |
| 120 | r1 SPRT | r1 | 0.957 | 0.090 | 232 | 1182 | 44 | 88 |
| 120 | r2 DE-CuSum best | r2(h=30) | 0.988 | 0.006 | 82 | 1199 | 44 | 50 |

#### variant B_disagree_only, d=20, alpha=0.001

| B | choice  rule | P_H | P_N | delay_H | delay_N | labels_H | labels_N |
|---|---|---|---|---|---|---|---|---|
| 40 | obl max-min | burstcap(b=0,qs=1.0) | 0.085 | 0.046 | 1447 | 1172 | 39 | 40 |
| 40 | obl min-delay | burstcap(b=40,qs=0.5) | 0.085 | 0.000 | 1377 | 1200 | 39 | 40 |
| 40 | r1 SPRT | r1 | 0.084 | 0.000 | 1378 | 1200 | 39 | 40 |
| 40 | r2 DE-CuSum best | r2(h=3) | 0.085 | 0.000 | 1377 | 1200 | 39 | 40 |
| 60 | obl max-min | burstcap(b=0,qs=1.0) | 0.161 | 0.109 | 1435 | 1164 | 55 | 56 |
| 60 | obl min-delay | fixed(q=1.0) | 0.198 | 0.000 | 1215 | 1200 | 57 | 60 |
| 60 | r1 SPRT | r1 | 0.196 | 0.000 | 1218 | 1200 | 57 | 60 |
| 60 | r2 DE-CuSum best | r2(h=3) | 0.198 | 0.000 | 1215 | 1200 | 57 | 60 |
| 80 | obl max-min | burstcap(b=0,qs=1.0) | 0.196 | 0.124 | 1430 | 1161 | 58 | 60 |
| 80 | obl min-delay | fixed(q=1.0) | 0.327 | 0.000 | 1034 | 1200 | 72 | 80 |
| 80 | r1 SPRT | r1 | 0.326 | 0.001 | 1051 | 1200 | 72 | 79 |
| 80 | r2 DE-CuSum best | r2(h=30) | 0.328 | 0.000 | 1033 | 1200 | 72 | 48 |
| 120 | obl max-min | burstcap(b=0,qs=1.0) | 0.181 | 0.123 | 1427 | 1157 | 58 | 59 |
| 120 | obl min-delay | burstcap(b=120,qs=0.25) | 0.770 | 0.000 | 421 | 1200 | 88 | 120 |
| 120 | r1 SPRT | r1 | 0.698 | 0.003 | 557 | 1200 | 86 | 89 |
| 120 | r2 DE-CuSum best | r2(h=3) | 0.769 | 0.000 | 423 | 1200 | 89 | 120 |

#### variant B2_disagree_only_rho0.2, d=0, alpha=0.05

| B | choice  rule | P_H | P_N | delay_H | delay_N | labels_H | labels_N |
|---|---|---|---|---|---|---|---|---|
| 40 | obl max-min | burstcap(b=0,qs=0.25) | 0.488 | 0.456 | 1137 | 868 | 32 | 33 |
| 40 | obl min-delay | burstcap(b=0,qs=0.5) | 0.465 | 0.402 | 1047 | 815 | 32 | 34 |
| 40 | r1 SPRT | r1 | 0.472 | 0.046 | 807 | 1151 | 32 | 40 |
| 40 | r2 DE-CuSum best | r2(h=100) | 0.470 | 0.044 | 820 | 1164 | 31 | 36 |
| 60 | obl max-min | burstcap(b=0,qs=0.5) | 0.755 | 0.703 | 841 | 604 | 39 | 42 |
| 60 | obl min-delay | burstcap(b=0,qs=1.0) | 0.734 | 0.643 | 737 | 545 | 40 | 45 |
| 60 | r1 SPRT | r1 | 0.720 | 0.332 | 468 | 871 | 40 | 56 |
| 60 | r2 DE-CuSum best | r2(h=100) | 0.754 | 0.264 | 436 | 1029 | 39 | 50 |
| 80 | obl max-min | burstcap(b=0,qs=0.5) | 0.869 | 0.849 | 788 | 533 | 44 | 47 |
| 80 | obl min-delay | burstcap(b=0,qs=1.0) | 0.897 | 0.833 | 591 | 379 | 42 | 49 |
| 80 | r1 SPRT | r1 | 0.878 | 0.606 | 267 | 628 | 42 | 67 |
| 80 | r2 DE-CuSum best | r2(h=100) | 0.896 | 0.417 | 256 | 942 | 41 | 59 |
| 120 | obl max-min | burstcap(b=0,qs=0.5) | 0.973 | 0.967 | 759 | 500 | 45 | 49 |
| 120 | obl min-delay | burstcap(b=0,qs=1.0) | 0.971 | 0.961 | 550 | 294 | 47 | 54 |
| 120 | r1 SPRT | r1 | 0.969 | 0.906 | 185 | 414 | 46 | 77 |
| 120 | r2 DE-CuSum best | r2(h=100) | 0.966 | 0.652 | 172 | 843 | 45 | 67 |

#### variant B2_disagree_only_rho0.2, d=0, alpha=0.001

| B | choice  rule | P_H | P_N | delay_H | delay_N | labels_H | labels_N |
|---|---|---|---|---|---|---|---|---|
| 40 | obl max-min | burstcap(b=0,qs=0.25) | 0.089 | 0.071 | 1445 | 1157 | 39 | 39 |
| 40 | obl min-delay | burstcap(b=0,qs=0.5) | 0.082 | 0.062 | 1425 | 1144 | 39 | 39 |
| 40 | r1 SPRT | r1 | 0.069 | 0.001 | 1399 | 1199 | 39 | 40 |
| 40 | r2 DE-CuSum best | r2(h=10) | 0.069 | 0.000 | 1399 | 1200 | 39 | 40 |
| 60 | obl max-min | burstcap(b=0,qs=1.0) | 0.200 | 0.146 | 1302 | 1058 | 56 | 58 |
| 60 | obl min-delay | burstcap(b=0,qs=1.0) | 0.200 | 0.146 | 1302 | 1058 | 56 | 58 |
| 60 | r1 SPRT | r1 | 0.196 | 0.018 | 1216 | 1183 | 57 | 60 |
| 60 | r2 DE-CuSum best | r2(h=100) | 0.193 | 0.012 | 1225 | 1193 | 56 | 53 |
| 80 | obl max-min | burstcap(b=0,qs=0.5) | 0.396 | 0.340 | 1253 | 993 | 71 | 73 |
| 80 | obl min-delay | burstcap(b=0,qs=1.0) | 0.381 | 0.307 | 1149 | 923 | 71 | 74 |
| 80 | r1 SPRT | r1 | 0.393 | 0.083 | 939 | 1127 | 70 | 79 |
| 80 | r2 DE-CuSum best | r2(h=100) | 0.379 | 0.054 | 967 | 1169 | 70 | 67 |
| 120 | obl max-min | burstcap(b=0,qs=1.0) | 0.751 | 0.697 | 903 | 661 | 90 | 95 |
| 120 | obl min-delay | burstcap(b=0,qs=1.0) | 0.751 | 0.697 | 903 | 661 | 90 | 95 |
| 120 | r1 SPRT | r1 | 0.743 | 0.468 | 499 | 851 | 90 | 109 |
| 120 | r2 DE-CuSum best | r2(h=100) | 0.737 | 0.303 | 505 | 1054 | 89 | 89 |

#### variant B2_disagree_only_rho0.2, d=20, alpha=0.05

| B | choice  rule | P_H | P_N | delay_H | delay_N | labels_H | labels_N |
|---|---|---|---|---|---|---|---|---|
| 40 | obl max-min | burstcap(b=0,qs=0.25) | 0.484 | 0.448 | 1151 | 885 | 32 | 33 |
| 40 | obl min-delay | burstcap(b=0,qs=0.5) | 0.491 | 0.426 | 1035 | 804 | 32 | 34 |
| 40 | r1 SPRT | r1 | 0.455 | 0.000 | 839 | 1200 | 32 | 40 |
| 40 | r2 DE-CuSum best | r2(h=3) | 0.464 | 0.000 | 823 | 1200 | 32 | 40 |
| 60 | obl max-min | burstcap(b=0,qs=0.5) | 0.719 | 0.669 | 882 | 642 | 40 | 43 |
| 60 | obl min-delay | burstcap(b=0,qs=1.0) | 0.742 | 0.646 | 744 | 559 | 40 | 46 |
| 60 | r1 SPRT | r1 | 0.732 | 0.008 | 462 | 1192 | 40 | 60 |
| 60 | r2 DE-CuSum best | r2(h=100) | 0.731 | 0.001 | 442 | 1199 | 40 | 32 |
| 80 | obl max-min | burstcap(b=0,qs=0.5) | 0.871 | 0.849 | 806 | 552 | 44 | 47 |
| 80 | obl min-delay | burstcap(b=0,qs=1.0) | 0.860 | 0.814 | 645 | 417 | 44 | 51 |
| 80 | r1 SPRT | r1 | 0.881 | 0.057 | 273 | 1146 | 44 | 80 |
| 80 | r2 DE-CuSum best | r2(h=100) | 0.882 | 0.015 | 229 | 1194 | 43 | 34 |
| 120 | obl max-min | burstcap(b=0,qs=1.0) | 0.979 | 0.970 | 556 | 309 | 45 | 54 |
| 120 | obl min-delay | burstcap(b=0,qs=1.0) | 0.979 | 0.970 | 556 | 309 | 45 | 54 |
| 120 | r1 SPRT | r1 | 0.979 | 0.395 | 164 | 880 | 45 | 112 |
| 120 | r2 DE-CuSum best | r2(h=30) | 0.977 | 0.163 | 99 | 1117 | 46 | 101 |

#### variant B2_disagree_only_rho0.2, d=20, alpha=0.001

| B | choice  rule | P_H | P_N | delay_H | delay_N | labels_H | labels_N |
|---|---|---|---|---|---|---|---|---|
| 40 | obl max-min | burstcap(b=0,qs=0.25) | 0.075 | 0.065 | 1456 | 1162 | 39 | 39 |
| 40 | obl min-delay | burstcap(b=0,qs=1.0) | 0.085 | 0.048 | 1412 | 1151 | 39 | 40 |
| 40 | r1 SPRT | r1 | 0.069 | 0.000 | 1400 | 1200 | 39 | 40 |
| 40 | r2 DE-CuSum best | r2(h=3) | 0.072 | 0.000 | 1396 | 1200 | 39 | 40 |
| 60 | obl max-min | burstcap(b=0,qs=0.5) | 0.173 | 0.145 | 1370 | 1092 | 57 | 58 |
| 60 | obl min-delay | burstcap(b=0,qs=1.0) | 0.195 | 0.135 | 1313 | 1072 | 57 | 58 |
| 60 | r1 SPRT | r1 | 0.197 | 0.000 | 1218 | 1200 | 57 | 60 |
| 60 | r2 DE-CuSum best | r2(h=10) | 0.206 | 0.000 | 1204 | 1200 | 56 | 60 |
| 80 | obl max-min | burstcap(b=0,qs=0.5) | 0.385 | 0.351 | 1268 | 995 | 71 | 73 |
| 80 | obl min-delay | burstcap(b=0,qs=1.0) | 0.374 | 0.300 | 1165 | 936 | 71 | 74 |
| 80 | r1 SPRT | r1 | 0.357 | 0.001 | 998 | 1199 | 72 | 80 |
| 80 | r2 DE-CuSum best | r2(h=30) | 0.357 | 0.000 | 992 | 1200 | 72 | 74 |
| 120 | obl max-min | burstcap(b=0,qs=1.0) | 0.776 | 0.715 | 898 | 663 | 89 | 94 |
| 120 | obl min-delay | burstcap(b=0,qs=1.0) | 0.776 | 0.715 | 898 | 663 | 89 | 94 |
| 120 | r1 SPRT | r1 | 0.774 | 0.045 | 471 | 1166 | 88 | 119 |
| 120 | r2 DE-CuSum best | r2(h=30) | 0.753 | 0.014 | 446 | 1193 | 89 | 103 |

### Summary: best oblivious versus responsive (min over {H,N} of P(detect), and mean of H/N delay)

Selected rows from the grid (variant B2, d=0; the full set is in the tables above and CSV).

| alpha | B | obl max-min P | r1 min P | r2 best min P | obl best avg delay | r1 avg delay |
|---|---|---|---|---|---|---|
| 0.05 | 60 | 0.703 | 0.332 | 0.264 | 641 | 669 |
| 0.05 | 80 | 0.849 | 0.606 | 0.417 | 485 | 447 |
| 0.05 | 120 | 0.967 | 0.906 | 0.652 | 422 | 299 |
| 0.001 | 80 | 0.340 | 0.083 | 0.054 | 1036 | 1033 |
| 0.001 | 120 | 0.697 | 0.468 | 0.303 | 782 | 675 |

With d=20 the responsive rules collapse further (B2, alpha=0.05, B=120: r1 min P 0.395, r2 0.163,
oblivious 0.970; r1 avg delay 522 against 432).

## Null control

Mean = eps everywhere, 1000 seeds per (cell, rule): no rule breaches alpha (largest observed rate
0.029 at alpha=0.05; at most 2/1000 at alpha=0.001; mean rates 0.010 and 0.00013). Largest exact
one-sided 95% Clopper-Pearson upper bound 0.039 at alpha=0.05 (below 0.05). At alpha=0.001 and
n=1000 the exact bound cannot go below 0.003, so validity at 0.001 is supported (observed
rates far below alpha) but not certified by this run. Validity is by construction (predictable q,
nonnegative factors); the run is a sanity check. Variant A is also valid but uninformative.

## Honest reading

1. **The predicted separation does not appear.** In every informative cell (variants B and B2,
   both d, both alpha) the best oblivious rule's min-over-{H,N} detection probability is at least as
   large as that of r1 and r2, usually by a wide margin (B2, alpha 0.05, B=80: 0.85 versus 0.61 and
   0.42). The best oblivious rule is "ignore the burst" (b=0, q_sparse near 1), which detects in the
   sparse phase in both instances. It is oblivious (it only uses the D run length), and it nearly
   attains the oracle for N. It is not a failure of Claim 1's counting argument, but it breaks the
   conjecture's premise that an oblivious rule must trade P_H(burst) against P_N(by T): here the
   sparse phase alone is enough for H as well (only delay, not detection, is lost in H).
2. **Where responsive rules do help: delay only, and modestly.** At B2, d=0, alpha=0.05 r1 cuts the
   average H/N delay by 8% (B=80) and 29% (B=120); at alpha=0.001, B=120 by 14%. This is bought with
   a lower P_N (0.906 versus 0.967; 0.468 versus 0.697) and vanishes at tight budgets (B<=60) or with
   delay d=20. This is not the claimed "oblivious fails one instance, responsive succeeds in both".
3. **Why Claim 2 fails numerically (mechanisms, from the logs).**
   - The SPRT stop is a constant-confidence decision. By SPRT drift arithmetic (not measured separately) N still costs about 6-10 burst labels
     before stopping, and under H a wrong stop has probability up to roughly 0.25. A wrong stop
     in H forfeits the burst for good, so P_H falls too.
   - The shared e-process carries a wealth debt. N-burst labels have negative drift, so
     they cost wealth as well as budget. An oracle-restart diagnostic (N rows only, wealth zeroed at s+L;
     `..._restart_diag.csv`; not a valid monitor) lifts r1's P_N to about the
     oblivious b=0 level (B2 alpha=0.05, B=120: 0.964 versus 0.973) but never above it.
     So in a no-restart e-process, the cost of burst evidence is not "m_delta labels" but a debt of
     about log-wealth that takes more labels to repay. Claim 2's accounting `B >= K_alpha + m_delta`
     omits this. It points at Lane A's all-onset e-detector mixture as the right engine for a
     responsive rule, and that is a different baseline to compare against.
   - Delay: pending labels are charged at request, so with d=20 the responsive rule overspends up to
     d labels on a burst it would have stopped (labels_N 112 against 54 for B2 d=20 alpha 0.05 B=120).
   - r2 (DE-CuSum on-off): a wait of 1/h per skipped disagreement is large against only 60-240 sparse
     opportunities, so it under-samples the harmful sparse phase (P_N 0.04 at B=120, rho=0.05).
     DE-CuSum is built for long streams and an average duty-cycle constraint. It is not natural for a
     hard cap with a rare-event stream. Even the best h in the grid does not rescue it.
4. **Regime caveats.** At alpha=0.001 the tight-budget regime (K<=B<2K) is empty at rho=0.05
   (K_sparse exceeds the 60 available events). In B2 at alpha=0.001, B in {40,60} nobody detects, so a
   scale-with-alpha statement is weak. As alpha falls from 0.05 to 0.001 the responsive rules'
   deficit in min P grows in relative terms (B2, B=120: 0.906/0.967 to 0.468/0.697), the opposite
   of the conjectured gap growing in favour of the responsive rule.
5. **Variant A** (literal brief) is degenerate: agreement drag makes detection essentially impossible.
   If the real platform scores agreements as -eps events in the e-process, the sparse-bust instance
   should not be used at rho this small.

**Assessment for B1.** The numerical check does not support the conjectured separation in this
family: the best oblivious rule is near-oracle in detection probability in both instances, which
under the lane's own exit rule (an oblivious rule near-oracle in both classes) points to
**stop or pivot, not continue**, unless the instance is changed so that the post-burst phase cannot
carry H, for example a bounded post-burst horizon, or a harmful phase that ends, or costly late
detection, so that burst evidence is the only source of value in H. Nothing here tests that regime.
The only surviving signal is a modest delay gain for an SPRT-stop rule at d=0 and generous B. Suggested
follow-ups, each beyond this brief: (i) repeat with an all-onset e-detector mixture
to remove the wealth debt; (ii) an instance with a short post-burst harmful window; (iii) a
delay-adjusted stopping rule with a reserve for the d pending labels.
