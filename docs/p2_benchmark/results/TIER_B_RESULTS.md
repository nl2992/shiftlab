# P2 Tier B validity gate: results (H8, 2026-11-07)

**Verdict.** H8c is **supported**: the full two-tier gate admits `gated_adaptive_range`, the single
gate rejects it, and it costs 37.5 less than the single gate's only admittee (99% CI [−41.3, −33.9]).
H8b is **not supported**: QSG's decision harm on the ρ = .95 null is positive, but SMCS's is not
distinguishable from zero, and the rule required both. Tier B discriminates. It rejects 4 of the 16
policies that pass Tier A, but it admits 12, not the 6 predicted.

Registration: [TIER_B_GATE_PROTOCOL.md](../TIER_B_GATE_PROTOCOL.md) (commit `32a71c59`, plus
Amendment 1, `f20fc0f0`). Raw output: [tier_b.json](tier_b.json), [tier_b.md](tier_b.md).

## Results against the registered rules

| ID | Rule | Result | Verdict |
|---|---|---|---|
| H8a | Descriptive: number of the 16 that pass Tier A | **16/16** (replicates W4) | — |
| H8b | QSG **and** SMCS: decision harm on F5_dep_null_r95, 99% LB > 0 | QSG 7.47, LB **+2.93**; SMCS 1.58, LB **−1.53** | **Not supported** |
| H8c | P\* = gated_adaptive_range: two-tier admits, single rejects, paired 99% UB of J(P\*) − J(S\*) < −5 | Admitted (worst UB 2.36); single gate rejects; S\* = discern_style; difference **−37.5** [−41.3, −33.9] | **Supported** |
| H8d | Descriptive: predicted vs observed admitted set | **10/16** agree | — |

## Gate outcomes

| Policy | Claims | Tier B worst null | Worst UB (≤ 5) | Two-tier | Single gate | J on alternatives |
|---|---|---|---:|---|---|---:|
| D2 | V1 | F5_dep_null_r95 | 9.01 | **rejected** | rejected | 342.4 |
| QSG | V1 | F5_dep_null_r95 | 10.78 | **rejected** | rejected | 345.7 |
| gated_deployment+QCE+front | V1 | F5_dep_null_r95 | 5.29 | **rejected** | rejected | 356.1 |
| gated_adaptive_range+front | V1 | F5_dep_null_r95 | 4.20 | admitted | rejected | 356.4 |
| choe_ramdas_eb+front | V1 | F5_dep_null_r95 | 4.80 | admitted | rejected | 357.4 |
| rmm:gated_deployment+RMM | V1 | F5_dep_null_r95 | 6.62 | **rejected** | rejected | 361.4 |
| SMCS+retain-incumbent | V1 | F5_dep_null_r95 | 3.96 | admitted | rejected | 365.4 |
| choe_ramdas_eb | V1 | WP2_o2_null | 2.83 | admitted | rejected | 373.4 |
| xu_acquisition_only | V1 | F5_dep_null_r95 | 3.96 | admitted | rejected | 374.4 |
| gated_deployment+QCE | V1 | F5_dep_null_r95 | 3.56 | admitted | rejected | 376.2 |
| gated_adaptive_range | V1 | F5_dep_null_r95 | 2.36 | admitted | rejected | 392.3 |
| discern_design_floor | V1 | F5_dep_null_r95 | 1.79 | admitted | rejected | 393.2 |
| A5b | V2 | WP2_hs_null | 1.87 | admitted | rejected | 395.2 |
| D5 | V2 | WP2_sm_null | 1.76 | admitted | rejected | 396.6 |
| gated_deployment | V1 | WP2_o2_null | 1.09 | admitted | rejected | 417.9 |
| discern_style | V1 | F5_dep_null_r8 | 0.00 | admitted | admitted | 429.8 |

J is mean all-in cost per episode over the six fresh synthetic alternatives (200 seeds each),
weighted equally by regime. `CONTROL_never_switch`: J = 419.9 on the same alternatives. That is
**cheaper than discern_style** (429.8), the single gate's only admittee, and about the same as
gated_deployment (417.9).

## How to read it

- **The gate is not degenerate any more.** Tier A alone admits all 16. Adding Tier B removes the four
  policies with the clearest dependence harm, which include the two cheapest on the alternatives
  (D2, QSG). The single all-null gate still admits only `discern_style`, which on the alternatives
  costs more than never switching at all.
- **The reordering is large.** The registered contrast (gated_adaptive_range vs discern_style) is
  −37.5 per episode. The cheapest two-tier admittee is `gated_adaptive_range+front` (356.4), 73
  below discern_style. That figure is **descriptive** (selected on the same data, not registered).
