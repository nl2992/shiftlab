# Exact screen: one-step economic information under a safety gate

> **Scope update:** This is a fixed-gate counterexample, not an intrinsic label requirement for
> every alpha-safe policy. See [the risk-frontier audit](switching_risk_frontier_audit_v1.md).
> Historical calculations remain valid; the Bellman optimum here is only within its stated gate.

2026-10-28. Registered before code execution. **Mechanism hypothesis, not a novel method.**
The previous continuation's repository read alone was no progress; this registered counterexample
and executable exact comparison advance the mechanism decision. Historical protocols are unchanged.

## Candidate and rejection criterion

Test the plausible rule 'buy a label when its expected improvement in future switching utility,
integrating pending outcomes, exceeds its price'. The precise candidate evaluates one additional
query and then optimizes all future actions assuming no further acquisitions. It repeats that
calculation at every decision round. Existing pending observations are included. This is
one-step value of sample information (VOI); its decision relevance and pending-label awareness
alone are already established ideas, not a new contribution.

Reject this candidate if it takes no samples in the instance below while an equally equipped
admissible acquisition/action policy has strictly better expected net cost. An exact Bellman
solution is the established comparator/upper performance frontier in this known finite model,
not the proposed contribution. No tuned simulation, real data or confirmatory efficacy claim.

## Frozen model

T=20 rounds; hard budget B=3 labels; delay d=2; query price c=1/100; switch charge k=1/10;
initial policy 0; prior mass 1/2 each on theta=1/4 and theta=3/4. Conditional on theta, labels
Y_t are IID Bernoulli(theta). A queried label reveals losses l_t(0)=Y_t and l_t(1)=1-Y_t;
unqueried outcomes remain hidden. Outcomes and query coins are independent of deployment.
Covariates are constant. Both methods know the same prior, law, costs, horizon and delay.

At the start of each round, reveal the labels due then, choose action and query, and charge
costs. Query at t arrives at the start of t+2. Charge every request immediately. The posterior
depends on arrived counts (n,s), while the pending queue records requests by due time.

For a frequentist false-promotion constraint under theta=1/4, permit a 0->1 promotion only when
the likelihood ratio L=3^(2s-n) is at least 10 (alpha=1/10). Rollback to 0 is always allowed.
Under this IID null, predictable querying and deterministic delay preserve the likelihood-ratio
martingale on arrived queried outcomes; Ville's inequality controls any promotion by alpha.
The cap B=3 forces s=n=3 at any permitted promotion. This is a simple-null guarantee, not a
conditional-drift or future-profit certificate. It is an exact special case on which a general
acquisition rule must at least avoid the cold-start failure.

## Analytical counterexample before computation

Initially, a lone label cannot make L>=10: its largest likelihood ratio is 3. With no other
pending or future queries, promotion remains prohibited, so both possible label values leave
the deployment action at 0. Every single query has zero deployment VOI and positive cost.
The candidate therefore never queries and incurs prior expected cost T/2=10.

Now consider the feasible policy requesting at t=1,2,3, promoting at t=5 only if all three
labels are positive and holding 1 thereafter. Otherwise it stays at 0. It uses exactly B labels.
The probability of three positives is ( (3/4)^3+(1/4)^3 )/2=7/32. The posterior-weighted
per-round improvement on that event is 13/128. There are 16 rounds from 5 through 20.
Thus its expected net improvement over never switching/querying is

    16*(13/128) - (1/10)*(7/32) - 3/100 = 2517/1600 = 1.573125.

Its expected cost is 13483/1600=8.426875 and its null promotion probability is (1/4)^3=1/64.
No expected-budget relaxation, extra candidate access, quicker feedback or looser gate is used.
The Bellman optimum must have cost at most 8.426875. It may save a query when early negative
feedback renders the gate unreachable. Label complementarity, rather than an outcome-model
failure, defeats one-step acquisition here.

## Exact computation and checks

Implement `scripts/screen_switching_economic_acquisition.py` using rational arithmetic and a
memoized finite-horizon Bellman recursion on (round, remaining budget, arrived n,s, pending
request queue, previous action). All queries cost budget at request time. Future label branches
use the posterior predictive probability. Current expected losses and switch charges are included.
Also implement the candidate's one-query-versus-no-query planner using the same no-more-query
action optimization, and evaluate its resulting policy recursively. Reconstruct the optimal
policy's exact null promotion probability as a separate calculation under theta=1/4; do not
confuse Bayes expected cost with a frequentist error probability.

