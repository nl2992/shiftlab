# C_ATLAS_PROTOCOL: mechanistic dependence-aware failure atlas (workstream C)

Registered 2026-11-09 before the dev pilot results were read (code at base `8af33afe` plus uncommitted workstream
files; the exact SHA of each run is in `ledger/atlas.jsonl`). Everything here is **dev / exploratory**. No
confirmatory claim. Real c4 streams are all exposed (Papers 1/2) and are labelled exploratory.

## 1. Stream model (evaluator-side truth never reaches a policy)
T=2000. At each event the two frozen models disagree w.p. `dis`; on a disagreement the challenger is right
(D=l0-l1=+1) w.p. `p_t`, else the incumbent (D=-1); agreement gives D=0 (10% both-wrong). The sign process is a
two-state chain: keep the previous sign w.p. `rho` per event, else redraw Bernoulli(`p_t`) (so g-step persistence is
exactly `rho^g`; same generator family as `scripts/failure_atlas_v2/regimes.py`).
Alt stream: `p=.5` before `onset` (boundary null), `p=.5+Delta` for `dwell` events, then `p=.35` (a stale promotion is
harmful). Null twin: `p=.5` throughout (same cell parameters, independent stream). The label of a query at t is released at
`t+delay` (equal) or `t+4*delay` when D=+1 (**informative**: favourable outcomes arrive late; rule hidden from policies).
Cost: `J = sum loss + c_q * queries + k * switches`; hard pathwise budget `B = round(B/T * T)`; pending queries are
deducted at request time.

## 2. Space-filling design (32 cells)
Scrambled Sobol (scipy, seed 20261109) over 7 axes: onset in [200,1200], dwell fraction (top quartile of the unit
interval = persists to T; else 15-100% of the remaining horizon, min 100), Delta in [.10,.30], label delay in [10,200],
budget fraction in [.05,.25], query tariff c_q in [.01,.20], switch cost k in [1,20], disagreement rate in [.10,.50]
(a deterministic mix of Sobol coordinates). `rho in {0,.5,.8,.95}` cycles with the cell index and delay type
(equal/informative) alternates every 4 cells, so both are balanced (8 cells per rho, 16 per delay type).

