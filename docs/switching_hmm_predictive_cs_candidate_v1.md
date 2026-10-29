# Candidate: delayed-HMM predictive confidence gate

**Registered development hypothesis, 2026-10-29.** This is not a validated novel method, not a
confirmatory protocol, and not evidence that the information structure is unoccupied. The goal is
to replace the impossible distribution-free current-value claim with a model-conditional guarantee
that allows latent regimes to reverse under a fixed recurrent HMM.

## Contract

The latent regime is a finite-state HMM with unknown but fixed parameter `theta` in a declared
finite model set `Theta`. Conditional paired loss differences `X_t` are bounded in `[-1,1]`, with
known emission family and transition structure indexed by `theta`. The hidden state and unqueried
losses are not observed. Queries are chosen predictably, at most one per event, under a pathwise
cap `B`; a queried `X_s` is released exactly `d>=1` events later. Querying does not affect the
outcome process. Decisions may use covariates and all labels released before the decision; no
unreleased label or latent state is available. Model parameters do not change with time, although
the hidden regime can transition and reverse benefit repeatedly. Safety is relative to the true
model's current predictive mean
`mu_t(theta) = E_theta[X_t | learner-observable history before the action]`.
This is explicitly model-conditional; arbitrary transition/emission drift is outside the claim.

## Anytime confidence-set lemma

Let `L_t(theta)` be the likelihood of the observed query/action/release history through time `t`
under model `theta`, including adaptive query selection and fixed-delay release. The policy's
randomization kernels are functions of observable history and are the same under every `theta`.
For a fixed prior `pi` with support on `Theta`, define

```text
E_t(theta) = sum_{theta' in Theta} pi(theta') L_t(theta') / L_t(theta)
C_t = {theta in Theta : E_t(theta) < 1/alpha}.
```

For the true parameter `theta*`, the likelihood-ratio terms are nonnegative likelihood-ratio
martingales under `theta*`; therefore `E_t(theta*)` is a nonnegative martingale with initial mean
one. Ville's inequality gives

```text
P_theta*(exists t : theta* not in C_t) <= alpha.
```

This remains true under predictable adaptive query times and delayed release when the likelihood
is the correct marginal likelihood of the released data under the known sampling policy. At each
release, HMM forward filtering marginalizes unqueried and still-pending outcomes; one must not
pretend pending outcomes are observed. If likelihood support fails, regularize the family or define
`E_t=+infinity` and stop safely.

## Predictive safety corollary

Permit promotion at time `t` only when

```text
min_{theta in C_t} mu_t(theta) > h.
```
If the confidence set is empty, do not promote. On the simultaneous-coverage event, every
permitted promotion has `mu_t(theta*)>h`; hence

```text
P_theta*(exists promotion t with mu_t(theta*) <= h) <= alpha.
```
The proof is containment: a false promotion while `theta* in C_t` contradicts the gate, so any
false promotion implies confidence-set failure. Unlike a historical benefit e-process, the gate
recomputes `mu_t(theta)` from the current released history at every decision; post-reversal labels
can lower the current forecast. The result controls conditional expected benefit under the true
fixed HMM parameter, not realized latent-state sign, HMM misspecification, or out-of-family change.
The hard query cap is enforced by any acquisition policy used with the gate; the lemma itself does
not establish acquisition efficiency or regret.

## Novelty audit and candidate mechanism boundary

