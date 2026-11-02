# Failure Atlas: next method proposal

Date: 2026-11-01. Status: research proposal; no new method results. This follows the completed cycle-7 validation and bounded fallback diagnostic. It does not amend their acceptance outcomes or consume confirmation seeds.

## Recommendation

Develop **gap-aware evidence with deadline-aware acquisition**: score each observation using its actual sampling gap, and request it only when its arrival can improve deployment or rollback enough to justify its cost. Keep a single request governor for every acquisition branch. Start with a restricted binary Markov model and fixed release delay; establish useful evidence on a uniform calendar before adding adaptive scheduling.

The intended contribution is a practical coupling of evidence and acquisition in delayed, budgeted decisions. Conditional betting, observation control, finite-horizon value of information, and rollback are established ideas. Their combination alone does not establish novelty. The candidate contribution must be an attributable improvement over strong, faithfully implemented competitors under the same information and safety contract. A modest scoped gain is sufficient; universal dominance, a revolutionary mechanism, or a new lower bound is not required.

## What the atlas supports

| Finding | Consequence for development |
|---|---|
| Cycle 3 reclassified 116/123 earlier shared failures as cost of validity under a matched reference. | Do not target all of the Bayes gap as removable algorithmic waste. |
| Tiny-horizon constrained optimisation did not establish large reference conservatism; its never-switch degeneracy limits extrapolation. | The realistic constrained optimum remains unknown. Compare achievable policies rather than promise to close an oracle gap. |
| Recurrence produced no reproduced shared failure. Dependence and informative-delay cost failures often persisted in their independent/equal-delay controls. | Keep these controls; do not claim one ubiquitous causal failure. |
| Release-order inflation at independence did not reproduce. Triggered betting largely expressed a known early/late onset tradeoff. | Do not rebuild around either explanation as a newly established mechanism. |
| Undecided-only acquisition helped in some settings but fixed pending capacity made throughput approximately P/d. Long delay could reverse the benefit. | Model pending labels and time remaining explicitly. Uncertainty alone is not a request criterion. |
| Cycle 7 improved mean primary cost by .03772 per round, with 13/16 qualifying primary wins, but failed neighbourhood safety and dependence criteria. | Preserve the acquisition signal without promoting DSS as an accepted solution. |
| Uniform acquisition ablation removed the cost advantage; removing the delay switch removed only 2.58% of the primary gain. Gap 1 was cheaper than gap 4. | Credit the existing acquisition mechanism; new scheduling rules must earn their contribution through ablation. |
| Two adverse primary cells and their neighbourhoods remained worse. Gap enforcement in fallback did not affect those cells. | Treat late expensive information and unnecessary intervention as explicit regression targets. |
| Enforcing fallback spacing reduced both sampling and false promotions in one diagnostic, but did not fix rho=.8. | A fallback patch is not the next method. Match sample counts when attributing safety to spacing. |
| The current Markov comparator was safe but often powerless for late/transient alternatives. | It is a baseline to improve, not evidence that all valid Markov methods must be powerless. |

Primary evidence: [cycle-7 decision](failure_atlas_cycle7_decision_v1.md), [validation results](failure_atlas_cycle7_validation_results_v1.md), [followup results](failure_atlas_cycle7_followup_results_v1.md), and the historical [ledger](failure_atlas_v1_ledger.md). The registered comparator collection contains local adaptations; it is not yet a source-faithful reproduction of every relevant SOTA method.

## Minimal method

### 1. Make the evidence respect the observation clock

An observation spaced g events from the preceding observation is not generally an iid draw. Fixed thinning reduces dependence but does not remove it. Begin with Z=1[D<0], D in {-1,+1}, a stationary favourable probability p <= q0=(1+h)/2, and nonnegative Markov persistence rho in [0,rho_bar]. The bound rho_bar must be externally declared or conservatively justified, not set to hidden simulator truth or an uncertified plug-in estimate.

Under this restricted null, the g-step favourable probability given the previous observed state z is p+(z-p)rho^g. A conservative upper bound is

    u_g(1) = q0 + (1-q0) rho_bar^g
    u_g(0) = q0.

Condition on the first observed label. For a prediction r made from previously released observations, use a neutral factor when r <= u; otherwise use

    f(Z) = (r/u)^Z ((1-r)/(1-u))^(1-Z).

For any true conditional probability v <= u,

    E[f | observed past] = 1 + (v-u)(r-u)/(u(1-u)) <= 1.

This is an elementary conditional betting construction, not a novelty claim. It supplies a candidate local factor, **not a completed proof for the full pipeline**. Before implementation, verify the observed filtration, predictable requests, queued observations, episode starts, and multiplicity allocation. Fixed delay preserves event order; the first prototype must exclude value-dependent releases, extra informative covariates, and unmodelled persistence. A stationary Markov null is also different from an arbitrary conditional-mean null.

