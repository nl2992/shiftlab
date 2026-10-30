# G1 intersection screen: recurrent regimes, randomized intervention, finance task

**Date:** 2026-10-29. **Status:** task-contract and feasibility screen; no algorithm, theorem,
novelty claim, holdout access, or empirical result. This records the user's direction to pursue
all three structural dimensions together.

## Decision

The three dimensions can be represented in one mathematical model, but the repository does not
currently contain an eligible real task for that joint model. Treating them as independent features
of the old paired-loss replay would be incorrect. A fixed HMM for paired predictive losses is an
outcome model unaffected by the switching action; randomizing which predictor is deployed does not
make those evaluator-only paired outcomes causal or action-dependent. Conversely, once deployment
changes the reward or state transition, the two actions generally no longer have a common paired
outcome, and current value must be defined by a policy-level counterfactual estimand.

The existing Binance task is still useful for point-in-time recurrent-regime predictive-loss
diagnostics under its frozen price-taker idealization. Its held-out 2026 segment remains locked and
cannot test the proposed causal intervention claim. The general action-dependent route, known-HMM
confidence-set gate, and costed-sensing composition already have separate source screens; their
combination is not itself a novelty delta. No G1 candidate is selected by this screen.

## Candidate contract to reopen only if the data design is available

Use a finite controlled hidden Markov model with observed context `X_t`, latent recurrent regime
`Z_t`, and a randomized deployed policy/action `A_t` from a frozen set `{0,1}`. Both the outcome
kernel and latent transition kernel may depend on `A_t`; outcomes are bounded and released after a
declared delay. At each decision, the learner observes only the context, assignment propensity,
past assignments, and labels actually released. It may query/retain an eligible outcome subject to
a pathwise budget that counts pending outcomes at request time. It pays an externally supported
switching cost when deployed action changes. The regime parameter is fixed, while the latent state
can recur; misspecification is outside a model-conditional theorem.

The causal estimand must be a finite-horizon net-value contrast between two named deployment
strategies, including their induced state distributions, carryover, fees, and reference strategy.
It cannot be `E[Y_t(1)-Y_t(0) | observed history]` unless the assignment and outcome design really
identifies both potential outcomes under that history. Randomized assignment propensities must be
bounded away from zero and one wherever the target strategies differ; the transition, carryover,
interference unit, and delayed-release mechanisms must be explicit. The model-conditional current
benefit forecast must be recomputed from current released data. Historical promotion evidence stays
a separate object and cannot certify value after a regime reversal.

The primary risk event should be stated at the strategy level: any time the learner initiates or
continues a challenger deployment whose model-conditional remaining-horizon net value is at or
below the declared hurdle. A theorem must state whether it controls this event under the true fixed
controlled-HMM parameter or only a fixed test-epoch null; it must also state how randomized probes,
pending labels, and reversals count. A hard cap and a current-value forecast alone do not resolve
causal identification.

## Evidence and prior-art boundary

- Repository screens already cover performative feedback and bandit feedback, randomized causal
  regime comparison, HMM current-value confidence sets, delayed feedback, controlled sensing, and
  finite two-law planning. The candidate must therefore show a strict theorem-level advantage over
  the source-matched composition, not merely add those components.
- Primary-source checks find established adaptive-experiment inference for dependent,
  nonstationary assignment streams, micro-randomized trials with Markov contexts and time-varying
  effects, and randomized experiments for long-run rewards in MDPs. These establish that randomized
  sequential causal estimation with state dynamics is an existing area. A finite controlled-HMM
  state augmentation followed by constrained planning is not a novelty claim.
- Required head-to-head baselines: (i) the strongest safe randomized policy-learning / adaptive
  experiment method with delayed rewards, (ii) a model-based controlled-HMM planner with the same
  confidence/risk constraint, and (iii) the finite exact two-law oracle on small cells. The theorem
  must identify a structural interaction where the proposed acquisition-and-switching rule beats
  these methods under identical propensities, feedback, budget, delays, and costs.

## Data eligibility result and next gate

The existing Binance replay has exchange timestamps and a dated fee reference, but the R3 contract
explicitly assumes price-taker execution and evaluator-computable clipped signal loss. It does not
identify market impact, randomized treatment effects, or causal policy value. OPSD likewise scores
paired reserve-loss under a replay contract, not randomized intervention effects. Other repo audits
find no data source that jointly provides action randomization, action-dependent outcomes,
point-in-time covariates and release timestamps, recurring latent regimes, and defensible switching
costs. Free labels also mean the observation budget is an imposed review capacity unless a real
acquisition mechanism is supplied.

