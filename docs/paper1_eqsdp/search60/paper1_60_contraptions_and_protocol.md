# Paper 1: 60 contraptions for EQSDp + cutoff

Parent: `s2armr_H1100 = EQSDp_l0.98_g0.3 + cutoff at t+delay>T-1100`

All 60 entries are hypotheses, not demonstrated improvements or claims of novelty. Every add-on sees only model predictions, time, remaining budget, pending-label metadata and released purchased feedback. No event label may be observed early.

## Catalog

### A: Post-cutoff monitoring/reopening

| ID | Module | Implementation | Parameter candidates |
|---|---|---|---|
| A01 | Periodic sentinel | After cutoff, buy one disagreement label every m eligible events. | m=40,80,160; reserve=10,20 |
| A02 | Geometric sentinel | After cutoff, grow the sentinel interval geometrically until a warning resets it. | m0=20,40; growth=1.2,1.5 |
| A03 | Hazard-responsive sentinel | Set sentinel probability using a posterior change hazard, with an irreducible floor. | hazard=0.0005,0.002; floor=0.01,0.03 |
| A04 | Disagreement CUSUM | Track prediction-only disagreement indicator with a two-sided CUSUM; reopen a bounded query window on alarm. | window=50,100; threshold=2,4 |
| A05 | Disagreement Page-Hinkley | Apply Page-Hinkley to the online prediction-disagreement rate; reopen on alarm. | threshold=3,5; decay=0.95,0.99 |
| A06 | Prediction-pair transition alarm | Monitor frequencies of observable (0,1) versus (1,0) model-output patterns. | window=100,200; z=2,3 |
| A07 | Disagreement burst alarm | Compare short versus long disagreement-frequency EWMAs and reopen on a burst. | fast=20,50; slow=150,300 |
| A08 | Prediction turnover alarm | Detect a change in each model's observed prediction-flip frequency (not label error). | window=50,100; z=2,3 |
| A09 | Feedback-staleness sentinel | Force a disagreement query if no released informative label has arrived for m events. | max_age=60,120,240 |
| A10 | One-shot reopening window | At predeclared checkpoints past cutoff, reopen for W events under a reserved budget. | checkpoint=1000,1300; width=100,200 |

### B: Budgeted label acquisition

| ID | Module | Implementation | Parameter candidates |
|---|---|---|---|
| B11 | Maximum eligible-query gap | Never leave more than G disagreement opportunities without buying one label. | G=20,50,100 |
| B12 | Randomized minimum propensity | Impose positive acquisition probability p_min after cutoff before horizon-feasibility check. | p_min=0.01,0.03,0.05 |
| B13 | Split-period budget reserve | Reserve a fixed fraction of the 200 labels for t>800. | reserve=10%,20%,30% |
| B14 | Post-promotion reserve | Reserve a small packet of labels for the first W events after model-1 promotion. | packet=5,10; W=100,200 |
| B15 | Post-reversal reserve | Reserve queries immediately after returning to model 0. | packet=5,10; W=100,200 |
| B16 | Pending-queue cap | Suppress redundant acquisition when too many already-requested disagreement labels are in flight. | pending_cap=5,10,20 |
| B17 | Pending-age priority | Prefer query windows where queued labels are unlikely to arrive early enough to change an action. | max_pending_age=50,100; age_penalty=0.3,1 |
| B18 | Posterior-uncertainty pacing | Multiply the parent query propensity by a clipped posterior-variance score. | gain=0.5,1.5; floor=0.1,0.3 |
| B19 | Decision-boundary proximity pacing | Increase buying near the original EQSDp payback boundary, but retain a nonzero sentinel floor. | band=2,5,10; floor=0.05,0.15 |
| B20 | Prediction-pattern stratified acquisition | Maintain separate acquisition quotas for (0,1) and (1,0) disagreement patterns. | target_balance=0.5,0.75; min_rate=0.01 |

### C: Evidence and posterior adaptation