For q0=.55 and rho_bar=.8, a preceding favourable state gives u=.91 at gap 1, .73432 at gap 4, and .598318 at gap 10. At rho_bar=.95, gap 4 still gives .91653. This explains why gap 4 cannot itself justify iid evidence. A grid arithmetic check of the displayed expectation gave a maximum 1.0000000000000002 (roundoff); it does not establish performance or the pipeline proof.

This envelope may sacrifice too much power. Compare it immediately with a gap-aware Markov likelihood using transition matrices P^g and a valid treatment of the composite null. Certify any required maximisation; a coarse parameter grid that underestimates the null likelihood is unsafe. Numerator predictions must be prequential. Existing whole-history homogeneous-skeleton evidence is not the strongest possible comparator for transient changes.

Use a small frozen restart mixture or explicit error allocation for late changes. Never reset evidence or reuse alpha for free. More responsive alternatives can improve power, but cannot eliminate genuine onset multiplicity costs.

### 2. Buy useful observations, not merely uncertain observations

The governor tracks remaining horizon and request budget, pending labels and their ages, deployment state, evidence, and reserved rollback capacity. Budget is charged when requesting; pending labels are never treated as observed evidence.

For a small set of candidate next-request gaps, estimate the difference in future total decision cost between requesting and waiting. Include arrival time, other pending labels, query cost, switching cost, remaining opportunity after release, and the opportunity cost of spending budget now. A short rollout followed by a frozen calendar policy is sufficient for a prototype; a full POMDP is unnecessary. Request only for positive estimated net benefit. All fallback branches pass through this governor.

Retain undecided-only acquisition as the starting policy, but let pending capacity respond to useful throughput rather than fix it at two. The quantity ceil(delay * remaining_budget / remaining_horizon) is a throughput diagnostic and simple control, not a mandate to spend all budget or a novel result. For delay 50 and budget 50 over 1000 rounds it is three, already exceeding the old cap. Keep a small frozen rollback reserve as a separate ablation.

The acquisition working model can be wrong. Fit/freeze it on development streams; never expose true onset, duration, effect or persistence. Evidence validity should depend on the declared null class, not correctness of the acquisition value model. Economic benefit has no such automatic guarantee and must be measured.

## Resolve the decision target without rewriting old results

A stationary boundary-null promotion can have positive short-term conditional value under persistence. For illustration, q0=.55, rho=.8, last observed Z=1 and delay 1 imply next-step expected benefit 2(.55+.45*.8)-1=.82, although the stationary hurdle is .1. Over ten future rounds, conditional excess benefit above the hurdle is

    2(1-q0) rho^delay (1-rho^10)/(1-rho) = 3.21345.

Subtracting two switch costs of .1 leaves 3.01345, before label cost and parameter uncertainty. This calculation is explanatory, not an evaluated policy or evidence that cycle-7 false promotions were beneficial.

For future protocols, distinguish sustained regime certification from a temporary reversible action. Retain legacy false-promotion scoring for comparable safety tests and add conditional expected finite-horizon decision value as a diagnostic. Any different primary decision target requires prospective specification. This observation neither validates the iid gate nor retrospectively rescues cycle 7. Do not make the method win by silently moving the endpoint.

## Closest work and the narrow novelty question

