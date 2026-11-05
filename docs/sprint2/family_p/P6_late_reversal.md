# P6: late improvement and reversal repair

## 1. What must change before another RMM-A5b integration is meaningful

This initial hypothesis was written before the P6 screen, from fam_m.py, merge_results.md and the P1
diagnostic. The later P6 screen below tests it and shows that the retained-fraction pattern is
regime-dependent.

Amendment 6 (fam_m) ran two configurations.

* **M_LRMD_SUI** has no host, so its detector gets every label. In the two Amendment-6 late regimes,
  its retained fraction was .221 on V_late_600 and .132 on W_late_1000. The later P6 screen found
  .22 on F1_late_800 but -1.11 on F1_late_1200 and -.68 on W_late_1000. The no-host architecture
  removes host label expenditure, but these comparisons do not isolate detector evidence as the
  cause of its losses.
* **M_RMMSUI_A5b** uses the A5b host and shared budget. In Amendment 6 it retained -.429 on
  V_late_600 and -.278 on W_late_1000. The later P6 screen found -.51 on F1_late_800, -2.15 on
  F1_late_1200 and -2.06 on W_late_1000. This is consistent with poor late performance in those
  screens; it does not by itself prove that the host front-loads labels before each change.

Three mechanisms follow, ordered by how directly the evidence supports them.

1. **The start prior charges late starts heavily.**
   * `fam_a.MarkovSUI(**_B)` gives start 1 a weight of .75 and start m >= 2 a weight of
     .5/(m(m+1)), with a start every 10 outcomes.
   * A start at outcome 101 (m=11) pays log(1/w) = 5.6 nats; one at outcome 151 pays 6.3 nats.
   * A uniform prior over the at most B/10 = 20 starts that a 200-label budget allows pays 3.0 nats.
   * iid RMM's detector already uses that uniform prior.
   * The P1 diagnostic shows that a 100-query segment at p=.65 carries only 2–4.6 oracle nats. A
     6-nat start penalty therefore removes most of the late evidence that exists. This is the
     largest single, fixable loss.
2. **Budget exhaustion by the host.** The fix is a reserve the host cannot spend.
3. **Free-rho absorption.** Within a post-start segment this costs about 1–1.5 nats (P1 table). It is
   real but smaller than (1). The "null restricted to the post-start segment" is already what a
   started SUI computes, since each start takes its own null sup over its own segment.
4. **Restart starts add real-data risk.**
   * A cheaper start prior increases the effective number of looks. It stays valid under the
     first-order Markov null, because the weights still sum to 1.
   * Twin real streams are not first-order Markov, so this risk must be measured on twins, not
     assumed away.

The candidate therefore changes (1) and (2) and measures (4). It is `fam_p.ReservedRestartMonitor`.

* **P6_RRD** uses a UniformStartSUI detector with 20 starts and a 25% detector-only reserve, on the
  A5b host.
* **Ablations:**
  * `-nores`: no reserve;
  * `-bprior`: fam_m's prior;
  * `-renewal`: renewal-evidence detector, not certified here because it is fed host labels whose
    gaps are not i.i.d.;
  * `P6_LRMD_U`: no host, uniform-start detector. This is the direct counterpart of M_LRMD_SUI.

A bug was found after the first screen. With reserve = 0 the detector never acquired its own labels
(`test_p6_no_reserve_detector_still_acquires`). Those dev_syn and dev_real rows for P6 are superseded
by `outputs/sprint2/P/dev_p6` and `dev_real_p6`.

## 2. Screen results (development)

Setup: 20 seeds, base 2026110701. Raw records are in `outputs/sprint2/P/dev_p6`, and the comparators
are paired from `dev_syn`. Values are paired ΔJ with 95% CI.

