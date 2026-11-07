# Failure Atlas v2: frozen validation results

2026-11-03. Candidates and the primary family were frozen in
[failure_atlas_v2_development.md](failure_atlas_v2_development.md) (commit `1ee1060`) before
this run. Validation: 13 regimes never run before (`regimes.VALIDATION_REGIMES`, registered in
commit `ade273f`), seeds 5000-5099 at seed base 20261104; 9 real streams, 168 episodes x 20
replay seeds; 25 policies; 116,500 episode runs (32,500 synthetic + 84,000 real); 49 minutes. Raw:
`outputs/failure_atlas_v2/validation/records.jsonl` (manifest with code/data SHA-256). Analysis:
`scripts/failure_atlas_v2/analyse_validation.py` -> [validation_analysis.json](failure_atlas_v2_results/validation_analysis.json).

**Deviation from the protocol (recorded, not material to the claim):** real replay seeds were
5000-5019 rather than the 1000-1019 written in the protocol, because the runner applies one seed
offset to both synthetic and real runs. Both ranges are unused under the new seed base.

```bash
uv run python scripts/failure_atlas_v2/run_atlas_v2.py --regimes validation --real rialto,openml_ldpa,spam,weather,uci_occupancy,airlines,bank,elec2,criteo --n-seeds 100 --seed-offset 5000 --real-seeds 20 --seed-base 20261104 --workers 9 --policies "$(cat outputs/validation_policies.txt)" --extra-module v2_candidates --out outputs/failure_atlas_v2/validation
uv run python scripts/failure_atlas_v2/analyse_validation.py outputs/failure_atlas_v2/validation/records.jsonl docs/failure_atlas_v2_results/validation_analysis.json
```

Comparators: "best controlled" is, per regime, the lowest-mean-cost of Gated, DISCERN, SMCS,
Xu, Qiu*, front-loaded Gated and front-loaded DISCERN, chosen on the same validation seeds
(which favours the comparator). "Best any" adds the seven online selectors with no promotion
guarantee. Intervals: 95% percentile bootstrap over seeds (synthetic) or episodes (real).

## Registered criteria

**Timing caveat (audit finding 1).** The protocol at `ade273f` fixed the criteria but did not
name the primary family; it was fixed in `1ee1060` after development had shown harm on
reversal/transient/recurrent regimes. The adverse-family result below must always be read
together with the primary-family result. **Criterion (3) caveat (audit finding 2):** at n=100
the Wilson bound <= .10 requires <= 4 promotions, so a method at exactly the nominal .05 fails
it with probability ~.56; on 600 out-of-protocol scratch seeds the auditor measured V_null
promotion .032 for LRMD and .012 for Gated+RMM. LRMD's registered FAIL stands, but it is weak
evidence about LRMD's true null rate.

Primary family = V_late_600_p65, V_late_1000_p72, V_late_1400_p72, V_late_1000_d50,
V_late_1000_d250, V_better_p62, V_better_p70 (per-seed family mean; net-cost differences).

| Criterion | RMM on Gated | RMM on DISCERN | RMM on SMCS | LRMD (standalone) |
|---|---|---|---|---|
| (1) improves its base | **-25.61 [-27.16,-24.09]** | **-27.06 [-28.53,-25.59]** | **-8.21 [-9.79,-6.59]** | n/a |
| (2) vs best controlled comparator | **-2.83 [-4.19,-1.46]** | **-3.16 [-4.60,-1.80]** | **-3.71 [-5.02,-2.44]** | **-5.40 [-6.53,-4.35]** |
| (3) V_null promotion (Wilson UB <= .10) | .01 (UB .05) PASS | .01 (.05) PASS | .01 (.05) PASS | **.06 (UB .12) FAIL** |
| (4) stationary harm on nulls (< +2) | V_null +0.23, V_worse +0.02 PASS | +0.21, +0.02 PASS | -0.25, +0.01 PASS | +1.07, +0.90 PASS |

**Outcome.** The attachable RMM repair meets every registered criterion on the primary family
for three independently developed error-controlled methods. The standalone LRMD has the largest
cost advantage but fails the registered null-safety bound (6/100 promotions on the exact
boundary null p=.5; its Ville guarantee is alpha=.05 for the conditional null, and 6/100 is
statistically compatible with .05, but the registered criterion is the Wilson bound and it
fails). LRMD is therefore reported as exploratory, not confirmed.

## Per regime (difference in mean net cost; negative favours the candidate)

| regime | best controlled | LRMD - best ctrl | Gated+RMM - Gated | DISCERN+RMM - DISCERN | SMCS+RMM - SMCS |
|---|---|---:|---:|---:|---:|
| V_late_600_p65 | Xu | -7.88 [-12.05,-3.75] | -17.15 | -15.96 | -20.80 |
| V_late_1000_p72 | Xu | -6.06 [-9.09,-3.22] | -18.10 | -18.11 | -16.20 |
| V_late_1400_p72 | Gated front-load | +1.88 [+1.43,+2.37] | -0.08 (ns) | -0.21 (ns) | -0.18 (ns) |
| V_late_1000_d50 | Xu | -5.46 [-8.75,-2.45] | -15.24 | -16.85 | -12.24 |
| V_late_1000_d250 | Gated front-load | -2.27 [-3.96,-0.88] | -5.40 | -6.08 | -5.38 |
| V_better_p62 | Gated front-load | -15.28 [-19.53,-11.47] | -30.66 | -29.30 | -5.90 |
| V_better_p70 | Gated front-load | -2.73 [-5.40,-0.25] | -92.68 | -102.92 | +3.24 (ns) |
| V_transient_500_1200 | DISCERN | +15.96 | +16.06 | +16.00 | +13.30 |
| V_reversal_1000 | DISCERN | +30.93 | +27.46 | +35.72 | -3.32 (ns) |
| V_recurrent_400 | Gated front-load | +9.48 | +8.64 | +8.41 | +8.55 |
| V_null | Xu | +1.07 | +0.23 | +0.21 | -0.25 (ns) |
| V_worse_p40 | Gated front-load | +0.90 | +0.02 | +0.02 | +0.01 |
| V_dep_null_r8 | DISCERN | +1.65 (ns) | +1.09 (ns) | +2.47 (ns) | +1.28 (ns) |

