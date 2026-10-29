# Response-adaptive sampling with switching costs: source-level boundary

**Date:** 2026-10-28. **Status:** primary source inspected; generic acquisition/switch-cost combination closed, target contract still open.

## Source and exact scope

Janis P. Hardwick and Quentin F. Stout, “Response Adaptive Designs that Incorporate Switching Costs and Constraints,” *Journal of Statistical Planning and Inference* 137(8), 2007, 2654–2665, DOI 10.1016/j.jspi.2006.04.013. The author-hosted primary PDF is cached at `outputs/switching_source_audit_v1/hardwick_stout_response_adaptive_switching_2007.pdf`, 216,140 bytes, SHA256 `618ce65e687c05b3c894ad5abc61ebf32151b514fc1c50ff7dd139853e450147`.

Inspected Sections 2–4, the two optimal dynamic programs in Appendix Figures 7–8, and the complexity discussion. There are K Bernoulli populations, independent Bayesian priors, a fixed total sample size N, and a terminal objective on the final posterior/count state. At each observation, the experimenter chooses which population to sample. One model limits the number of allocation switches; another adds a cost c(i,j) when sampling allocation changes. Backward dynamic programming computes optimal designs for arbitrary terminal objectives. Their adaptive hyperopic heuristic replans fixed allocations at each posterior state and incorporates sampling-switch costs. The paper evaluates minimizing failures and nonlinear Bayes risk. It notes that optional stopping can be accommodated by interpreting N as a maximum sample size.

## Relation to budgeted delayed model switching

This is direct prior art against claims that jointly adapting which evidence to acquire and paying a switching cost is itself novel. The difference is semantic and material: their switch changes the population being sampled, while ShiftLab's switch changes the deployed predictive policy and incurs economic deployment cost. Their objective is Bayesian expected terminal design value; there is no anytime false-promotion constraint, adversarial conditional null, fixed label-release delay or pending-query reservation. Their sampling cost discussion is not a pathwise acquisition budget over delayed labels. These gaps motivate a precise target theorem but do not establish one.

The new candidate must show how deployment action value, delayed paired outcomes, a pathwise remaining query budget including pending labels, and robust false-promotion risk create a result beyond their optimal dynamic program/hyperopic construction plus standard sequential testing. Generic posterior-aware VOI, lookahead, or adding switch cost to adaptive sampling does not pass G1.

## Decision

Reject generic adaptive acquisition with switching cost as a contribution. Preserve Hardwick–Stout as a mandatory conceptual comparator in future G1 reviews; do not claim a faithful reproduction where its experimental-assignment switching semantics differ. No algorithm, theorem advantage, efficacy test or real-data claim follows from this audit.