| ID | Module | Implementation | Parameter candidates |
|---|---|---|---|
| C21 | Fast/slow Beta evidence blend | Maintain two discounted Beta counts and combine their switching signals, preserving the original EQSDp as default. | lambda_fast=0.8,0.9; mix=0.2,0.5 |
| C22 | Surprise-triggered discount | Temporarily decrease lambda after low-probability released-label outcomes. | surprise=0.01,0.05; lambda_alert=0.8,0.9 |
| C23 | Soft posterior reset | Shrink old discounted counts toward their prior after an observable released-feedback change alarm. | shrink=0.25,0.5; threshold=3,5 |
| C24 | Hazard-mixture Beta filter | Use a stable-versus-redraw posterior mixture to adjust the evidence summary. | hazard=0.0001,0.001; prior_strength=1,3 |
| C25 | Bayesian run-length posterior | Track the posterior since last likely change using only released disagreement outcomes. | hazard=0.0005,0.002; truncate=50,200 |
| C26 | Two-regime hidden-state belief | Infer latent persistent challenger-better versus incumbent-better regimes. | self_transition=0.98,0.995; smoothing=0.1,0.3 |
| C27 | Dependence-adjusted effective sample size | Reduce effective Beta counts as observed label autocorrelation rises. | strength=0.5,1; cap=0.9 |
| C28 | Request-time discount correction | Discount a released label according to its event timestamp rather than only its release order. | age_tau=100,300; min_weight=0.2,0.5 |
| C29 | Robust Beta prior ensemble | Average or take a conservative envelope across weak and concentrated Beta priors. | alpha_beta=(1,1),(2,2),(5,5) |
| C30 | Joint disagreement-and-win-rate belief | Maintain separate Beta filters for observable disagreement probability and conditional challenger win rate. | rate_lambda=0.95,0.99; gain_lambda=0.9,0.98 |

### D: Switching/rollback control

| ID | Module | Implementation | Parameter candidates |
|---|---|---|---|
| D31 | Two-observation promotion confirmation | After parent proposes promotion, require one additional informative released disagreement before switching. | needed=1,2; timeout=100,200 |
| D32 | Reversible probation after promotion | Apply a short probation phase with elevated monitoring and conditional rollback. | probation=50,100; extra_queries=5,10 |
| D33 | Fast negative-evidence rollback | During probation, reverse when an observed short-window loss gap is strongly adverse. | window=5,10; threshold=2,4 |
| D34 | Direction-specific conservative quantiles | Use separate promotion and reversal gamma values around original baseline gamma. | gamma_enter=0.2,0.35; gamma_exit=0.1,0.3 |
| D35 | Switch-count-dependent hurdle | Increase marginal switch cost in the decision rule following repeated reversals. | slope=1,3; decay=100,300 |
| D36 | Persistence-adjusted payback | Replace raw remaining horizon by expected duration of the advantage under a hazard model. | hazard=0.0005,0.002; floor_horizon=100,300 |
| D37 | Alarm-conditioned emergency promotion | After a strong label-based change alarm, reduce the promotion hurdle for a bounded window. | hurdle_scale=0.6,0.8; window=100,200 |
| D38 | Query-burst confirmation before switching | When payback is near the hurdle, buy a brief evidence packet then decide. | packet=3,5; band=2,5 |
| D39 | Horizon-dependent quantile level | Vary risk tolerance through the episode while leaving Beta evidence and payback structure intact. | gamma_early=0.3,0.45; gamma_late=0.1,0.2 |
| D40 | Posterior no-action switch band | Require additional predicted incremental benefit when posterior uncertainty makes repeated switching likely. | band=1,3,5 |

### E: Tail protection and risk

| ID | Module | Implementation | Parameter candidates |
|---|---|---|---|
| E41 | Missed-switch expected-loss proxy | Estimate downside of withholding another label under a finite-horizon future-change mixture. | rollout_h=100,300; hazard=0.0005,0.002 |
| E42 | Paired-cost tail-aware acquisition | Purchase labels when estimated upper-tail excess cost of skipping is high. | alpha=0.9,0.95; risk_weight=0.5,2 |
| E43 | Posterior risk budget per deployment | Track posterior expected downside of wrong switches against a preallocated loss budget. | risk_budget=5,10,20 |
| E44 | Prior-robust payback envelope | Check economic benefit under multiple posterior priors before allowing a risky state change. | priors=weak,balanced; envelope=quantile,mean |
| E45 | Ambiguity-triggered parent fallback | If an add-on decision is too uncertain, use frozen EQSDp+cutoff behaviour. | ambiguity=0.05,0.1; cooldown=50,100 |
| E46 | Positive-propensity feedback correction | Use capped inverse-propensity weighted statistics for diagnostics or decision calibration where valid. | weight_cap=5,10; shrink=0.25,0.5 |
| E47 | Released-loss CUSUM monitor | Apply CUSUM to purchased-label signs, with explicit delay and monitoring floor. | threshold=3,5; reset=soft,hard |
| E48 | Next-information arrival value | Penalize actions that rely on evidence arriving after the last economically useful switch time. | arrival_discount=0.5,1; lookahead=50,150 |
| E49 | Posterior lock-in detector | Flag high-confidence states with few recent labels and force monitoring. | confidence=0.95,0.99; age=80,160 |
| E50 | Observed-regret risk score | Compute a downside proxy from purchased-label regret, carefully respecting query propensities. | window=10,30; upper_q=0.9,0.95 |

