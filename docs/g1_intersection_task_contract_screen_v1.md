# G1 intersection screen: recurrent regimes, randomized intervention, finance task

**Date:** 2026-10-29. **Status:** task-contract and feasibility screen; no algorithm, theorem,
novelty claim, holdout access, or empirical result. This records the user's direction to pursue
all three structural dimensions together.

## Decision

There is a viable local finance task if “action-dependent outcome” means the trader's
account-level utility, not an action-induced change in the market's data-generating process. For a
small price-taking trader, the next-bar return stream is exogenous to the chosen strategy, while
realized position utility depends on the selected strategy and transaction fees. Under this
explicit no-impact assumption, the same next-bar return identifies both frozen strategies'
potential account utilities, and randomized switching actions have known propensities. This is a
causal decision-utility estimand under the replay model; it does not identify market impact, fills,
slippage, or changes to market regimes induced by the trader.

The local Binance ETHUSDT hourly archive has exact UTC bar clocks and a price-taker replay contract,
with a 2025 development block and locked 2026 confirmation block. The R3 task freezes those data
windows, but its primary estimand is clipped signal loss, not account utility. Evaluating account
utility therefore requires a separately frozen evaluation contract and method protocol. Prior Lane
B development analyses used 2025, so it is exposed development data, not fresh confirmation. No
2026 holdout rows may be accessed until a separate method/protocol freeze and guarded opening
procedure pass. This is a scoped real-data path, not a market-impact evaluation.

The three requested dimensions can coexist under an HMM for exogenous market regimes, randomized
strategy-selection actions, and action-dependent net portfolio utility. Market transitions are
action-independent here; reward mappings and turnover fees depend on the action. If the scientific
claim requires market-impact feedback into prices or regime transitions, Binance is ineligible and
the AHL/raw execution-log route remains an access requirement. The general acquisition-and-
switching composition still needs a G1 novelty result; the data do not create novelty by themselves.

## Candidate contract to reopen only if the data design is available

For the local Binance task, use a finite recurrent HMM for exogenous market returns with observed
pre-decision context `X_t`, latent regime `Z_t`, and randomized deployed strategy `A_t` from the
frozen 24-bar/168-bar long-flat policies. The market transition/emission law is independent of
`A_t` under the price-taker assumption; standalone account reward for policy `a` is
`U_t(a)=p_{a,t} r_{t+1}-f|p_{a,t}-p_{a,t-1}|`, with policy-switch rebalance fees defined separately
from standalone turnover. This account-utility estimand is not the current R3 clipped-loss outcome
contract and needs its own freeze. The next-bar return is available at the next bar close (`d=1`);
the request cap is imposed analyst-review capacity and must count pending requests at request time.
Model switching incurs the separately declared turnover/rebalance cost. The regime parameter is
fixed while latent market states may recur; misspecification and market impact are outside this
model-conditional contract.

For an environment-action task where the outcome or state transition itself depends on deployment,
use a different dataset or explicitly limit the claim to simulation. Do not silently transfer the
Binance price-taker replay to that broader causal estimand.

The estimand is a finite-horizon net account-value contrast between the frozen deployment
strategies, including position turnover, strategy-switch fees, and the fixed reference strategy.
On Binance, paired potential account utilities are identified only under the stated common-price-
path, full-fill, zero-impact assumption; report this as a price-taker replay. Randomized
assignment propensities must be bounded away from zero and one wherever the target strategies
differ. The model-conditional current-benefit forecast must be recomputed from current released
data. Historical promotion evidence stays separate and cannot certify value after reversal.

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

**Correction (2026-10-30):** The older paragraphs below treated the absence of historical
randomized assignments as ruling out all local real-data evaluation. That was too strict for the
scoped account-utility estimand. Binance supports a real-data price-taker replay: returns are the
common exogenous market path, while strategy positions and transaction fees determine
action-dependent account utility. Under full fills and zero market impact, both frozen policies can
be scored on paired returns. This does not identify market impact, fills/slippage, market-state
effects, or historical randomized treatment effects. Randomized propensities apply to the proposed
online protocol; the offline replay is paired policy scoring. The observation cap is imposed
analyst-review capacity because returns are already observed. The 2025 block is exposed development
data; 2026 remains locked until a separate method/protocol freeze and guarded opening. The older
eligibility wording below is superseded to this extent; keep its stronger-claim boundary and AHL
access requirement for execution/market-impact claims.

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

