# Detection Augmented Learning: close nonstationary regret prior

2026-10-28. **Status:** primary arXiv v1 audited at theorem and proof-scope level. This is a
close prior-art boundary, not a novelty conclusion for the remaining ShiftLab contract.

## Source and theorem

Gerogiannis, Huang, Bose and Veeravalli, [*Detection Augmented Learning in Non-Stationary
Bandit Environments*](https://arxiv.org/abs/2610.25782), arXiv v1 submitted 2026-10-19 (36 pages;
the arXiv comments describe it as an extension of arXiv:2501.19401). The primary PDF, extracted
text, byte count and SHA256 are recorded in `switching_source_manifest_v17.json`. I inspected the
formal model, Algorithm 1, detector Property III.1, Definitions III.7 and Assumption III.8,
Theorem III.9 and Corollary III.10, and Appendix E's regret decomposition and false/late-detection
bounds. The theorem statement was visually checked in the rendered PDF.

The model is piecewise stationary with conditionally independent bounded or sub-Gaussian
feedback within each segment. The comparator is the per-round best policy in a policy class, so
the objective is dynamic regret. DAL combines a stationary bandit learner, a nonstationarity
detector and periodic forced exploration over a finite cover. The detector is required to have
finite-horizon false-alarm probability at most `delta_F` and pre/post-change sample windows
`m_D, ell_D = O(log T + log(1/delta_F) + log(1/delta_D))`. Theorem III.9 requires sufficiently
separated changes (Assumption III.8) so each change yields the samples needed by the detector.
With its specified exploration frequencies, the theorem gives

    R_T = O~((N_T+1) R_B(T/(N_T+1))
            + Delta_bar * sqrt(|C| N_e (N_T+1) T)),

where `R_B` is the stationary learner's concave increasing regret bound, `N_T` is the number of
changes, `N_e` is cover size, and `Delta_bar` is the maximum mean-reward gap. Appendix E separates
regret into forced-exploration cost, detection-delay cost and stationary-learning regret, then
controls false and late detections using the detector guarantees and a union bound over monitored
histories. The source notes that Assumption III.8 is used in the theorem but is not imposed in its
experiments. This limits theorem scope; it does not invalidate the empirical results.

## Mapping to ShiftLab and exact contract gaps

Two frozen ShiftLab models can be viewed as two bandit actions, and a queried common outcome
reveals both action losses. Thus one ShiftLab label is closer to full-information feedback on a
selected event than DAL's ordinary bandit feedback. DAL's forced exploration chooses actions to
obtain detector samples; it does not select paid outcome labels independently of the deployed
action.

The theorem uses immediate feedback. It has no paid-query price, no pathwise total-query cap
(forced exploration is a frequency schedule), no pending-label queue, and no deployment
switching cost. Its error control is a change-detector false-alarm guarantee under the specified
piecewise-IID/sub-Gaussian segment model, not a worst-case time-uniform false-promotion guarantee
over the ShiftLab conditional-null family. It assumes minimum separation/detectability for its
regret theorem and does not bound economic losses during a failed model intervention or rollback.
These are concrete contract gaps, not novelty by themselves.

## Research consequence

DAL closes novelty claims based on the generic combination “change detector + exploration +
restarting learner” or on detector-triggered resets yielding dynamic regret. Do not revive
ShiftGuard's three-stage structure under a new name. The residual algorithmic question, if it
survives further audit, must exploit the paired full-information label, pathwise total budget,
fixed release delay and costed deployment in one theorem with the global conditional-null risk
event. It must be compared against a risk-valid adaptation of DAL where the feedback permits one,
and against delayed batch and sequential-design baselines under matched budgets. The current
source does not answer that residual question, and the differences do not establish that it is
unoccupied. G1 remains open; no method, new theorem, efficacy result or real-data claim is passed.

## Provenance

The cached source is under ignored `outputs/switching_source_audit_v1/`. The SHA256 was computed
from the downloaded PDF. `pdftotext -layout` was used to locate theorem/proof passages, and the
Theorem III.9 page was rendered to verify the displayed bound. This is a focused source audit,
not an exhaustive novelty search or independent verification of every proof detail.
