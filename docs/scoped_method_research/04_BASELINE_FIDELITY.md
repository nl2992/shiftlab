# Baseline fidelity audit

This audit distinguishes implementation parity, statistical target, and deployment information.
The authoritative expanded prior-art matrix is in
[`03_PRIOR_ART_AND_NOVELTY.md`](03_PRIOR_ART_AND_NOVELTY.md); corrected outcomes and hashes are in
[`CORRECTED_REPLAY_AUDIT.md`](../scoped_method_research_2026-11-06/CORRECTED_REPLAY_AUDIT.md).

| Baseline | Status in ShiftLab | Fidelity / interpretation issue | Required comparator treatment |
|---|---|---|---|
| Gated / adaptive-range host | Implemented; corrected replay available | Conditional null and information filtration must be stated. Empirical null rate is not a proof. | Same horizon, labels, delays, costs and information. |
| Gated+front and pace-tuned | Implemented in Family C | Acquisition policy can alter the host's error behavior; report nulls separately. | Mandatory late-improvement comparator. |
| C2 / C6 | Implemented and previously exposed | Existing candidates; selected late-cell benefit mostly query-cost reduction; C2/C6 have adverse regimes and dependent-null stress. | Report as prior methods, not novelty. |
| RMM / Family B | Implemented; historical ledger | RMM is a strong adaptive monitoring/deployment comparator. Reserve and deadline can delay promotion and couple post-promotion budget. | Match budget including pending queries; show no-rollback and rollback ablations. |
| E_rb | Implemented (`fam_e.py` wrapper over `RecoveryMonitor`) | Alpha, start grid and host are consequential. Conditional guarantees depend on assumptions; inspected horizon gate was nonbinding. | Match alpha and start grid; report `-nogate`, alpha .05/.10 and false reversals. |
| E_srr/CUSUM and SR | Implemented detector swaps | SRR's stated interpretation is ARL, not E_rb's anytime FWER; don't present as equal-validity without calibration. | Include matched two-sided, delayed-feedback and restart-grid versions. |
| DISCERN-style | Corrected formula port; not author-native parity | Earlier local implementation omitted `/4` while retaining the leading factor 4, inflating the variance penalty fourfold. The corrected form is `4·residual²·((-log(1−λ)-λ)/4) = residual²·(-log(1−λ)-λ)`. Pre-correction outputs are stale and must not be treated as current comparator results. See `docs/failure_atlas_v2_flq/results/comparator_validity_audit_20261105.md`. | Use only corrected-code runs with matching manifests; distinguish formula port from author-native deployment parity. |
| Xu | Acquisition-only implementation present | Does not implement Xu's published certificate. | Label as acquisition-only; no certificate/guarantee claim. |
| SMCS / robust and fast-selector methods | Present in the paper protocol / baseline work | Applicability depends on candidate, observable gaps, drift and matching information; confirm each implementation's paper target. | Include if information contract applies; otherwise mark inapplicable with reason. |
| Fixed reserve / front-loaded schedule | Existing Family B/C variants | Conventional controls can explain observed label allocation benefit. | Match schedule and total query cost; do not call generic composition novel. |

For every reported comparator, validate source version, objective, delay handling, budget accounting,
threshold selection, guarantee class and observable inputs against its primary paper/code. The current
bounded pilot is a mechanism audit, not a complete fresh implementation audit of every published
competitor. That requirement remains open for any future frozen claim.
