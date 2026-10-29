# ShiftLab agent guidance

This repository supports a research programme on detecting, measuring, and mitigating decision
harm under distribution shift. Read [the research charter](docs/research_charter.md) and the
relevant paper protocol before changing research code, metrics, or claims. Treat the charter as the
current scientific direction; paper folders and reports record implementation status and evidence.

## Scientific scope

- Keep distributional change `D(P_t, P_0)`, predictive degradation `R_t(f)-R_0(f)`, and decision
  harm `R_t(pi_t)-R_t(pi_ref)` separate. Paper 1 targets the last quantity against an explicit
  frozen or predictably selected reference policy. Shift detectors are sentinels and baselines;
  their alarms alone do not establish harm.
- Paper 1's conditional excess-cost null is a research target, not an established guarantee. State
  the filtration, feedback/label-availability regime, policy predictability, dependence conditions,
  and any adaptive sampling assumptions. An e-process name or implementation does not establish
  validity by itself.
- Keep the candidate contributions distinct: Paper 1 monitors incumbent harm; Paper 2 evaluates a
  frozen candidate's net benefit before promotion; Paper 3 allocates finite label, compute, and
  intervention budgets across information and actions. Each must be independently testable against
  strong baselines. Do not silently turn the existing conformal or retraining baseline studies into
  novelty claims.
- Synthetic oracle truth belongs only to evaluator-side data and must not be visible to learners,
  monitors, or adaptation policies. Real datasets rarely supply causal shift times or application
  utilities; do not infer them from alarms or convenient cost settings.
- CRSP is a retrospective stress-test dataset. Its market dates are not verified causal change
  labels or point-in-time feature publication timestamps. Respect the CRSP execution guide.

## Implementation practice

- Inspect the existing implementation, tests, configuration, data contracts, and Git state before
  editing. Reuse working components; make changes in runnable vertical slices, not placeholder
  architecture. Do not replace working experiments without evidence and a clear reason.
- Preserve event and label-availability semantics, chronological splits, train-only preprocessing,
  provenance, and checksum validation. Represent delayed, missing, out-of-order, or selectively
  sampled feedback explicitly. Paired policy comparisons require both action losses to be
  identifiable from observed outcomes or a stated causal/off-policy design.
- Start with CPU-sized tests and smoke runs. Do not launch full factorial sweeps or large downloads
  by default. Lock hypotheses, thresholds, primary metrics, information budgets, and test windows
  before confirmatory runs; keep tuning separate from final evaluation.
- Never fabricate results, theorem validity, hardware measurements, prior-art conclusions, or data
  acquisition. Record failures and negative results in the relevant research log. Distinguish
  descriptive diagnostics, smoke checks, and confirmatory evidence.
- Use PaperBanana for research visuals, including method diagrams and empirical figures. For
  quantitative plots, derive the data and labels from validated analysis outputs, then inspect the
  exported visual against those source values. If PaperBanana is unavailable in the active
  environment, report that dependency instead of silently substituting another visual generator.
- Run relevant tests and quality checks after changes. Include reproducible commands, exact data and
  code versions, limitations, and a continue/pivot/stop assessment when reporting research results.
- Keep licensed/raw data, credentials, and large experiment artifacts out of Git. Follow the
  repository's data agreements and [cross-device data guide](docs/cross_device_data_access.md).

## Current repository map

The existing `papers/paper1_decision_drift` work is a decision-loss monitoring baseline study;
`papers/paper2_adaptive_conformal` contains supporting conformal baselines; and
`papers/paper3_cost_aware_adaptation` contains adaptation-cost baselines. Their current directory
names are retained for continuity. The research charter defines the candidate paper questions;
existing reports define what has actually been implemented and validated.

## Codex autonomous research lane

This checkout is the independent Codex lane on
`research/risk-preserving-switching-approx-2026-10-29`.
Keep all edits, environments, run state and outputs in this checkout. Never edit,
reset, clean, merge into, or run jobs from the main or Claude worktrees. Do not
reuse their writable environments or output directories. No global skill or hook
installation is required. Read `docs/codex_autoresearch_setup.md` before using
this lane's project-local skills.

Use Ponytail for small reusable implementations, HKUSTDial Supervisor-Skills for
research evaluation and evidence-grounded writing, and ARIS Codex skills for
experiment and review orchestration. Existing scientific protocols and explicit
user scope govern experiments; third-party defaults do not authorize paid jobs,
remote deployment, notifications, publication, or opening confirmation data.
The governing branch mission is [the user research brief](docs/risk_preserving_approx/RESEARCH_BRIEF.md).
Read it and [the initial plan](docs/risk_preserving_approx/INITIAL_PLAN.md) before
research. It supersedes older future-work priorities and any ingredient-only
novelty rejection standard. Preserve historical verdicts and evidence unchanged.
Retain the finite-horizon two-law switching formulation; investigate A, B, then C.
Specify the theorem and audit complete guarantees before candidate implementation.
All branch-local documentation, simulation and commits belong in this worktree.
Record negative results and proof status in the append-only research ledger.
Push only this designated branch. Never merge automatically or open holdouts.
