# Core streaming adapters — implementation checkpoint

Implemented local streaming adapters for direct IPW betting, PPE factors, fixed
start mixtures, reliability-gated proxies, block PPRM, predictable PPRM reliance,
CUSUM, frozen deployment, greedy/hysteresis selection, certification-triggered
switching, rollback, and contextual cost selection. These are component adapters,
not a completed baseline reproduction or SOTA comparison.

The learner constructor accepts labeled source calibration, public events and
arrived feedback only. It never accepts a SyntheticWorld or evaluator truth.
Source calibration is paid/training information and must be charged consistently
in the eventual experiment manifest. Q1 uses a source empirical loss plus a
Hoeffding allowance; its IID coverage does not automatically extend to G3/G4.
Q2 and Q3 evidence uses signed incumbent-minus-challenger decision losses and
Bonferroni across two challengers. A fixed global bet is used; changing query
propensities does not change the bet as a function of current covariates.

PPE reuses the audited factor correction and nonnegativity floor. Queried factors
are resolved through the existing event-order buffer; zero-propensity events after
budget exhaustion contribute factor one. Missing queried labels stall the prefix.
The multi-start mixture has fixed starts and weights. These structural safeguards
do not establish a conditional null for every generated world or auxiliary proxy.
Reliability gating and growth/variance query rules are LOCAL_HEURISTIC extensions.

PPRM reuses the existing batch estimator and CM-EB monitor, with fixed or
history-predictable reliance. The current block assembly permits only uniform
querying. Empty labeled/unlabeled blocks are skipped, and a hard cap can truncate
a block. Source/target independence, random block sizes, cap truncation, dependence
and missing feedback require further contract review before validity claims or
matched confirmatory comparisons. No PPRM source theorem is transferred here.

CUSUM thresholds require separate calibration. Contextual cost selection is
explicitly CAMS-inspired; it is not a reproduction of CAMS or its regret theorem.
Rollback uses current empirical economic information separately from historical
certification evidence and remains an unvalidated S10 hypothesis.

Nineteen focused tests passed: all thirteen adapter modes process independent
random delayed labels under a hard cap, five querying rules obey their positivity
floor, and the PPRM adapter refuses nonuniform selective querying. Tests establish
interface and numerical behavior only. No registered candidate experiments were
launched at this checkpoint. The full 500–1,500 configuration screen, source
adapters for other mandatory families, tuning, calibration and independent
confirmation remain outstanding.
