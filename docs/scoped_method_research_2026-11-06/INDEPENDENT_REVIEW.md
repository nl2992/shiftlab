# Independent critical review

## Reviewer and scope

This is the read-only internal review returned by the `independent_critic` research subagent on 2026-11-06. It inspected the saved reports and audits. It is not an external human review, independent rerun, or proof review.

## Decision

**`BENCHMARK_OR_CASE_STUDY_ONLY`**.

| Gate | Review status | Basis |
|---|---|---|
| C1 Diagnosis | PARTIAL | Retrospective 10-late/5-cluster and 16-reversal/7-cluster cohorts; late contrast NOT_SUPPORTED; exposed data and corrected-comparator replay caveat. |
| C2 Explanation | PARTIAL | Useful ablations, but RMM does not beat matched SRR on late real episodes; E_rb gain tracks alpha/start-grid, with non-binding horizon gate. |
| C3 Repair | FAIL | No frozen new repair or demonstrated advantage over strongest matched/corrected baselines. |
| C4 Real confirmation | FAIL | No untouched independent real cohort; current streams are development-exposed. |

## Critical limitations

The adaptive-range predictability defect affects 130 runs / 411 policy entries. Corrected Atlas replays exist, but affected Sprint 2 comparisons remain provisional until same-seed replay completes. The worktree starts at `c13f232edd72f7d56c286aba5c3cd68e0315b68b`, one commit beyond the charter's `origin/main` SHA, and preserves 22 pre-existing dirty/untracked user changes in an isolated worktree. Do not conflate the source checkout with the charter revision.

## Smallest recommendations

1. Complete and audit corrected same-seed Sprint 2 replays.
2. Freeze one rollback ablation with matched alpha/start-grid and two-sided SR/CUSUM.
3. Obtain an authentic, untouched chronological real-source evaluation with source-level uncertainty.
4. Obtain human/external review before a methods-paper claim.

The internal review does not itself establish that these steps will yield a publishable method.

## Lead's append-only update after corrected replay

The replay step is complete, so recommendation 1 above is superseded. The corrected evidence is summarized in `CORRECTED_REPLAY_AUDIT.md`: two existing C2/C6 variants show about 7.4–7.8 lower cost than Gated+front on two late synthetic cells without more promotion, but this is exposed and is accompanied by 12.6–21.6% promotion on two out-of-class marginal-null stresses. Front-loaded and tuned pacing are indistinguishable in the five-source exposed real replay; source-level intervals are wide, and C2/C6 add no clear real-data benefit. These findings do not change the benchmark-only decision. E_rb still lacks a matched start-grid/two-sided SR/CUSUM screen. An OPSD/Binance task freeze exists, but the required method freeze/opening runner does not; no holdout was accessed. Tests were rerun at c66185 (171 passed in isolated groups; exact commands and timing in `EXPERIMENT_LOG.md`). This lead update is not a second independent reviewer opinion; the original reviewer read the earlier package.