| contrast | F1_late_800 | F1_late_1200 | W_late_1000 | F3_reversal_800 | S_reversal_400 | F0_better | F5_dep_better_r8 |
|---|---|---|---|---|---|---|---|
| **P6_LRMD_U vs M_LRMD_SUI** (start-prior ablation) | **-9.0 [-14.3,-3.7]** | **-11.8 [-16.8,-6.8]** | **-10.1 [-16.2,-3.9]** | -8.8 [-21.7,+4.2] | **-25.9 [-45.7,-6.2]** | +7.7 [+2.9,+12.5] | +13.2 [+0.4,+25.9] |
| P6_LRMD_U vs `xu_acquisition_only` (Xu acquisition + ShiftLab paired certificate) | **-17.5 [-28.4,-6.6]** | **-15.9 [-23.6,-8.2]** | **-12.1 [-19.4,-4.8]** | -7.3 | -15.7 | +11.1 | +47.0 |
| P6_RRD vs A5b | -0.1 | -0.8 | 0.0 | +1.0 | -3.2 | +8.6 [+1.1,+16.2] | +2.2 |
| P6_RRD vs M_RMMSUI_A5b | -1.3 | -0.8 | 0.0 | -1.3 | -11.3 [-22.2,-0.5] | +8.6 | +1.3 |

**Late gain retained, relative to iid gated RMM:** (J - J_never) / (J_RMM - J_never).

| regime | P6_LRMD_U | M_LRMD_SUI | P6_RRD | A5b |
|---|---|---|---|---|
| F1_late_800 | .68 | .22 | -.45 | -.46 |
| F1_late_1200 | 1.43 | -1.11 | -1.99 | -2.15 |
| W_late_1000 | 1.39 | -.68 | -2.06 | -2.06 |

On F1_late_1200 and W_late_1000, P6_LRMD_U's mean J is below iid RMM's.

**False promotion on nulls** (20 seeds). Every P6 variant scored 0 on F0_null, Markov r8/r95/r98
and order-2. P6_LRMD_U reached .05 on the HMM null. P6_RRD reached .05 on semi-Markov and .20 on HMM;
A5b is .15 on HMM.

**Twin known-null streams** (40 evenly spaced episodes per dataset, from `p2p3`):

| policy | appliances | beijing | bike | household | metro |
|---|---|---|---|---|---|
| P6_LRMD_U | .075 | .050 | .100 | .025 | 0 |
| M_LRMD_SUI | .100 | 0 | .125 | .025 | 0 |
| P6_RRD | .025 | 0 | .025 | .025 | 0 |

With 40 episodes per dataset these rates have wide CIs. bike_hour at .100 is about the .0936 bound,
so it is not cleared.

**Fresh real mean J** (62 episodes):

| policy | appliances | beijing | bike | household | metro |
|---|---|---|---|---|---|
| P6_LRMD_U | 780 | 649 | 364 | 631 | 314 |
| M_LRMD_SUI | 774 | 642 | 344 | 612 | 236 |
| P6_RRD | 832 | 656 | 366 | 604 | 213 |
| A5b | 831 | 659 | 345 | 604 | 221 |
| D2 | 574 | 545 | 258 | 534 | 121 |

## 3. Verdict

* **The start-prior mechanism is supported in the tested no-host synthetic ablation.**
  * The start-prior change alone (P6_LRMD_U vs M_LRMD_SUI) lowers cost: -9 to -12 on all
    three late regimes and -26 on the early reversal.
  * It is cheaper than `xu_acquisition_only` on the three late regimes by -12 to -17.5. This is an
    acquisition-adapter comparison, not a result against Xu et al.'s published certificate. A
    later post-development comparison against the corrected certificate-policy class is reported
    below; it is descriptive, same-sample selected, and not selection-adjusted.
  * Synthetic Markov-null validity is unchanged, at 0/20.
* **The integration with the A5b host still fails (P6_RRD).**
  * A 25% reserve is 50 labels paced over 2000 events; in this configuration it did not recover late
    performance for the detector.
  * The host controls the remaining 150-label budget; these runs do not isolate its within-episode
    request timing as the cause of the observed late-regime costs. A larger reserve alone did not
    recover the late benefit in this configuration.
