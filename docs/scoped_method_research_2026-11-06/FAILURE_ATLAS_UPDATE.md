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

## Rare-disagreement F8 control reconciliation (2026-11-07)

F8 (`F8_rare_better`: 3% model disagreement; challenger correct with probability .90 on
disagreements) is a distinct positive **regime-specific control** result. On 100 fresh synthetic
streams, `fixed_challenger` saved 6.174 net-cost units versus CAMS (paired 95% bootstrap CI
[-6.857, -5.544]), meeting the registered 5-unit F8 gate. The policy uses zero labels and pays
one switch cost. It is an ordinary static deployment policy whose premise is that the challenger
is already known to be preferable; the experiment does not show how an online controller can infer
that premise. Its adverse controls are material: on `F0_null`, it cost 3.98 more than never-switch
(363.31 vs 359.33); on `F3_reversal_800`, it cost 39.45 more than never-switch (384.22 vs 344.77).
See `docs/scoped_method_research_2026-11-06/eia930_f8_synthetic_followup/RESULTS.md` and its frozen
protocol. These results establish a scoped baseline advantage, not a repair or a universally safe
rule.

The EIA-930 replay is consistent with that fixed-control advantage but is not independent-provider
confirmation. Its preselected fixed challenger saved 12.239 units per episode over CAMS (hierarchical
paired 95% CI [−21.231, −7.218]) and 9.191 over the lowest-mean registered panel method with a
selection-aware interval [−13.958, −4.555] on the frozen 2026 window. The result uses 17 episodes
across 11 correlated BAs, revised historical values, a simulated one-hour feedback schedule,
hypothetical prices, and disclosed aggregate progress-row exposure. The ordinary model choice had
been selected from an earlier development profile; it is not a novel algorithm. Full provenance is
in `research/scoped_method/pilots/eia930_f8_2026_confirmation_20261107/RUN_STATUS.md`.

A separate prospective EIA profile screen tried to construct a trained challenger for the F8
mechanism; only one of three BAs passed both profile thresholds, below the frozen two-of-three gate.
No method comparison was run, and the reserved 2024–25 holdout remains unopened. This is a
pair-profile mismatch, not evidence against F8 or a method failure (`research/scoped_method/pilots/eia930_f8_ml_challenger_20261107/DECISION.md`).

An additional bounded Elexon BMRS metadata audit now verifies publication-time queries, historical
forecast/actual records, repeated forecast vintages, about 25-minute post-interval actual release on
sampled dates, and 46/50-interval DST days. It makes Elexon a credible chronological development
candidate, but no model outcomes were computed. It is one operator/source cluster and is not yet an
independent confirmation dataset. See `research/scoped_method/ELEXON_SOURCE_FEASIBILITY_20261107.md`.

**Updated interpretation:** the atlas contains a real positive F8 opportunity when a strong
challenger is known in advance. The best tested solution is conventional fixed deployment, and the
information needed to choose it prospectively is not identified by the F8 labels alone. The user
requested distinct method objective therefore remains open; do not recast this baseline result as a
novel method claim. Any next method experiment must first specify a prospectively observable signal
that selects the F8 regime and beat both CAMS and a calibrated horizon-aware baseline, while
controlling null and reversal harm.

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

## P7s versus published deployment baselines (exposed loss replay)

The previously missing P7s-to-SOTA comparison is now available at
`research/scoped_method/pilots/p7s_vs_sota_loss_replay_20261106/`. This is a loss-only replay on
previously exposed Rialto and OpenML-LDPA episodes. P7s is cheaper than Gated deployment on LDPA
by 57.75 units (paired 95% episode-bootstrap interval `[−79.75,−38.13]`) and cheaper than Xu
acquisition-only by 10.90 `[−19.33,−3.85]`. It costs 46.49 more than Model Picker
`[+35.00,+58.53]` and 43.39 more than Model Selector `[+30.95,+56.35]`; on Rialto it costs 3.85
more than Gated `[+2.45,+5.71]`. Both label encodings are numerically identical.

This resolves the candidate-versus-published-baseline question only under the artificial
prediction/label reconstruction used by this replay. It is not an authentic model-pair prediction
stream, independent real confirmation, or an all-comparator win. P7s therefore supplies no repair
claim or basis for opening a fresh confirmation source. The narrower result against Gated on
LDPA is an exposed diagnostic; stronger applicable selectors remain cheaper.

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