Before calling the screen complete require: candidate cost exactly 10 with zero queries;
Bellman cost no greater than the explicit feasible policy; null promotion probability <=1/10;
all branch budgets and queue clocks valid; pending outcomes integrated rather than imputed;
and a result file containing parameters, exact rational values and source hash. This is an
analytical mechanism rejection test, not a synthetic efficacy study of a new method.

## Contribution boundary

Chick–Forster–Pertile's costed delayed experimentation and standard sequential design already
motivate the Bellman comparator. Multiple-label complementarity is not a new theorem merely
because a switching certificate exhibits it. If the candidate fails, adding generic multistep
look-ahead or a scout/confirmation phase does not pass novelty: those mechanisms are also prior
work. A viable new rule needs a substantive, efficient joint allocation insight and its own
performance result beyond these constructions. The full methodological goal remains unchanged.

## Result: reject the candidate

The rational-arithmetic run returned:

| Quantity | Exact value | Decimal |
|---|---:|---:|
| One-step candidate expected cost | 10 | 10 |
| One-step expected label requests | 0 | 0 |
| Bellman expected cost | 539/64 | 8.421875 |
| Explicit three-query policy cost | 13483/1600 | 8.426875 |
| Candidate excess cost over Bellman | 101/64 | 1.578125 |
| Bellman promotion probability under null | 1/64 | 0.015625 |

The Bellman calculation visited 297 memoized states. A separate forward occupancy calculation
using each *true* theta, rather than posterior-predictive branches, reproduced its Bayes value.
Under theta=1/4 it requested 9/4 labels on average and had expected cost 16477/3200;
under theta=3/4 it requested 11/4 and had cost 37423/3200. Every branch obeyed B=3.
Their equal-weight cost average is 539/64. The optimal policy improves the explicit feasible
policy by 1/200, consistent with canceling the third request after a first negative label.

Reproduce with:

    python scripts/screen_switching_economic_acquisition.py

Output: `outputs/switching_economic_acquisition_screen_v1/results.json`, including exact values,
parameters, forward checks and script SHA256. Ruff and formatting checks passed. This is an
exact stationary counterexample and correctness screen, not a broad empirical comparison,
confirmation or real-data result. No independent proof review has been performed.

## Why a fixed-depth patch is insufficient

**Supporting proposition; originality unestablished.** In the same two-hypothesis label model,
let a 0->1 gate require likelihood ratio at least 3^m, with budget B=m, positive query price,
no initial pending labels and equal prior probabilities. Any rule evaluating plans with fewer
than m additional labels and assuming no acquisitions thereafter assigns zero deployment value
to every plan at the initial state: even all positive outcomes yield likelihood ratio at most
3^(m-1). It therefore buys no label. Repeating the calculation leaves the same state.

Yet querying at 1,...,m and promoting at m+d only if all m labels are positive gives expected
net improvement over no acquisition of

    (T-m-d+1) * ((3/4)^m-(1/4)^m)/4
      - k*((3/4)^m+(1/4)^m)/2 - m*c,

for T>=m+d. This is strictly positive for sufficiently large T at fixed m,d,k,c. Its null
promotion probability is (1/4)^m<=3^(-m), so it meets the matching likelihood-ratio risk gate.
Thus no fixed finite acquisition depth with a no-future-query continuation can guarantee a
uniformly useful approximation across certificate depths. This is a restricted-class failure,
not an impossibility result for multistep or adaptive sequential acquisition generally.

There is also an exact reachability pruning rule: with action 0, arrived log-likelihood ell,
r pending labels and b unused requests, no future promotion is possible if

    ell + (r+b)*log(3) < log(1/alpha).

In this stationary model, additional labels then cannot change any deployed action; positive-cost
querying is dominated. This explains the canceled request, but branch-and-bound reachability
and multistep planning are established ideas. Neither proposition is nominated as novel.

## Updated hypothesis decision

**NO-GO for one-step economic VOI, even when pending labels are integrated.** This is a concrete
rejected acquisition mechanism, not a claim that the full research direction is impossible.
Any next mechanism must price sequences that can actually reach the statistical gate, account
for their delay before utility accrues, and reserve budget for later decisions. Merely increasing
look-ahead to a fixed number of labels or using the exact Bellman recursion is not a contribution.
The missing advance is an efficient rule with a performance guarantee beyond those established
approaches, followed by matched nonstationary and real-data evidence.