* **What P6_LRMD_U costs.**
  * It has no host, so it pays on stationary alternatives (+8 to +47).
  * On real data it is worse than M_LRMD_SUI on 5/5 datasets (+6 to +78).
  * The real cost gap and the twin-null promotion rates are directionally consistent with the
    extra looks from a cheaper late-start prior. These comparisons do not establish that the extra
    looks caused the real-data cost gap.
* **Disposition:** P6_LRMD_U SCREENED_PROMISING, scoped to synthetic late improvement and reversal.
  P6_RRD SCREENED_NEGATIVE.

## Post-development twin-bike follow-up (2026-11-04)

The P6 next-action replay completed with seed base `2026110812`, 1,000 seeds per episode, and four
policies over all 120 registered `twin_bike_hour` episodes (20 source splits from one dataset).
The original 4-worker and 8-worker partial outputs are retained separately. The full run used a
worker-local NPZ cache wrapper that called the unchanged frozen `screen._job`; a pre-run cached vs
uncached smoke comparison matched every policy metric (excluding wall-clock runtime). The full
record file has exactly 480,000 rows, with complete, duplicate-free episode × seed × policy coverage.
The completion manifest was reconstructed after a manifest-only runner error (`IMPORT_ERRORS` was
read from the wrong module); it records exact code/data hashes and leaves runtime unavailable rather
than inferring it. See `outputs/sprint2/round5/p6_twin_bike_1000/manifest.json`.

On the reused bike-hour twin construction, mean promotion rates averaged equally over 20 split
clusters were: P6_LRMD_U **.076** (cluster-bootstrap 95% CI [.036,.122]), M_LRMD_SUI .097
[.047,.153], A5b .058 [.017,.100], and never-switch 0. P6's upper bound remains above the .0936
screening convention, so this replay does **not** clear the P6 known-null concern. P6 minus its
parent M_LRMD_SUI mean net cost was +.16 (cluster-bootstrap 95% CI [-.24,+.62]), with no clear
cost difference. This is Monte Carlo evidence over 20 split clusters within one reused dataset;
1,000 seeds do not create new independent datasets or establish transfer.

Analysis: `p6_twin_bike_1000.json`; reproduce with:

```sh
uv run python scripts/sota_sprint/finalize_p6_twin_manifest.py
uv run python scripts/sota_sprint/analyze_p6_twin_bike.py outputs/sprint2/round5/p6_twin_bike_1000 --out docs/sprint2/family_p/p6_twin_bike_1000.json
```

## Post-development multiplicity-adjusted comparator sensitivity (2026-11-04)

The corrected 100-seed records were additionally analyzed with a paired-seed max-statistic
bootstrap over the five certificate-policy ports present in that run
(`gated_deployment`, `gated_adaptive_range+front`, `discern_style`,
`SMCS+retain-incumbent`, `choe_ramdas_eb+front`). For each regime, the simultaneous one-sided 95%
upper bound on the maximum P6-minus-comparator cost contrast is -20.37 on F1_late_800, -9.57 on
F1_late_1200, and -19.26 on W_late_1000: within this exact fixed port set, these bounds support lower
P6 cost in those three synthetic late regimes. The bound is not below zero on either reversal or on
F0_better. See `P6_selection_adjusted.json` and reproduce with:

```sh
uv run python scripts/sota_sprint/analyze_p6_selection_adjusted.py outputs/sprint2/round5/P6_corrected_comparators_100/records.jsonl --out docs/sprint2/family_p/P6_selection_adjusted.json
```

This corrects for selecting among the five listed ports within each regime only. It does not adjust
across regimes, candidate development, or other analyses; the follow-up remains post-development,
uses common-contract adapters rather than author-native full methods, and does not establish real-data
transfer or a confirmatory main-track claim.

## Round-5 100-seed comparator-label correction

