# Failure Atlas update: scoped methods evidence

## Registered failure mechanisms

1. **Late-improvement blindness under scarce/delayed labels.** The existing synthetic atlas includes late improvement, delayed labels, rare disagreement and fixed label budgets. Its original F0_better discovery contrast establishes a deployment gap for some certificates, but the subsequent corrected real WP1 evidence does not establish that RMM repairs it: 10 retrospectively classified late episodes / 5 source clusters; every one of four RMM-vs-best-certified intervals crosses zero. RMM also fails to beat matched SRR on that real stratum. Treat the discovery finding as a scoped failure pattern, not a new-method result.
2. **Inadequate rollback following reversals.** Synthetic E_rb reversal evidence is favorable: mean paired net-cost difference versus RMM is −6.65, 95% t CI [−7.31, −6.00], across three reversal settings and four hosts, but this is post-development. Real evidence comprises 16 retrospective reversal episodes / 7 clusters; only 2/4 host intervals exclude zero. The existing ablation attributes the synthetic gain to rollback alpha/start-grid; its horizon gate never binds.

## Validity and fidelity update

The 2026-11-05 comparator audit documents a predictable bet-range ordering defect in GatedAdaptiveRange. It affected 130 runs / 411 policy entries. Corrected Failure Atlas replays exist. Sprint 2 comparisons affected by the shared host remain provisional pending same-seed replay and corrected null suite. DISCERN port scaling was corrected and its earlier results are superseded. Preserve historical records as historical; do not silently replace their status.

## Atlas interpretation table

| Failure/claim | Current evidence | Status |
|---|---|---|
| Fixed budget/pacing can miss late gains | synthetic discovery and exposed retrospective episodes | Scoped diagnostic; real repair contrast unsupported |
| Restarting helps over a single long-lived process | ablations on selected late episodes | Mechanism evidence, but selection/exposure and matched SRR limits remain |
| RMM's mixture is the key gain | matched SRR on late real: no significant RMM advantage | Not supported as unique real mechanism |
| Rollback reduces reversal cost | synthetic post-development E_rb vs RMM and mixed real reversal intervals | Useful benchmark finding; not a novel method result |
| Cost-to-go/horizon gate explains rollback benefit | WP1 reports gate never bound | Contradicted for the evaluated configuration |

All values and limitations are summarized from `docs/sprint2/wp1/RESULTS.md`, `docs/failure_atlas_v2_flq/results/validation_synthetic.md`, and `docs/failure_atlas_v2_flq/results/validation_real.md`. The analysis does not create new episode truth or causal change times.

## Correction-replay amendment

The Sprint 2 same-seed adaptive-range correction replay is now complete for five suites. The primary checkout audit reports 99 matched regime-policy cells and 130 individual run changes; null counts are unchanged for the front-loaded methods except corrected ordinary-Gated cells in some regimes. Corrected outputs show front-loading gains across previously exposed real sources: equal-source front−Gated is −24.55 J [−42.81,−6.29] over 14 source clusters, while front−tuned pacing is −0.30 [−1.05,+0.45]. These are source-cluster intervals on development-exposed streams, not confirmation. C2/C6 reduce synthetic net cost by approximately 7.4–7.8 in two late regimes against Gated+front, largely by issuing fewer labels without a higher promotion rate; they also have elevated promotion in out-of-class marginal-null stress tests. Details and hashes are in `CORRECTED_REPLAY_AUDIT.md`.

This amendment supersedes any statement in this report or the earlier exit audit that Sprint 2 affected comparisons remain unreplayed. It does not replace, delete or rewrite the historical records.

## PFA-SR matched-host confirmation amendment (2026-11-06)

The new `PFA-SR` screen tests a published PFA-weighted e-Shiryaev–Roberts detector on
the same deployment hosts as corrected RMM. The matched-host confirmation results are in
`research/scoped_method/pilots/pfa_srr_transfer_confirmation_20261106/run/RESULTS.md`;
its protocol and detector definition are in the sibling `protocol.md` and
`scripts/sota_sprint/pfa_srr_baseline.py`. In the frozen strong-persistent synthetic cell,
PFA-SR saved 18.34 net-cost units against Xu's acquisition-only adapter
([−25.57, −11.11]) and 14.24 against same-host RMM ([−20.71, −7.77]). Null promotions
were 0/100 and 1/100 for the two hosts. The weaker persistent cell did not resolve a
5-unit benefit; the delayed/scarce cell failed the same-host RMM criterion for the
adaptive-range host. In the reversal diagnostic, both PFA-SR hosts cost materially more
than never-switch.

This does not revise the atlas into a new-method claim. The PFA start-time prior is
published prior art (Shin et al., 2026); the run is a same-host application comparison.
The evidence localizes an economic deployment opportunity to strong persistent gains
with an iid conditional feedback model. It does not show robust correction of reversals,
general benefit under scarce/delayed feedback, or validity on dependent real streams.
No new real-data confirmation was run: candidate originality was not established, and
available chronological sources audited for this turn lack verified label-release times
for the intended deployment-stream test. The raw matched records and their hashes are
preserved in the run directory; this amendment supersedes no earlier atlas observations.

