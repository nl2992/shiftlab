# Claim-closure next step — 2026-11-04

## Current decision

Continue the retrospective benchmark and failure-analysis manuscript path, but treat its publication-level differentiation as unresolved. The evidence map has credible, bounded results: a synthetic estimand-separation demonstration (C1), a no-detected-advantage comparison for the direct paired-cost monitor (C2), conditional synthetic component gains (C3–C4), and a mixed integrated confirmation with important failure modes (C6). The real-data studies address separate tasks and information contracts (C7–C10). Together these support careful reporting; they do not yet prove that the combined empirical contribution is distinct from prior work.

No current method lead warrants another tuning or confirmatory experiment. The P7s comparison loses to the best implemented suite method on all five exposed streams; the versioned budget/reversal screen and restart-mixture pilot also failed their frozen gates. These are stop decisions for those candidate families, not proof that no future method can work.

## Finite next action

Complete a claim-to-source closure audit against [`manuscript_draft_v0.md`](manuscript_draft_v0.md), using [`claim_evidence_map_v1.md`](claim_evidence_map_v1.md), [`sota_fidelity_matrix.md`](sota_fidelity_matrix.md), and [`comparator_scope_decision_v1.md`](comparator_scope_decision_v1.md):

1. Extract each manuscript claim and numeric result into a finite ledger.
2. For each claim, record the nearest primary sources, the exact estimand and feedback/information contract, the artifact that supports the claim, and the permitted wording.
3. Mark each comparator as task-compatible, scope-only, or unresolved, with a source-backed reason. In particular, include SMCS, CC-SMCS, and SERPANT when assessing sequential selection/ranking claims.
4. Ask whether any supported empirical finding remains both reproducible and materially differentiated after those comparisons. If yes, state that finding narrowly and identify its supporting artifacts. If no, narrow to a replication/failure-analysis report or stop the publication path.

This is a review/traceability task; it does not authorize a new experiment or a novelty claim by itself. Reopen method work only if this audit identifies a precise uncovered contract and a testable theorem or empirical distinction.

## Prior-art boundary added

Gu et al., [“Anytime-Valid Inference for Online Ranking of Large Language Models,” ICML 2026](https://proceedings.mlr.press/v306/gu26l.html), use pairwise e-processes for familywise error control at any monitoring time and an adaptive tournament sampling strategy, with a top-k extension. This closes broad claims to anytime-valid adaptive pairwise ranking as a new idea. Its LLM preference-ranking target differs from ShiftLab's paired predictive-loss and deployment decisions; that difference is a comparison obligation, not evidence of novelty.
