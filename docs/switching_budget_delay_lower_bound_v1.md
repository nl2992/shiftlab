# A joint hard-budget and delay obstruction

2026-10-28. **Status: supporting proposition with proof; originality unestablished.**
The previous goal turn made progress: a reference implementation and its checks were completed.
This proposition studies the original hard budget, delayed feedback and global-null risk contract,
not the reference's weaker unconstrained fixed-comparator objective. It is not the sought algorithm.

## Proposition

Fix T>=1, pulse length 1<=h<=T, 0<=B<=T, integer delay d>=1, alpha in [0,1], and
0<Delta<=1. Covariates are constant and outcomes are action-independent. Every queried label
identifies both fixed policies' losses and arrives at the start of round s+d, after request s.
Unqueried losses are never revealed. The query cap is pathwise, including pending queries.

In the null environment P0, both losses are 1/2 at every round. The learner starts at action 0
and satisfies P0(any promotion to action 1 by T)<=alpha. For each onset nu in {1,...,N},
N=T-h+1, define Pnu by changing the losses on [nu,nu+h-1] to

    l_t(0)=(1+Delta)/2,  l_t(1)=(1-Delta)/2,

and leaving them equal to 1/2 elsewhere. The comparator switches to 1 at nu and returns to
0 after the pulse if time remains. It pays at most two switching charges and buys no labels.

Then **every adaptive randomized learner** satisfying the null risk and hard budget has
average expected gross decision regret over these alternatives at least

    R_gross >= Delta * sum_(j=0)^(h-1)
                         max(0, 1-alpha-B*max(0,j-d+1)/N).

With switch charge k>=0 and query charge c>=0 its average expected net-cost excess is at least
this quantity minus 2k. There is consequently at least one fixed onset with at least the average
lower bound. The same net lower bound holds against the best at-most-S switching oracle for
S>=2, since that oracle has no larger expected cost than this feasible comparator.

This is a lower bound on the original regret objective, not a detection-delay statistic conditioned
on successful detection. All missed pulses count. Granting the learner Delta and h does not
weaken the argument; nu and the pulse outcomes remain unobserved until queried labels arrive.

## Proof

Couple all the learner's private random coins across P0 and Pnu. Run the entire null trace and
let Q0 be its random requested-event set, with |Q0|<=B on every path. At the action in round
t=nu+j, a different label could have arrived only from a query in

    I_(nu,j) = [nu, nu+j-d],

which is empty for j<d. If Q0 misses this interval, induction in calendar time shows that the
alternative and null histories and decisions coincide through t. Indeed, no differing outcome
has been released before the next possibly differing decision. This statement does not assume
that the learner's query schedule stays unchanged *after* an informative label arrives.

Thus Pnu(A_(nu+j)=1)<=P0(A_(nu+j)=1)+P0(Q0 intersects I_(nu,j)). The first term is at most
alpha by the global false-promotion constraint. For fixed j, each null query s belongs to at
most w_j=max(0,j-d+1) of the intervals I_(nu,j), as nu ranges over 1,...,N. The union bound
and pathwise cap give

    sum_nu P0(Q0 intersects I_(nu,j)) <= E0[|Q0|]*w_j <= B*w_j.

On each pulse round, action 0 incurs Delta extra loss. Averaging the preceding inequality over
nu yields at least Delta*(1-alpha-B*w_j/N) expected extra loss at relative time j. Since extra
loss is also nonnegative, clip at zero and sum over j. Outside the pulse both action losses are
equal. Learner query/switch charges are nonnegative; comparator switch charges are at most 2k.
This proves both statements. QED.

## Interpretation and limitations

- For h<=d, the complete pulse is hidden until after its useful decision window. Gross regret
  is at least (1-alpha)*Delta*h even with B=T.
- For d<h and B*h/N small, much of the pulse is necessarily missed regardless of adaptive
  allocation. A lower bound exists even in a noiseless problem; noise adds other difficulty.
- This is an onset-average lower bound and hence a worst-onset bound. It does not prove uniform
  querying is minimax optimal, determine the noisy information term, or rule out useful gains.