Arnold et al., “Sequential model confidence sets,” JRSS B (published 2026), already provide
anytime-valid confidence sets for strongly/weakly superior forecasters using e-processes for
conditional expected loss differences. This closes generic “confidence set then model switch.”
Their stated object is a set of forecasters' relative performance, not a parameter confidence set
for an adaptively sampled, delayed hidden-state HMM followed by a current HMM-filter forecast; that
difference is a research question, not proof of novelty. See the [primary article](https://doi.org/10.1093/jrsssb/qkag066).
Likelihood-ratio confidence sequences, HMM filtering, and active sensing are established separately.
The corollary above is a standard Ville argument and is not claimed as a new theorem by itself.

The only possible method contribution left in this candidate is a query-allocation rule that uses
(1) the current HMM-filter forecast, (2) the confidence-set ambiguity over its sign, (3) remaining
query rights, (4) release delay and pending labels, and (5) promotion/rollback costs, with a proved
regret or approximation advantage over a matched safe calendar, sequential model-confidence-set
baseline, and the exact two-law oracle. Before implementation, audit active sensing and sequential
forecast comparison at source level and test whether this reduces to a standard finite-horizon
constrained POMDP or controlled-sensing policy. If it does, close it. Do not claim current-value
safety under misspecified or time-varying HMM parameters.

## Stop conditions and next gate

Do not run confirmatory simulations or real-data studies yet. G1 passes only if the query allocation
rule has a nontrivial theorem-level advantage beyond the confidence-set gate, active sensing, robust
FSC/POSG planning, and sequence-form oracle. Next: audit the exact delayed/adaptive likelihood
factorization (including query-policy terms), derive a small exact HMM confidence-set example, then
source-audit the proposed query score. The full research goal and G2-G5 remain open/held.

## Exact adaptive-delay mechanism check

`python scripts/check_switching_hmm_predictive_cs.py` enumerates a two-model one-state HMM
(Bernoulli parameters `1/10` and `9/10`, prior `1/2`), with `alpha=1/8`, fixed delay one and
pathwise budget two. It always queries event 1, queries event 2 iff the released first label is
positive, and otherwise queries event 3. This is predictable, uses exactly two queries on every
path, and respects release times. Exact enumeration gives confidence-set failure probability
`1/100` under either true model; after one released label neither model is excluded, and only the
two-same-sign outcome after two labels excludes the true model. The script and JSON output are
mechanism verification only; the one-state family has no latent reversal and no acquisition/value
comparison.

## Expanded source boundary

Arnold et al.'s sequential model confidence sets define strong superiority using conditional loss
differences at every time and provide simultaneous time-uniform coverage for the superior set;
they also study weaker average superiority. This confirms that time-uniform conditional forecast
comparison is established. Their theorem is not itself the parameter-set/filter construction above.
Kapoor and Nair, AISTATS/PMLR 2026, already formulate costed sensing as an MDP whose state records
when sensing is due, prove policy suboptimality bounds, and give an efficient policy-improvement
algorithm. Together with the repository's delayed-POMDP and constrained-POMDP audits, this means
that “confidence-set state + delayed queue + hard remaining budget + expected value of sensing”
is at high risk of being a standard state augmentation and planning composition. See the [PMLR
primary paper](https://proceedings.mlr.press/v300/kapoor26a.html) and the [JRSS B primary article](https://doi.org/10.1093/jrsssb/qkag066).
The source boundary does not say these papers solve ShiftLab's exact robust two-law problem; it
means their gap differences are not a novelty argument by themselves.

## Acquisition-score no-go 2026-10-29

The proposed score “query when the current confidence set straddles the switching hurdle and the
label is expected to resolve that ambiguity” is a decision-focused value-of-information rule. It
is not a novelty delta: [Huang, Bickford Smith and Rainforth, AISTATS/PMLR 2026](https://proceedings.mlr.press/v300/huang26b.html), derive acquisition
objectives directly from downstream decision loss; Kapoor and Nair, AISTATS/PMLR 2026, formulate
costed sensing as a belief-state MDP with a policy-improvement algorithm and suboptimality bounds.
The repository also already has an exact fixed-gate counterexample in
`switching_economic_acquisition_screen_v1.md`: one-step VOI spends no labels when a three-label
complementary test has positive value. Thus this particular myopic score is rejected before any
additional experiments.

A dynamic planner over `(HMM belief, parameter confidence set, delay queue, remaining budget,
incumbent, promotion state)` would be the corresponding standard state augmentation. The current
candidate also needs to preserve the original broad causal-null any-promotion guarantee; the HMM
parameter confidence set alone gives only model-conditional safety. A version with both gates is a
plausible comparator, but adding two established certificates and a constrained planner is not a
method claim. G1 survives only if a concrete joint allocation rule has a proved finite-sample or
approximation advantage over (i) this two-gate composition, (ii) costed sensing / loss-driven active
learning, and (iii) the exact two-law oracle. Otherwise close this candidate and revise the research
hypothesis. No additional experiment is authorized by this screen.

## Delayed HMM likelihood audit and exact adaptive check

At decision time `t`, write `R_t` for queried event indices whose labels have actually been
released, `Y_{R_t}` for their observed values, and `H_{<t}` for the observed query/action
transcript. Under a fixed ordered delay and outcome-independent querying, the likelihood of a
valid transcript under parameter `theta` is

```text
P_theta(H_<t, Y_Rt)
  = [product_{s<t} kappa(a_s,q_s | H_s)]
    * sum_{z_1:t, x_1:t} pi_theta(z_1)
        product_{s<t} A_theta(z_s,z_{s+1})
        product_{s<=t} g_theta(x_s | z_s)
        product_{s in R_t} 1{x_s = y_s}.
```

Here `kappa` is the learner's policy kernel and is common across candidate parameters. Pending
queried outcomes, unqueried outcomes, and hidden states are marginalized; they must not be inserted
as if observed. For a realized transcript, the policy-kernel factor cancels from likelihood ratios.
This remains true when query choices are predictable functions of released labels, because the
choice at `s` is fixed conditional on the observed history that generated it. Parameter-dependent
querying, outcome-dependent arrival, informative delay, parameter-dependent covariate laws, or
incorrectly using pending labels would invalidate this cancellation and require a different joint
likelihood.

This factorization uses the standard HMM missing-observation likelihood construction; Perets et
al.'s primary [AISTATS 2023 paper](https://proceedings.mlr.press/v202/perets23a/perets23a.pdf),
Appendix B, writes the HMM joint distribution and handles known missing observation locations by
marginalizing them. Emmenegger, Mutny and Krause's primary [NeurIPS 2023 paper](https://papers.nips.cc/paper_files/paper/2023/hash/5491280797f3192b895bce84eb83df8d-Abstract-Conference.html)
establishes anytime-valid likelihood-ratio confidence sets for sequential decisions. These sources
support the ingredients; neither is a theorem about this project's delayed adaptive query policy,
and their combination is not claimed as a novelty result. The martingale coverage corollary above
follows directly from the Radon–Nikodym likelihood-ratio martingale for the observed transcript.

The exact check in `scripts/check_switching_delayed_hmm_likelihood.py` enumerates a two-state,
two-parameter Bernoulli-emission HMM for `T=8`, fixed delay `d=2`, and hard query cap `B=4`. The
learner queries the first two events, then queries only when the latest due queried label is 1 and
budget remains. Across all `2^8 * 2^8 = 65,536` hidden-state/outcome paths, all 88 distinct
valid-prefix/model likelihoods agree exactly with the forward HMM likelihood after pending and
unqueried outcomes are marginalized. For the prior-weighted mixture likelihood ratio with
`alpha=1/20`, exact all-time confidence-set failure probabilities are `1379/200000 = 0.006895`
under model 0 and `0` under model 1. The result JSON is
`outputs/switching_delayed_hmm_likelihood_v1/results.json` and is ignored by Git.

This is a likelihood and coverage-mechanism check for one correctly specified finite family. It
does not show power or acquisition value, compare switching utility, handle the broad causal-null
adversary, justify HMM specification, or establish safety under parameter drift. It validates the
confidence-set gate as a comparator only; G1 remains open and no efficacy experiment follows.
