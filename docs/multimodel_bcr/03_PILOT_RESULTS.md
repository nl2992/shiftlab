# Feasibility pilot results

Run: 10 environments × 40 seeds (seed base 2026111101, fresh) × 86 policy configs. Raw output in
`outputs/multimodel_bcr/pilot/` (gitignored); analysis in `pilot_analysis.txt`.

```bash
cd scripts/multimodel_bcr
OPENBLAS_NUM_THREADS=1 python run.py --envs E1_persist,E2_late,E3_reversal,E4_specialist,E5_ambiguous,E6_null,E6_worse,E2_late_K5,E5_ambiguous_K5,E6_null_K5 --seeds 40 --seed-base 2026111101 --workers 12 --out ../../outputs/multimodel_bcr/pilot
python analyze.py ../../outputs/multimodel_bcr/pilot/records.jsonl
```

## Family winners (in-sample, equal environment weights)

| family | best config | net | labels | switches | expected-oracle regret |
|---|---|---|---|---|---|
| B2 K-Wald + disagreement | `kw_anydis_l0.95_g0.1` | **558.67** | 200 | 2.56 | 39.3 |
| B4 MP acquisition + Wald | `kw_mp_l0.85_g0.05` | 559.42 | 96 | 2.67 | 40.0 |
| B5 BCR | `bcr_l0.95_g0.05_zu0.5_rm0.3` | 559.82 | 179 | 2.01 | 40.6 |
| B1 K-Wald + uniform | `kw_uniform_l0.9_g0.05` | 569.38 | 200 | 2.39 | 50.3 |
| B0 never switch | — | 580.93 | 0 | 0 | 60.4 |
| B3 Model Picker adapter | — | 587.79 | 95 | 6.88 | 67.8 |

Best BCR minus each family's best, paired over seeds:

| comparator | Δ (95% CI) |
|---|---|
| B2 | +1.15 [−1.37, +3.66] |
| B4 | +0.40 [−2.28, +3.08] |
| B1 | −9.56 [−12.60, −6.52] |
| B3 | −27.98 |
| B0 | −21.11 |

**Per environment (BCR − B2).**
- BCR wins where eliminating candidates saves labels and switches: E5_ambiguous −6.9, E1 −4.0.
- BCR loses where a pruned challenger later matters: E3_reversal +20.5, E4_specialist +8.6,
  E2_late_K5 +6.8.

**Regime-weight-free check.** Against the lower envelope of all 72 K-Wald configs in the
(change, stable) cost plane, the best BCR config gains −0.06 at its most favourable weight. Every
other BCR config is behind the envelope.

## Verdict: FEASIBILITY FAIL

Stop rules met (directive §8):
- tuned multi-model Wald performs essentially as well;
- there is no identifiable contribution beyond ordinary disagreement sampling and Wald switching;
- BCR's savings come only from monitoring fewer candidates, which delays recovery.

That is the same information trade-off documented in the two-model programme.

## K-model findings worth keeping (C1 candidates, development evidence only)

1. **Active selection without an economic hurdle churns.** The Model Picker deployment adapter
   switches 6.9 times per episode (11.6 at K=5 ambiguous) and costs +28 vs the best K-Wald. This
   concerns the adapter's argmin deployment rule, not Model Picker's published goal
   (best-model identification).
2. **Multiple-comparison churn grows with K.** On nulls, switches for the best Wald variants
   rise from 1.6–2.6 at K=3 to 2.4–3.8 at K=5. All adaptive policies lose about 18–28 to
   never-switch on null environments.
3. **Label efficiency.** Model-Picker acquisition with Wald deployment matches disagreement
   pacing's net cost with half the labels (96 vs 200). On this contract the saved label cost
   (≈5) is offset by worse decisions. That is a label-efficiency result, not a net-cost gain.