Therefore keep G2-G5 held. The next F1 input is either (a) an already-authorized, de-identified
randomized execution/intervention log with assignment propensities, event and release timestamps,
policy-dependent outcomes and cost records, or (b) an explicitly scoped paper-trading/randomized
simulation contract whose claims remain simulation-only. Do not open the frozen Binance/OPSD
holdouts to answer this causal question. If a suitable source is supplied, freeze the causal unit,
estimand, propensity design, feedback clock, budget accounting, cost source, and exact comparator
before writing the algorithm. Kill the joint real-data claim if no source meets that contract.

### Closest identified finance source: AHL randomized execution experiment

Bojinov and Shephard analyze AHL Partners' 2016 experiments assigning eligible futures orders at
random to human or algorithmic execution. The paper reports ten markets, randomized Bernoulli
assignment (with assignment probability changed in three markets), and per-order signed VWAP
slippage as the outcome. Execution duration varies by treatment and market; reported market-level
median durations range from 0.6 to 44.7 minutes. This is an unusually close *task family* for
randomized finance intervention with action-dependent realized costs and temporal carryover.

It does not currently pass our data gate. The article states AHL supplied the data and does not
publish the order-level records; exact assignment/outcome timestamps, label-release timestamps,
and any deployment switching costs are not available in the paper tables. The described treatment
randomization is i.i.d. and ignores past data, and the published causal analysis already derives
time-series estimands and exact randomization tests. Thus it cannot be treated as data in this repo,
and the method contribution cannot be “randomized time-series inference for trading.” Reopen it
only if order-level data and release/cost metadata are licensed and accessible. A realized-market
regime model would need an explicitly justified observable state proxy or an explicitly
model-conditional latent-regime assumption; the paper does not establish a recurrent HMM.

The source paper is [Bojinov and Shephard, *Time Series Experiments and Causal Estimands: Exact
Randomization Tests and Trading*](https://arxiv.org/abs/1706.07840). Its reported application is
stronger than a synthetic causal simulation, but weaker than a point-in-time, delayed, budgeted
switching evaluation. It provides a concrete access lead for F1, not a current eligible real-data
result.

### Existing simulator/oracle boundary

The repo's `PerformativeEnvironment` is a useful action-dependent component: deployed actions shift
a scalar Gaussian target and the next scalar state. Its verified dynamics do not include a latent
recurrent HMM, delayed label release, an observation/query cap, or order-level finance utility. The
finite `CausalSwitchingGame` is a useful delayed-feedback/risk oracle with an HMM alternative and a
history-adaptive null, but its HMM transition and paired binary outcome law are independent of the
learner's action. The AHL paper supplies a randomized finance task family but not accessible logs.
Combining these pieces in code would therefore create a *new synthetic contract*, not reuse an
already-valid joint benchmark. No joint simulator or algorithm is implemented or evaluated yet.

Before building that contract, the source-level G1 audit must still answer whether action-dependent
controlled-HMM planning with delayed observations and a hard label cap has a theorem-level gap over
Bayes-adaptive/constrained-POMDP planning, and whether the causal-null safety event adds more than
standard safe exploration and sequential randomization inference. If not, revise the method
hypothesis instead of treating simulator integration as the contribution.

## Sources checked

- Hadad et al., *Confidence intervals for policy evaluation in adaptive experiments*,
  [primary article](https://pmc.ncbi.nlm.nih.gov/articles/PMC8054003/).
- Qian et al., *The stratified micro-randomized trial design*,
  [primary article](https://pmc.ncbi.nlm.nih.gov/articles/PMC8049613/).
- *Experimenting on Markov Decision Processes with Local Treatments*,
  [primary preprint](https://arxiv.org/abs/2407.19618).
- The repository's narrower prior-art and data records remain controlling context:
  `switching_action_dependent_pivot_screen_v1.md`,
  `switching_hmm_predictive_cs_candidate_v1.md`,
  `switching_real_data_eligibility_v1.md`, and `lane_b_burst_allocation/R0_real_data_eligibility.md`.