Reanalysis of `outputs/sprint2/round5/P6_LRMD_U_eval/summary.md` confirms the old `best cert`
column selected `xu_acquisition_only`; its -15.5/-12.4/-15.2 late-change contrasts are **versus
Xu's acquisition adapter + ShiftLab certificate**, not versus P6's parent. The correctly labeled
parent contrasts are -10.9 [-13.2,-8.5] on F1_late_800, -8.7 [-10.6,-6.8] on F1_late_1200,
and -11.8 [-14.3,-9.2] on W_late_1000. Versus internal baselines D2/A5b, the corresponding
late contrasts are -11.9/-20.0, -9.4/-13.3, and -12.7/-19.7. The original evaluation did not
include the other certificate-policy ports; a separately frozen corrected comparator-class
follow-up is specified in `P6_COMPARATOR_AMENDMENT_20261104.md`.

For the two synthetic reversals, parent deltas were -14.5 [-21.2,-7.9] and -17.5 [-23.9,-11.2];
D2 deltas were -23.9 [-33.0,-14.9] and -82.2 [-93.2,-71.3]. The large D2 contrast on
S_reversal_400 reflects that episode's regime-specific costs and should not be generalized. All
contrasts are paired over 100 synthetic seeds and are post-development evidence.

## Corrected published-certificate-class comparison (post-development)

The frozen amended run (`outputs/sprint2/round5/P6_corrected_comparators_100/`, 100 paired seeds,
seed base 2026110815) compared P6 with the certificate-policy ports after excluding Xu from that
pool. The same-sample lowest-cost certificate port was `gated_adaptive_range+front` on the three
late regimes: P6 minus that port was -24.1 [-28.5,-19.8] on F1_late_800, -12.2 [-15.1,-9.3]
on F1_late_1200, and -23.1 [-27.2,-18.9] on W_late_1000. On reversals, the same-sample selected
port was `discern_style`; P6 was more costly by +25.9 [+19.5,+32.3] on F3_reversal_800 and +4.9
[+1.0,+8.9] on S_reversal_400. P6 was also more costly than the selected port on F0_better by
+31.5 [+23.9,+39.0]. These are descriptive same-sample comparisons after candidate selection and
against common-contract ports, not author-native SOTA or selection-adjusted confirmation.

The generated summary is `P6_corrected_comparators_100.md/json`; reproduce with:

```sh
uv run python scripts/sota_sprint/analyze.py outputs/sprint2/round5/P6_corrected_comparators_100 --candidates P6_LRMD_U --hosts P6_LRMD_U=M_LRMD_SUI --out docs/sprint2/family_p/P6_corrected_comparators_100.json
```


## Post-development 14-source real-stream economic replay (2026-11-05)

A frozen follow-up replayed all nine previously used Atlas cached sources and the five UCI sources
used earlier in this sprint, with 20 policy-randomness seeds per stored episode. Policy seeds are
averaged within episodes; they do not represent new data units. The source-level paired contrasts
and resource outcomes are in `P6_all14_real_results.md` and `.json`.

Equal-source mean net cost was 525.24 for P6_LRMD_U, 500.83 for its M_LRMD_SUI parent, 495.69 for
A5b, 404.92 for D2, 423.47 for the RMM host, 414.14 for gated adaptive-range, and 597.89 for
never-switch. P6's equal-source paired cost was +24.41 versus its parent (higher cost on 11 sources,
lower on two, tied on one), +29.54 versus A5b, +120.32 versus D2, +101.77 versus RMM, and +111.10
versus gated adaptive-range. It was 72.65 below never-switch on the equal-source mean. The source mix
is curated, and source windows may be dependent; these averages are descriptive.

This evidence does not change the scoped synthetic late-improvement result. The nine cached sources
have no verified causal event or feature-publication times, and the five UCI streams do not provide
causal late-change labels. No late-improvement or independent-generalization claim is made. Reproduce
from the saved manifest and records with the command in `docs/sprint2/REPRODUCIBILITY.md`.