## Late-label heavy-tail prior screen (2026-11-06)

To target late-improvement blindness under delay, a fixed `q=1.2` start prior proportional
to `1/[s log(e s)^q]` was compared with canonical `q=2` PFA-SR after normalizing both to
the same total finite-budget mass. The frozen development protocol and implementation are
`research/scoped_method/pilots/heavy_tail_pfa_screen_20261106/protocol.md` and
`scripts/sota_sprint/pfa_srr_baseline.py`; full results and raw rows are in the sibling
`run/` directory. In the late, 400-step-delay, B=100 cell, the candidate costs 4.40 more
than canonical PFA-SR (95% CI [−1.27, +10.07]), 5.30 more than same-host RMM
([−0.01, +10.61]), and 4.09 more than the Xu adapter ([−0.48, +8.66]). It promoted 1/30,
versus 3/30 for canonical PFA-SR; this did not yield a cost advantage. It also costs
57.97 more than never-switch on the reversal diagnostic ([+48.50, +67.44]). The fixed
candidate fails its preregistered development gate and is stopped; no confirmatory run or
novelty claim follows. This is a failed prior-shape candidate, not evidence against the
separate strong-persistent PFA-SR application result.

## Independent chronological-news stress test (2026-11-06)

The one eligible fresh source, Wild-Time HuffPost, adds a real chronological instance of the
late-improvement failure. Validation selected a fixed model pair with a 40.46-point error
advantage for the later model; on 3,877 test events with at most 200 delayed labels, PFA-SR
acquired the full budget and did not promote. Its cost was 3,163 versus 2,039 for same-host RMM
and 1,454 for Xu acquisition-only. Paired PFA-SR-minus-RMM cost was +289.91/1,000
(`[+193.64,+391.18]`); versus Xu it was +440.80 (`[+394.19,+486.84]`). This failed the
frozen practical/statistical transfer rule. The test uses one source cluster and a simulated
24-hour label clock, so this is a scoped retrospective failure case, not independent source-level
generalization or method confirmation. The 11-category row-ID corrected pretest result supersedes
the separately preserved headline-tie pretest artifacts; neither version inspected test outcomes
before the one-time opening. Full artifacts are registered in the chronological-news pilot
directory. The finding strengthens the diagnosis of PFA-SR's slow promotion under scarce labels,
but PFA-SR is prior art and the result supplies no repair.

## Publisher-context screen on MN-DS (2026-11-06)

Q3 showed opposing source-specific model-pair effects, so a frozen Q3 static selector and a
standard per-context promotion/rollback composition were replayed on Q4. The replay is **not
confirmatory**: it was opened before the broader synthetic economic-headroom and novelty gates had
passed. Preserve it only as an exposed descriptive screen; the opening manifest and the deviation
are documented in `research/scoped_method/pilots/context_stratified_mnds_20261106/DECISION.md`.

On 3,052 October–December events, Q3-selected static deployment promoted the challenger only for
Sputnik. The context-wise gate made no promotion and spent 5 label-cost units. It matched
never-switch's 1,033 errors and cost 1.64 more per 1,000 than never-switch. It was 2.29 cheaper per
1,000 than the static selector, but its simultaneous 99% paired block interval was
`[-5.75,+3.62]`, and the point improvement missed the 5-unit practical threshold. The candidate
therefore fails its registered primary gate. Named-publisher intervals are descriptive and each
named publisher is a single cluster; this one corpus does not establish transfer across datasets.

This screen does not alter the atlas's scoped diagnosis of late-promotion failures or reversal
costs and supplies no method repair. It adds evidence that a validation-selected static source
advantage can fail to transfer across adjacent quarters. It is not evidence that a dynamic
context-specific controller solves that problem. Keep the overall disposition
**`BENCHMARK_OR_CASE_STUDY_ONLY`** and do not open another real-data source from this candidate.

## Slower-pacing restart falsification (2026-11-06)

The existing E-SR `k=0.5` horizon-weighted pacing configuration passed a fresh iid-null calibration
(20/1,000 promotions; one-sided 95% Wilson upper 2.87%) and independent iid-null check (also
20/1,000, upper 2.87%). It did not improve the registered late cell over default E-SR: on
`F1_late_800` candidate-minus-default net cost was +1.69/1,000 events (95% paired t CI
[−0.51,+3.90]). The candidate was +10.92/1,000 more costly than default E-SR in `F0_better`,
and +20.04 [17.26,22.82] / +15.02 [12.90,17.14] more costly than never-switch in the 800/1200
reversal cells. It also lost to Qiu/Gong ports on the late cell; those are not safety-equivalent
certificate baselines. Since the pacing rule is conventional prior art and the target gate failed,
this is a falsification, not a method advance. Full results and hashes:
`research/scoped_method/pilots/srr_tail_pacing_20261106/RESTART1_RESULTS.md`.
