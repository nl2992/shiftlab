# Drift2Act reproduction boundary and ShiftLab delta audit — 2026-11-04

## Decision

Do not open a Drift2Act replication or copy its controller as a new ShiftLab direction. Its generic combination of delayed random label audits, anytime finite-window risk certification, and costed drift intervention is already prior art and is already represented in the ShiftLab switching audits. The preprint is a useful required comparator for future deployment-control work, but its published headline does not itself show that it dominates ShiftLab's distinct paired fixed-model replacement contract.

## Primary-source details checked

The ICLR 2026 CAO Workshop paper is available on [OpenReview](https://openreview.net/pdf?id=tcUgT2jE5W), and its source is [arXiv:2603.08578](https://arxiv.org/abs/2603.08578). The source states:

- Risk target: the mean bounded loss over the recent finite window, not paired challenger-minus-incumbent net value.
- Audit design: uniform random sampling from each current window, independent of unobserved labels conditional on observed history (Condition A). Its Appendix D bound assumes the queried losses for a fixed window are IID from the finite-window population; Theorem A.2 allocates error across sample counts and monitoring times.
- Delay: fixed delay in the experimental protocol. Appendix D.7 says delay changes the number of arrived labels while preserving validity under its stated uniform-sampling condition; this does not supply a general outcome-dependent arrival-order theorem.
- Control: a learned belief over drift type and an offline synthetic gain table feed a one-step cost/violation utility. The certificate gates fallback/action feasibility; the theorem proves risk coverage, not optimal switching, future post-action value, or regret.
- Resources: a finite total label budget and intervention costs/cooldowns are implemented in the paper's protocol.
- Experiments: Camelyon17, DomainNet, and synthetic drift. This workspace has WILDS CivilComments offline studies, but no identified local Camelyon17 or DomainNet stream artifact. The source record and paper expose no code repository or reproducible artifact link in the materials checked on 2026-11-04. Thus a paper-faithful head-to-head is not currently executable from the local checkout.

## Contract comparison

| Dimension | Drift2Act | ShiftLab switching target | Status |
|---|---|---|---|
| Estimand | Absolute recent-window risk of deployed predictor | Paired net-value difference between two frozen policies; separate causal-null false-promotion event | Material target difference |
| Label selection | Uniform audit sample from current window | Selective acquisition can target decision-informative labels | Drift2Act is not a direct matched acquisition baseline without a task adapter |
| Label timing | Fixed delayed protocol; theorem uses uniform-within-window representativeness | Delayed released outcomes, pending requests charged at request time | Exact delay/cap filtration still needs an explicit adapter |
| Action value | Belief-weighted one-step gains calibrated offline | Promotion/reversal economics under changing paired value | Drift2Act has no post-switch value or switching-regret theorem |
| Safety | Simultaneous bound on finite-window absolute risk | Global any-promotion control under a conditional null | Neither guarantee implies the other |
| Empirical evidence | Vision streams and generated drifts; paper-reported safety/cost results | Synthetic paired-loss and separate local task studies; no validated end-to-end field stream | No valid direct numeric comparison at present |

These differences are candidate comparison obligations, not a claim that ShiftLab is novel. The exact ShiftLab control objective itself has extensive prior-art screens and no surviving algorithm lead. A future candidate must show a theorem or registered empirical separation from Drift2Act plus the paired switching, active testing, delayed feedback, and exact finite oracle baselines documented in [`switching_novelty_delta_v1.md`](../switching_novelty_delta_v1.md) and [`budgeted_switching_research_goals.md`](../budgeted_switching_research_goals.md).

## What this audit changes

1. Drift2Act remains a mandatory scope comparator and closes broad “monitor + delayed labels + risk certificate + costed action” novelty claims.
2. It does not close selective paired fixed-model switching with a global causal-null event. However, that contract distinction is still not a research contribution without a surviving method/theorem and an admissible empirical stream.
3. No local data qualify for a paper-faithful Drift2Act reproduction: the WILDS CivilComments assets lack verified event/release times and implement offline candidate selection, while the required vision stream assets are absent.
4. The known-window finite-population confidence-bound refinement was considered and rejected before implementation: finite-population correction and repeated-window error allocation are standard inference refinements already represented in the repository prior-art matrix; they would not by themselves satisfy the project objective of a meaningful SOTA improvement.

## Next eligible gate

No method or experiment is nominated by this audit. Before any new algorithm work, screen for a source-audited, genuinely new structural assumption or acquire a stream with (i) paired frozen-policy outcomes, (ii) observable feature and outcome release clocks, (iii) an external decision-cost contract, and (iv) enough maturity for selective delayed evaluation. If neither appears, retain the evidence-bounded benchmark/failure analysis and do not describe it as a new SOTA improvement.
