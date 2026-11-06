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
