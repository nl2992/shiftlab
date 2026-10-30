# A1 registered protocol: exact joint vs fixed-calendar separation under the causal-null risk game

Registered 2026-10-30 before execution. Status: development kill test (not confirmatory).
Solver source: branch `research/risk-preserving-switching-approx-2026-10-29` commit `2bd2e8e`
(`src/shiftlab/dive/causal_switching_game.py`, `scripts/decompose_switching_calendar_gap.py`).
The runner must refuse to run unless the solver checkout is at exactly that commit with those two
files unmodified, and must record their sha256.

## Question

Under the repository's exact two-law contract (alternative-law expected cost; worst-case
causal-null false-promotion risk <= alpha with root-mixture calibration; pathwise hard budget B;
release delay d; reversible promotion/rollback), is there a material value gap between

- J: the exact joint planner (`FirstPromotionDecomposedGame`, calibrated total cost), and
- C*: the best fixed query calendar with exactly optimised risk-constrained switching
  (`CalendarOpportunityGame`, minimised over every calendar of size <= B; slots may be skipped)?

Why calendar is the separable comparator: if the acquisition rule may depend on the full released
history, it can reconstruct the deterministic deployment state, so "history-adaptive acquisition +
optimal switching" coincides with J (see 04_EXACT_ORACLE_SEPARATION.md, Lemma 1). The only
information-matched separations are therefore (i) non-adaptive acquisition timing (calendar) and
(ii) acquisition optimised for a different objective. (ii) is classical value-of-information
misalignment and is not tested here.

## Grid (fixed before execution)

- Primary: T in {6, 7, 8}; B in {2, 3, 4}; d = 2; transition (both ways) in {1/20, 1/10};
  emissions in {(1/10, 9/10), (1/50, 49/50)}; alpha in {1/20, 1/10}; switch cost in {1/10, 1/2};
  query cost 1/100; prior1 and any other model field set exactly as in the source
  `T8_B4_CALENDAR_RESULTS_V1.md` configuration (recorded by the runner). 144 cells.
- Secondary: same with d = 1 (144 cells), run only if primary finishes within budget.
- Adversarial search: 200 instances at T = 6, B = 3, d = 2 with parameters drawn uniformly from a
  rational grid (transition in {1/20..9/20 step 1/20}, emission accuracy in {11/20..49/50},
  alpha in {1/20, 1/10}, switch cost in {1/20, 1/10, 1/4, 1/2, 1}, query cost in {1/100, 1/20,
  1/10}), seed 20261030. Reports the maximum relative gap found.
- Compute cap: 2 worker processes, 3 wall-clock hours total. Cells not finished are reported as
  not run; no cell is dropped after seeing its value.

## Primary metric and decision rule

Relative gap g = (C* - J) / J per cell, computed exactly in rationals where the solver provides
them. Also record the absolute gap, best calendar, solve times, and node counts.

- KILL (joint-acquisition method claim closed): max g < 0.05 over all completed cells AND, for
  every fixed (B, d, transition, emission, alpha, cs), g does not increase monotonically with T
  across T = 6, 7, 8 by more than 0.01 in total.
- CONTINUE to A2 theory: any cell with g >= 0.10 (the programme's practical threshold), or a
  monotone increase with T of more than 0.02 in some parameter slice.
- Otherwise: INCONCLUSIVE; record and choose the cheapest decisive follow-up.

Sanity checks (must pass or the run is invalid; run with the source documents' exact parameters,
independent of the grid): J <= C* in every cell (tolerance 1e-12); reproduce T=6, B=3, d=2, transition 1/10, emissions (1/10, 9/10), alpha 1/10, cq 1/100, cs 1/10
cost 22083523/7812500; reproduce T8_B4 gap 6744087/781250000 for transition 1/10 emissions
(1/10, 9/10) if that cell is in the grid configuration.