| cell | onset | dwell | Delta | rho | delay | delay type | B/T | c_q | k | dis | gated/DISCERN/SMCS null | C1 (rho_max .95) null |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 923 | 739 | 0.23 | 0.0 | 185 | equal | 0.16 | 0.182 | 9.9 | 0.18 | valid-null | valid-null |
| 1 | 351 | 843 | 0.14 | 0.5 | 50 | equal | 0.08 | 0.067 | 11.1 | 0.41 | INVALID-null | valid-null |
| 2 | 654 | persist | 0.29 | 0.8 | 136 | equal | 0.11 | 0.020 | 1.0 | 0.27 | INVALID-null | valid-null |
| 3 | 1120 | 261 | 0.19 | 0.95 | 97 | equal | 0.23 | 0.134 | 20.0 | 0.17 | INVALID-null | valid-null |
| 4 | 1059 | persist | 0.11 | 0.0 | 71 | informative | 0.20 | 0.173 | 3.5 | 0.22 | valid-null | valid-null |
| 5 | 464 | 358 | 0.21 | 0.5 | 114 | informative | 0.14 | 0.094 | 17.5 | 0.37 | INVALID-null | valid-null |
| 6 | 267 | 1116 | 0.16 | 0.8 | 24 | informative | 0.06 | 0.047 | 7.6 | 0.39 | INVALID-null | valid-null |
| 7 | 757 | 555 | 0.27 | 0.95 | 163 | informative | 0.19 | 0.124 | 13.4 | 0.35 | INVALID-null | valid-null |
| 8 | 776 | persist | 0.16 | 0.0 | 118 | equal | 0.10 | 0.145 | 5.0 | 0.11 | valid-null | valid-null |
| 9 | 248 | 597 | 0.26 | 0.5 | 67 | equal | 0.16 | 0.032 | 16.0 | 0.22 | INVALID-null | valid-null |
| 10 | 570 | 1071 | 0.12 | 0.8 | 167 | equal | 0.25 | 0.079 | 6.8 | 0.23 | INVALID-null | valid-null |
| 11 | 954 | 580 | 0.21 | 0.95 | 21 | equal | 0.11 | 0.193 | 14.2 | 0.38 | INVALID-null | valid-null |
| 12 | 1163 | 486 | 0.29 | 0.0 | 42 | informative | 0.13 | 0.113 | 9.1 | 0.33 | valid-null | valid-null |
| 13 | 611 | 561 | 0.18 | 0.5 | 193 | informative | 0.22 | 0.035 | 11.9 | 0.12 | INVALID-null | valid-null |
| 14 | 433 | persist | 0.24 | 0.8 | 88 | informative | 0.19 | 0.082 | 2.6 | 0.10 | INVALID-null | valid-null |
| 15 | 840 | 220 | 0.14 | 0.95 | 144 | informative | 0.07 | 0.161 | 18.4 | 0.47 | INVALID-null | valid-null |
| 16 | 867 | persist | 0.26 | 0.0 | 29 | equal | 0.23 | 0.043 | 11.7 | 0.18 | valid-null | valid-null |
| 17 | 407 | 241 | 0.15 | 0.5 | 156 | equal | 0.12 | 0.105 | 9.3 | 0.48 | INVALID-null | valid-null |
| 18 | 604 | 865 | 0.22 | 0.8 | 78 | equal | 0.08 | 0.154 | 19.4 | 0.14 | INVALID-null | valid-null |
| 19 | 1169 | 303 | 0.12 | 0.95 | 110 | equal | 0.17 | 0.089 | 1.6 | 0.40 | INVALID-null | valid-null |
| 20 | 1012 | 754 | 0.18 | 0.0 | 131 | informative | 0.20 | 0.028 | 17.0 | 0.48 | valid-null | valid-null |
| 21 | 513 | 803 | 0.28 | 0.5 | 104 | informative | 0.06 | 0.150 | 4.0 | 0.45 | INVALID-null | valid-null |
| 22 | 209 | persist | 0.15 | 0.8 | 178 | informative | 0.15 | 0.198 | 14.0 | 0.45 | INVALID-null | valid-null |
| 23 | 814 | 386 | 0.24 | 0.95 | 55 | informative | 0.21 | 0.074 | 7.0 | 0.19 | INVALID-null | valid-null |
| 24 | 701 | 852 | 0.13 | 0.0 | 84 | equal | 0.10 | 0.101 | 15.4 | 0.46 | valid-null | valid-null |
| 25 | 323 | 729 | 0.23 | 0.5 | 152 | equal | 0.24 | 0.165 | 5.6 | 0.21 | INVALID-null | valid-null |
| 26 | 501 | persist | 0.19 | 0.8 | 35 | equal | 0.15 | 0.117 | 14.8 | 0.35 | INVALID-null | valid-null |
| 27 | 1023 | 216 | 0.30 | 0.95 | 197 | equal | 0.09 | 0.054 | 6.2 | 0.16 | INVALID-null | valid-null |
| 28 | 1095 | persist | 0.20 | 0.0 | 171 | informative | 0.07 | 0.063 | 12.5 | 0.20 | valid-null | valid-null |
| 29 | 678 | 339 | 0.11 | 0.5 | 14 | informative | 0.18 | 0.186 | 8.5 | 0.32 | INVALID-null | valid-null |
| 30 | 356 | 1195 | 0.27 | 0.8 | 126 | informative | 0.22 | 0.138 | 17.9 | 0.13 | INVALID-null | valid-null |
| 31 | 918 | 509 | 0.17 | 0.95 | 62 | informative | 0.13 | 0.016 | 3.1 | 0.15 | INVALID-null | valid-null |

## 3. Seeds
Dev: seed indices 0-29 per cell under seed base **7,300,000** (stream seed = SeedSequence[7300000, seed, cell, null]).
Distinct from every range named in prior atlas docs (0-19, 3000-3099, 5000-5099, 170000-170019, 181000-181039,
250000-250019, 290000-290199, bases 20261103/4). Real c4: seed base 7,500,000. Reserved, unused: 7,400,000 (model
selection), 7,600,000 (confirmation). All methods see the same realised stream and delays (paired).

## 4. Methods (fixed registered defaults, ZERO tuning; alpha=.05; shared paced disagreement acquisition unless stated)
| method | label | notes |
|---|---|---|
| never_switch | control | pays no fees |
| gated_mope | DOCUMENTED_ADAPTER (Karampatziakis+21 MOPE CS, ported from main), one-shot | verdict stops acquisition |
| discern_fixed | DOCUMENTED_ADAPTER, psi_E fixed | see C_FIDELITY_AUDIT |
| smcs_retain | DOCUMENTED_ADAPTER (SMCS + retain-incumbent; port of the author-R-validated code) | no rollback |
| cusum (h=4), cusum_cal (h=log(B/alpha)) | IN_HOUSE_HEURISTIC | Bernoulli LLR p1=.65, mirrored rollback |
| page_hinkley (delta .1, lam 6) | IN_HOUSE_HEURISTIC | mirrored rollback |
| edetector (thr 1/alpha), edetector_cal (thr B/alpha) | IN_HOUSE (Shiryaev-Roberts mixture over starts and bets .15/.3/.5) | mirrored rollback |
| wald_econ | IN_HOUSE_HEURISTIC | SPRT .5 vs .65; promote only if estimated payback > k; reverse-SPRT rollback |
| iid_gate / thinned_iid (gap 10) / markov_skeleton | DOCUMENTED_ADAPTER | betting gates, shared down e-detector rollback, alpha spending alpha/2^j over <=4 restarts |
| **c1_gapaware** | candidate repair C1 | rho_max=.95 declared ex ante, never read from the cell |
| c1_gapaware_rho80 | C1 stress | declared bound .80 (misdeclared when rho=.95) |
| c3_spaced_iid, **c1c3** | candidate repair C3 (+C1) | spacing acquisition g_min=min(ceil(ln .25/ln rho_max), .7T/B), pending cap ceil(d/g_min)+1 |