- **H8b partly fails.** QSG carries positive decision harm under strong persistence (mean 7.5 per
  episode, about 1.5 switch costs). SMCS's development estimate (7.5) did not replicate (1.6, with
  the 99% interval covering 0). The registered claim "Tier A admits harmful published certificates"
  holds for QSG only. QSG is ShiftLab's own method, not a published comparator.
- **H8d: development over-rejected.** Six predicted rejections were admitted: SMCS, both
  Choe–Ramdas variants, gated_adaptive_range+front, gated_deployment+QCE and xu_acquisition_only.

### Post-hoc diagnostics (not registered)

1. **Why the predictions missed.** Per-episode decision harm on F5_dep_null_r95 is heavy-tailed
   (SD about 28–39; the top five episodes carry 17–72% of the total). At 200 seeds the 95% upper
   bound sits about 4.5 above the mean, so only policies with near-zero mean pass. At 500 seeds it
   sits about 2.5 above. The development means also ran high: SMCS 7.5 → 1.6, Choe–Ramdas+front
   5.8 → 2.1, gated_adaptive_range+front 3.0 → 1.7. QSG (8.4 → 7.5) and D2 were stable. The code
   path is the same (`git diff 1564c122 f20fc0f0 -- scripts src` touches only the twin builder and
   the runner prefix), and promotion rates are similar (SMCS .375 vs .326). Ordinary sampling noise
   is consistent with this (SMCS: about 2.3 combined SEs). **Consequence:** a Tier B admission
   depends on the number of seeds. The benchmark must fix n (500 here) as part of the gate.
2. **Real twin nulls never bind.** On twin v4 the largest decision-harm upper bound for any policy is
   1.46 (SMCS, beijing_pm25), with promotion rates up to .37 (QSG). All-in excess cost there is
   0.8–8.3, which is mostly label spend. So on real exchangeable twins, "invalid" promotions are
   nearly free in decision terms. This is consistent with H2 (promotions are conditionally
   informed). Every Tier B rejection comes from the synthetic ρ = .95 null.
3. **Real-data leaderboard (descriptive, exposed W4 fresh run):** among the two-tier admittees,
   choe_ramdas_eb+front (416.9), gated_adaptive_range+front (421.8) and SMCS (444.2) are
   cheapest, vs 602.8 for discern_style. This is not an H8 test.

## Deviations and checks

1. The runs record git `f20fc0f0` = registration `32a71c59` + Amendment 1 (runner prefix). No other change.
2. The twin v4 builder reproduced twin v3 split 40 exactly for all five datasets before building.
   Its NumPy "degrees of freedom" warnings come from the one-split reproduction statistics.
3. The registered script takes one synthetic directory. The null and alternative runs were
   concatenated into `outputs/p2_benchmark/tier_b/synth/records.jsonl` (88,400 records) unchanged.
4. Analysis run as committed (`analyze_tier_b.py` SHA-256 `10f0a7f4…`, 4,000 draws, registered
   expected counts).

## Provenance

| Run | Records | SHA-256 of `records.jsonl` | Wall time |
|---|---:|---|---:|
| synth_nulls (8 × 500 seeds × 17) | 68,000 | `6a3da185aa61601a786471a64c1a662c8a0977dcd00e10d2b73cb8fc3859c740` | 3,078 s |
| synth_alts (6 × 200 seeds × 17) | 20,400 | `80b8e82e41545eceeb96c907dd2d4598dec11e604e8bcfc0decf8382789ae8b8` | 697 s |
| twin v4 (7,440 episodes × 17) | 126,480 | `db5a12f18a2f9e467f1230056e2623664382dda33cba6d0ea9e61832741ea798` | 4,079 s |

Twin v4 statistics and array hashes are in [twin_v4_stats.json](twin_v4_stats.json). Runs are under
`outputs/p2_benchmark/tier_b/` (not in Git).

```bash
D=outputs/p2_benchmark/tier_b
cat $D/synth_nulls/records.jsonl $D/synth_alts/records.jsonl > $D/synth/records.jsonl
PYTHONPATH=scripts/promising_directions/sota .venv/bin/python scripts/p2_benchmark/analyze_tier_b.py \
  --synth $D/synth --twin $D/twin --out docs/p2_benchmark/results/tier_b
```

## Assessment

- **Continue (F8, restated):** "Tier A alone admits every certified method. Adding a Tier B
  decision-harm gate rejects four, and admits methods about 37–73 per episode cheaper than the
  all-null gate's only admittee." This claim is supported on fresh synthetic seeds and new twin
  splits.
- **Drop:** "published certificates carry decision harm under dependence". It held for QSG (an
  internal method) but not for SMCS.
- **Add to the paper:** decision harm on real twins is near zero, so the economic case against
  "invalid" promotions rests on synthetic strong-persistence nulls. Tier B admission depends on
  the seed count, so fix it.
- **Limitations:** exposed regime parameters and UCI sources; the +5 tolerance is a choice; label
  spend is outside the gate; the alternatives are synthetic.
