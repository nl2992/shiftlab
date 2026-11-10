# Paper 3 programme mandate (condensed)

Source: user "ShiftLab Paper 3 — Master Autonomous Research & Implementation Prompt", 2026-11-09.
Branch `research/paper3-safe-budgeted-intervention-2026-11-09`, worktree
`ICML/shiftlab-paper3-2026-11-09`, rooted at origin/main `8af33afe`.
No result or novelty is claimed in advance. Suggested algorithms and the 2.5% stretch target are
hypotheses, not findings.

## Question
Budgeted information acquisition and safe interventions under distribution shift: joint budgets for
labels, compute, switching, retraining and intervention. Paper 1 (EQSDp + late-label cutoff) and
Paper 2 (NAD) work must not be altered or claimed as Paper 3's contribution; they are comparators.

## Four candidate workstreams (portfolio, not four assumed novelties)
- **A** joint action-conditioned value of information: A0 belief-state planner (baseline, not novel),
  A1 queue-aware VOI (QVOI), A2 risk-envelope two-law controller, A3 dual-price controller,
  A4 learned continuation value with external gate, A5 ranking-reversal lookahead.
- **B** future economic payback certification: reproduce the reversal impossibility
  (`docs/switching_current_regime_evidence_v1.md`); B0 classic hurdle, B1 bounded-drift envelope
  (already in `docs/switching_mechanism_screen_v1.md`, not novel alone), B2 adaptive batch with
  valid optional continuation, B3 dwell-time certificate, B4 lower/upper bounds in (B,d,h,Delta,k).
- **C** dependence-aware failure atlas + decision-ranking inversions (alarm metrics vs economic rank).
- **D** cross-stream transfer of monitoring/acquisition decisions to unseen streams/families,
  strict leave-family-out; GPU allowed (RTX 4060 Laptop, 8 GB).

## Contract (Phase 2)
Rounds t=1..T. Two frozen policies, losses ell_t(0), ell_t(1) in [0,1] on a common outcome;
Z_t = ell_t(0) - ell_t(1) (>0 favours challenger). At the start of t release labels with
available_time <= t; choose action a_t, query q_t, optional compute u_t from observed history and
independent randomisation only. Query cost booked at request time; feedback from request t arrives
at t+d_t; pending labels count against budget B pathwise. a_0 = 0.
J(pi) = E[sum ell_t(a_t) + c_q sum q_t + k sum 1{a_t != a_{t-1}} + c_compute sum u_t + c_retrain N_retrain].
Report separately: global-null false promotion, current-regime value, future payback, intervention
safety, dynamic regret. Hindsight oracles are unattainable diagnostics, labelled as such.

## Hard rules
- No simulator truth (change points, regime, potential outcomes, future labels) in learner inputs.
- Budget is pathwise; pending queries reserved at request time.
- Comparators labelled NATIVE_SOURCE_FIDELITY / DOCUMENTED_ADAPTER / IN_HOUSE_HEURISTIC; equal,
  documented dev-only tuning budgets; record configs tried and wall-clock.
- Seeds: smoke < dev < model-selection < confirmation, disjoint registered ranges. Confirmation
  opened once, after freeze. Every real stream in `data/c4_sealed` and `data/saes_dev` is already
  exposed by Papers 1/2: classify as exploratory/dev-exposed.
- Ledger every attempt (`05_EXPERIMENT_LEDGER.jsonl`), keep negative results
  (`05_NEGATIVE_RESULTS.md`). Never fabricate numbers, proofs, reviews or citations. A manual
  checklist audit is labelled MANUAL_FALLBACK, not "ARIS ran".
- Effect grading (user standard): substantial >=10%, meaningful ~3-10% with CI excluding 0,
  small ~1-3%, negligible <1%. Thresholds are interpretive, not pass/fail gates.
- PaperBanana is required for research visuals; if unavailable, log it and keep numeric tables.
- Missing component? `git grep` all refs (incl. origin/*) and port with a source-commit citation
  before rewriting. Do not modify other branches.
- Do not run `ruff check --fix .` repo-wide; lint only paper3 paths.
- Environment: `../shift-research-starter/.venv/Scripts/python.exe`, `PYTHONPATH=src`,
  `OPENBLAS_NUM_THREADS=1`. Long runs: resumable scripts launched detached.

## Settled findings not to re-run without a new mechanism
Deadline alignment = standard POMDP control (g1 kill doc). Costed query+act has prior art (Atan &
van der Schaar 2016; Chick et al.; Cheng et al. ICML 2023; Drift2Act). Fixed calendar is exactly
optimal at tight risk (alpha .05, B<=4; risk-approx worktree `2bd2e8e`); joint planner gap
0.7-1.2% at alpha .10 B=4. Free labels worth <=5.3 units to tuned Wald (SAES). 12 next-method
mechanisms tie tuned Wald. Multi-model BCR ties K-Wald. Failure Atlas v2 headline numbers need the
DISCERN variance/psi_E fidelity fix and dependence-safety caveats before reuse.
