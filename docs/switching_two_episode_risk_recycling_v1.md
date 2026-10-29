# Two-episode conditional risk recycling: exact toy frontier

**Date:** 2026-10-28. **Status:** exact two-look calculation; baseline diagnosis only.

## Contract slice

There are at most two promotion attempts. At each attempt, request one binary common-outcome label; its fixed delay is one round. If a promotion occurs, stop. Otherwise, a second query and attempt are allowed. A label is positive with conditional probability at most `1/2` under the full-history null. Each attempt independently promotes on a positive label with probability `gamma_i`, using private randomness. Under a stationary working alternative, labels are independent Bernoulli(`q`) with `q>1/2`. This slice isolates error allocation; it omits rollback economics, query fees and a changing alternative, so it is not the target algorithm.

## Exact causal-null risk

Let `a_i=gamma_i/2` be the local worst-case false-promotion probability for attempt `i`. For any causal conditional null, the probability of ever promoting is

```text
r = p1*gamma1 + (1-p1*gamma1)*p2*gamma2,
```

where `p1,p2` are conditional positive-label probabilities along the no-promotion branch. This expression is nondecreasing in both `p1,p2` on `[0,1/2]`; its maximum is attained at `p1=p2=1/2`. Therefore

```text
r = a1 + (1-a1)*a2 = 1 - (1-a1)(1-a2).
```

This is exact under the full-history conditional null, not just an IID calibration. To use total risk `alpha`, the admissible levels satisfy `(1-a1)(1-a2)>=1-alpha`. Equal Bonferroni allocation `a1=a2=alpha/2` is conservative, with risk `alpha-alpha^2/4`. A conditional-error allocation can exhaust the risk exactly: for any `a1<=alpha`, set `a2=(alpha-a1)/(1-a1)`.

Under the IID stationary alternative, probability of any promotion is `1-(1-q*gamma1)(1-q*gamma2)`. At `alpha=1/10`, `q=9/10`, equal Bonferroni levels `(a1,a2)=(1/20,1/20)` yield promotion probability `1719/10000`. The exact conditional allocation `(a1,a2)=(1/20,1/19)` yields `837/4750`. Both use the same expected query count `1+(1-q*gamma1)=191/100`, since the second query is issued only after no first promotion.

## Decision

Conditional-error spending improves on a union-bound allocation in this two-look example, but the multiplicative familywise-risk formula and predictable conditional error allocation are standard sequential-testing machinery. Posch and Bauer's primary paper on adaptive two-stage designs explicitly uses the conditional error function to permit data-dependent sample-size reassessment while retaining the alpha level ([Biometrical Journal, 1999](https://onlinelibrary.wiley.com/doi/pdf/10.1002/%28SICI%291521-4036%28199910%2941%3A6%3C689%3A%3AAID-BIMJ689%3E3.0.CO%3B2-P)). That source does not supply our hard query cap or switching problem, but it closes generic conditional-error recycling as a novelty claim. The toy separation does not establish an acquisition advantage and contains no model switching or reversal. Do not elevate it to the method. Retain it as a correctness baseline for future adaptive episode-risk allocation; a candidate must prove value beyond this standard procedure and existing constrained-planning/sequential-design references.
