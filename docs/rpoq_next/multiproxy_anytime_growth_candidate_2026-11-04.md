# Multi-proxy anytime evidence growth: candidate screen

**Status:** source-audited research hypothesis; not yet a method lead or novelty claim.

## Why this is the next candidate to screen

The local history-predictable-bound method has two disjoint synthetic confirmations: it increased
detection by 3.95 points on an independent-stream design and 5.66 points on a Markov-volatility
design versus its fixed-bound pair, while using about 135 fewer labels. Those are real positive
results for the registered generators, but they do not compare against the strongest active-
evidence query rules and the construction itself is standard.

Three primary sources expose a narrower intersection worth one development screen:

| Source | What it establishes | Contract missing from that source |
|---|---|---|
| Hsu and Shekhar, [*Efficient Sequential Evaluation of Large Language Models*](https://arxiv.org/html/2607.17409v1), §§3–6 | Time-uniform test-supermartingale confidence sequences and growth-oriented adaptive querying, including practical prediction-based rules | One target proxy family over a fixed question bank; it does not jointly optimize multiple per-event predictor subsets, delayed releases, and a pathwise pending-inclusive query cap |
| Sfyraki and Wang, [*Revisiting Active Sequential Prediction-Powered Mean Estimation*](https://arxiv.org/html/2604.18569v1), §§4–6 | Sequential active PPI mean estimation, non-asymptotic time-indexed concentration, and a query rule that can favor the budget ceiling | A scalar proxy/variance-oracle design; its budget is an expected sampling-rate constraint, and it does not provide the same anytime e-process plus fixed-delay hard-cap contract |
| Brawand et al., [*Active Multiple-Prediction-Powered Inference*](https://arxiv.org/html/2605.08429v1), §§3–5 | Cost-aware per-instance routing over predictor subsets, joint labeling and proxy weighting, and asymptotic variance optimality | Fixed-horizon asymptotic confidence intervals on i.i.d. instances, without an anytime sequential risk bound or delayed hard-cap protocol |

These are adjacent contracts, not a novelty proof. The proposed distinction is the **joint** use of
multiple proxy predictions and eventwise evidence-growth acquisition for one anytime-valid sequential
decision under delayed feedback and a pathwise cap. Hsu already covers growth-based querying, while
AM-PPI already covers multi-proxy routing; a direct combination may still be too routine. The screen
must show either a nontrivial oracle-regret/rate statement or a material power-per-label improvement
over faithful versions of both families.

## Validity lemma to anchor an implementation

Let the bounded paired outcome be `D_s in [-M,M]`. At issue time `s`, choose a proxy
`H_s` as a convex combination of bounded predictions, so `H_s in [-M,M]`, and a query propensity
`q_s >= q_min > 0`. Draw `Q_s ~ Bernoulli(q_s)` independently of `D_s` conditional on the
pre-query information. Define the prediction-powered increment

```text
X_s = H_s + Q_s (D_s - H_s) / q_s.
```

If the query propensity and proxy are chosen without seeing `D_s`, then averaging over the query
coin gives `E[X_s | pre-query history] = E[D_s | pre-query history]`. Also
`|X_s| <= M(2/q_min - 1)`. Thus, under the **event-time** conditional null
`E[D_s | G_s] <= 0`, where `G_s` contains all information available before the event-s
query coin and outcome, the factor
`1 + lambda_s X_s / B`, with `B=M(2/q_min-1)` and predictable `lambda_s in [0,1]`, is a
nonnegative e-factor. A product or fixed mixture of such processes controls anytime crossing by
Ville's inequality. Stop issuing requests before the pathwise cap, counting pending labels at
request time.

The event-time process is valid because its conditional expectation averages over the current
query coin. The arrival-time filtration generally reveals that coin before the label arrives, so
the same increment need not be a supermartingale in that filtration. The implementation's
contiguous-prefix alarm rule avoids needing that stronger claim: every alarm is pathwise a crossing
of the valid event-time process. An arrival-time conditional null is not the condition used by this
lemma. Separately, if later policy-visible features predict earlier outcomes, the event-time null
must condition on the full history used by the policy; a marginal or issue-time null alone is not
enough. The local proof note `docs/delayed_event_prefix_validity.md` states this scope.

The validity lemma is standard composition. It is included to make the experiment's null, event
clock, and bound auditable, not as the novelty delta.

## Frozen development question and stop rule

Test a deliberately complementary-proxy stream where proxy A is accurate on one observable stratum
and proxy B on another, with a held-out regime that swaps which proxy is better. Use the same event
outcomes, delay, hard cap, label price, e-process family and query random numbers for:

1. Uniform querying with the strongest available one-proxy PPI e-process.
2. Variance-directed active PPI and the Hsu–Shekhar growth-oriented adaptation, both given the same
   pilot proxies and the same hard-cap stopping wrapper.
3. AM-PPI-style proxy routing followed by an anytime PPI e-process, with its expected-cost design
   adapted to the same realized cap.
4. A joint proxy/query rule that maximizes pilot-estimated worst-case e-log growth, with all query
   decisions fixed before the current label and all proxy choices bounded by the same global `B`.

Keep the null family nondegenerate and conditional-mean-valid; calibrate every arm on independent
null streams before evaluating power. Primary outcomes are power by a fixed deadline and labels to
first crossing at the same familywise `alpha`; report pre-change crossings as competing outcomes.
The reversal block is a required robustness cell, not a tuning target.

**Stop before confirmation** if the joint rule does not beat the strongest of arms 1–3 on the
predeclared power-per-label frontier, if it violates simultaneous null calibration, or if its gain
vanishes when the favored proxy switches. Do not claim novelty from the theorem lemma alone. If the
screen passes, the next gate is a disjoint independent-stream confirmation and a source-level
oracle-rate analysis; the exposed CRSP and five-stream UCI suites remain development-only.

## Source-read detail

- Hsu–Shekhar formulate a finite question set with independent question-level correctness variables,
  construct time-uniform CSs by inverting test supermartingales, and choose queries through a
  worst-case one-step expected log-growth surrogate. They explicitly report that uniform can beat
  their adaptive rules.
- Sfyraki–Wang study a sequential mean estimator whose guarantees use martingale concentration and
  expected budget-rate constraints. Their scalar-query/variance tradeoff is not a hard-cap,
  delayed e-process test of paired model replacement.
- AM-PPI's Theorem 1/Corollary 1 give asymptotic normality and asymptotic coverage under i.i.d.
  instances and propensity bounded away from zero. Its optimization minimizes asymptotic AIPW
  variance; predictor routing, query sampling, and proxy weights are jointly optimized.

These full-text reads replace the old snippet-only/unread labels for these three sources in the
RPOQ-next source audit. They do not change the closed status of historical Candidates A–C.
