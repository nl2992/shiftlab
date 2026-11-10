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

The cohorts were opened once on 2026-11-09/10. The code is at the registration commit (`1f78943a`); the
analysis script was committed before opening (`2f2427a5`). Full output:
[results/confirm.md](results/confirm.md). Records: `outputs/p2/confirm/{salt,c4,twin,snull}`
(24,000 / 125,820 / 124,000 / 80,000 rows; not in Git).

| ID | Result | Verdict |
|---|---|---|
| H1 | J(A) − J(A5b), S-alt: −11.31, 99% CI [−13.79, −8.84] (−2.9%) | **PASS** |
| H2 | J(A) − J(A5b), C4: +0.23 [−0.85, +1.30] (+0.1%) | **FAIL** (tie) |
| H3 | vs D5: S-alt −12.17 [−14.84, −9.48] PASS; C4 +0.14 [−1.22, +1.70] FAIL | **FAIL** |
| H4 | A promotion: F0_null .002, F5_dep_null_r8 .002 (bound .0695) | **PASS** |
| H5 | A max 95% UB of decision harm 1.40 (F5_dep_null_r95) ≤ 5 | **PASS** |
| H6 | B max 95% UB 1.47 (F5_dep_null_r95) > 1.0 | **FAIL** |
| H7 | J(B) − J(A5b), S-alt: −0.32 [−3.21, +2.59] | **FAIL** |

### Frontier (reported without a pass/fail rule)

- **Synthetic alternatives.** A costs 385.3. Cheaper policies all promote on persistent marginal
  nulls (r95):
  - author-endpoint `gated_deployment_native` (+5.4 [+3.2, +7.6] cheaper than A): .254
  - `gated_adaptive_range_native`: .316
  - QSG: .686
  - D2: .614
  - the uncertified selectors: .76–.96

  A promotes at .150 on r95 (out of its class) and has max harm 0.06. Among policies with r95
  promotion ≤ .20, A is the cheapest. The next cheapest are NAD-m80-g10 (−2.9), quad-endpoint
  GAR (−7.7) and DISCERN-floor (−9.0).
- **C4 real streams.** All certified methods lie within about 2% of each other. A is cheaper than
  gated_deployment_native (−0.6%), quad GAR (−1.9%), env8 (−2.3%), DISCERN-floor (−2.4%) and
  never-switch (−10.7%). It ties A5b and D5, and costs more than native GAR (+0.6%), the V1
  front-loaders and the uncertified selectors (+1.2 to +2.2%).
- **Real twins v1 (registered cohort, 1,240 episodes × 5 seeds).** A promotes at .006–.100 per
  dataset; native MOPE at .015–.443.

### Post-registration descriptive check: twin v3 (7,440 episodes, seed base 2026110961)

| Policy | Pooled promotion | Datasets with 99% LB > .05 |
|---|---|---|
| PB80-g10 | .015 | 0 |
| A5b | .028 | 1 (bike_hour .089) |
| NAD2S-g10-f6 (A) | .037 | 1 (bike_hour .107) |
| NAD-m80-g10 | .044 | 1 (bike_hour .129) |
| choe_ramdas_eb+front | .113 | 4 |
| gated_deployment_native | .148 | 4 |
| gated_adaptive_range_native | .151 | 4 |
| SMCS+retain-incumbent | .175 | 4 |
| QSG | .224 | 4 |

On real twins, mean decision harm is ≤ +0.8 for every certified policy and is negative on
appliances and bike_hour. This replicates F2: "invalid" promotions on real marginal nulls are
conditionally informed and economically harmless. Appliances v3 differs from its recorded hash
in 1 of 720,000 cells (`_twin_v3_rebuild.md`).

### Assessment

- **Supported.** Within the dependence-robust class, A is about 3% cheaper on synthetic
  alternatives (H1, H3a), keeps level α in its class (H4) and passes Tier B (H5).
- **Not supported.**
  - On weakly dependent real replacement streams, A is not cheaper than A5b or D5 (H2, H3).
  - The payback arm did not reach its harm tolerance (H6) or beat A5b (H7).
- **Frontier.** Methods cheaper than A pay with marginal-null validity. That includes the
  author-faithful MOPE, at .15 pooled promotion on real twins. But that invalidity costs little
  economically on the real data available.