### F: Hybrid controllers

| ID | Module | Implementation | Parameter candidates |
|---|---|---|---|
| F51 | Front-loaded startup pulse | Spend a small fixed packet before first actionable delayed feedback. | packet=5,10; duration=100,200 |
| F52 | Backloaded adaptive evidence pulse | Keep budget for a predeclared late evidence pulse after cutoff. | packet=5,10; start=1100,1400 |
| F53 | Alarm-triggered reserve release | Unlock a protected budget reserve when free or paid change alarms fire. | reserve=10,20; alarm_z=2,3 |
| F54 | Sequential surprise query burst | After two surprising released labels, temporarily raise query propensity. | surprises=2,3; burst=5,10 |
| F55 | Unlabeled/labeled sensor fusion | Require agreement or Bayesian fusion between prediction-pattern alarms and released-loss alarms. | fusion=OR,AND,weighted; horizon=100 |
| F56 | Sentinel-to-rollback cascade | A post-cutoff sentinel surprise triggers high-rate querying plus rapid rollback review. | alert=2,3; burst=5,10; review=50 |
| F57 | Alarm-gated fast/slow evidence | Use fast Beta counts only after a change warning, otherwise retain parent evidence. | fast_lambda=0.8,0.9; duration=100,200 |
| F58 | Two-policy economic arbitration | Maintain parent and experimental policy states; use released labels to select action cautiously, charging all switches. | score_window=30,100; penalty=1,3 |
| F59 | Lightweight learned acquisition controller | Train a small threshold policy on observable state features, then freeze it on a development fold. | model=tree,logistic; depth=2,3 |
| F60 | Multi-label short-rollout VOI | Estimate net value of a bundle of 2–4 future labels, conditional on their arrival times. | bundle=2,3,4; horizon=100,200 |

## Fixed experiment contract

Nine datasets: sf_311, kc_311, montgomery_traffic, dallas_311, dc_311, austin_311, cincinnati_311, oakland_311, sandiego_311.

T=2000; B=200; cost(label)=0.05; cost(switch)=5; 10 policy seeds; feedback delay as registered. Parent and all existing 25 uncertified comparator implementations must remain in the results. Include additional Wald variants with identical cutoff and any add-on-specific acquisition scheduling as matched controls.

## Search policy

- Each candidate consists of 1–5 unique modules from the catalog, with no change to parent code or the original benchmark records. All-off candidate must reproduce `s2armr_H1100` exactly.
- Keep all original nine datasets (including Kansas City). Use equal-dataset pooled cost as the primary objective, alongside prediction-loss difference, labels, switches, late adoption, false promotion and upper-tail paired excess costs.
- Do not require a 95% CI excluding zero, no-losing-dataset rule or a 2% improvement before exploring combinations. Prefer candidates with positive predicted savings at similar prediction accuracy; record all results.
- A module can disable a parent cutoff only by using a predeclared monitoring override; ensure the total label budget remains <=200 and labels are only released with declared delay.
- Because even/odd episodes were already exposed in prior research, any within-nine cross-validation is development only; claim independent success only after a separate future validation.
- Use singletons first, then sparse pair/3/4/5 combinations guided by uncertainty-aware regression or Bayesian optimization. Do not enumerate 5,985,197 full simulations.

## How to combine modules

Operational hooks: (1) observable-signal monitors; (2) belief updates on released labels; (3) base paced propensity and cutoff; (4) reserves/monitoring overrides; (5) optional switch/rollback overlays; (6) risk/fallback protections. Log the final query decision and which hooks caused it.

For any pair of modules that controls the same quantity, implement a documented composition (e.g. safety floor then gate then budget cap), or mark the combination unsupported. Never silently let one overwrite another.

## Interpretation

Positive results vs the original 25 adapter panel can support a scoped package claim; beating Wald itself requires comparators to receive the same cutoff and analogous additions, or must be explicitly described as a baseline-package comparison.
