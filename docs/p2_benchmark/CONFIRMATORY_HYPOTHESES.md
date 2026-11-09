# P2 confirmatory hypotheses: registration (W4, 2026-11-06)

**Result (2026-11-07):** H1, H2, H4, H5 and H6b pass, and H3 passes its equivalence rule. In H7 the
leading policy changes between gates, but the Tier A-only gate admits all 16 certified policies.
See [results/CONFIRMATORY_RESULTS.md](results/CONFIRMATORY_RESULTS.md).

**Status:** registered before any confirmatory data exist. The new twin splits (40–159) have not
been built, because their raw UCI source files are not on this machine. No new policy run has
been made. The registration record is the commit adding this file.

## Validity criterion (frozen for the P2 benchmark)

Every method is scored with the **two-tier rule** used in
[FLQ_TWO_TIER_PROTOCOL.md](FLQ_TWO_TIER_PROTOCOL.md):
- **Tier A:** promotion rate ≤ the binomial bound on the null the method *claims*.
- **Tier B:** on nulls outside its claim, promotion rate and all-in excess cost are reported, with
  a tolerance of +5 (one switch cost) vs its host or a stated reference.

This is the benchmark's protocol; it is not a test of any single method.

## Data and seeds

| Cohort | Construction | Size | Seeds |
|---|---|---|---|
| **Twin v3 (new)** | `twin_null` construction on splits **40–159** for metro, beijing_pm25, bike_hour, appliances, household_power | 120 splits per dataset (power analysis below) | policy seed base **2026110691** |
| Synthetic dependent alternatives | F0_better, F5_dep_better_r8, S_dep_better_r95, WP2_o2_better, WP2_sm_better, WP2_hs_better | 200 seeds each | **2026110692** |

Contract: T=2000, B=200, c_q=.05, c_s=5, α=.05, registered delays, corrected (wmaxfix) ports.

**Panel.** The WP2 panel P (25 policies, `sprint2/wp2/protocol.md`). The **strict published certified
pool** is gated_deployment, gated_adaptive_range, gated_adaptive_range+front, discern_style,
discern_design_floor and SMCS+retain-incumbent (`sprint2/wp2/COMPARATOR_CLASS_AUDIT.md`).

## Hypotheses and decision rules

Five directional tests (H1, H2, H4, H5, H6b) use **Bonferroni 99% intervals** (95% family over
the five). Cluster = (dataset, split) for twins and seed for synthetic data. Use a 4,000-resample
cluster bootstrap, stratified by dataset when pooling.

| ID | Finding | Rule |
|---|---|---|
| H1 | Conditional-null certificates break the marginal null on real twins | Pooled first-promotion rate of the strict pool on twin v3: 99% lower bound > .05 |
| H1b | ...and the rate grows with horizon | Descriptive: pooled rate at T = 1000/2000/4000 re-windowings |
| H2 | Those promotions are conditionally informed | Pooled mean `adv_rest` at first promotion over the strict pool: 99% lower bound > 0 |
| H3 | Neither null tracks economic appropriateness | Equivalence: 95% CI of `pi_EI(mean-reverting synthetic nulls) − pi_EI(twin v3)` lies within ±.15, **and** both point estimates lie in [.3, .7] |
| H4 | Uncertified selectors fail on real nulls | `cams_adapter` and `model_picker_adapter`: per-dataset 99% lower bound on promotion > .5 on all five datasets |
| H5 | Dependence robustness costs economic value | Pooled synthetic `J(A5b) − J(QSG)` over the six dependent alternatives: 99% lower bound > 0 |
| H6 | Validity of a marginal-null method on real twins | A5b per dataset: report the 95% upper bound vs .0936. **H6b** (directional, from development): bike_hour 99% lower bound > .05, i.e. a real failure rather than design noise |
| H7 | The validity gate reorders the leaderboard | Descriptive: rank certified policies by mean J on fresh real alternatives under (i) the single all-null gate and (ii) the two-tier rule; report admitted sets and the rank of the top policy |

