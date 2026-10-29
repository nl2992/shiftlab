# Causal risk accounting before contingent acquisition planning

2026-10-28. Previous goal turn: progress (optimized fixed-cohort comparator completed).
This is a registered correctness screen and a mechanism rejection, not efficacy evidence.
Do not enlarge the stationary cohort grid or nominate generic constrained planning as new.

## Source-level constraints on the proposed mechanism

[Hu, Cai and Vlatakis-Gkaragkounis, Prudent-Banker v1](https://arxiv.org/pdf/2605.23351v1)
already addresses delay-aware safe switching through a missing-feedback correction to a phased
aggression threshold. Read Section 2, Algorithm 1, Theorem 4.1, Appendix C.4's proof and C.7's
aggregation discussion. Its oblivious-adversary bandit protocol receives the selected arm's loss
every round after delay. Safety means expected comparator regret relative to a fixed exploratory
mixture with all probabilities at least delta, not a false-promotion probability or a deterministic
incumbent. The theorem gives near-minimax pseudo-regret and logarithmic-in-total-delay baseline
regret, with regularizer/baseline-dependent constants. No hard observation cap or switching
charge appears in the inspected contract. Full proof verification and reproduction are unperformed.
Thus it is an explicit comparator obligation, not a faithful plug-in or evidence for our novelty.

[Osogami, ICML 2015](https://proceedings.mlr.press/v37/osogami15.pdf) already develops robust
POMDP value iteration and robust belief updating. Read Section 2, equations (1)-(4), Algorithms
1-2, Theorem 1 and Appendix A's mixed-strategy minimax step. The uncertainty is convex and
specified per state/action transition kernel. Its robust backup is not automatically the correct
backup for a pending-label process with different causal information. Nevertheless, robust
belief planning, convexification and policy pruning are established techniques. A generic
risk-constrained planner with a pending-label state fails our novelty gate. The following
elementary constructions clarify our contract; they are not claimed as new POMDP results.

Both primary PDFs are cached and hashed in `switching_source_manifest_v4.json`.

## Two mistakes with different directions

Let each queried binary outcome obey P(Y_s=1 | full event history and current choices)<=1/2.
Its value is generated at event s and released at s+d. Independent policy coins drawn later
are unavailable when the environment chooses that outcome's conditional law. The environment
may see past outcomes, including unreleased ones, and public past actions, but cannot see future
fresh randomness. The learner sees only released labels, its own coins and public decisions.

**IID-only calibration can be unsafe.** Query event 1. If its eventual outcome is zero, query
one later event and promote if that label is positive; otherwise never promote. At the IID
boundary the promotion probability is 1/4. A valid conditional null sets the first label to zero
and the second to Bernoulli(1/2), raising it to 1/2. With an independent activation probability
2/5 before the first query, the apparent risk is 1/10 but the actual worst risk is 1/5.
Every path uses at most two labels. Delay changes the wait, not these probabilities. Therefore
an IID-calibrated contingent planner cannot inherit our composite-null guarantee by assertion.

**Arrival-time rectangularization can be conservative.** Query one outcome at event 1. Draw a
fresh fair bit U strictly after event 1 and before its label is released (take d>=2). Promote
upon release iff Y_1=U. For any causal conditional null, P(promotion)=1/2: average over U
before maximizing over p=P(Y_1=1)<=1/2. If a backup instead lets the environment choose p
after seeing U, its answer is 3/4: choose Y_1=0 when U=0 and p=1/2 when U=1. With upfront
activation probability 1/5 the true risk is 1/10 but the relaxed backup reports 3/20. Every path
uses at most one label. This rule is a semantics witness, not an economically useful proposal.

In general, for a binary terminal decision table f(y,u), define

    C(f) = max_{p in [0,1/2]} E_U[(1-p)f(0,U)+p f(1,U)],
    A(f) = E_U[max_{p in [0,1/2]} ((1-p)f(0,U)+p f(1,U))].

Then C(f)<=A(f); swapping maximum and average grants future information to the environment.
Both maxima occur at p=0 or p=1/2. If f(1,u)>=f(0,u) for every u, both select p=1/2 and
equality holds. Thus there is no causal/arrival distinction for this monotone subclass. This
does not prove that optimal economic policies with contingent querying and reversals belong
to that subclass, or that arrival-time e-processes generally fail. The existing event-predictable
betting construction has a separate valid proof; none of its reported risk calculations is revoked.

## Registered finite verification

Implement `scripts/check_switching_causal_risk.py` using exact rational arithmetic. Enumerate
all 16 rejection subsets of two queried outcomes, calculating both IID-boundary risk and the
worst conditional-null risk by endpoint backward induction. At alpha=1/4 expect five IID-safe
subsets but only two robust-safe subsets. Check all 16 binary tables f and U success probabilities
0,1/4,1/2,3/4,1: C<=A in all 80 cases, with equality whenever f is increasing in y. Confirm
the activated examples at alpha=1/10. These are arithmetic/semantics checks, not policy efficacy.

Reproduce with `python scripts/check_switching_causal_risk.py`; save exact tables and source
hash to ignored `outputs/switching_causal_risk_v1/results.json`. Do not claim a new theorem
from elementary max/expectation ordering or endpoint recursion.

## Concrete next mechanism obligation

The proposed generic risk-budget Bellman rule is **not nominated**: constrained sequential
design/robust planning already supplies its core idea, and an arrival-only scalar risk state
has not been shown to preserve event-time causality. Do not implement it as a new algorithm.
Any replacement must supply an explicit causal strategy or certificate, hard-cap accounting
including pending requests, and the same null/randomization permissions for its comparators.
It must then prove a computational or decision-regret advantage beyond an established planner,
not merely differ in its state variables or use a more favorable safety definition.

A candidate may restrict to monotone decisions only if that restriction is justified against
economic switching and reversal; the equality above alone is not sufficient. An enlarged-null
backup can serve as a conservative reference if labeled as such. Passing this screen does not
pass G1 or substitute for new theory, matched empirical evidence and an eligible real task.

## Executed evidence and continuation decision

The registered script completed: all 16 two-label rules agreed with independent enumeration of
eight extreme causal null strategies each. At risk 1/4, five rules passed IID calibration and
only two passed composite-null calibration. The 80 future-coin cases had 45 monotone equalities,
six strict causal/arrival gaps and a maximum gap of 1/4. Both activated examples reproduced
the exact risks above. Ruff passed and the recorded script/PDF hashes were verified.

Continue only with the causal strategy constraint explicit. Reject the generic risk-budget
planner as a contribution and reject IID-only calibration as a safety verifier. No new simulation
grid was run. The next candidate needs a substantive, source-audited performance result against
established planning and delayed-safe-learning methods before prototype efficacy expansion.
