# Certificate-reaching burst rollout: finite screen

> **Scope update:** All optima and comparisons here are within the declared evidence gate.
> [The risk-frontier audit](switching_risk_frontier_audit_v1.md) supplies equally valid decisions
> outside that gate; this screen does not characterize the entire alpha-safe frontier.

2026-10-28. Registered before execution. Previous turn: progress (exact rejection of one-step
VOI). This is a bounded mechanism/equivalence screen, not G3 efficacy evidence or a new method.

## Rule and equivalence verdict

Retain the exact stationary two-law model from `switching_economic_acquisition_screen_v1.md`.
At each state, evaluate every feasible number n of consecutive new requests starting now.
During that committed request sequence, optimize action decisions using all labels that arrive;
after the sequence, optimize actions with no more requests. Also evaluate no new requests.
Choose the plan of least expected net cost, execute only its first action/request, then replan.
The policy integrates all pending label outcomes, charges queries at request, obeys the hard cap
and uses the same likelihood-ratio promotion gate.

This is **ordinary multistep rollout over a restricted plan library**, with the no-more-query
policy as its base. Certificate reachability allows pruning impossible promotion plans, but
does not change that equivalence. Neither optimizing a batch nor replanning after an arrival
is a substantive novelty claim. Do not nominate this rule as the contribution even if it wins
over one-step VOI. Its role is a stronger reference for subsequent acquisition research.

## Supporting guarantee, not a novel theorem

Let V0(s) be the optimal future action cost when no further queries are allowed. Let B_n(s)
be the value of committing to n consecutive new requests followed by V0, with optimal actions
throughout, and define W(s)=min_n B_n(s), including n=0. For every state of this finite model,
the receding-burst policy has value V_R satisfying

    V_opt(s) <= V_R(s) <= W(s) <= V0(s).

Proof: if the chosen plan starts a nonempty burst, its successor continuation is B_(n-1),
while W at that successor is no greater. If it chooses no burst, the successor continuation
is V0 and W is again no greater. Backward induction in remaining calendar rounds therefore
gives V_R<=W. The n=0 plan gives W<=V0 and optimality gives V_opt<=V_R. This is the usual
rollout improvement argument. It neither bounds the gap to V_opt nor extends to misspecified
or nonstationary outcome laws. A strict cost win over the no-query base alone is insufficient.

## Frozen finite grid and checks

Use exact rational arithmetic, not Monte Carlo. T=20, equal prior on theta in {1/4,3/4},
alpha=1/10, B in {3,5}, d in {1,3}, c in {1/100,1/5}, k in {1/10,1}: 16 development cells.
These are mathematical stress cases, not independent confirmations. Freeze this grid before
evaluating it; report every cell, including ties and failures.

Compare exact full Bellman, one-step VOI, receding-burst rollout and no query. All methods share
the prior, label model, delay, request cap, switching charge and promotion gate. Enforce the
state conservation identity observed+pending+remaining=B on every branch. Enumerate the
rollout's null promotion probability under theta=1/4 separately from its Bayes expected cost.
Check V_opt<=V_R<=W<=V0 exactly, include query counts, and record source hashes for the new
script and its imported earlier exact model. Require at least one strict improvement over
one-step VOI to show that the implemented rule addresses the diagnosed label complementarity;
this does not make it novel. Do not claim optimality from agreement on a finite grid.

Reproduce with:

    python scripts/screen_switching_certificate_bursts.py

Output: `outputs/switching_certificate_burst_screen_v1/results.json`.

## Next methodological obligation

Any later rule must justify its departure from this standard plan-library rollout, a full
Bellman solution and published multiphase sampling. Computational savings must be compared at
the same decision quality, not asserted from a shorter search horizon. Dynamic regime changes,
unknown-law guarantees, reversal losses and eligible real-data timing remain required. A win
on this stationary finite screen does not satisfy those requirements.

## Results and decision

All 16 cells passed exact Bellman/rollout/base ordering, budget conservation and null-risk checks.
Rollout strictly improved on the one-step rule in all 16 cells; it equaled the Bellman value in
12 and had strictly higher cost in four. All four gaps occurred at B=5 and query cost 1/5:

| Delay | Switch cost | Exact Bellman cost | Burst rollout cost | Excess cost |
|---:|---:|---:|---:|---:|
| 1 | 1/10 | 16547/2048 | 41949/5120 | 1163/10240 |
| 1 | 1 | 17177/2048 | 8667/1024 | 157/2048 |
| 3 | 1/10 | 17601/2048 | 17829/2048 | 57/512 |
| 3 | 1 | 18231/2048 | 18459/2048 | 57/512 |

Independent forward occupancy calculations under theta=1/4 and theta=3/4 reproduced the
posterior-predictive backward rollout costs and expected query counts in every cell. The null
forward promotion probabilities matched the separate null recursion. These checks were added
as verification of the registered calculation, not additional tuned evaluation cells.

For B=5,d=1,c=1/5,k=1/10, a positive-probability decision discrepancy is already present at
round 2 after the first negative label: state (budget=4,n=1,s=0,pending=empty,action=0).
Rollout requests no label; the full Bellman planner requests one. Taking the rollout's immediate
decision and then behaving optimally has excess expected cost 39/1024 at that state. The state
has probability 1/2 under their common first-round query. The exact planner values a contingent
future sampling plan, including its option to cancel after further negative outcomes. Pricing
only unconditional consecutive batches can miss this value even though execution later replans.
This discrepancy is a local diagnosis, not a decomposition of the entire initial-state gap.

**Novelty verdict: NO-GO as a proposed contribution.** The exact cost improvement follows the
standard rollout argument. Author-hosted prior descriptions explicitly cover multistep and
selective-depth rollout with a base heuristic; see
[Bertsekas et al., rollout for stochastic scheduling](https://faculty.engineering.asu.edu/bertsekas/wp-content/uploads/sites/129/2020/03/rollout_algorithms_for_stochastic_scheduling_problems.pdf)
and [constrained rollout](https://faculty.engineering.asu.edu/bertsekas/wp-content/uploads/sites/129/2020/03/Rollout_Constrained.pdf).
Those method-description passages were inspected; this is not a full source-proof audit or a
claim that either paper contains our particular likelihood-gated numerical instance.

Keep burst rollout as a matched reference. Do not relabel winning over the already-failed
one-step baseline as a methodological advance. Also do not keep expanding this stationary toy
grid in search of a publishable win: its purpose, exposing complementary evidence and the
value of conditional cancellation, is complete. The next derivation must address the original
nonstationary repeated-switch problem and a new performance advantage, rather than a cosmetic
repair of standard rollout.

Validation: Ruff check, Ruff format check and `git diff --check` passed. Results include exact
cell values, law-specific forward checks and both source hashes. No full repository test run,
new statistical calibration, independent proof review or real-data method evaluation is claimed.