F6 (the pacing confound) is **not** registered here. It needs untouched real sources (scope item
W5), and will be registered with that cohort.

## Power analysis

Source: the exposed v2 twin run (splits 20–39, `outputs/sprint2/WP2/run1_twin2/records.jsonl`,
SHA-256 `aaac531f9543fe4867fd7f4a413f17067d62151550142e75b3ab2d1a88b4cb00`). Computed with
`scripts/p2_benchmark/twin_power.py`; full output is in
[results/twin_power.json](results/twin_power.json). Splits needed for 80% power on the rule
"UB ≤ .0936 when the true rate is .05", using the observed A5b between-split SD:

| Dataset | SD | Power at 20 splits | Splits needed |
|---|---:|---:|---:|
| appliances | .106 | .45 | 60 |
| beijing_pm25 | .058 | .92 | 20 |
| bike_hour | .152 | .25 | 100 |
| household_power | .049 | .98 | 20 |
| metro | .054 | .95 | 20 |

120 splits per dataset covers the hardest case with margin. At 20 splits, a valid method would have
failed the bike_hour rule about 75% of the time. This explains the earlier H1b and P6 "failures"
there (criteria review C7). The SDs are measured at the observed rates, so they are conservative
for a true rate of .05. The other hypotheses have large effects in development (for example, pooled
promotion .141 vs .05; CAMS twin promotion .71–.91), so 120 splits leaves them well powered.

## Execution order

1. **Requires your approval:** download the five public UCI source archives that
   `scripts/sota_sprint/fresh_real.py` reads (`data/raw/sprint_fresh/`) and verify their recorded
   checksums.
2. Build twin v3 splits 40–159 and record content hashes.
3. Commit the analysis script before any policy run on twin v3.
4. Run the panel, then the analysis, and record the results with deviations.

## Limitations

The twins are built from five UCI-derived sources that the programme has already used; the new
splits are new model fits on development-exposed events, not unseen data. Synthetic seeds are new,
but the regime parameters are exposed. Empirical rates are not guarantees.

## Amendment 1 (2026-11-07, before any confirmatory policy run)

The UCI sources were downloaded and match their recorded SHA-256 values. This amendment fixes
cohort details that the registration left implicit; no rule or threshold changes.

1. **Synthetic cohort** (seed base 2026110692, 200 seeds each): the six dependent alternatives, plus
   the seven mean-reverting nulls named in H3 (F5_dep_null_r8, F5_dep_null_r95, O_null_semimarkov,
   O_null_order2, WP2_o2_null, WP2_sm_null, WP2_hs_null), plus **F0_null**, the iid null used as
   Tier A for H7.
2. **H7 fresh-real cohort:** the five fresh UCI sources (metro, beijing_pm25, bike_hour, appliances,
   household_power), already used in Sprint 2, with new policy seed base **2026110691** and 3 seeds,
   panel P. H7 stays descriptive.
3. **H1b:** the T=1000/4000 re-windowings of twin v3 are run on the six strict-pool policies plus
   `CONTROL_never_switch`, policy seed base 2026110691.
4. **H7 gates:** the single gate admits a certified policy if its promotion rate is ≤ .0936 on every
   synthetic null and every twin v3 dataset. The two-tier rule admits it if it passes Tier A on its
   claimed null(s): F0_null for V1 claims; F0_null, F5_dep_null_r8 and F5_dep_null_r95 for V2 claims.
   The bound is `.05 + 2·sqrt(.05·.95/200) = .0808`.
5. **Analysis script:** `scripts/p2_benchmark/analyze_confirmatory.py`, committed with this
   amendment. A smoke run on the exposed v2 development runs (20 splits, 50 bootstrap draws)
   checked the plumbing only; its output is not a result.
6. **Runner:** `wp2_run.py` now recognises the `twin3_` prefix when looking up a dataset's
   registered label delay (one-line change).
