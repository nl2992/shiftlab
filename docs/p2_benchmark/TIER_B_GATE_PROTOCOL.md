# P2 Tier B validity gate: registration (H8, 2026-11-07)

**Result (2026-11-07):** H8c supported; H8b not supported (SMCS); Tier B admits 12 of 16 and rejects 4. See [results/TIER_B_RESULTS.md](results/TIER_B_RESULTS.md).

**Status:** registered before any H8 cohort exists. The fresh synthetic seeds and twin v4 splits
(160–279) below have not been built or run. The registration record is the commit adding this file
together with `scripts/p2_benchmark/analyze_tier_b.py` and `scripts/p2_benchmark/build_twin_v4.py`.

## Why

The W4 confirmatory run ([results](results/CONFIRMATORY_RESULTS.md)) showed that the
single all-null gate admits only `discern_style`, the costliest certified policy. The Amendment 1
"two-tier" gate checked only Tier A and admitted all 16 certified policies. Finding F8, that the
validity gate reorders the leaderboard, therefore needs a gate that can reject something. This file
registers Tier B as an economic gate and tests whether the full two-tier gate discriminates and
admits a materially cheaper policy than the all-null gate.

## Gate definitions (frozen)

Panel: the 16 certified policies in W4 H7, plus `CONTROL_never_switch` as the reference.
`A5b`, `D2`, `D5`, `QSG`, `SMCS+retain-incumbent`, `choe_ramdas_eb`, `choe_ramdas_eb+front`,
`discern_design_floor`, `discern_style`, `gated_adaptive_range`, `gated_adaptive_range+front`,
`gated_deployment`, `gated_deployment+QCE`, `gated_deployment+QCE+front`, `rmm:gated_deployment+RMM`,
`xu_acquisition_only`. Claim classes are read from `bench2.NULL_TESTED`: A5b and D5 claim V2,
and the rest claim V1.

**Decision harm.** For one episode, decision harm is `−db`, where `db = Σ l0 − Σ loss − c_s·switches`.
This is the policy's loss plus switch cost in excess of the frozen incumbent, which the charter
writes as `R_t(π_t) − R_t(π_ref)` with `π_ref` = never switch. Label spend is excluded from the gate.
It is a budgeted information cost that every budget-using policy pays (up to 10 per episode, which
alone exceeds the tolerance). It is reported separately and enters the leaderboard J.

1. **Tier A (claimed null).** Promotion rate ≤ `.05 + 2·sqrt(.05·.95/n)` on each claimed null, where
   n is the number of seeds (n = 500 gives .0695). Claimed nulls: F0_null for V1, and F0_null,
   F5_dep_null_r8 and F5_dep_null_r95 for V2.
2. **Tier B (dependent nulls outside the claim).** The Tier B nulls are every H8 null that the
   policy does not claim: the eight synthetic nulls below and the five twin v4 datasets. On each
   one, the upper end of the 95% stratified cluster-bootstrap interval (97.5% quantile, 4,000 draws)
   of mean decision harm must be ≤ **+5** (one switch cost).
3. **Two-tier gate:** passes 1 and 2. **Single gate** (unchanged from Amendment 1): promotion rate
   ≤ .0936 on every synthetic null and every twin v4 dataset.

## Cohort (fresh)

| Part | Construction | Size | Policy seed base |
|---|---|---|---|
| Synthetic nulls | F0_null, F5_dep_null_r8, F5_dep_null_r95, O_null_semimarkov, O_null_order2, WP2_o2_null, WP2_sm_null, WP2_hs_null | 500 seeds each | **2026110801** |
| Synthetic alternatives (leaderboard) | F0_better, F5_dep_better_r8, S_dep_better_r95, WP2_o2_better, WP2_sm_better, WP2_hs_better | 200 seeds each | **2026110801** |
| Twin v4 nulls | `twin_null` construction on new splits **160–279** of the five UCI sources | 120 splits per dataset | **2026110802** |

Contract: T = 2000, B = 200, c_q = .05, c_s = 5, α = .05, registered delays. The leaderboard metric
is mean J over the six alternatives, weighted equally by regime. The fresh real streams are
deterministic model fits that were already used in W4. They cannot be re-drawn, so real-data J is
reported only descriptively, from the W4 fresh run.

## Hypotheses and decision rules

Three directional tests (H8b-QSG, H8b-SMCS, H8c) use **99% intervals**, giving a family-wise level
of at most 3%.

| ID | Claim | Rule |
|---|---|---|
| H8a | Tier A alone does not discriminate (replication of W4 H7) | Descriptive: number of the 16 that pass Tier A |
| H8b | Tier A admits policies with positive decision harm under dependence | For **QSG** and **SMCS+retain-incumbent** separately: mean decision harm on F5_dep_null_r95 has a 99% lower bound > 0. Both must pass |
| H8c | The two-tier gate admits a materially cheaper policy than the single gate | For the named policy **P\* = `gated_adaptive_range`**: (i) it passes the two-tier gate, (ii) it fails the single gate, and (iii) the paired 99% upper bound of J(P\*) − J(S\*) on the alternatives is < **−5**. S\* is the lowest-J policy the single gate admits; if it admits none, S\* = `CONTROL_never_switch`. All three must hold |
| H8d | Prediction scorecard | Descriptive: observed vs predicted two-tier admitted set (below) |

Choosing S\* as the cheapest single-gate admittee on the same data favours S\*, so it works against
H8c. Clusters are seeds for synthetic data and (dataset, split) for twins. Paired J differences are
bootstrapped by seed, stratified by regime.

## Predictions from development (exposed W4 data)

A development Tier B pass on the W4 synthetic (200 seeds) and twin v3 runs was made before this
registration and is not evidence. It predicts:

- **Two-tier admits (6):** A5b, D5, discern_design_floor, discern_style, gated_adaptive_range,
  gated_deployment. **Rejected by Tier B (10):** D2, QSG, SMCS+retain-incumbent, choe_ramdas_eb,
  choe_ramdas_eb+front, gated_adaptive_range+front, gated_deployment+QCE,
  gated_deployment+QCE+front, rmm:gated_deployment+RMM, xu_acquisition_only. F5_dep_null_r95 is the
  binding null for most of them.
- **Fragile:** gated_adaptive_range's worst Tier B upper bound was 4.52 against the 5 tolerance
  (mean 2.12, 200 seeds). discern_design_floor's was 4.95. Either could be rejected on the fresh
  cohort, and H8c fails if gated_adaptive_range is.
- **Effect:** development J on the alternatives was 392.3 for gated_adaptive_range vs 429.3 for
  discern_style. QSG and SMCS showed decision harm of 8.4 and 7.5 on F5_dep_null_r95 (95% lower
  bounds 3.2 and 3.4).

## Execution order

1. Commit this file, the twin v4 builder and the analysis script (smoke-tested on development data only).
2. Build twin v4. The builder fails closed unless rebuilding split 40 reproduces the stored twin v3
   arrays exactly.
3. Run the panel on the three cohort parts, then the analysis. Record the results with deviations.

## Limitations

The synthetic regime parameters and the five UCI sources are exposed. The twin v4 splits are new
model fits, not unseen data. The +5 tolerance is a policy choice (one switch cost), not a derived
quantity. Excluding label spend from the gate means a policy can pass Tier B while paying the full
label budget. Empirical bounds are not guarantees.

## Amendment 1 (2026-11-07, before any H8 run)

`wp2_run.py` now recognises the `twin4_` prefix when it looks up a dataset's registered label delay.
This is the same one-line change made for `twin3_` in W4. No rule, cohort or threshold changes.
