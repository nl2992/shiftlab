# P2-NAD frozen confirmation: registration

**Status:** registered before any confirmation run. The registration commit freezes
`scripts/p2/nad.py`, `scripts/p2/comparators.py`, `scripts/sota_sprint/wp2_run.py`, the
analysis scripts `scripts/p2/paired.py` and `scripts/p2/real_table.py`, and this file.
Results are appended below the line "RESULTS" after the single opening. The arms, panel,
cohorts and rules do not change after opening.

## Frozen arms

- **A (primary): `NAD2S-g10-f6`.**
  - An envelope e-process with ρ̄ = .8 runs on a sign-independent flagged subsequence: the first
    disagreement at least 10 events after the previous flagged issue, with 60% of the budget
    reserved.
  - A5b's unbounded-ρ universal-inference e-process runs on all outcomes, with A5b's density.
  - Bonferroni split α/2 + α/4.
  - Claimed class: M(.8), a stationary Markov sign with persistence ≤ .8.
- **B (secondary, economic-validity arm): `PB80-g10`.**
  - Envelope ρ̄ = .8, gap 10, payback hurdle h(τ) = (c_s + κ)/(2·dis·(T−τ)).
  - Claimed: P(promotion with p ≤ 1/2 + h(τ)) ≤ α under M(.8).
- **Descriptive:** `NAD-m80-g10`.

The selection history is in docs 02–04. Development used seed bases 2026110901, 2026110911 and
2026110921, plus the 14 exposed real streams.

## Panel (20 policies)

- Arms: A, B, `NAD-m80-g10`.
- Dependence-robust comparators: `A5b`, `D5` (V2), `QSG-env8`.
- Published-certificate ports:
  - author-endpoint MOPE: `gated_deployment_native`, `gated_adaptive_range_native`, `gated_adaptive_range_native+front`;
  - quad-endpoint MOPE: `gated_adaptive_range`;
  - `discern_style`, `discern_design_floor`, `SMCS+retain-incumbent`, `choe_ramdas_eb+front`.
- Other: `QSG`, `D2`, `economic_replacement`, `cams_adapter`, `model_picker_adapter`, `CONTROL_never_switch`.

## Cohorts (fresh)

| Cohort | Construction | Size | Seed base |
|---|---|---|---|
| S-null | F0_null, F5_dep_null_r8, F5_dep_null_r95, O_null_semimarkov, O_null_order2, WP2_o2_null, WP2_sm_null, WP2_hs_null | 500 seeds each | 2026110951 |
| S-alt | F0_better, F5_dep_better_r8, S_dep_better_r95, WP2_o2_better, WP2_sm_better, WP2_hs_better | 200 seeds each | 2026110951 |
| C4 | 27 chronological replacement streams, 2,097 episodes (`06_REAL_DATA.md`); never run in P2 | 3 policy seeds per episode | 2026110952 |
| Twin | `data/sprint_twin_losses` v1, five UCI datasets, exact marginal nulls | 5 policy seeds per episode | 2026110953 |

Contract: T = 2000, B = 200, c_q = .05, c_s = 5, α = .05. Delays: synthetic 100, C4 100 (from the
npz), twins as registered per dataset.

## Hypotheses and rules

Paired differences are bootstrapped by seed (synthetic, stratified by regime) or by
(source, episode) cluster (C4, source-equal weights). Directional tests use **99%** percentile
intervals (4,000 draws).

| ID | Claim | Rule |
|---|---|---|
| H1 | A is cheaper than A5b on synthetic alternatives | 99% UB of J(A) − J(A5b) < 0 |
| H2 | A is cheaper than A5b on C4 real streams | 99% UB of J(A) − J(A5b) < 0 (source-equal) |
| H3 | A is cheaper than D5 on both cohorts | 99% UB < 0 on S-alt **and** on C4 |
| H4 | A keeps level α in its claimed class | Promotion rate ≤ .0695 (= .05 + 2√(.05·.95/500)) on F0_null and F5_dep_null_r8 |
| H5 | A passes Tier B on every synthetic null | 95% UB of mean decision harm ≤ 5 on all 8 S-null regimes |
| H6 | B has negligible decision harm | 95% UB of mean decision harm ≤ 1 on all 8 S-null regimes |
| H7 | B is cheaper than A5b on synthetic alternatives | 99% UB of J(B) − J(A5b) < 0 |

**Reported without a pass/fail rule (frontier):**

- J(A) − J(c) with 95% CIs on S-alt and C4, for every panel member c.
- Promotion rate and decision harm of every policy on every null, and twin promotion rates per
  dataset.
- C4 per-source win counts.
- The robustness value is recorded by NAD-m80-g10 only.

**Expected (from development, not a rule):**

- A is cheaper than A5b, D5 and env8.
- A costs more than native adaptive-range MOPE and the V1 front-loaders, which promote on 15–70%
  of persistent nulls.
- A may tie native gated_deployment.

## RESULTS

(appended after the single opening)
