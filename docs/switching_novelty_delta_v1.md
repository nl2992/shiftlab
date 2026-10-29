# Switching novelty delta v1

> **Checkpoint update:** primary-source access and theorem-scope audits were extended on
> 2026-10-28. See [source audit v2](switching_source_audit_v2.md) for the verified reading scope,
> corrected assumptions and proof limitations. This table records the current audit state.

2026-10-28. **Verdict: unresolved.** No new method is selected. This is a source-access and
equivalence checkpoint, not a completed novelty audit. Existing detailed source reads remain
in `papers/shiftguard_unified/challenger_switching_fidelity_audit.md` and
`docs/research_refinement_v1/PRIOR_ART_AND_NOVELTY_MATRIX.md`; their differing verification
levels must not be silently upgraded.

## Primary sources checked this session

| Source | What was verified | Remaining source-level work |
|---|---|---|
| [Gafni–Iyengar–Zeevi, ICML 2026](https://proceedings.mlr.press/v306/gafni26a.html) | Official proceedings PDF and Appendices A.3/A.5/A.6 inspected: full-observation piecewise-IID sub-Gaussian mean tracking, ATC upper bound, minimax lower-bound relaxations, and missed-change SNR-contamination argument | This is squared tracking error under full feedback, not paired-loss model switching with a hard query cap, delayed labels, switch/query charges or causal-null promotion risk. A fixed-calendar ATC adapter needs a new calendar-time delay/observation bound and separate safe-switch rule. See [`switching_gafni_theorem_audit_v1.md`](switching_gafni_theorem_audit_v1.md); source hash in manifest v34 |
| [Digalakis et al., The Challenger v2](https://arxiv.org/pdf/2512.18390v2) | Sections 3.2–3.3 and EC.1.3 proof of Theorem 2 inspected: irreversible adoption/discard, finite-VC/ERM meta-regret under bounded gain and terminal timing/consistency conditions; theorem does not require the power-law curve | Direct economic deployment and look-ahead are occupied. Reversals, hard query cap and delayed label feedback are outside the audited theorem; see [`switching_source_audit_v2.md`](switching_source_audit_v2.md) |
| [Lamaakal et al., Drift2Act v1](https://arxiv.org/pdf/2603.08578) | Sections 5.2–5.3 and Appendix D.1–D.4/D.7 inspected, including proof of Theorem A.2: capped labels, uniform-window auditing, bounded-loss concentration and summable allocation | Window-risk certification and one-step gain/violation utility are covered. Delayed arrived subsets need the source's sampling/representativeness assumptions; this is not a post-switch future-benefit certificate. No claim of invalidity or novelty from the distinction. See [`switching_source_audit_v2.md`](switching_source_audit_v2.md) |
| [Lindon–Kallus, ICML 2026](https://proceedings.mlr.press/v306/lindon26a.html) | arXiv v2 Theorems 4.4, 4.6, 4.9, Proposition 4.8 and relevant Appendix A.1–A.2 proof steps inspected; the displayed confidence sequence in Theorem 4.6 is asymptotic and uses strong approximation | Calendar-time cumulative counterfactual reward and arm-specific delayed filtrations overlap. Generic finite-sample bounded-martingale tools prevent asymptotic-vs-finite-sample distinction alone from being a contribution; future switching value is a different target. See [`switching_source_audit_v2.md`](switching_source_audit_v2.md) |
| [Cheng et al., ICML 2023, Understanding the Role of Feedback in Online Learning with Switching Costs](https://proceedings.mlr.press/v202/cheng23f/cheng23f.pdf) | Full primary-text read: Section 4 has a hard cap on individual loss observations; Theorem 2 gives soft-Theta(T sqrt(K/B)) minimax expected regret against the best fixed action; Algorithm 1 / Proposition 2 use batched full-information feedback and Shrinking Dartboard with O(T sqrt(K log K/B)) upper bound; Appendix C proof inspected | Exact gaps remain for delay queues, paired query pricing, a dynamic S-switch comparator, and anytime false-promotion risk. Documented in [`switching_cheng_audit_v1.md`](switching_cheng_audit_v1.md); these are comparison obligations, not a novelty claim |
| [Braverman et al., Optimally Pacing Budget Spending and Learning, arXiv v1](https://arxiv.org/pdf/2610.11074) | Full 38-page primary PDF inspected: Theorem 4.6 gives D-pacing expert regret under hard resource budgets; Theorem 5.8 / Corollary 5.9 add sampled play, pathwise budget feasibility and high-probability regret | The learner observes current reward/cost vectors (full-information or selected-action bandit); no delayed purchased labels or anytime conditional-null false-promotion event. Generic budget pacing and spending-potential novelty are closed, while the delayed safe-acquisition interaction remains only a comparison obligation. See [`switching_budget_pacing_prior_audit_v1.md`](switching_budget_pacing_prior_audit_v1.md) |
| [Prabhu et al., IEEE TIT 2022, Sequential Multi-hypothesis Testing in Multi-armed Bandit Problems](https://arxiv.org/pdf/2007.12961) | Complete 53-page v2 source inspected; selected model, theorem and proof passages checked. Adaptive sensing, stationary exponential-family parameters, terminal false-detection probability, sensing-switch cost, Proposition 1 converse, Proposition 6 admissibility proof route, Proposition 7 achievability proof route and Theorem 4 asymptotic result verified at the source-text level | Strong mandatory reduction for stationary one-shot controlled testing. It has immediate observations, no hard total query cap, and sensing switches rather than repeated deployment switches; these gaps do not establish novelty. See [`switching_sequential_safety_prior_v1.md`](switching_sequential_safety_prior_v1.md) and source manifest v10 |
| [Helmeczi et al., constrained POMDP LP methods](https://arxiv.org/abs/2206.14081) and [Wen et al., finite-horizon partially observed probability-risk control](https://www.sciencedirect.com/science/article/pii/S0167637724001238) | Full 42-page CPOMDP v2 source downloaded; relevant finite-horizon formulation and budget/objective sections inspected; publisher abstract/model summary inspected for Wen et al. | Generic belief-state planning, resource constraints and terminal probability-risk control are established. CPOMDP uses expected resource budget; the risk-probability paper's full model is not verified. Neither abstract-level difference proves novelty. See [`switching_constrained_control_prior_v1.md`](switching_constrained_control_prior_v1.md) and manifest v11 |
| [Wen, Xia and Yu, finite-horizon partially observed semi-Markov games with probability risk](https://arxiv.org/abs/2508.17791) | Full 29-page v1 source inspected for game model, information structure, belief/remaining-goal augmentation and comparison/Shapley/equilibrium results | Closest audited control/game prior. It uses a common observed history and belief for both players, and a model-based terminal threshold probability. Our null adversary may see pending queried outcomes hidden from the learner; our objective is expected economic utility subject to worst-case anytime risk and pathwise query budget. These differences define exact reduction tests, not novelty. See [`switching_partial_observation_risk_game_prior_v1.md`](switching_partial_observation_risk_game_prior_v1.md) and manifest v12 |
| [Shin, Ramdas and Rinaldo, E-detectors](https://nejsds.nestat.org/journal/NEJSDS/article/59/text) | Full 32-page published source inspected for e-detector definitions, mixtures over consecutive starts, weighted false-alarm control, and likelihood-ratio delay results | Strong anytime change-point detection baseline. A weighted mixture of per-onset e-processes handles late changes; Bernoulli likelihood-ratio betting and the delay bound are established. Predictable query skipping and fixed ordered release preserve this test's null validity under our stronger event-time null, but do not solve budget allocation or economic switching. See [`switching_change_point_safe_baseline_v1.md`](switching_change_point_safe_baseline_v1.md) and manifest v13 |
| [Li et al., Active Sequential Two-Sample Testing, TMLR 2024](https://wayne0908.github.io/Publications/TMLR2024.pdf) | Primary source downloaded; Sections 3.2–5.3, Theorems 5.1/5.4 and Appendix A.2 inspected | Already combines adaptive label selection, a finite label budget, adaptive classifier updates, anytime Type-I control and a power analysis. Its IID unlabeled-pool independence null, immediate labels and terminal test omit online switching economics, delayed pending feedback, and repeated reversals. These differences are a remaining reduction obligation, not novelty. See [`switching_active_sequential_two_sample_audit_v1.md`](switching_active_sequential_two_sample_audit_v1.md) and manifest v15 |
| [Geng, Bayraktar and Lai, Bayesian Quickest Change-Point Detection with Sampling Right Constraints](https://arxiv.org/abs/1309.5396) | Full source model, Theorems 1–3 and proof appendices inspected from the primary arXiv source | A one-stream Bayesian change detector with a finite number of sample rights jointly optimizes sampling intervals and posterior-threshold stopping by recursion. Generic unknown-onset timing and sequential stopping are therefore occupied. The geometric change prior, immediate observation after each sample and scalar delay/false-alarm objective differ from our global conditional-null risk, fixed-delay pipeline, pathwise finite horizon and repeated costed deployment. See [`switching_sampling_rights_qcd_audit_v1.md`](switching_sampling_rights_qcd_audit_v1.md) |
| [Lau and Tay, Asymptotically Optimal Sampling Policy for Quickest Change Detection with Observation-Switching Cost](https://arxiv.org/pdf/1912.11693v4) | Full 49-page primary PDF downloaded and hashed; model, GLR-CuSum, Lemma 2, Proposition 1, Theorem 1, open-loop reductions and Section VI two-stage observation-dependent design inspected | Joint acquisition and detection under sampling-mode switching costs is directly established, including an observation-dependent two-threshold policy. Their theorem is asymptotic for one permanent change with known likelihoods, ARL false alarms and average sampling-mode costs; it omits hard total label cap, delayed release, repeated reversible deployment and robust finite-horizon conditional-null risk. Exact comparison obligations, not novelty. See [`switching_observation_switching_qcd_audit_v1.md`](switching_observation_switching_qcd_audit_v1.md); source hash in `switching_source_manifest_v18.json` |
| [Khonji, Jasour and Williams, Approximability of Constant-horizon Constrained POMDP](https://www.ijcai.org/proceedings/2019/0775.pdf) | Primary 8-page IJCAI source downloaded and hashed; CC-POMDP model, sequence ILP, horizon-two hardness, Theorem 5.4 and Corollary 5.5 inspected | A generic finite-horizon chance-constrained planning or FPTAS claim is occupied. Their FPTAS assumes a fixed stochastic kernel and is polynomial in expanded tree size for constant horizon; it does not directly cover our robust causal-null game or variable long horizon. See [`switching_ccpomdp_approximation_audit_v1.md`](switching_ccpomdp_approximation_audit_v1.md), source manifest v19 |
| [Chick, Forster and Pertile, Bayesian decision-theoretic model of sequential experimentation with delayed response (JRSS B 2017)](https://doi.org/10.1111/rssb.12225) | Sections 2–2.2, Bellman equations (8)–(9), and Proposition 2.2 inspected; source PDF/text cached and hashed in manifest v2 | Direct one-switch overlap: stationary Gaussian paired net benefit, per-query sampling cost, a hard maximum sample size, fixed pipeline delay, and one-time adoption cost. A generic delayed economic sample-and-adopt rule is occupied. Their Bayesian stationary one-adoption objective does not give our repeated-reversal, conditional-null anytime risk guarantee. The exact mapping is recorded in [`switching_delayed_comparator_audit_v1.md`](switching_delayed_comparator_audit_v1.md) |
| [Huang et al., UCB-Driven Controlled Sensing for Quickest Change Detection](https://arxiv.org/abs/2603.28563) | Formal multichannel model, UCB-CuSum procedure and Theorem 1 inspected from the primary preprint | Jointly adapts channel choice and change detection, with first-order asymptotic Lorden-delay optimality under an MTFA constraint. In our single common-outcome paired-query model the informative-channel choice collapses to one stream; immediate sensing and MTFA do not match a pathwise query-right cap, fixed delay, and deployment switching. See [`switching_ucb_controlled_sensing_audit_v1.md`](switching_ucb_controlled_sensing_audit_v1.md) |
| [Ryabchenko, Attias and Roy, Capacity-Constrained Online Learning with Delays](https://arxiv.org/abs/2503.19856) | Section 1.1 protocol, batch partitioning, Theorems 3.1–3.2 and Section 4.1 inspected; PDF hash in manifest v16 | Fixed-delay minimax regret with pathwise concurrent tracking capacity and sampled-round feedback. A paired query revealing both model losses maps to full-information feedback; total-query cap and concurrent tracking capacity must be matched separately. No switching cost, dynamic comparator or false-promotion event. See [`switching_delay_capacity_audit_v1.md`](switching_delay_capacity_audit_v1.md) |
| [Gerogiannis et al., Detection Augmented Learning, arXiv v1](https://arxiv.org/abs/2610.25782) | Formal piecewise-stationary model, Algorithm 1, HLD detector property, change-separation assumption, Theorem III.9 and Appendix E proof decomposition inspected | Directly establishes detector + forced exploration + restart learning with dynamic regret. Uses immediate bandit/structured feedback, no paid total query budget or switching cost; false-alarm model is segmentwise sub-Gaussian and theorem needs detectable separated changes. See [`switching_dal_prior_audit_v1.md`](switching_dal_prior_audit_v1.md) |
| [Li et al., Sequential Hypothesis Test with Online Usage-Constrained Sensor Selection](https://arxiv.org/abs/1601.06447) | Primary PDF; finite-horizon posterior-adaptive sensing/stopping DP, Theorems 1 and 3, and appendix proof arguments inspected | Closes generic adaptive evidence acquisition and stopping under a finite maximum sample count plus type-I/type-II constraints. Sensor-use limits are expected, observations are known IID simple hypotheses, and deployment has no switching cost; see [`switching_usage_constrained_sequential_testing_prior_audit_v1.md`](switching_usage_constrained_sequential_testing_prior_audit_v1.md) |
| [Cubuktepe et al., Robust Finite-State Controllers for Uncertain POMDPs](https://ojs.aaai.org/index.php/AAAI/article/view/17401/17208) | Full primary source inspected: finite-memory policies, interval transition uncertainty, robust expected-reward/reachability specifications, SCP local optimization and exact verification | An exact-history augmentation can encode the causal-null delayed safety branch as a robust POMDP, but grows exponentially; their single-model FSC solver does not give our two-kernel objective or regret guarantee. Any compression/theorem must be compared directly; see [`switching_robust_fsc_reduction_audit_v1.md`](switching_robust_fsc_reduction_audit_v1.md) |

The contract-matched DAL translation screen in [`switching_dal_translation_screen_v1.md`](switching_dal_translation_screen_v1.md)
replaces forced actions by a deterministic paired-label calendar and separates the e-process risk
gate from current-window change evidence. It proves only the pathwise budget and the calendar
conversion `sample windows -> calendar windows + d`; it explicitly does **not** import DAL's
dynamic-regret theorem. A source-audited proof of the adapter's full bound is now a baseline task,
not a novelty claim.

The Bernoulli information lower bound in [`switching_noisy_information_lower_bound_v1.md`](switching_noisy_information_lower_bound_v1.md)
uses adaptive KL chain rule and binary data processing to quantify the unavoidable utility loss
from alpha-safety, finite B and delay together. This is standard testing mathematics and a
contract-specific lower-bound reduction, not a new information inequality or algorithm. It
constrains which regimes can support a useful gain claim; it does not pass G1 or G2.

Access failures are unresolved reading tasks, not evidence that a result is absent. None of
these rows establishes an unoccupied gap. Do not pool abstract statements and historical notes
into a claimed proof-level audit.

## Candidate delta to test

Hypothesis only: in the two-fixed-policy common-outcome model, allocate queries according to
their ability to change a *future net-value decision before evidence expires*, conditioning on
pending feedback, remaining budget and a declared drift envelope. Couple promotion and reversal
through that same economic target. A useful theorem would identify when this coupling improves
over equally equipped acquisition plus switching rules, not merely inherit concentration.

Immediate rejection tests:

1. Does Cheng's observation-budget algorithm plus an existing delay reduction already give the
   desired regret rate? If yes, no new rate claim without a different provable refinement.
2. Does challenger look-ahead evaluation plus a standard confidence sequence implement the same
   decision rule under our assumptions? If yes, identify a substantive new step or stop the rule.
3. Does standard value-of-information dynamic programming already yield the acquisition rule?
   An exact finite-state solution alone is not a new algorithmic insight.
4. Does future certification merely insert a known drift envelope into a standard confidence
   bound? That alone is supporting algebra; demand a new allocation/performance result.
5. Do purported advantages disappear when pending-label accounting, horizon knowledge, drift
   envelope and reserve logic are supplied to every comparator? If yes, record the failure.
6. Does active sequential two-sample testing plus an economic switching wrapper already yield
   the claimed rule after an exact reduction to paired outcomes and delayed releases? If yes, the
   proposed acquisition/test coupling is occupied; only a separate proved improvement can pass.

The composition boundary in [`switching_safe_composition_boundary_v1.md`](switching_safe_composition_boundary_v1.md)
shows that the false-promotion wrapper itself is standard: predictable query skipping, a hard cap,
fixed ordered delay, and weighted unknown-onset e-detectors preserve validity; episode resets
with summable alpha handle repeated promotion attempts. This proves safety feasibility, not
economic query allocation or dynamic-regret control. The required delta must be a joint
acquisition/deployment performance theorem beyond this composition.

The structural lemma in [`switching_monotone_promotion_reduction_v1.md`](switching_monotone_promotion_reduction_v1.md)
shows that for any pure policy whose *any-promotion event* is coordinatewise increasing in the
full potential-outcome tape, the worst causal conditional null is exactly IID `Ber(1/2)`, even
when query timing itself is nonmonotone. This can compress the robust-risk side of an optimizer,
but it is only stochastic domination; no utility-optimality result or scalable policy
parameterization is established. It is a candidate tractability condition, not a novelty result.
The exact restricted-policy screen in [`switching_monotone_promotion_reduction_v1.md`](switching_monotone_promotion_reduction_v1.md)
enumerates all 16 pure plans in a `T=2` cell: the monotone-mixture optimum equals the known
`987/1000` analytic benchmark, and the explicit monotone cohort also matches the recovered
`T=5` recurrent policy. These finite matches show zero observed cost in those cells only; they do
not establish a scalable optimizer or a general approximation guarantee.

The delay counterexample in `switching_problem_v1.md` rules out a zero-delay-penalty ambition;
it is not the proposed methodological contribution. Budget-dependent upper/lower bounds and
the novel mechanism remain open.

## Decision and next checkpoint

**CONTINUE source-level feasibility work; HOLD algorithm selection and experiments.** Produce
the missing theorem comparisons, then either derive one nontrivial mechanism or record a
precise pivot. The broad direction is authorized; no new user approval is needed to do this work.

### 2026-10-28 baseline delta: fixed uniform acquisition is rejected

The finite-horizon calculation in [`switching_uniform_safe_baseline_v1.md`](switching_uniform_safe_baseline_v1.md)
shows that a fixed evenly spaced query schedule paired with the uniform all-onset mixture can be
completely unresponsive in a moderate-budget late-onset cell. This closes only that composition.
It does not separate from query allocation tuned to the horizon, nonuniform onset weights,
sequential test design, randomized tests or constrained planning. The source-level novelty gate
must compare against those stronger methods at identical information, risk, budget, delay and
switch cost. No candidate has yet passed G1.

### Checkpoint 2026-10-28: UAI 2026 costly-observation result audited

`switching_costly_observation_uai26_audit_v1.md` records inspection of Reyzin, Saha and Wu's
accepted primary paper, including the formal round protocol, m-EXP3/m-ELIM algorithms and stated
regret theorems/proofs. Adaptive selection among costly observations and gap-dependent observation
allocation are established. The paper uses immediate feedback, per-round observation cost, a
fixed-expert comparator and no intervention-risk event or deployment switching charge. These
mismatches are not novelty by themselves. G1 remains open; include a budget-semantics-preserving
reduction or matched cost-adaptive baseline before claiming an acquisition advance. Source hash
and provenance are in `switching_source_manifest_v14.json`.

### Finite causal oracle checkpoint (same registered cell)

The follow-up in [`switching_reversal_diagnostic_v1.md`](switching_reversal_diagnostic_v1.md)
solves the fixed-cohort frontier and a no-rollback adaptive-query restriction under the same
Markov alternative, causal conditional null and pathwise cap. It verifies compact safe policies
for all three comparators. Adaptive early stopping yields a small query-cost saving; rollback has
only a smaller marginal value. This confirms that the numerical delta is explained by established
sequential sampling/control primitives in this cell. The generic joint-acquisition hypothesis does
not pass G1. Do not run further cells or efficacy studies for it; a narrower theorem target must
survive the prior-art gate first.


### Monotone-event restriction fails universal utility preservation (2026-10-28)

The exact separation in [switching_monotone_class_separation_v1.md](switching_monotone_class_separation_v1.md)
shows the risk-compression condition can be economically vacuous under reversal-predictive signed
future value. In the two-label model, every increasing promotion event has nonpositive value,
while event `01`, randomized upfront to respect the same causal null, has value 19/200. Thus
there is no positive multiplicative approximation guarantee for monotone promotion policies over
this broad alternative family. This does not close the novelty audit or show that a restricted
reversal-free model is scientifically justified. The next candidate must keep robust risk for
nonmonotone events or state and defend an alternative restriction, then compare against robust
finite-horizon planning and controlled sensing at source/theorem level. Do not treat this
separation as the target algorithm or theorem contribution.


### Additional risk-search and active-testing priors (2026-10-28)

switching_risk_search_active_test_audit_v1.md records primary-source scope for Santana et al.'s
RAO* (AAAI 2016) and Vershinin et al.'s active sequential testing with non-homogeneous costs
(arXiv:2509.11632). RAO* already gives exact finite-horizon execution-risk recursion and
risk-pruned policy search for known stochastic POMDPs; the active-testing paper already allocates
heterogeneous sampling effort by expected discrimination/cost under average error. Their assumptions
do not directly match the causal conditional null, pending feedback, hard total query cap, and
repeated switching economics. These are explicit reductions and matched-baseline obligations, not
novelty claims. Together with the monotone-event separation, this means the current broad
mechanism does not pass G1; no algorithm or efficacy experiment is selected.


### Partial-feedback switching-cost prior (2026-10-28)

The primary-source addition in [switching_risk_search_active_test_audit_v1.md](switching_risk_search_active_test_audit_v1.md)
records Rangi and Franceschetti (AISTATS 2019), Algorithms 2–3 and Theorems 5–6. Their
feedback-graph EXP3 methods already adapt action distributions to partial feedback while
controlling expected switches/regret. They lack paid hard-budget labels, delay and false-promotion
risk. These differences require a theorem-preserving reduction and matched baseline; they do not
validate generic joint acquisition and switching as novel. G1 remains open.


### Finite-horizon utility-driven sensing prior (2026-10-28)

switching_finite_horizon_sensing_prior_audit_v1.md records inspection of Ferrari, Zhao and
Scaglione's primary source, arXiv:1705.05960v1. Their finite-horizon POMDP already jointly
optimizes sensing selection, stopping and exploit/discard decisions using time-varying posterior
thresholds. This closes generic finite-horizon utility-driven acquisition and threshold/VOI
controllers. Delay queues, hard pathwise label caps, causal-null risk and repeated reversible model
switching are absent; any delta must prove a result from that interaction beyond established
sequential sensing and robust planning. No candidate has passed G1.

### Reward/detection two-threshold control prior (2026-10-28)

`switching_reward_detection_control_prior_audit_v1.md` records a primary-source read of
Banerjee, Liu and How, arXiv:1609.06757v2 (ACC 2017). Their two-threshold controller already
trades reward-optimal behavior against information-maximizing behavior before switching to a
post-change policy, and the source discusses repeating the procedure across sufficiently
separated changes. Therefore a generic evidence-band exploration/controller is occupied. The
audited source does not provide ShiftLab's hard paid label cap, delay, switching fee or
conditional-null false-promotion bound; those differences remain comparison obligations. The
remaining acquisition question is when to spend a query right on one shared paired-outcome stream,
with a theorem under the same risk and delayed reversible economics. G1 remains open; no
experiment is authorized by this audit.

### Conditional episode-risk recycling (2026-10-28)

`switching_two_episode_risk_recycling_v1.md` exactly checks a two-look positive-only test under
the causal conditional null. Conditional risk levels compose multiplicatively, allowing a
conditional-error allocation to improve over Bonferroni. Posch and Bauer's primary two-stage
design paper already uses conditional error to adapt sample size while preserving the type-I
level; thus generic adaptive risk recycling is established. The ShiftLab toy has no reversible
control or delay-driven acquisition advantage and does not pass G1. Keep as a baseline, not a
candidate.

### Cost-aware correlated-action bandits and two-phase reduction (2026-10-29)

`switching_costly_bandits_two_phase_audit_v1.md` records primary-source inspection of Schur,
Lago and Fiez (UAI 2026), including Lemma 1 and its Appendix B.1 proof. Their stationary model
already supports action-dependent observation costs, correlated rewards, cost-sensitive acquisition,
and a uniform reduction from arbitrary policies to an initial labeled prefix followed by one-action
commitment. The result does not cover delayed labels, a pathwise total query cap, recurrent hidden
regimes, repeated reversible deployment, or causal-null promotion risk. Thus it closes another
generic acquisition/two-phase claim, while the exact contract mismatch remains a comparison
obligation rather than evidence of novelty. No efficacy grid was run; G1 remains unresolved and
G2–G5 remain held.

### Markov state sensing cost and truncated planning (2026-10-29)

`switching_markov_state_sensing_cost_audit_v1.md` records a primary-source audit of Kapoor and
Nair (AISTATS 2026), including the state-expansion protocol, SPI, and Theorems 4.1, 4.2 and 4.4.
The paper already provides Markov-state sensing costs, blind-action look-ahead, an always-sense
optimality threshold, and a computable truncation/suboptimality bound. It observes the latent state
when sensing, and has neither delayed noisy paired labels nor a hard total budget, reversible
deployment fees, or the separate causal-null reachability constraint. Thus it closes generic
Markov sensing and approximate-planning claims but does not resolve the exact ShiftLab interaction.
The mismatch remains an obligation, not a novelty claim; G1 is still open and G2–G5 are held.

### Delayed-observation information states (2026-10-29)

`switching_delayed_pomdp_information_state_audit_v1.md` records a primary-source check of
Subramanian et al. (JMLR 2022), Theorem 5 and its proof, and the delayed-POMDP example in Section
2.4. Exact Bellman planning from a sufficient information state is established; for delayed POMDPs
the cited example uses a delayed-state belief and the last delay-window controls. Consequently,
adding a known-HMM belief, pending-label queue, request budget and deployed action is not a method
contribution for the economic single-law problem. The source does not cover the separate causal-null
reachability constraint with hidden pending outcomes, so the full two-law problem remains open. The
remaining novelty target is a risk-preserving information state with a bound against the full
two-law oracle, or a growing-family memory lower bound. Source hash and cache path are in manifest
v27. This closes only queue/belief augmentation, not G1 overall.

### Comparator update 2026-10-29: finite-horizon onset weights

The persistent one-change calendar/e-detector comparator has a stronger finite-horizon version:
optimize its start-mixture weights against the worst-onset regret bound, rather than use the
infinite-horizon default prior. The derivation and implementation are in
[`switching_finite_horizon_mixture_frontier_v1.md`](switching_finite_horizon_mixture_frontier_v1.md)
and `scripts/optimize_switching_onset_mixture.py`. This tightens a standard comparator only; it
does not close the delayed recurrent-switching gap or establish novelty. The registered
moderate-signal case remains vacuous under this bound.
