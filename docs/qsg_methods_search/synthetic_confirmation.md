# C3 frozen synthetic confirmation: results

Protocol: [synthetic_confirmation_protocol.md](synthetic_confirmation_protocol.md), locked in
commit `10ba0237` before the run. Fresh seed base 2026110799, 100 seeds × 14 regimes × 12
policies (1,400 jobs). Raw records (gitignored): `outputs/qsg_methods_search/c3_confirm/`.

```bash
OPENBLAS_NUM_THREADS=1 PYTHONPATH="scripts/qsg_methods_search;scripts/failure_atlas_v2_flq" uv run python scripts/failure_atlas_v2_flq/run_atlas_v2.py --kind synthetic --seeds 100 --seed-base 2026110799 --regimes F1_late_400,F1_late_800,F1_late_1200,F2_transient,F3_reversal_800,F3_reversal_1200,F4_recurrent,V_late_600,V_reversal_1000,V_recurrent,F0_better,F0_null,V_worse,V_null --extra c3_extra --policies "$(cat outputs/qsg_methods_search/c3_policies.txt)" --workers 14 --out outputs/qsg_methods_search/c3_confirm
cd scripts/qsg_methods_search && uv run python analyze_c3.py ../../outputs/qsg_methods_search/c3_confirm/records.jsonl
```

## Verdict under the locked rule: **C3 PASS** (both arms)

Family-mean net-cost difference per 2,000-event episode; paired t over 100 seeds; Holm over 4.

| arm | comparator | Δ (95% CI) | Holm p | % of comparator cost | % of comparator exp.-oracle regret |
|---|---|---|---|---|---|
| A `EQSDp_l0.95_g0.2` | tuned Gong–Zhang (W=100, m=10) | **−4.84 [−5.84, −3.84]** | 7e-16 | −1.3% | −9.8% |
| A | Qiu delayed movement | **−5.72 [−6.54, −4.90]** | 2e-24 | −1.6% | −11.3% |
| B `EQSDp_l0.9_g0.2` | tuned Gong–Zhang | **−8.77 [−9.81, −7.73]** | 5e-30 | −2.4% | −17.7% |
| B | Qiu | **−9.65 [−10.59, −8.72]** | 9e-37 | −2.7% | −19.1% |

Guard clause (guard mean − econF_mo5_m5 ≤ 5): A −2.91, B +2.76; both pass. Mechanism clause
(arm A − best point-estimate+margin ablation, `m20`): **−5.96 [−6.61, −5.31]**; passes.

Fair grading: on the total-cost scale the effect is *small* (1–3%). On the avoidable cost
(expected-oracle regret) it is *meaningful to substantial* (10–19%). It replicates the D2 and
D3 development estimates: A vs Qiu −6.1 (D2) and −7.0 (D3), confirmed at −5.7.

## Summary table (means over 100 seeds)

| policy | family | change (10) | guard (4) | exp.-oracle regret | null/worse promote | switches on null |
|---|---|---|---|---|---|---|
| B EQSDp λ=.9 γ=.2 | **354.1** | **347.1** | 371.7 | 40.8 | 0.88 | 3.3 |
| EQS-D with decision-at-stake acquisition | 357.3 | 353.5 | 366.8 | 44.0 | 0.76 | 2.5 |
| A EQSDp λ=.95 γ=.2 | 358.1 | 354.9 | 366.1 | 44.8 | 0.74 | 2.0 |
| tuned Gong–Zhang | 362.9 | 354.1 | 384.9 | 49.6 | 0.98 | 6.3 |
| Qiu | 363.8 | 359.5 | 374.6 | 50.5 | 0.84 | 4.5 |
| point estimate + margin 20 (ablation) | 364.0 | 358.7 | 377.3 | 50.7 | 0.93 | 4.9 |
| Gong–Zhang (as adapted, untuned) | 368.9 | 362.3 | 385.3 | 55.6 | 0.92 | 7.4 |
| econ+front (D1 winner) | 369.4 | 369.5 | 369.0 | 56.1 | 0.75 | 0.9 |
| Model Selector (causal adapter) | 375.9 | 375.0 | 378.1 | 62.6 | 0.85 | 5.9 |
| never switch | 377.8 | 379.0 | 374.9 | 64.5 | 0 | 0 |
| QSG (certified) | 386.9 | 394.9 | 366.8 | 73.6 | 0.01 | 0.0 |

## Failure boundaries (must be reported with the claim)

- **No false-promotion guarantee.** The arms promote on 74–88% of null/worse streams. Under an
  exact null this costs about 2–3 switches per episode. On null streams every arm costs 18–28
  more than never switching (F0_null 379.7 vs 361.5; V_null 419.0 vs 399.6). Where a certified
  promotion is required, QSG/certified hosts remain the right tool; this claim is about expected
  net cost.
- **F4_recurrent**: A 405.5 vs never 365.3 and econ+front 383.9. Fast recurrence at this
  disagreement rate is lost by every adaptive method except econ+front.
- **V_worse**: A 336.9 vs never 319.3 and QSG 329.3.
- The family has equal regime weights. The gain is concentrated in reversal/late cells (vs Qiu)
  and in null churn (vs tuned Gong–Zhang). A different regime prior changes the size of the gain.
- Synthetic Bernoulli disagreement streams only; dependence regimes were not in the family.

## What this does and does not establish

C3 (synthetic, scoped) is met for a frozen economic switcher against the strongest matched
comparators, with the distinguishing mechanism isolated by ablation. It does **not** establish
novelty (audit pending: confidence-bound switching under switching costs has close prior art),
real-data transfer (C4), or any safety property.
