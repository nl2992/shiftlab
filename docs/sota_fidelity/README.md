# SOTA fidelity programme (started 2026-11-06)

Goal: before any new method search (methods-paper strategy, tracks A/B), confirm exactly how each
named SOTA comparator is built, check the confirmation independently, and only then implement or
correct the ShiftLab port. Every step is recorded here.

## Workflow per method

1. **Retrieve** (subagent): read the primary source in full (proceedings PDF or arXiv, pinned
   version) and the official code if any (pinned commit SHA). Write `specs/<id>.md`.
2. **Check** (independent subagent): re-read the source without trusting the spec; confirm or
   correct every equation, default, assumption and the fidelity-tier call. Write
   `checks/<id>.md`.
3. **Opus review**: the lead session reviews spec + check against the existing ShiftLab code and
   decides: keep, fix, implement, or exclude. Recorded in `LEDGER.md`.
4. **Implement** (subagent): code + CPU-sized tests that reproduce paper-stated numbers or
   identities where possible.
5. **Opus review**: code review and test run before the method enters any comparator pool.

## Fidelity tiers

- **T1 author-native**: the authors' code (pinned) or a line-by-line port validated numerically
  against it.
- **T2 audited mathematical port**: no usable author code; implemented from printed equations and
  algorithm boxes, each line traceable to an equation/section, with identity or numerical checks.
- **T3 common-contract adaptation**: the paper's core rule mapped onto ShiftLab's contract (two
  frozen models, paired loss, hard label budget B, delayed labels, switch cost). Every deviation
  listed. Never described as the authors' algorithm.
- **Inspired-by**: shares an idea only. Must not be called by the paper's name in result tables.

## Spec template (`specs/<id>.md`)

1. Citation, venue, exact version read (URL, arXiv vN, page count), code repo + commit SHA or
   "no official code found" with how it was searched.
2. Native problem and estimand (what is tested/estimated/optimized; null hypothesis; feedback).
3. Exact algorithm: pseudocode with every line tied to equation/algorithm/section numbers. Short
   verbatim quotes (< 15 words each) only for the key definitions; otherwise paraphrase.
4. Hyperparameters and defaults used in the paper's experiments.
5. Guarantee: theorem number, exact assumptions (iid/exchangeability, boundedness, filtration,
   predictability, dependence), and what it does *not* cover.
6. Mapping to ShiftLab's deployment contract; achievable tier (T1/T2/T3) and every deviation.
7. Existing ShiftLab code: file:line, what matches, every discrepancy, current honest tier.
8. Paper-stated numbers or identities usable as reproduction tests.
9. Open questions / anything not verified (mark UNVERIFIED explicitly).
