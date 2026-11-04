# B3 P6 validity scope audit — 2026-11-04

## Finding

There are two different procedures called P6 in the archived work. The 5.3876% boundary-null
counterexample applies to the old repeated `n=25` mean-threshold rule that resets and retests. It
does not apply to the current `scripts/promising_directions/b3_real_data.py::run_p6` procedure.
The current procedure tests once, after at most 50 released queried disagreement labels, and never
tests again or rolls back.

## What the current code fixes

`run_p6` issues queries on disagreements using the public uniform draw and a pacing rate based on
time, remaining budget, prior rate, and the count of free disagreements. Neither the query rule nor
the 50-label cap reads queried label signs. The test is a one-sided exact binomial upper-tail test
against success probability 1/2. When the budget is exhausted, it waits for all issued labels and
uses the resulting count (up to 50). Thus there is no repeated-testing/rollback multiplicity in this
implementation. The budget-exhaustion sample count is determined by the query/availability path,
not by the observed signs.

## What is and is not established

The protocol states exchangeability of disagreement outcomes as P6's validity assumption. A
different sufficient route would be to establish, conditional on the complete sign-blind selection
path and relevant free information, a sequential upper bound of 1/2 on each selected sign's success
probability. Then the fixed-count upper tail is dominated by `Binomial(n, 1/2)`; a single test is
conservative without requiring iid signs.

That alternative proof is **not yet established from P3b's written conditional null**. P3b's
fixed-delay null conditions each event on side information available through its release, while
P6's terminal count can depend on later disagreement/query availability over the rest of the
episode. The current code is sign-blind, but sign-blind selection alone does not show that
conditioning on the full selection path preserves the per-sign conditional bound. Nor do
deterministic archived real streams instantiate a stochastic null. Therefore do not describe
current B3 P6 as invalidated by the 5.3876% example, and do not yet claim it has a proven
conditional-null guarantee under P3b's null. Its stated exchangeability assumption remains the
supported scope unless a filtration argument or stronger assumptions are supplied.

## Provenance and next step

The original B3 runner hash is still unrecovered. The saved arrays support arithmetic replay, not
full runner-to-row attribution. A valid comparator claim additionally needs the exact runner (or a
newly registered replay), a proof of the P6 stopping/selection condition under the intended null,
and matched query budget, delay, costs, and estimand. This audit corrects the counterexample scope;
it does not make P3b a surviving method lead.

## Sources in this repository

- Current implementation: `scripts/promising_directions/b3_real_data.py`, `p6_reject` and `run_p6`.
- Protocol: `docs/promising_directions/protocols/B3-real-data-certified-switching.md`.
- Conditional-null statement: `docs/promising_directions/05_PAIRED_CERTIFICATION_THEORY.md`.
- Historical repeated-rule counterexample: `../shiftlab-retrospective-audit-2026-11-01/docs/retrospective_audit_2026_11_01/31_P6_BATCH_VALIDITY_SCOPE.md`.
