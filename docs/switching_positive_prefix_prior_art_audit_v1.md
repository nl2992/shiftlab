# Prior-art boundary for positive-prefix query stopping

**Audited:** 2026-10-28. **Question:** does the recovered rule—query again only after a positive prefix, while protecting a terminal promotion decision—constitute a new acquisition method?

## Audited primary sources

| Source | Directly overlapping idea | Material difference from the registered switching game |
| --- | --- | --- |
| Brown and Rutemiller, [“A Sequential Stopping Rule for Fixed-Sample Acceptance Tests” (1971)](https://doi.org/10.1287/opre.19.4.970) | Explicitly considers abandoning a fixed-sample acceptance test after early failures when continuation probability is low and testing cost is high. The paper gives a cost-based continuation rule and examples including Bernoulli data. | Does not state a hidden recurrent regime, changing deployment utility, a hard pathwise query cap with delayed release, or the history-adaptive endpoint causal-null constraint used here. |
| Gould and Pecore, [“Group sequential methods for clinical trials allowing early acceptance of H0 and incorporating costs” (1982)](https://doi.org/10.1093/biomet/69.1.75) | Extends group-sequential designs to allow early stopping for acceptance/futility and includes cost. The source abstract reports lower expected costs than designs without early acceptance. | The tested object is a group-sequential clinical-trial design with classical type-I/type-II operating constraints, not repeated switching under a recurrent latent regime and adversarial conditional null. |
| Hampson and Jennison, [“Group sequential tests for delayed responses” (2013)](https://doi.org/10.1111/j.1467-9868.2012.01030.x), [author manuscript](https://people.bath.ac.uk/mascj/papers/HampsonJennison_2.pdf) | Directly models pipeline outcomes caused by delayed responses, optimizes delayed group-sequential designs, and discusses response-dependent sample-size choices, futility and decision reversals. | Their inferential constraints and fixed statistical hypotheses differ from the paired-query causal-null model and changing HMM-based action utility. Their design already covers the central “delay plus early stopping” motif, so that motif cannot be claimed as new. |
| Naghshvar and Javidi, [“Active Sequential Hypothesis Testing” (Annals of Statistics, 2013)](https://arxiv.org/abs/1203.4626), [full text](https://arxiv.org/pdf/1203.4626) | Formulates dynamic selection of sensing actions based on the current information state, with sampling cost and a penalty for a wrong terminal declaration; gives dynamic-programming bounds and policies. | The hypothesis is static and the error loss is Bayesian. It does not include recurrent regime reversals, a causal conditional-null false-promotion cap, delayed labels consuming a hard budget on request, or deployment switching costs. |

The source-level check therefore rejects novelty of the positive-prefix/futility mechanism itself. It also rejects any claim that adding feedback delay to that mechanism is new. It does **not** prove that the full composed objective has been solved in the literature: the differences listed above are real contract differences, but they are a motivation for an exact equivalence audit, not evidence of a novel algorithm.

## Primary-text addendum — 2026-10-29

The delayed-response source was checked against the full author-hosted 40-page manuscript,
including its formal rule (Section 2.1), canonical-joint-distribution Theorem 1 (Section 2.2),
constrained optimality construction and backward-induction criterion (Section 2.4 and Appendix
8.1), response-dependent group-size extension (Section 3.3), and delayed-response error-spending
construction (Section 4.1). It explicitly treats stopping for acceptance/futility, pending
responses, expected sampling cost and optimization subject to type-I/type-II requirements. The
paper's exact distributional theorem is for its normal-response canonical model; it is not a
theorem for the ShiftLab causal conditional null or recurrent HMM. The full Brown–Rutemiller
primary PDF was also checked: it considers sequential Bernoulli acceptance tests and stopping
after early failures using estimated continuation and abandonment costs, but its cost rule is a
plug-in heuristic, not a robust risk guarantee. The publisher's full Gould–Pecore PDF was not
accessible, so only its abstract is used as corroboration, not as a verified theorem.

The finite ShiftLab policy has an exact reduction to this established futility structure. It
promotes only if the three-label terminal word is `111`; the adaptive rule requests the next label
only while the observed prefix is all positive. On the first zero it stops, and its terminal
decision is then the same no-promotion decision as the fixed three-query test on that tape. The
private `4/5` entry lottery makes causal-null risk `(4/5)(1/2)^3=1/10`; it is standard test
randomization. Under the alternative HMM, early stopping saves `919/1000` expected queries, hence
exactly `919/100000` query cost at `c=1/100`, with no change to the tape-wise terminal action.
Thus the entire observed gain over the matched cohort lottery is classical cost-saving futility
stopping; the finite adaptive-versus-deterministic-calendar separation is not a new acquisition
mechanism.

The registered script and independent exact verifier were rerun on 2026-10-29 after refreshing
source hashes. The verifier confirms exact risk/cost reconstruction, all 26 rational calendar
dual certificates, and the certified positive gap from the deterministic-calendar class. It does
not certify optimality over every randomized calendar mixture, and the recovered adaptive LP
optimizer remains numerical. This reinforces the candidate no-go; it does not settle whether a
different recurrent two-law objective admits a new theorem.

## Registered finite result and implication

In `switching_action_matched_adaptive_acquisition_v1.md`, an explicit positive-prefix policy reproduces the recovered adaptive LP policy exactly in expected metrics and causal-null risk. Rational dual lower bounds for all 26 deterministic terminal calendars are checked without an optimizer, establishing a finite separation from that deterministic class. A feasible static lottery over no query and calendar `(3,4,5)` shows that early stopping after a negative label saves `919/1000` expected queries and `919/100000` cost in the registered cell at the same risk.

This result supplies an acquisition-only structural diagnostic and a strong baseline implementation. It does not beat the established conceptual class of cost-aware sequential/futility designs and does not optimize the full randomized-calendar class. The next G1 step is to formulate a faithful composition of delayed sequential testing, finite-horizon hidden-regime control and the exact causal-null constraint, then search for a theorem or counterexample beyond classical futility stopping. Keep false-promotion validity distinct from evidence of present-regime benefit after a reversal. G1/G2 remain open; G3/G4 remain held.