| Prior work | Already established | Remaining candidate question |
|---|---|---|
| [Banerjee and Veeravalli, observation control](https://arxiv.org/abs/1105.1361) | On/off sampling coupled to quickest detection and observation cost. | Does actual-gap evidence plus pending-label scheduling improve delayed finite-horizon decision cost under the same safety target? |
| [Naghshvar and Javidi, active sequential testing](https://arxiv.org/abs/1203.4626) | Adaptive informative action selection and sequential cost/error tradeoffs. | Can a small implementable governor exploit arrival deadlines and rollback needs rather than only information gain? |
| [Ferrari et al., finite-horizon sensing](https://arxiv.org/abs/1705.05960) | Sensing/exploitation utility and finite-horizon policies. | Does the proposed evidence-aware scheduler improve on a strong sensing policy with identical observations and costs? |
| [Nguyen, autoregressive inference](https://arxiv.org/html/2009.11124v2) | Time-uniform likelihood-based inference under autoregressive structure. | The adaptive sampled-gap, delayed-release contract still needs its own verification. |
| [Saha and Ramdas, non-partitioned e-detectors](https://arxiv.org/html/2607.28322v1) | Restartable change-detection constructions, including Markov likelihood examples. | Reuse appropriate machinery; do not conflate average-run-length guarantees with probability-of-ever-false-promotion control. |

These are primary-source checks, not exhaustive novelty clearance. Robust Markov testing and response-adaptive switching audits already in this repository further narrow the claim. The publishable contribution, if it exists, is an experimentally isolated improvement in this concrete decision problem, with a correct contract and sufficient distinction from these policies. “First to combine” is not the proposed claim.

## Staged development and stopping rules

This document is a proposal, not an execution preregistration. Reserve fresh development seeds and freeze exact thresholds, comparators and multiplicity treatment in the next protocol before running anything.

1. **Contract and evidence first.** Verify the filtration and local factor algebra; audit the target distinction. On uniform calendars compare iid evidence, the existing Markov gate, the conservative gap envelope, and an appropriate exact-gap likelihood baseline. Match requested labels, delay, restart budget and assumptions. Test rho=0,.5,.8,.95, bound misspecification, and early/late/transient changes. If correct evidence cannot offer useful power at the available budgets, stop the scheduler project or narrow the dependence range openly.
2. **Small coupled prototype.** Use a 2x2 evidence/acquisition comparison, with the same predictive model and budgets across arms. Include uniform, original undecided acquisition, and the new governor. Separately ablate deadline valuation, pending capacity and rollback reserve. Include matched-label controls. Mandatory regression cells are `on0.6_L1_strong_harmful_d50_b0.05_s0.1` and `f3_rho0_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1`, their neighbours, and independent/recurrence negative controls. Stop if the new controller adds no attributable benefit over uniform with the same valid evidence.
3. **Scoped validation only after a useful pilot.** Freeze a practical cost margin and acceptable neighbourhood harm before inspecting fresh validation. A suggested starting discussion value is .01 per round for a worthwhile primary gain; it is not a newly passed criterion. Preserve alpha=.1 where that is the agreed contract, report binomial uncertainty with enough null streams to assess it, and evaluate parent neighbourhoods rather than let an aggregate hide local losses. Select a defensible operating range instead of demanding wins everywhere. Refresh source-faithful competitors and give them the same dependence information. Use confirmation seeds only after the scoped claim and protocol are frozen.

A full atlas sweep is not the next action. The decisive first result is whether gap-aware evidence can be both valid and sufficiently powerful on a fixed calendar. Only then is sophisticated acquisition justified.

## HKUSTDial / ARIS idea evaluation

Applied local `C:/Users/nigel/.claude/skills/idea-evaluator/SKILL.md` and its fatal-flaws reference. This is a self-critique, not an independent external review. The user's practical novelty objective supersedes a demand for paradigm change.

- **First impression:** prospective method contribution; request information when it can change a useful decision, with an explicit dependence contract.
- **Fatal-flaw audit:** the tested fixed-gap repair is rejected as a general dependence solution. The new proposal is untested rather than data-refuted. Its principal unresolved risks are conservative evidence with negligible power, scope restricted to a known dependence bound, and a coupling that fails to improve over existing sensing methods. No current evidence establishes that these risks are fatal or solved. The staged tests are the defenses, not promised successes.
- **Capability/lifecycle:** the repository has a working CPU simulator, paired analysis and saved baselines. A restricted prototype fits that infrastructure; available weekly hours, deadline and wall-clock cost are unknown. No completion-time claim is made. Focus on one method rather than add a benchmark/theory/system agenda.
- **Dimensions (all start at 5):** Higher 5 (no measured new gain); Faster 6 (mechanism-based: fewer late useless requests, pending confirmation); Stronger 7 (mechanism-based: actual-gap null envelope, conditional on the restricted contract and pipeline proof); Cheaper 6 (mechanism-based: positive-value requests, pending paired cost ablation); Broader 5 (no grounds for extension beyond the declared model).
- **Paradigm probe:** first-principles target distinction is useful; a field-wide hidden problem, technology-cycle advantage and transformative impact are not established. No paradigm-shift claim.
- **Feasibility:** synthetic data available; compute low for an initial fixed-calendar diagnostic, unmeasured for a full sweep; engineering risk moderate around the filtration and pending queue; timeline unknown. Avoid learned world models and large planning searches in the first version.
- **Verdict: Accept with Revisions for a small prototype.** First settle the observation contract; then test the strongest feasible gap-aware evidence on uniform acquisition; then test whether deadline valuation adds cost benefit. Novelty and SOTA superiority remain unverified.

## Trail and limitations

Earlier negative results, frozen cycle-7 artifacts and acceptance failures remain intact. This proposal adds no empirical wins and changes no published guarantee. Its broadest limitation is structural: no scheduler can recover unavailable timely information, remove all validity/onset costs, or guarantee benefit under an arbitrary misspecified dependence model. A useful outcome could be a narrower safe operating region with a modest cost improvement, rather than one solution to every atlas cell.