Deployer-visible inputs: T, B, c_q, k, alpha, delay, declared rho_max. Not visible: rho, onset, Delta, regime.
No method was tuned on atlas data (equal, zero tuning budget); this is a limitation, not a fairness proof. Methods lacking
a rollback in their source (Gated, DISCERN, SMCS) are run as published (one-shot / no rollback).

## 5. Null-assumption status per gate and cell class
(`shiftlab.paper3.atlas.cells.validity`; statements about assumptions, not proofs. **Invalid-null cells are stress tests, not
validity claims.**)
* gated_mope / discern / smcs: conditional-mean null `E[d_t|F_{t-1}]<=0`. rho=0: valid. rho>0: **invalid** (the conditional
  mean given the past is nonzero even when the marginal is at the boundary). Informative delay alone is not invalidating
  because labels are consumed in query order (supremum argument).
* cusum/page_hinkley/edetector/wald_econ: iid ARL / SPRT error rates only; no anytime guarantee in any cell; the
  "calibrated" variants use a union-over-labels threshold valid only for iid.
* thinned_iid: valid only if rho^gap is negligible (rho=0); invalid for rho>0.
* markov_skeleton: Markov bound with one homogeneous nominal gap T/B; approximate when actual gaps differ.
* C1: valid when true rho <= declared rho_max. **Sketch (not a proof):** let x_k be the sign at the k-th used query and g_k
  the event-time gap to the previous used query. For the stated chain with marginal `pi<=1/2`,
  `P(x_k=1|x_{k-1}=1,g) = rho^g + (1-rho^g) pi <= (1+rho^g)/2 <= (1+rho_max^g)/2` and
  `P(x_k=1|x_{k-1}=0,g) = (1-rho^g) pi <= 1/2`. With `m_k` that bound and a bet `lam_k in [0, .9/m_k]` predictable w.r.t.
  earlier used signs, `E_k = prod (1 + lam (x - m))` is a nonnegative supermartingale in query order, so Ville gives
  `P(sup_k E_k >= 1/alpha) <= alpha`; the real-time decision index is a random index of that sequence, so
  `E_{k(tau)} <= sup_k E_k` for any delay. Assumptions NOT proven here: query times depend on the history only through
  released labels and independent randomisation (true in the code); the delay of a query depends only on its own outcome;
  restarts spend alpha/2^j; the rollback detector (iid e-detector) is not covered. Violated when rho > rho_max.

## 6. Metrics (per episode, paired, accounting identity asserted)
Alarm: null false promotion (`null_fp`: any promotion in the null twin), pre-onset false alarm, EDD (first deployment inside
the good window minus onset, censored at window length), missed detection. Economic: `J` and, with D realised and regimes
good/neutral/bad from the schedule,
`J = L0 - sum_good D + fees + intervention + harm_bad + noise_neutral + forgone_good`; `forgone_good` splits into
certification lag (before the first deployment in the first good window) and re-miss. The identity and the budget are
asserted per episode (1e-6).

## 7. Registered analyses
Inversion: per cell, Kendall tau between each alarm ranking (EDD, null FA, composite of EDD/FA/missed ranks) and the J
ranking over the 12 non-control, non-repair methods (sensitivity: add never_switch). Pairwise inversion: X alarm-dominates Y
(EDD_X<EDD_Y and FA_X<=FA_Y) but J_X>J_Y; frequency over dominated pairs, magnitude in J units. CIs: seed-cluster bootstrap
(resample the 30 seed indices jointly across cells and methods, 300 reps). Axis drivers: Spearman and standardised OLS of the
per-cell inversion rate on the 10 axes (n=32 cells, low power, descriptive). Repairs: paired J differences against
markov_skeleton, thinned_iid, gated_mope, iid_gate, wald_econ, cusum_cal and never_switch, seed-cluster bootstrap over
equal-weighted cells. Effect grading per the project standard. Real c4: 30 episodes per stream, B=200, c_q=.05, k=5; no
causal truth, so EDD proxy = first promotion in episodes with realised sum D >= 20 and FA proxy = promotion in episodes with
sum D <= -20 (ex post, evaluator-side); streams need >=3 episodes of each kind.
