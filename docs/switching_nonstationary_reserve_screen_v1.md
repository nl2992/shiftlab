# Nonstationary acquisition/reversal screen: one reserved observation

> **Scope update:** The joint Bellman optimum below is constrained by a particular e-product
> gate, not optimized over every policy meeting the same global-null error bound. See
> [the risk-frontier audit](switching_risk_frontier_audit_v1.md). The numerical results remain
> correct within that gate; none establishes a full statistically admissible frontier.

2026-10-28. Registered before execution. Prior turn: progress (nonstationary information/safety
contract and 50 targeted checks). This is a finite analytical development screen, not a new
algorithm nomination, G3 confirmation or a replacement for the intended methodological result.

## Question and fixed design

Does retaining one of five request rights for after promotion improve net cost over immediately
spending the cap, in a recurrent regime model? Is a fixed reserved observation competitive
with contingent acquisition under the same information, costs, delay and promotion gate?

Use the model in `switching_nonstationary_contract_v1.md`: T=12, B=5, known symmetric transition
rate 1/20 per event, emission probabilities 1/20 and 19/20, and prior S0=1. A degenerate initial
prior is shared working-model information; realized future states remain unknown to every method.
Query charge 1/100, switch charge 1/10; delay d in {1,2}; alpha=1/10. Report both delay cells.
The model is correctly specified for this screen. Do not infer robustness to unknown regimes or
prospective real-data validity from it.

Working-model forecasts propagate the last observed-event posterior to current t. Evidence uses
the clipped predictive likelihood factor from the nonstationary contract and global conditional
no-benefit null. Any 0->1 action requires e>=10; returning to 0 is always allowed. The statistical
constraint is not relaxed for any policy, and all outstanding rights count immediately.

## Methods

1. **Frontload:** request every round until five rights are spent, excluding requests that could
   not arrive before T. Use the costed action rule below.
2. **Reserve one, wait two/four:** spend at most four rights until the first promotion. The fifth
   request becomes eligible two/four rounds after that promotion. If no promotion occurs, retain
   the right unused. Same action rule and clocks; do not force a fifth query merely to match counts.
3. **Exact joint Bellman:** optimize action and query on the full learner-visible state, including
   remaining rights, pending event times, last-observed posterior/time, wealth and previous action.
   This is the established optimal-control comparator under the known working model, not a new
   algorithm. It must be no more costly than any tested feasible policy.
4. **No query, continue:** stays at policy 0; report its model-expected cost, not T/2 by assumption.

For the heuristics, compare the current action with switching and committing through T based on
the current forecast, charging a switch once. If the two expected costs tie, retain the current
action. This is a specified heuristic, not a future-benefit certificate. Apply the e gate before
allowing promotion. The exact planner can value future reversals and query cancellation.

## Exact evaluation and checks

Use rational arithmetic and memoization, not Monte Carlo or sampled hidden trajectories. At a
future label release, branch using the working-model predictive probability for that label's
*event*, update its event posterior/evidence, and propagate onward for subsequent current costs.
Current expected costs are computed from current-time beliefs. The learner state never contains
the actual hidden state or unqueried Y. Bounded computation: stop with an incomplete-screen
record if a cell exceeds 100,000 planner states; do not silently shrink parameters or alter the
protocol to obtain a result. Do not launch a broader grid from these development cells.

Check full state conservation on every branch, exact Bellman dominance, model forecast timing,
and null promotion probability by a separate recursion under IID Bernoulli(1/2) labels. For that
null calculation continue to choose actions using the same fixed working model. Report query
counts, switches, rollbacks, and losses separately alongside total net cost. At least one method
must permit contingent actions after promotion; do not use a one-shot adoption comparison.

Reproduce with:

    $env:PYTHONPATH = (Resolve-Path src).Path
    python scripts/screen_switching_nonstationary_reserve.py

Results must include all specified policies/cells, exact values, source hashes and planner-state
counts at `outputs/switching_nonstationary_reserve_screen_v1/results.json`. This finite model's
Bellman value is not a novel regret theorem or comparison to all published algorithms. If a
simple reserved label helps only in a chosen cell, keep the result scoped and do not rebrand
the heuristic. A new mechanism still needs a specific derivation, source-level novelty delta,
theoretical advance, matched synthetic evidence and an eligible real-data task.

## Results and verification

Both fixed cells completed below the 100,000-state cap: 73,237 Bellman states for d=1 and
46,935 for d=2. Exact expected net costs, rounded here only for readability:

| Policy | Delay 1 | Delay 2 |
|---|---:|---:|
| Continue without querying | 8.906160 | 8.906160 |
| Frontload all rights | 5.968891 | 6.505832 |
| Reserve one, wait two | 5.784542 | 6.353344 |
| Reserve one, wait four | 5.753502 | 6.429769 |
| Exact joint Bellman | 5.745112 | 6.350564 |

Every policy that promoted had null promotion probability 1/16 under IID Bernoulli(1/2),
below the declared 1/10 bound; continue had zero. This is a scoped exact error calculation,
not a claim of per-switch benefit in the recurrent model. All branches met the same hard cap.

Retaining a right helped over frontloading in these two cases. The better fixed wait changed
with delay: four for d=1, two for d=2. Higher rollback frequency did not automatically imply
lower cost. Frontload had no rollbacks at d=2; reserve-four rolled back more often than
reserve-two but cost more. The exact planner optimized the whole path rather than maximizing
rollback count. Neither fixed reserve schedule matched it.

For d=2, the exact planner and reserve-two have the same expected decision loss and switching
charge; their 0.00278 total-cost gap is exactly 0.278 fewer requests at price 0.01. For d=1,
the exact planner also changes action timing. These distinctions are recorded in the full
decision/query/switch decomposition; do not attribute every gain to earlier reversal.

A second forward evaluator explicitly evolved hidden state S_(t-1)->S_t, sampled queried
Y_t conditional on the actual state and held pending outcomes until their due rounds. It
reproduced all six expected metrics for all ten policy/delay combinations as exact fractions.
Only the evaluator held hidden states and unreleased labels; policy decisions used the visible
state. This check shares the posterior-state update routine with backward planning, so it is
not a fully independent implementation. It independently checks the latent-law weights and
current-time expected costs, with the information module's hidden-path tests checking filtering.

Ruff check, formatting and Git whitespace checks passed. Results record both implementation
hashes and `latent_forward_verified` for each policy. No wider sweep, statistical confirmation,
dynamic-oracle regret computation or real-data scoring was performed.

## Research decision

**Continue toward an adaptive allocation derivation; do not nominate a fixed reserve rule.**
This screen makes the original pre-rollback-loss issue concrete in a model with delayed,
budgeted evidence and an explicit null-risk gate. It also supplies a stronger known-model
joint-planning reference. A reserved observation is useful here, but reserving one label and
choosing a wait is ordinary scheduling, not an ICML-level contribution. The small cells cannot
establish broad superiority or a need for a new algorithm over published POMDP methods.

Next derive a scalable contingent allocation rule and a defensible performance advantage, or
reject that hypothesis. Its theory must distinguish hard-cap rights from expected-budget
relaxations and account for the certificate's label complementarity. Do not keep enlarging
this known-model grid or report its utility improvement as the sought novel-method result.
