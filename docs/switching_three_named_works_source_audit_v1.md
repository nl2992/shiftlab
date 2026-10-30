# Three named adjacent works: source-level theorem boundary

**Date:** 2026-10-29. **Status:** primary-source audit of the user-identified comparators; no
novelty conclusion for the overall research program.

## The Challenger

Digalakis, Pérignon, Saurin and Sentenac, *The Challenger: When Do New Data Sources Justify
Switching Machine Learning Models?* ([arXiv:2512.18390](https://arxiv.org/abs/2512.18390)). I
inspected the full author manuscript, including its problem/value model (Sections 2–3), sequential
procedures (Section 4), and Theorem 6.2, Corollary 6.3 and Proposition 6.4 (Section 6 and proofs).

The method explicitly combines challenger data acquisition/training costs, the foregone gains of
waiting, one-time switching cost and a finite deployment horizon. Its one-shot, greedy and lookahead
evaluation policies make this a direct economic model-switching comparator. Theorem 6.2 gives
`O(T^(2/3) sqrt(log T))` regret relative to an oracle that knows the challenger learning curve,
under finite VC dimension/ERM and conditions including a decision epoch of order `T^(2/3)` and a
switch/discard rule sufficiently close to the true incremental value. Corollary 6.3 and Proposition
6.4 give sufficient schedules for OSE and LSEc under the paper's setting. In particular, the
theorem's switching condition is stated using the unobservable `Delta V`; the paper explicitly
notes that it is a sufficient structural condition, not itself a directly implementable rule.

The problem is a single challenger, one-way switch-or-discard optimal stopping problem with a
specified learning curve and sample flow. Its budget constraint is a cumulative economic-cost
feasibility cutoff, not a pathwise cap on selectively requested labels with pending delayed
feedback. It has no repeated rollback/re-promotion, global causal-conditional-null any-promotion
risk, or current-regime guarantee after a reversal. Therefore economic acquisition plus delayed
one-way switching and regret are established ingredients; these differences remain exact
comparison obligations, not a novelty claim.

## Drift2Act

Lamaakal et al., *Drift-to-Action Controllers: Budgeted Interventions with Online Risk
Certificates* ([arXiv:2603.08578](https://arxiv.org/abs/2603.08578)). I inspected the full preprint,
including its active certificate (Section 4, Appendix D), controller (Appendix B), and delayed-label
and budget protocol (Appendix E).

Drift2Act uses uniform random label audits from a current finite window, bounded losses, and a
stitched Hoeffding radius with summable error allocation. Theorem A.2 gives simultaneous window-risk
coverage over times under Condition A; Corollary A.3 shows the safety gate cannot issue predictions
while that window risk exceeds its threshold except on the confidence failure event. It includes
fixed label delays, a total labeling budget, intervention costs and cooldowns in its implementation
and experiments. This closes novelty from the generic combination of delayed budgeted auditing,
anytime window-risk certification and cost-aware intervention gating.

The guarantee is conditional on uniform random auditing within each current window and bounds a
finite-window empirical risk estimand. It is not a global false-promotion bound under an arbitrary
history-adaptive conditional null, a utility/regret guarantee for model switching, or a guarantee
that pre-reversal evidence certifies present value. Its intervention controller selects actions by
belief-weighted one-step utility and costs; the cited theorem proves the risk certificate, not
optimality of that controller or a switching regret bound. The user-stated ShiftGuard failures
therefore still matter, but copying the certificate/controller architecture is not a methodological
delta.

## Lindon–Kallus

Lindon and Kallus, *Design-Based Anytime-Valid Inference for Randomized Experiments with Delayed
Outcomes and Staggered Entry*, ICML 2026 ([PMLR 306 paper](https://proceedings.mlr.press/v306/lindon26a.html)).
I inspected the full proceedings PDF, including the observer and single-arm filtrations (Section 3),
Theorem 4.4, the asymptotic arm-level confidence sequence in Theorem 4.6, the incremental-effect
sequence in Theorem 4.9, Corollary 4.10, and the proofs.

The paper handles staggered randomized treatment assignment and outcome-dependent delayed event
times. It shows that the IPW treatment-effect error is generally not a martingale under an ordinary
observer filtration, then constructs arm-specific event-time filtrations under which the unit-level
martingale condition holds. Its confidence sequences are asymptotic, built using a strong
approximation and a martingale mixture boundary; treatment-effect coverage combines two arm-level
sequences by a union bound. This is a required inference comparator whenever the data arise from a
randomized experiment with asynchronous potential outcomes.

It does not optimize which labels to acquire under a hard query cap, choose a model to deploy,
control a global causal-null promotion event, or bound switching regret. Its randomized assignment
design and design-based estimand also differ from ShiftLab's paired predictive loss/HMM alternative
and separate history-adaptive causal null. Anytime-valid inference with delayed outcomes is
established; it cannot be called the missing switching algorithm by adding an acquisition or
controller layer.

## G1 effect

These audits close three broad novelty routes: (1) economic model switching coupled to data
acquisition and one-way sequential stopping; (2) delayed budgeted audit labels plus anytime risk
certification and costed intervention; and (3) anytime-valid inference for randomized experiments
with staggered delayed outcomes. None of the inspected theorem statements directly solves the exact
two-law ShiftLab contract. No distinct algorithm or theorem emerges from that mismatch. G1 remains
open only for a structural acquisition/switching result with explicit global causal-null risk and
economic regret/cost bounds beyond these sources and the exact sequence-form oracle; G2–G5 remain
held.

For any candidate implementation, maintain separate fields for test-epoch evidence and a
current-regime economic forecast. Historical e-wealth can control the former's false-promotion event
under its declared null; it does not certify the latter after reversal.

## Provenance

- Cached source PDFs and text extraction are under ignored
  `outputs/switching_source_audit_v1/`.
- SHA256 `digalakis_challenger_2025.pdf`:
  `C7065A611F723182EED3ABB68051C35523960A295186C1E2F101D65E6CEA18F1`.
- SHA256 `drift2act_2026.pdf`:
  `6ECE39E72A45188F5F3459D1AB334A056D76D65FDD55F2343FAA7F353F2E67F1`.
- SHA256 `lindon_kallus_icml2026.pdf`:
  `B52C7BB539068AFB25412B1DCC693509ABEBE9BEC9331C135FD692FF95D58F3D`.
- These are theorem-scope audits of the inspected versions, not independent reproofs or evidence
  that the literature contains no later or uninspected result.
