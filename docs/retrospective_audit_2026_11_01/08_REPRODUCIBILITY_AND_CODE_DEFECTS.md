# Confirmed audit repairs — 2026-11-01

## AUDIT-TEST-001: clean-worktree smoke test depends on ignored output

At base e74fdc3, tests/test_atlas_mechanism_check.py invokes the runner without --kappa. The default reads outputs/failure_atlas_v1_cycle3/family1/state.json, absent from a clean checkout. The five-suite Atlas run therefore produced 109 passed / 1 failed (exit 1, 332.98s), with FileNotFoundError at runner line 143. The runner already accepts an explicit --kappa; the test now supplies .05 and asserts that recorded value. Direct rerun: 1 passed in 12.25s. This repairs test portability, does not alter production defaults, and is not a scientific efficacy rerun. No historical output invalidated.

## AUDIT-REPORT-001: false missing-comparator statement

At base e74fdc3, scripts/run_failure_atlas_loop.py:739 always appends “the hard-budget pacing comparator is still missing” whenever R6 wrappers load. Local cycle5 family3 and family4 reports contain that sentence while recording hard_budget_pacing among loaded methods. Current generator now emits the missing sentence only if the recorded method list lacks that method, falling back to available methods when no run list exists. No numerical result, comparator implementation, or protocol was changed.

A fixture renders a real Runner summary with controlled available/recorded method lists. Before the fix, the present-method case failed; the absent-method case passed. After the fix both passed (2 passed in 3.35s); extended cases also test precedence of recorded methods over currently installed methods. The initial fixture needed its r6_status dependency mocked before it exposed the intended assertion. Historical summaries stay intact; this document is their additive erratum for the missing-comparator wording only. Presence of a name does not verify source fidelity or completeness of the method's scientific evaluation.

The repairs are MINOR reproducibility/editorial defects. They do not establish that all Stage-0 or programme defects have been audited. Whole relevant Atlas suites are being rerun after the test repair; new report regressions and audit tests are also running. G06 and G17 remain unsigned. Reviewer: lead INTERNAL_ONLY.

Extended report regression cases plus the audit suite and mechanism smoke test: 13 passed in 11.58s, exit 0. Full five-suite Atlas rerun still pending.
