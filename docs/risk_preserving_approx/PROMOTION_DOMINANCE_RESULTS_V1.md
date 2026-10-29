# Promotion-dominance screen: exact safety and bounded value loss

2026-10-29. **Status:** contract-specific pruning lemma PROVED subject to the
finite-HMM assumptions below; computational gain, novelty and generalization
UNRESOLVED. The diagnostic and restricted LP are research checks, not a new
end-to-end optimizer or real/synthetic efficacy result.

## Lemma

Use the finite two-law game of `PROBLEM_AND_THEOREM_TARGET.md`, and suppose the
alternative is a known finite-state HMM with conditionally independent emissions
given the hidden state, fixed transition/emission probabilities, common binary
outcome Y, and action losses Y for incumbent and 1-Y for challenger. The learner
chooses its action before observing that event's outcome. Costs c,k are
nonnegative. Consider any pre-promotion learner history h at time t. Let
p_s=E_alt[Y_s | h] and let e_z=P_alt(Y_s=1 | state_s=z), with the appropriate
conditional propagation including any unreleased outcomes. Define

    S(h) = sum_{s=t}^T p_s,
    L(h) = k + (1-p_t)
           + sum_{s=t+1}^T E_alt[min(e_{state_s},1-e_{state_s}) | h].

S is the cost of staying on the incumbent and never querying again. L is a lower
bound for every continuation that promotes immediately: pay the current switch,
then let an unrealistically informed controller see the current hidden state at
every *future* event, ignore future query and switch charges, and choose its
best action against that state's emission probability. It is not allowed to see
future emission noise, since real actions are selected before the outcome.
Conditional independence and the absence of extra predictive covariates beyond
the HMM information are necessary to justify this lower bound.

For epsilon>=0, forbid an immediate promotion at every h with L(h)>=S(h)-epsilon,
while leaving all non-promotion actions and histories unchanged. If the original
full-history constrained optimum is V* and the restricted optimum is V_epsilon,
then

    V* <= V_epsilon <= V* + epsilon.

The statement is about the unrestricted two-law objective and exact robust risk,
not merely a relaxed POMDP. For epsilon=0, eliminating the marked choices leaves
the optimum unchanged.

**Proof.** Take any feasible policy pi. On a trajectory where its first promotion
would occur at a marked h, replace that promotion branch by the incumbent-only,
no-query continuation. Its alternative conditional future cost increases by at
most S(h)-L(h)<=epsilon; pre-h costs agree and the branch event is unique, so
unconditionally the increase is at most epsilon. The replacement uses no more
queries on any path. It never creates a promotion on the replaced branch, and
on every other branch it behaves exactly like pi up to first promotion. Couple
any causal-null strategy on common history until the replacement: a promotion
under the modified policy is also a promotion under the original policy for the
same prefix. Once replacement occurs, no later promotion occurs, whatever the
null observes. Thus its worst-case null risk does not increase, including if
Nature sees the changed public query/action; private randomization used to select
behavioral branches stays hidden from the null except through public actions.
The modified policy is in the restricted class. Apply the construction to an
optimal policy, or an arbitrarily close feasible sequence if the infimum is not
attained. The reverse inequality holds because the restricted class is a subset
of the original class. The result is independent of the late-feedback queue's
contents so long as the lower bound and S are conditioned on the learner's valid
information and the HMM emission assumptions hold. QED.

This is a deliberately loose latent-state relaxation. Stronger valid lower
bounds may prune more, but observing the *realized current or future outcome*
before deciding would change the information structure. Outside the binary-HMM
emissions model or when covariates carry additional predictive information, this
formula requires a new justified lower bound.

## Registered checks

The preregistered exact-arithmetic screen is in
`PROMOTION_DOMINANCE_PROTOCOL_V1.md`; source is
`scripts/research_risk_approx/screen_promotion_dominance.py`, and results plus
source hashes are in `promotion_dominance_screen_v1.json`. For T=5,6,7 it checked
170, 352 and 658 promotion/query continuations respectively; no lower-bound
violation occurred. At T=6 it marked 93/236 information sets for exact pruning,
and 98/236 with epsilon=1/100. These include off-path states; the fraction alone
is not evidence of faster execution.

The separately preregistered restricted-LP check is in
`PROMOTION_RESTRICTED_ORACLE_PROTOCOL_V1.md`; runner and results are
`scripts/research_risk_approx/check_promotion_restricted_oracle.py` and
`promotion_restricted_oracle_v1.json`. On the T=6 anchor, setting to zero all
132 exact-dominated promotion realization columns, or all 140 epsilon=1/100
columns, yielded the same recovered cost 461083/160000 and independently evaluated
causal-null risk 1/10 as the unrestricted reference. Both LPs reported zero
constraint residuals. The two checks are consistent with the lemma for this one
cell; numerical LP solutions do not independently establish a general theorem.

The runner first builds the entire original game and computes all exact
continuation values, and then fixes columns to zero. Thus all three solves still
report 1,799 builder nodes. The result does **not** demonstrate a runtime or
memory improvement and is not a matched policy efficacy comparison. Exact
rational risk is checked for the recovered policy; reported LP optima are
numerical, not new exact dual certificates.

## Prior-art and next decision

POMDP action pruning with optimistic full-information/MDP bounds and feasible
blind-policy bounds is established; see the primary IJCAI paper
[AEMS, Ross et al. 2007](https://ijcai.org/proceedings/2007/417) and the
[RAO* chance-constrained planning paper](https://ojs.aaai.org/index.php/AAAI/article/view/10423).
The bound here is a contract-specific adaptation, not an algorithmic novelty claim.
Whether the global causal-null mixture and epsilon accounting require an additional
published lemma is **UNRESOLVED — EXACT REDUCTION REQUIRED**. A full novelty claim
requires a meaningful improvement over these methods, not merely preserving safety.

The next technical question is whether marking histories *before* continuation
construction can eliminate enough work in the actual pre-promotion builder without
changing information sets or the null game. Measure construction, LP time and
memory against the exact decomposed oracle under a new registered protocol; verify
returned policies and the additive gap independently. If the builder still has the
same asymptotic bottleneck or the savings do not overcome overhead, keep the rule
as a safe baseline and investigate a stronger candidate. No holdouts or historical
results are touched.
