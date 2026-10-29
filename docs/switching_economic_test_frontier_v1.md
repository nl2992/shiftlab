# Exact economic test-design reference under the actual risk bound

2026-10-28. Registered before execution. Previous turn: progress (fixed-gate risk-frontier
restriction identified and checked). This repairs a comparator omission; it does not reopen
the stationary rollout grid or nominate a new algorithm.

## Exact reference class and guarantee

Use T=20,d=2,c=1/100,k=1/10 and alpha=1/10, with equal working-prior mass on stationary
theta in {1/4,3/4}. Losses are Y_t and 1-Y_t. The statistical null remains the composite
conditional bound E[Y_t|full past and query choice]<=1/2. An upfront private lottery selects
a query count n<=B and a terminal test. On that path, request events 1,...,n; decide at n+d
after all requested labels have arrived. Promote at most once and hold through T. The
no-query/no-promotion plan is available. Every lottery outcome obeys the hard cap; averaging
the query count is not a substitute for it.

Optimize the test itself rather than freezing an e-product. This class includes randomized
count-tail tests and randomization over cohort sizes. It excludes contingent query stopping,
multiple switches and regime changes. **The optimum is only within this stated reference class.**
It is a stronger missing comparator, not a claim to characterize the complete alpha-safe frontier.

## Elementary reduction (supporting mathematics, no originality claim)

For a fixed n, let H=T-n-d+1 and let s be the positive-label count. Under boundary-null
theta=1/2, each outcome word has probability 2^(-n). Its prior-weighted benefit from promotion,
before query charges, is

    a_s = ((H/2-k)*(3/4)^s*(1/4)^(n-s)
          +(-H/2-k)*(1/4)^s*(3/4)^(n-s))/2.

When H/2>=k, a_s strictly increases with s. If H/2<k, even perfect selection of the high law
cannot recover the switch charge over H rounds, so no positive-benefit decision is possible.
For fixed n, allocating error probability to words with the largest positive a_s/2^(-n) is
the standard fractional-knapsack/Neyman–Pearson exchange argument. Thus an optimal test
rejects above a count cutoff and may randomize at one count. No new statistical insight is claimed.

Every such rejection function is coordinatewise increasing. Coupling each null outcome to a
fresh uniform shows Y_t<=1{U_t<=1/2} under any predictable conditional success probability
<=1/2. Therefore the boundary IID null is least favorable. This proof covers the composite
conditional null, not merely IID theta=1/2. It also covers an upfront mixture: condition on its
independent coin, then average the valid null risks. Requests are fixed before their outcomes.

For each deterministic threshold (n,j), compute its boundary null risk r_(n,j) and expected
net gain g_(n,j), charging c*n even on nonpromotion outcomes. Include (0,0) for doing nothing.
Randomizing over plans solves a finite linear program: maximize expected gain subject to
total lottery mass 1 and average null risk <=alpha. Every point has n<=B. An optimum uses
at most two plans (an extreme-point argument with one risk constraint). Enumerating all single
points and all pairs straddling alpha therefore gives an exact rational solution. A concave-hull
implementation would be faster at large B; no computational-novelty claim is made for enumeration.

This is classical test design and finite constrained optimization. The randomized binomial
cutoff construction is described in [the Berkeley mathematical statistics notes](https://stat210a.berkeley.edu/fall-2024/reader/hypothesis-testing.html).
Economic sequential design has direct prior work including
[Chick and Frazier](https://people.orie.cornell.edu/pfrazier/pub/2012_ChickFrazier.pdf) and
[Hampson and Jennison](https://rss.onlinelibrary.wiley.com/doi/10.1111/j.1467-9868.2012.01030.x).
The relevant primary method descriptions were inspected, not their full proofs this session.
Their existence is an explicit warning against claiming economic/risk optimization as new.

## Frozen verification

Implement `scripts/solve_switching_economic_test_frontier.py`. For B=0,...,6, report all optimal
lottery weights, sample sizes, count cutoffs, expected costs, null risks and pathwise maximum
requests. At B=1, reproduce the optional-query one-label cost 4781/500=9.562 from the risk
audit. All costs must be nonincreasing with the cap; every positive lottery weight must use n<=B.

Verify each fixed-n optimum independently by enumerating all 2^n words and solving its
fractional-knapsack problem. Separately calculate the worst conditional-null rejection risk
by an adversary recursion that chooses each success probability in {0,1/2}; it must equal
the boundary-binomial risk for every deterministic count threshold. These are exact algebra
checks, not Monte Carlo, new efficacy evidence or independent proof review.

Reproduce with:

    python scripts/solve_switching_economic_test_frontier.py

Record full rational values, comparator class and source hash under
`outputs/switching_economic_test_frontier_v1/results.json`. Keep the full novel-algorithm,
theoretical-performance and real-data requirements open. The next research question concerns
joint *contingent* acquisition, test design and reversal under delayed nonstationarity, beyond
this fixed-cohort reference and the already-audited sequential-design methods.

## Executed result and decision

The registered calculation completed on 2026-10-28 with exact rational arithmetic. For hard
caps B=0,...,6, optimal expected costs within this class were respectively 10, 9.562, 9.1705,
8.7415, 8.60978125, 8.595578125 and 8.47019921875. Every positive-budget solution used null
risk exactly 1/10 and respected its pathwise cap. At B=4 the optimum mixes a four-query,
four-positive threshold (weight 2/5) with a three-query, three-positive threshold (weight 3/5).
Thus optimizing a single cohort at the maximum cap would omit useful randomized comparators.

All six fixed-cohort optima agreed with independent word-level fractional knapsack calculations
(126 total words). All 33 deterministic thresholds agreed with the conditional-null adversary
recursion. The B=1 cost reproduced 4781/500 exactly; costs were nonincreasing with the cap.
Ruff passed. These checks verify this reference calculation, not an independent theorem review.

Decision: retain this reference and stop expanding the stationary fixed-cohort calculation.
Do not compare its cost directly with the earlier likelihood-gated toy planner: that planner
used a different null and permits contingent acquisition and earlier action. The next mechanism
must declare the same null, admissible randomization, timing and policy class across comparisons.
Its technical delta must concern contingent acquisition/test/action decisions under delayed
nonstationarity and survive comparison to standard constrained sequential design. G1 remains open.
