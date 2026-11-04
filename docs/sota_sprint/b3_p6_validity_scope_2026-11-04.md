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

### Code-path correction (2026-11-04)

The last sentence above overstates the sample-size issue. Inspection of `run_p6` shows that every
test which actually fires uses the deterministic count `n = min(budget, 50)`: it fires when 50
labels have been released, or when the request budget is exhausted and every issued label has
released. If fewer than `n` labels are queried by the horizon, no test fires and no promotion is
possible. Thus P6 does **not** run its binomial test at an endogenous random terminal count. The
probability that the test fires can depend on query availability, but this alone does not invalidate
a fixed-`n` test under a suitable conditional null.

## Earlier assessment (superseded below)

The initial assessment in this section was written before the exact `run_p6` firing condition was
traced. Its random-terminal-count concern and open-filtration conclusion are superseded by the
corrections below.

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

**Superseded by the code-path and filtration correction below:** the test count on a path where it
fires is fixed, so the later-availability sample-size concern stated above does not apply to this
implementation. The unresolved issue is whether P6's exchangeability assumption is strong enough
for the exact binomial tail, and whether the stronger P3b conditional null transfers to the selected
signs.

### Sufficient conditional-null route

The code-level count result above gives a simple validity condition. Let `I_j` be the indicator
that the `j`th queried disagreement favors the challenger and `n=min(budget,50)`. Suppose each
queried sign, conditional on the release history and all side information available before that
sign is revealed, satisfies
`P(I_j=1 | history, selection information) <= 1/2`. Query selection must be predictable and
conditionally independent of the unrevealed sign, as in the P3b setup. Sequential coupling with
uniform random variables then upper-stochastically dominates the first `n` selected signs by
`Binomial(n,1/2)`. If fewer than `n` labels are queried, P6 does not test; padding such paths with
failures also preserves the upper-tail bound. Therefore the single exact binomial rejection event
has probability at most `.05` under this stronger conditional null.

The published protocol states exchangeability, which does not imply this condition. For example,
let all `n` signs equal one latent fair Bernoulli variable: the signs are exchangeable with marginal
success probability `1/2`, but the all-success tail has probability `1/2`, not `2^-n`. So the exact
binomial test is not justified by exchangeability alone.

For P3b's stronger null, the selected-sign implication follows as follows. At each event `t`, the
fixed-delay null bounds `E[D_t | side information through release, excluding Y_t] <= 0`. The
issue-time query draw is conditionally independent of `Y_t`, and the disagreement indicator and
query decision are predictable from that side information. On a queried disagreement,
`D_t in {-1,+1}`, so `P(D_t=+1 | side information, query issued) <= 1/2`. The fixed common delay
preserves event order. Conditioning successively in release order therefore gives this same bound
for each queried sign conditional on earlier queried signs and current selection information.
Sequential coupling then bounds the probability of a binomial upper-tail crossing by the fair
`Binomial(n,1/2)` tail. If fewer than `n=min(budget,50)` labels are queried, the code does not
promote; equivalently, pad the missing outcomes with failures, which cannot increase the upper
tail. Thus the one-shot test has false-promotion probability at most `.05` under the P3b
fixed-delay conditional null and predictable, outcome-independent query randomization.

This is a scope-specific proof, not a guarantee from exchangeability alone. It is still not a
repeated-testing or real-data calibration claim; deterministic archived streams remain descriptive.

## Provenance and next step

The original B3 runner hash is still unrecovered. The saved arrays support arithmetic replay, not
full runner-to-row attribution. A claim tied to those archived outcomes still needs the exact
runner (or a newly registered replay) and matched query budget, delay, costs, and estimand. This
audit corrects the P6 null and counterexample scope; it does not make P3b a surviving method lead.

## Sources in this repository

- Current implementation: `scripts/promising_directions/b3_real_data.py`, `p6_reject` and `run_p6`.
- Protocol: `docs/promising_directions/protocols/B3-real-data-certified-switching.md`.
- Conditional-null statement: `docs/promising_directions/05_PAIRED_CERTIFICATION_THEORY.md`.
- Historical repeated-rule counterexample: `../shiftlab-retrospective-audit-2026-11-01/docs/retrospective_audit_2026_11_01/31_P6_BATCH_VALIDITY_SCOPE.md`.