- It uses the declared global-null promotion risk, not a future-profit certificate. It makes no
  conditional-risk or real-data guarantee outside the specified deterministic environments.
- Arbitrary late short harmful regimes cannot be uniformly rescued by a new controller. Any
  advantage claim must specify the exploitable information or regime class and remain valid
  against comparators with access to that same information.

## Related work: novelty remains to be checked

[Geng–Bayraktar–Lai (IEEE TIT 2014)](https://faculty.engineering.ucdavis.edu/lai/wp-content/uploads/sites/38/2021/06/06862025.pdf)
already study Bayesian quickest detection with finite observation rights. Sections II–III,
the posterior recursion and Theorem 1's dynamic-programming statement were inspected. The
change-time prior is geometric; their objective combines false alarm probability and average
detection delay. Their theorem is not the displayed finite-horizon switching-regret inequality,
but it is direct precedent for finite observation rights and optimal acquisition. Full independent
proof verification was not performed. Do not claim the hard-budget obstruction as new.

Primary-source verification corrected a version/title issue: arXiv:1501.05930v5 is
[Chandar–Tchamkerten, *Sampling Constrained Asynchronous Communication: How to Sleep Efficiently*](https://arxiv.org/pdf/1501.05930),
whereas the transient-detection title belongs to an earlier version. Section III's transient model,
Theorem 5 and Section IV.B's converse and Lemma 1 proof were inspected. Their observation-rate
criterion is probabilistic, their onset uncertainty grows exponentially with pulse length and
their theorem is asymptotic. **The null-trace interval-coverage coupling used above is already
present in their Lemma 1 proof.** Our finite-horizon clipping, explicit label delay and costed
regret translation are supporting refinements, not a defensible standalone ICML novelty claim.
Their multiphase adaptive sampling also defeats novelty from sparse scouting followed by
increasing confirmation batches. A candidate must compare against that stronger mechanism.

Source URL/hash records are in `switching_source_manifest_v3.json`; primary PDFs stay in the
ignored source cache. No inference about absent prior results rests on a search snippet.

## Registered analytical check (before execution)

Implement `scripts/check_switching_budget_lower_bound.py` to enumerate every deterministic
null query set for T=1,...,9 and all h,d in 1,...,T. Verify interval-hit counting and the gross
bound at alpha=0 against a learner granted immediate knowledge of the onset on the first
arrived informative label. Also compare the analytical uniform-without-replacement miss
probability to exhaustive subset averaging. No random streams, fitting, tuning, confirmation
seeds or real data are used. Record a source hash with results. This is a proof/implementation
sanity check, not an efficacy experiment or evidence of novelty.

For uniform B-subset queries, before the first informative arrival the miss probability at
relative time j is exactly choose(T-w_j,B)/choose(T,B), with impossible binomial counts zero.
The resulting expected missed pulse rounds are the sum of these terms. This gives a useful
explicit reference curve; it does not establish optimality over all acquisition policies.

## Execution and research decision

The registered checker passed all 67,578 schedule/length/delay cases over 1,022 null query sets
with T<=9. The uniform-subset formula agreed with exhaustive averaging to 8.89e-16.
Ruff and formatting checks passed. Reproduce with:

    python scripts/check_switching_budget_lower_bound.py

Output: `outputs/switching_budget_delay_lower_bound_v1/checks.json`, including script SHA256.
This finite enumeration checks the occupancy arithmetic and alpha=0 specialization. The proof,
not enumeration of deterministic schedules, is what covers arbitrary adaptive random policies
and alpha>0. No claim of independent proof review or new statistical calibration is made.

**Decision:** keep this obstruction in the mathematical contract and rule out uniform rescue
of arbitrary unannounced short regimes. Do not nominate the lower bound or the classical
scout-and-confirm mechanism as our contribution. The hypothesis must specify a regime/information
structure where economically directed acquisition improves over the strongest multiphase and
cost-aware comparators. That advantage remains to be derived and tested; G1 is still open.
