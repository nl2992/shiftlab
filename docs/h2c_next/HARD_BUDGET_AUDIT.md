# Hard query-budget audit (budget = half the expected number of queries over T = 2000; queries charged when issued)
Budget 100 queries (10% labels) / 200 (20% labels): the stream stops issuing queries once the budget is spent. Two treatments of the evidence after exhaustion: `naive` keeps the nominal propensity q in the IPW weight although the realised inclusion probability is 0 (wrong propensity); `stop` sets the bet to zero after exhaustion. Null FA / harm power (concept δ=2 at t0=700):
| labels | rule | discounted (C1) | H2c |
|---|---|---|---|
| 10% | naive | .013 / .035 | .005 / .083 |
| 10% | stop | .013 / .030 | .005 / .077 |
| 20% | naive | .007 / .080 | .010 / .195 |
| 20% | stop | .003 / .068 | .010 / .168 |
**Findings.** (i) The naive treatment does not inflate false alarms here: with no labels the increment collapses to proxy − nominal, which is ≤ 0 on a calibrated source, so the error is conservative in this null; it would not be safe for a model whose proxy exceeds the nominal. This is an observation about this null, not a validity argument, and the recorded propensity (nominal q) differs from the realised one after exhaustion, so `naive` has no IPW guarantee. (ii) `stop` is the defensible rule and costs 0.003–0.027 power relative to naive. (iii) The budget was exhausted at roughly step 1000 (10%/20% labels), after the shift at 700, so detection power collapses (≤ .20) for every method: a hard budget this small is the binding constraint, not the algorithm. (iv) Pathwise compliance is by construction (the mask is truncated after the B-th query). Not tested: budget-pacing policies, reserve-for-alarm strategies.