Family aggregates beyond the criteria: against the best method of any kind, LRMD is worse on the
primary family by +12.69 [+10.97,+14.41] (Model Picker +2.85, Model Selector +7.70) and better
on the null family by -23.0 against either. On the adverse family (transient, reversal,
recurrent) every repair is worse than the best controlled comparator by +18 to +21; SMCS+RMM
is the least affected (+6.18 against SMCS).

## Safety under dependence (not covered by the guarantee)

V_dep_null_r8 promotion (Wilson UB): Gated .00 (.04); front-loaded Gated .16 (.24);
Gated+RMM .24 (.33); DISCERN+RMM .23 (.32); SMCS+RMM .23 (.32); LRMD .33 (.43); Model Picker
.95. The repair inherits and amplifies front-loading's dependence sensitivity. No claim of
dependence robustness is made; this is the main scope restriction.

## Real streams (replays of exposed streams; episode-level bootstrap)

| stream | K | Gated+RMM - Gated | DISCERN+RMM - DISCERN | SMCS+RMM - SMCS | LRMD - best ctrl (which) |
|---|---:|---:|---:|---:|---:|
| rialto | 16 | **+3.88 [+2.91,+4.80]** | -111.97 [-129.97,-93.15] | +1.14 [+0.86,+1.41] | +0.24 [-0.74,+1.39] (SMCS) |
| openml_ldpa | 32 | -72.29 [-98.42,-47.42] | -191.34 [-228.82,-153.13] | -6.55 [-29.96,+9.80] | -1.27 [-26.29,+18.16] (Gated FL) |
| spam | 1 | -134.47 | -310.19 | +0.40 | +7.10 (Gated FL) |
| weather | 3 | -13.75 [-26.59,+0.01] | -35.87 [-55.25,+0.02] | +2.69 [+0.02,+4.50] | -6.85 [-11.75,-0.82] (SMCS) |
| uci_occupancy | 4 | -49.93 [-145.69,+3.01] | -88.27 [-255.52,+3.13] | -4.39 [-13.81,+0.48] | +1.96 [-7.11,+10.16] (Gated FL) |
| airlines | 50 | -0.60 [-3.10,+1.26] | -4.37 [-9.33,-0.38] | -0.15 [-1.03,+0.50] | -0.39 [-3.02,+1.62] (Gated FL) |
| bank | 8 | **+4.13 [+1.80,+6.39]** | +3.10 [+0.78,+5.39] | +0.19 [+0.00,+0.56] | +7.03 [+1.69,+15.87] (Gated FL) |
| elec2 | 4 | -0.28 [-4.01,+3.01] | -0.09 [-1.41,+0.95] | -0.87 [-3.94,+1.17] | -4.90 [-11.04,+0.24] (SMCS) |
| criteo | 50 | +0.19 [-0.32,+0.71] | -1.11 [-2.37,-0.05] | +0.71 [+0.13,+1.34] | -0.42 [-1.14,+0.22] (SMCS) |

Real-data reading:
* Transfer: RMM lowers DISCERN's cost significantly on rialto, ldpa, airlines and criteo (plus
  large point estimates on spam K=1, weather and uci with intervals touching 0), and Gated's on
  ldpa. It costs Gated +3.9 on rialto and +4.1 on bank, SMCS +1.1 on rialto and +0.7 on criteo.
* SOTA on real data is **not** established: against the strongest error-controlled comparator
  (usually front-loaded Gated or SMCS), LRMD is significantly better only on weather (K=3,
  low power) and significantly worse on bank (+7.0). The real streams have no sign changes
  within an episode, so the late-change mechanism the repair targets is absent; the remaining
  real-data gain over front-loaded Gated is what front-loading already captures.
* All nine streams were exposed in B3 and in discovery; these are replays, not independent new
  case studies.

## Continue / pivot / stop

* **Continue (confirmed, scoped):** RMM as an attachable recovery wrapper for anytime
  certificate deployment methods, for late or stationary improvements under independent-style
  conditional nulls. Next: real streams with genuine within-stream improvement (e.g. a
  challenger retrained on recent data) to test the targeted regime on real data.
* **Pivot (LRMD):** its safety failure is at the boundary null; a version that spends alpha
  more conservatively on the first start (or uses alpha=.04 to target the Wilson bound) must be
  re-registered and re-validated on new seeds, not adjusted on these.
* **Stop:** claims of dependence robustness, of beating the uncontrolled selectors on
  alternatives, and of benefit in reversal/transient/recurrent regimes.
