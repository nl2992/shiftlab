# Repository state audit

**Recorded 2026-10-27, loop tick 1.** Read-only inspection of the ShiftLab checkout at
`C:\Users\nigel\OneDrive\桌面\ICML\shift-research-starter`.

## Remotes and synchronisation

| Item | State |
|---|---|
| Remotes | `origin` → `https://github.com/nl2992/shiftlab.git` only. **There is no GitLab remote** in this checkout, so GitHub/GitLab synchronisation cannot be checked from here. |
| Active branch | `research/phase-progress-2026-10-27` |
| Latest commit | `c0f84af` "Finalise stratified-monitor phase report at checkpoint B" (2026-10-27) |
| Ahead / behind the pushed branch | 42 ahead, 0 behind `origin/research/phase-progress-2026-10-27` (whose tip is `42709d7`) |
| Ahead / behind `origin/main` | 42 ahead, 1 behind. The one commit is `2e5451a`, the merge of PR #1, which brought the branch up to `42709d7` into `main`. `main` is not an ancestor of HEAD only because of that merge commit; there is no content divergence beyond it. |
| Unpublished work | The 42 local commits from `415f888` to `c0f84af` (2026-10-27): WP1 gated comparison (S0–S3), WP2 stratified prescreen, WP3 data-efficient prescreen, ADG prescreen, WP4 EIA validity, the exit ledger, and the final phase report. **None of this is on GitHub.** |
| Working tree | Clean except the new untracked `docs/research_refinement_v1/` (this folder). |

## Priority files named in the brief

All 11 exist:

| File | Lines |
|---|---:|
| `docs/research_charter.md` | 152 |
| `docs/next_phase_plan.md` | 378 |
| `docs/closest_prior_work.md` | 56 |
| `docs/methods_and_assumptions.md` | 280 |
| `papers/shiftguard_unified/decision_gate_report_2026-10-26.md` | 45 |
| `papers/shiftguard_unified/integrated_efficacy_confirmation_results_v1.md` | 56 |
| `papers/shiftguard_unified/novelty_audit.md` | 161 |
| `papers/shiftguard_unified/sota_fidelity_matrix.md` | 113 |
| `papers/shiftguard_unified/claim_evidence_map_v1.md` | 33 |
| `papers/shiftguard_unified/publication_scope_decision_v1.md` | 48 |
| `papers/shiftguard_unified/manuscript_draft_v0.md` | 205 |

**Newer than the brief's reading list:** the 2026-10-27 phase record, which the brief does not
mention. It postdates the 2026-10-26 decision gate and adds a second, narrower NO-GO:
- `docs/phase_report_stratified_monitor.md` (checkpoint B);
- `docs/algorithm_search_exit_ledger.md`;
- `docs/gated_monitor_comparison_results.md` (WP1 S3);
- `docs/eia_real_data_validity_results.md` (WP4);
- `docs/stratified_growth_prescreen_results.md` (WP2);
- `docs/data_efficient_edetector_prescreen_results.md` (WP3);
- `docs/agent_goal_stratified_monitor_phase.md` and `docs/agent_goal_sota_benchmark_supplement.md`.

Phase A2 must treat these as the most recent evidence.

## Code and test footprint

- `src/shiftlab/`: `core/`, `data/`, `dive/` (the decision-harm work, including this phase's
  gated monitor, orientation replay and EIA modules), plus top-level `benchmark.py`, `methods.py`,
  `monitoring.py`, `metrics.py`, `streaming.py`, `synthetic.py`, `learner.py`, `diagnostics.py`,
  `plots.py` and `decision_harm_experiment.py`.
- `tests/`: 165 entries.
- `papers/`: `paper1_decision_drift`, `paper2_adaptive_conformal`,
  `paper3_cost_aware_adaptation` and `shiftguard_unified`.

**Full test suite:** TEST_STATUS_PLACEHOLDER

## Tooling for this refinement

- **ARIS:** commit `18bceb3`, installed as described in `LOOP_CONTROL.md`.
- **Independent cross-model reviewer:** Codex CLI is signed in but over its usage limit until
  2026-11-02 01:08. **No independent review has taken place yet.**
- **PaperBanana:** no working configuration in the pinned environment, as of the phase report.

## Implications for the refinement

1. Treat the 42 unpublished commits as evidence for this audit. A reviewer reading GitHub would
   not see them; any external review must be given the relevant local files.
2. There are two prior NO-GO decisions, and both must be respected: 2026-10-26 (unified
   algorithm) and 2026-10-27 (Paper 1 monitoring algorithm).
3. Synchronising GitLab is impossible from this checkout. Ask the user whether a GitLab mirror
   exists.
