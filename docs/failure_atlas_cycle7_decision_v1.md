# Cycle 7 decision: retain the cost finding; repair the safety and scope gaps

2026-11-01. Cycle 7 is complete. Status: **not accepted under the registered full claim**;
useful acquisition-cost evidence survives. No confirmation run is warranted for unchanged DSS.

## Evidence and acceptance

The frozen evaluation used T=1000, 200 fresh validation seeds [290000,290200), 16 primary
failure cells, 96 unique neighbouring cells and the full 32-cell dependence-null grid.
There were 102 unique cost cells and 281,600 method runs. The seven gated comparators
included the Markov and gap-10 baselines. Four nongated R6 adaptations were supplementary.
All 147 relevant tests passed; smoke execution and the deterministic artifact audit passed.
The 31-minute execution preserved source hashes, the manifest, raw seed chunks and runtime
versions. Final confirmation seeds were not used.

| Criterion | Result | Meaning |
|---|---|---|
| A1 cost superiority | PASS | 13/16 cells have upper paired CI below -.01; equal-cell mean difference -.03772, 95% CI [-.04068,-.03476] |
| A2 no harm nearby | FAIL | 14/16 parent neighbourhoods pass; two have adverse mean differences |
| A3 registered safety | FAIL | Independent and moderate-dependence absolute checks pass; every rho=.8 relative comparison fails |
| A4 acquisition mechanism | PASS for whole acquisition component | Uniform acquisition removes 155.5% of the aggregate cost gain; this is not evidence that the two new rules cause the gain |
| A5 mild novelty | CONDITIONAL prior audit only | Existing absence search concerns the unchanged combination; empirical new-rule attribution remains weak |

The cost result is not universal dominance. Two primary cells are significantly worse than
their best registered comparator: the long-delay family-1 cell (+.01283 per round) and the
rho=0, earlier-onset, B/T=.1 family-3 cell (+.06451). A third primary cell does not clear
the margin. Their full IDs, comparators and intervals are retained in the result tables.

The two failing neighbourhood means are +.01539 [.01391,.01687] and
+.03867 [.03444,.04290]. They belong to those long-delay and higher-budget parent cells.
These are recorded failures, not grounds to remove those settings from the historical test.

Across the 96 unique neighbours, the descriptive equal-cell average is -.00880
[-.01000,-.00759] per round. This promised secondary aggregate was missing from the
original runner report and was computed separately after review; it does not override
the two failed per-parent A2 checks. Computation and status are recorded in
`docs/failure_atlas_cycle7_provenance_v1.json`.

For B/T<=.25, observed DSS null frequencies range from 0 to .03 at rho=0 and .01 to .025
at rho=.5; they range from .065 to .39 at rho=.8 and .44 to .975 at rho=.95. The registered
rho=.8 comparison fails in all six budget/delay cells. These are empirical frequencies
with per-cell intervals, not exact nominal guarantees. Markov LR has much lower null
frequencies here but often fails to promote on the primary late/transient alternatives.
Its homogeneous-skeleton approximation also limits its guarantee. Neither method name
establishes unrestricted dependence robustness.

## What the ablations actually say

- Uniform acquisition raises aggregate cost by .05866 [.05547,.06185] relative to DSS.
  Acquisition timing contributes substantially to the observed practical advantage.
- Removing the delay switch raises cost by only .000974 [.000747,.001201], removing
  2.58% of the aggregate A1 gain. This is a small average effect, not the main repair.
- Setting gap=1 lowers cost by .02106 [.01841,.02370] relative to DSS. The gap trades
  speed for reduced dependence exposure; it does not explain the cost advantage.

Accordingly, do not claim that DSS's two additions provide the observed competitive gain,
or that a scoped novelty-search pass establishes a contribution. Known acquisition
ingredients are allowed by the user's objective, but the new part still needs a measurable
practical role and an honest comparison to the existing straddle rule.

## Current usable claim

On the declared synthetic delayed, budgeted switching failure set, frozen DSS improves
mean cost over the best of seven implemented gated comparator adaptations, clears a
.01 paired-CI margin in 13/16 cells, and shows a substantial acquisition-timing effect.
It does not satisfy the registered neighbourhood or strong-dependence safety criteria.
These are fresh-seed validation results after exploratory selection, with unadjusted
intervals. They do not establish performance against all SOTA algorithms or a deployment
recommendation, and they are not final confirmation.

## Next bounded action

**Continue the method search, but do not retune DSS's gap on these validation seeds.**
The next useful prototype should separate acquisition timing from dependence evidence:

1. Investigate evidence that uses the actual query-to-query gaps under a declared binary
   Markov null, rather than treating unequal or adaptive gaps as a homogeneous skeleton.
   Condition on the observed query history, marginalise unobserved rounds, and justify
   the likelihood under predictable acquisition before using a safety label. Compare a
   uniform calendar and the same undecided-only acquisition under the identical evidence.
2. Screen long-delay and higher-budget acquisition behaviour explicitly. The two adverse
   neighbourhoods are required regression cases for a proposed repair, not optional cells.
3. Register a separate development protocol, code/spec manifest and unused seed range
   before running a new prototype. Include the existing straddle, DSS, uniform, Markov
   and strongest applicable gates. Preserve the cycle-7 validation set as exposed evidence.
4. Advance only a useful repaired or narrower candidate to a fresh full-registry validation.
   Then write a separate confirmation protocol if its scoped criteria pass. A new theorem
   is not required; sound assumptions, modest rule novelty and competitive evidence are.

This is a bounded next research question, not an implemented or validated cycle-8 method.
Cycle 7 and all its required comparisons, ablations, audit and decision documentation are
complete. Starting an open-ended new search is not necessary to call cycle 7 finished.

**Bounded follow-up closed:** [fallback diagnostic results](failure_atlas_cycle7_followup_results_v1.md)
record 640 further development runs. Enforcing gap 4 during fallback fixes one moderate-
dependence diagnostic but leaves the stronger-dependence failure and both cost regressions.
Do not promote that patch as a completed repair. No cycle-7 computation remains pending.

## Artifacts and trail

- Full tables: `docs/failure_atlas_cycle7_validation_results_v1.md`.
- Analysis contract: `docs/failure_atlas_cycle7_execution_v1.md`.
- Data: `outputs/failure_atlas_v1_cycle7/validation/{manifest.json,records.jsonl,results.json}`.
- Audit: `deterministic_audit.json` in that directory; mechanical checks only, not a
  cross-family independent integrity verdict.
- Runner: `scripts/run_atlas_cycle7_validation_v1.py`; audit:
  `scripts/audit_atlas_cycle7_validation_v1.py`.
- HKUSTDial/ARIS result-to-claim review is saved separately with native-review limitations.
  See `docs/failure_atlas_cycle7_claim_review_v1.md`; the reviewer independently recomputed
  A1/A2/A4 from the raw records and did not support the full claim. The review identified
  that uniform fallback bypasses the gap check; a separately registered development
  diagnostic is recorded in `docs/failure_atlas_cycle7_followup_diagnostic_v1.md`.

The starting source revision was `e61a3b0` with uncommitted work. Stage commits preserve
that distinction: later commits package work already run; they do not retroactively make
the original execution a clean-HEAD run. The frozen source hashes identify the executed
inputs. Raw outputs stay ignored, with complete tables and audit metadata retained in Git.
The stage commit normalized one baseline file from CRLF to LF. Exact in-memory newline
conversion reproduced its original frozen SHA256; the working file was restored to those
executed bytes and the strict audit passed again. No content or frozen manifest was changed.
The provenance JSON retains both hashes so a future checkout's newline convention is not
mistaken for a method change.
