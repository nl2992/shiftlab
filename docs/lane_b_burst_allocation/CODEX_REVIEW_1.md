# Codex methodology review of lane B (round 1)

`codex exec --sandbox read-only`, `model_reasoning_effort=xhigh`, worktree HEAD `6ce2db1`, 2026-10-28. Verbatim final answer:

**PIVOT.** The allocation question remains worthwhile, but current B1 supports neither the claimed theorem nor a genuinely new algorithm.

**1. The separation is plausible; the argument and numerical interpretation need correction.**

- **The first check tests the wrong endpoint.** Claim 1 concerns \(P_H(\text{alarm during burst})+P_N(\text{alarm by }T)\). The check instead rewards H alarms anywhere before \(T\). Skipping the burst therefore defeats the numerical objective without refuting Claim 1. Persistent H was explicitly in the draft; calling it a violation of the premise is incorrect. [B1 draft](/C:/Users/nigel/OneDrive/桌面/ICML/shift-claude-lane/docs/lane_b_burst_allocation/B1_problem_draft.md:39)

- **The scientific target changed.** Disagreement-only scoring tests a conditional-on-disagreement null. Under the stated population null, sparse-phase harm is \(\rho\mu=0.025\) or \(0.10\), neither exceeding \(\epsilon=0.10\). Thus N is a population-null instance throughout. Its reported “power” cannot establish detection of charter-defined harm. Predictability alone does not fix this; current-context conditioning and zero propensities require explicit treatment. [Numerical setup](/C:/Users/nigel/OneDrive/桌面/ICML/shift-claude-lane/docs/lane_b_burst_allocation/B1_numerical_check.md:33)

- **The counting sketch is incomplete.** Identical D laws correctly couple label-independent allocation schedules. But \(K_\alpha\) is not a deterministic sample requirement for every anytime test. Specify distributions, target power \(1-\beta\), least-favourable nulls, and prove a change-of-measure/strong-converse bound. The upper bound needs stopping-time tails, wrong-rejection probability, wealth debt or restart penalties, and pending requests. \(B\ge K_\alpha+O(1)\) is too sharp without a power margin.

- **The corrective check gives limited support.** At \(d=0,\alpha=.05\), responsive allocation improves the tested maximin powers substantially. Delayed-feedback results are mixed; the stringent-alpha cells are poorly powered. Keeping B, L and T fixed while reducing alpha does **not** test an asymptotic claim requiring \(B\asymp K_\alpha\). Consequently, “alpha scaling contradicted” overstates the evidence.

- **The oblivious benchmark is incomplete.** A pre-data randomized choice between existing oblivious schedules is an essential comparator. I optimized such two-rule mixtures using the saved CSV means. Applying the same 0.05 criterion leaves **3/8**, rather than 6/8, families “not refuted.” For example, at \((\rho,d,\alpha,B)=(.2,20,.05,80)\), a randomized oblivious mixture attains empirical minimum power **0.400**, versus **0.371** for the best responsive rule. This is exploratory reanalysis, not fresh evidence. [Saved grid](/C:/Users/nigel/OneDrive/桌面/ICML/shift-claude-lane/docs/lane_b_burst_allocation/B1_corrective_check_grid.csv)

The transient-harm correction was **legitimate exploratory development and a disclosed forking path**. Git history confirms registration before its results. It changes the problem after negative evidence; it cannot rehabilitate the original experiment. Changing both the instance and monitor also prevents attributing the recovery to either change.

Two implementation details further weaken interpretation: corrective \(P_H\) still counts alarms after harm ends, and \(P_N\) includes pre-onset alarms. Delayed label expenditure is recorded at the evidence event rather than actual alarm time, omitting intervening requests. [Scoring code](/C:/Users/nigel/OneDrive/桌面/ICML/shift-claude-lane/scripts/lane_b/separation_check.py:247)

E2 motivates investigating allocation; it does not establish a universal oblivious-rule limitation. Its table actually calls the horizon baseline best or tied post-onset, contradicting the narrative “loses in both.”

**2. The current theorem would most likely support a theory note.**

The mechanism is sequential screening plus resource reservation and a valid detector. Absence of one paper satisfying B0’s entire conjunction does not establish methodological novelty. Also, Geng’s greedy first-order optimality concerns the **replenishing-rights model**, not arbitrary finite hard-cap allocation. [Geng–Bayraktar–Lai](https://arxiv.org/html/1309.5396v2)

B0 misses particularly relevant prior art: Chandar–Tchamkerten already study transient detection through multistage adaptive sampling, and earlier work explicitly separates adaptive from non-adaptive sampling delay. Their constraints differ, but the general adaptivity advantage and screening mechanism are established. [Transient-search results](https://arxiv.org/html/1501.05930), [adaptive/non-adaptive separation](https://arxiv.org/abs/1302.6574)

A **checkable two-window target**, rather than the present sketch, would be:

For fixed Bernoulli laws \(p_0<p_\epsilon<p_1\), fixed \(\beta<1/2,\eta>0\), adequate window lengths, and \(d=o(K_\alpha)\), let
\[
K_\alpha=\frac{\log(1/\alpha)}{\mathrm{kl}(p_1,p_\epsilon)}.
\]
Under explicitly defined early-H/late-N deadlines and a common valid null, prove:

\[
B\le(2-\eta)K_\alpha
\implies
\sup_{\text{randomized oblivious rules}}\min(P_H,P_N)
\le\tfrac12+o(1),
\]
while an explicit responsive rule achieves power at least \(1-\beta\) using
\[
B\le(1+\eta)K_\alpha+O(m_\beta+d).
\]

These are **proof obligations**, not established results. Even proved, this looks like a counting argument plus sequential screening, with substantial combination risk.

For an ICML methods contribution, the stronger target is a **minimax budget–duration–delay frontier across multiple indistinguishable bursts**, including a lower bound over **all adaptive policies** and a matching implementable algorithm. The theorem must resolve how waiting, batching and outstanding requests trade against reserve depletion. Beating D-only rules is insufficient when established responsive compositions remain competitive. The present rule’s extra \(d\) requests are an implementation consequence, not a universal lower bound.

**3. Recommendation: PIVOT within acquisition.**

Target **hard-budget screening across finite harmful windows with delayed labels**, leaving economic switching to Lane A.

The single next step is to freeze and attack that minimax theorem—including the strongest multistage-screening composition—**before another simulation sweep**. If ordinary screening plus a capped detector attains the frontier, stop the new-algorithm claim and retain the two-window result as a note.

Reviewed worktree `6ce2db1`; no files changed, no experiments rerun, and no `data/` access.
