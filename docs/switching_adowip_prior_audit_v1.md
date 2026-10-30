# ADOWIP: delayed decision-loss prioritization prior-art audit

**Date:** 2026-10-29. **Status:** primary-source scope audit; narrows the acquisition/switching
candidate but does not establish equivalence to the full ShiftLab contract.

## Source inspected

Xibai Wang, *Adapt Only When It Pays: Budgeted Decision-Loss Priority for Delayed Online
Time-Series Adaptation*, [arXiv:2606.25068](https://arxiv.org/abs/2606.25068). I inspected the full
primary PDF and relevant method/theory/limitations sections. Cached PDF SHA256:
`9EE5246A6295BCE976BF008C84953B5892E9BB9F8380633CDABD869DAF7B9A1E` at
`outputs/switching_source_audit_v1/adowip_2026.pdf` (the output directory is ignored by Git).

## Protocol and contribution

The paper's delayed-feedback learner keeps sealed pending-label records, reveals labels only at
their due times, and chooses whether to accept each adaptation update after feedback arrives. An
accepted update spends an explicit hard compute/update budget. The primary observed-priority score
is downstream decision loss, optionally penalized by prediction MSE; the scheduler accepts when
that score exceeds both a cost threshold and an empirical quantile of previous scores, provided
budget remains. It deliberately avoids counterfactual update probes in the main scheduler.

The source proves exact hard-budget feasibility by refusing any spend above the cap. For a
projected linear residual adapter with convex accepted losses and bounded gradients, it gives the
standard projected-OGD `O(R G sqrt(K))` accepted-sequence regret bound. It also gives: (i) a
threshold-selection consistency result under a stationary release model, monotone/Lipschitz
expected benefit in the observed score, and score density bounded below near the budget threshold;
(ii) a finite-candidate calibration/evaluation gate-selection statement with a concentration term
and calibration-to-evaluation drift term; and (iii) margin-band statements for score-estimation
errors. These are not a dynamic-regret guarantee against a clairvoyant budgeted oracle, and the
convex OGD theorem does not cover the default nonconvex low-rank adapter. The source explicitly
separates theorem-backed results from its broader empirical extensions.

## Boundary for ShiftLab

This closes generic claims that (a) delayed downstream decision loss can prioritize scarce online
updates, (b) a hard update budget can be enforced by a release-aware gate, or (c) such a gate can be
empirically compared with always/fixed/drift-triggered updates. Those ideas must be acknowledged
and included as a matched comparator where the task permits.

ADOWIP spends update-compute capacity after labels arrive; it does not choose which labels to
request under a hard observation budget. It adapts a residual forecaster rather than selecting
between two frozen policies, and has no transaction/switch cost, repeated promotion/rollback, or
global false-promotion guarantee under a history-adaptive causal null. Its score is observed
decision loss used as a proxy for future update benefit, while ShiftLab's question concerns the
expected value of a costly action over a future regime-dependent horizon under delayed and
selectively acquired evidence. Its paper reports negative or mixed finance diagnostics, so it does
not validate a financial switching claim.

The exact ShiftLab delta cannot be “use decision-loss priority under a budget.” A candidate would
need to establish why *requesting* a label changes the future net switching decision enough to
outperform an ADOWIP-style revealed-loss/update gate, the delayed economic-switching baseline, and
the causal-risk oracle under the same label budget, delay, switch charges and risk event. A mere
adapter from update compute to label requests plus an e-process or known drift penalty is not a
new result. G1 remains unresolved; no G2/G3 method or efficacy run is authorized by this audit.

## Provenance and scope

The inspected preprint is versioned by the cached hash above. This is a theorem-scope reading, not
an independent reproof or a claim that no later version exists. See also
[`switching_information_risk_contract_v1.md`](switching_information_risk_contract_v1.md) for the
separate statistical-evidence/current-regime-value invariant: historical evidence does not certify
current benefit after reversal.
