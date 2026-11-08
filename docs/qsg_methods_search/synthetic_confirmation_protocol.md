# C3 frozen synthetic confirmation protocol (locked before running)

Locked 2026-11-07 in the commit that adds this file; the run starts only after that commit.

## Frozen claim

On the 14-regime change-and-stationary economic-switching family (contract T=2000, B=200,
c_q=.05, c_s=5, delay per regime), economic switching with discounted disagreement-outcome
counts and **Beta-quantile hysteresis** has lower family-mean net cost than (a) the tuned
Gong–Zhang discounted economic switcher and (b) the Qiu delayed-movement adapter. No
false-promotion guarantee is claimed.

## Frozen arms (code `scripts/qsg_methods_search/eqs_d.py`, `d3_extra.py`, this commit)

- **A (primary candidate)** `EQSDp_l0.95_g0.2`: lambda=.95, gamma=.2, paced acquisition.
  Parameters were set on D2 seeds and then replicated on D3 seeds.
- **B (secondary candidate)** `EQSDp_l0.9_g0.2`: selected in-sample on D3 seeds.
- Comparators: `gongT_w100_m10` (best tuned Gong–Zhang on D3), `qiu_delayed_movement`,
  `gong_zhang_paid_obs` (as published adapter), `econF_mo5_m5`, `model_selector_causal`, QSG,
  never switch. Ablations: `EQSDp_l0.95_g0.5_m10` and `EQSDp_l0.95_g0.5_m20` (point estimate +
  margin), `EQSD_l0.95_g0.2_pcinf_mf1.0` (with decision-at-stake acquisition).

## Data

Fresh seed base **2026110799**, **100** seeds per regime. The regime list is the D2 family:
F1_late_400, F1_late_800, F1_late_1200, F2_transient, F3_reversal_800, F3_reversal_1200,
F4_recurrent, V_late_600, V_reversal_1000, V_recurrent, F0_better, F0_null, V_worse, V_null.

## Primary analysis

Per seed, take the equal-weight mean net cost over the 14 regimes. Run four paired contrasts:
{A, B} − {gongT_w100_m10, qiu_delayed_movement}. Use two-sided paired t-tests over 100 seeds,
Holm-adjusted across the four contrasts at familywise .05.

**C3 PASS (for an arm)** requires all of:

- both of its contrasts are significant and negative after Holm adjustment;
- its guard-only mean is not worse than `econF_mo5_m5` by more than 5 units;
- the mechanism ablation `EQSDp_l0.95_g0.2 − EQSDp_l0.95_g0.5_m{10,20}` (better of the two) is
  negative with an unadjusted 95% CI that excludes 0 (arm A only).

Report alongside: effect sizes relative to the comparator's family cost and family
expected-oracle regret; change-only and guard-only splits; per-regime table; null promotion
rate and switches.

## Not allowed

No re-tuning after seeing these seeds. No changing the regime list, the weights or the
comparators. A failure is recorded as a failure.
