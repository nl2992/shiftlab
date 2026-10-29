# Delayed feedback in online multiple testing: novelty boundary

**Date:** 2026-10-29. **Status:** primary-source theorem-scope audit; no new method claim.

## Source and inspected results

Lu, Huo, Ren, Wang and Zou, “Feedback-Enhanced Online Multiple Testing with Applications to
Conformal Selection,” *Journal of Machine Learning Research* 27(186), 1–86 (2026). I inspected
the official JMLR paper and its model, feedback definitions, Theorem 3, Theorem 7, and Theorem 9.
The methods process a stream of hypotheses, issue a rejection decision, then use the revealed
binary truth labels—available immediately or after a fixed delay, with full or rejection-only
bandit feedback—to sharpen the online FDP estimator and recycle alpha wealth.

Theorem 3 gives online mFDR control under conditionally super-uniform null p-values and online FDR
control when null p-values are mutually independent and independent of non-null p-values, together
with the specified monotonicity condition. Theorem 7 gives the corresponding adaptive-GAIF results.
For locally dependent p-values, Theorem 9 gives mFDR control under their finite-lag dependence
definition. Feedback can be used to remove the alpha charge for hypotheses confirmed non-null and
reallocate it to future tests. This is a direct prior for delayed feedback, repeated testing, and
recycling statistical budget; none of those ingredients is new for ShiftLab.

## Consequence for ShiftLab

Any acquisition rule that saves statistical budget when a delayed outcome confirms a previous
candidate's value must compare against GAIF/Ada-GAIF-style feedback recycling, with the closest
available feedback pattern and delay. Where assumptions permit, the online FDR result is also a
strong comparator for repeated promotion decisions. A generic delayed-label alpha-wealth rule,
or a simulation showing it beats no-feedback spending, is therefore not a contribution.

The guarantees do not directly imply the target guarantee. FDR and mFDR control average false
rejections relative to the number of rejections; the ShiftLab safety event is that at least one
false promotion occurs over the run, even if it is later reversed. The paper's p-value assumptions
also differ from a full-history causal null with adaptively selected queries, serially dependent
paired losses, and one shared observation budget. Its hypothesis labels are eventually revealed;
it does not optimize economic deployment utility, transaction/switch costs, or rollback timing.
These differences preserve a comparison obligation, not evidence of a novelty gap.

Thus the remaining G1 target must show a structural improvement in net switching utility or delay
regret over a comparator that combines feedback-aware online testing (or a valid FWER/alpha-spending
version under the actual dependence) with the best available economic switching controller, under
the identical pathwise query cap and pending-label chronology. If the desired any-false-switch risk
can be obtained by routine alpha spending across GAIF tests and this controller composition, the
candidate is a no-go. If a result relies on current value after a regime reversal, it must use
post-reversal evidence or an explicit persistence model; historical confirmation remains distinct
from present benefit.

## Decision

This audit closes feedback-based online alpha recycling as a generic contribution and strengthens
the repeated-promotion baseline. It does not solve the full finite-sample two-law economic problem.
G1 remains open only for a theorem-level advantage against the feedback-aware, risk-matched
composition above; no efficacy or real-data study is opened by this audit.

## Provenance

- Official source: [JMLR article](https://jmlr.org/papers/v27/25-2123.html) and
  [full PDF](https://jmlr.org/papers/volume27/25-2123/25-2123.pdf).
- Cached official PDF: `outputs/switching_source_audit_v1/lu_etal_feedback_enhanced_online_multiple_testing_2026.pdf`.
- SHA256: `8C9002A68DD63B732731061A606388A48ACE1A83149D355BF88F0AACF3D8BCEF` (1,301,120 bytes).
- Theorem-scope audit, not an independent reproof.
