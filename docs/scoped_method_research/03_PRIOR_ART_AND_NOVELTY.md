# Prior-art and novelty challenge: economic rollback and late recovery

**Scope.** Targeted source-level novelty audit for the expanded research brief's primary
economically intelligent rollback question and secondary late-improvement recovery question.
The audit uses ShiftLab's existing source audits and inspects the cited primary papers or
publisher/author records listed below. It is not an exhaustive search, a patent-style originality
opinion, or evidence that any proposed method works. No held-out real outcomes were inspected.

**Decision date:** 2026-11-06. **Candidate status:** no new method has been specified at sufficient
algorithmic detail to establish originality. Generic ingredients and straightforward compositions
are closed. One narrower interaction remains testable, but novelty is not yet verified.

## 1. Scientific object and information contract

At decision time `t`, the controller's observable history may contain released queried paired
losses, query and deployment history, pending-query ages/counts, the active model, predictable
disagreement and remaining horizon/budget. It cannot contain unreleased labels, synthetic regime
identity, evaluator-side future loss, retrospective change points, or a known reversal time.
Requests consume the pathwise label cap when issued; pending labels consume budget. Loss comparisons
are only usable when both models' outcomes are identified by the paired feedback design. Switches
incur the registered deployment charge.

Let `a_t` be the active model, `q_t` a predictable query decision, `B_t` remaining query rights,
`P_t` pending feedback, and `H_t` remaining horizon. The economic objective is a pathwise-accounted
expected or realized cumulative loss plus query and switch charges. This objective must remain
separate from the event `P(any false promotion) <= alpha`: a promotion certificate does not certify
continued post-promotion benefit after a regime reversal. The deployment protocol and exact null are
therefore part of the method, not implementation details.

The possible method idea is a **joint information-and-action controller** that decides whether to
query, continue deployment, or rollback using (i) current-regime evidence, (ii) query and switch
costs, (iii) remaining time, (iv) labels in flight, and (v) risk-valid evidence. These state
variables alone are not a novelty claim. A generic dynamic program, belief state, adaptive query
rate, reserve, or economic threshold is already anticipated by standard sequential design,
controlled sensing, optimal switching and prior ShiftLab work.

## 2. Mandatory novelty matrix

| Proposed mechanism | Closest prior art | Same mathematical object? | Same information contract? | Exact delta that could matter | Strongest missing comparator | Verdict |
|---|---|---|---|---|---|---|
| Joint post-promotion query allocation and rollback, with the query/rollback choice coupled through remaining-horizon net value | Chick–Forster–Pertile delayed sequential adoption; DE-CuSum / controlled-sensing QCD; Bayraktar–Ludkovski hidden-Markov switching; constrained finite-horizon POMDP planning | **Partly.** All optimize information and/or actions over time; none of the inspected sources matches this entire tuple of recurrent paired model deployment, hard pathwise delayed-label cap, and conditional-null promotion risk | **No.** Closest sources have Bayesian one-shot adoption, known likelihood/QCD models, or fully modeled hidden-state observations; they do not share all ShiftLab observability and risk rules | A rigorously defined policy whose *joint* action has a finite-sample economic benefit over the best separated detector-plus-decision and query-plus-test compositions, while preserving the same promotion risk and cap. Merely appending state variables to a POMDP is not enough | Exact causal-null constrained planning on small instances; E_rb with tuned alpha/start grid; two-sided CUSUM/SR; controlled-sensing DE-CuSum/2E-CUSUM; Chick-style delayed adoption; Bayraktar–Ludkovski optimal switching | `NOVELTY_NOT_VERIFIED` |
| Adaptive acquisition specifically after a challenger has been promoted | Banerjee–Veeravalli DE-CuSum; Geng–Bayraktar–Lai finite sampling rights; Veeravalli–Fellouris–Moustakides controlled sensing; ShiftLab RMM and post-verdict acquisition ablations | **Yes, at component level.** Query timing conditional on prior evidence is established; post-verdict acquisition is already represented in ShiftLab | **Partial.** Published QCD sources use an unknown permanent change, sampling cost/right constraints and false-alarm/delay criteria. ShiftLab adds paired loss feedback, reversible deployment costs and a separate promotion gate | Only an interaction result where adaptive acquisition lowers net cost at matched *correctly specified* rollback performance, hard pathwise cap, delay, and null behavior beyond fixed, front-loaded, DE-CuSum and detector-plus-fixed-economic-rule schedules | Matched DE-CuSum / controlled sensing; fixed and front-loaded post-promotion queries; E_rb plus adaptive acquisition; detector + fixed economic rule; exact finite constrained oracle | `INCREMENTAL_BUT_TESTABLE` |
| Rollback when a deterioration detector crosses an economic threshold that depends on switching cost and remaining horizon | Standard optimal stopping / finite-horizon control; Bayraktar–Ludkovski hidden-Markov optimal switching; Rust replacement; ShiftLab E_rb and tuned threshold/start-grid ablations | **Yes.** Thresholded switching under running benefit and switching cost is a standard stopping/control object | **Partial.** The ShiftLab filtration and statistical validity constraint differ from the cited control models, but an economic threshold itself does not | A valid and measurable improvement over E_rb plus a separately tuned economic threshold, not just a different threshold or start grid | E_rb alpha/threshold tuning, no rollback, standard two-sided CUSUM/SR with the same economic rule | `KNOWN_COMPOSITION` |
| “Avoid unnecessary rollback” by using a two-sided CUSUM, SR/e-detector, GLR or restart mixture | Page CUSUM; Shiryaev–Roberts; Shin–Ramdas–Rinaldo e-detectors; Saha–Ramdas non-partitioned e-detectors; DAS-CUSUM; existing ShiftLab E_rb/RMM | **Yes.** Restarting, aggregating starts/scales, and two-sided change monitoring are established detector constructions | **Partial.** E-detectors provide their stated ARL/PFA control under their assumptions; they do not thereby provide ShiftLab's conditional false-promotion event or economic optimality | A new theorem or empirical interaction beyond the matched off-the-shelf detector and E_rb with identical labels, alpha accounting, start grid and switch costs | Conventional two-sided CUSUM/SR/e-detector and matched E_rb; same detector with fixed economic cutoff | `KNOWN_COMPOSITION` |
| Late recovery after a prior unfavorable certificate using continued post-verdict evidence and restart monitoring | ShiftLab's RMM prior audit; e-SR/e-CUSUM; M-UCB / GLR-klUCB; Giacomini–Rossi one-time reversal / fluctuation tests; Xu and other active certificate acquisition | **Yes, as currently described.** Continued acquisition and restart monitoring are already implemented/audited; forecast reversal tests already target relative performance changes | **Partial.** Most detector/reversal methods do not include a hard paired-label cap, delayed release and recurrent deployment risk contract | A nontrivial *joint* information allocation rule that outperforms Gated+front and the same acquisition attached to standard SR/CUSUM/E_rb without increasing in-scope null errors | Corrected Gated+front; corrected DISCERN where applicable; SMCS; RMM; matched SR/CUSUM/e-detectors; Xu acquisition-only explicitly labeled as such; Gated plus fixed/front-loaded acquisition | `KNOWN_COMPOSITION` |
| Query on observable disagreement, with remaining budget/horizon or expected value-of-information weighting | Active learning, controlled sensing, costly bandits, sequential experimental design, DE-CuSum/2E-CUSUM; ShiftLab's prior shadow-price/pending-label/deadline tests | **Yes, at component level.** Disagreement- or value-directed information acquisition is known; disagreement alone does not reveal which model has lower loss | **Partial.** Some methods observe action-specific rewards or have a model/posterior; ShiftLab's selective paired labels are delayed and only reveal outcomes for queried events | A predictable, correctly identified policy that improves the matched net-cost frontier and preserves the certificate filtration; no novelty from “query where models disagree” by itself | Uniform/front-loaded/paced queries, Xu `q*` acquisition-only adapter, DE-CuSum/controlled sensing, and standard active acquisition under the identical information contract | `KNOWN_COMPOSITION` |
| “Regime detector” that selects the rollback or late-recovery rule | Ordinary CUSUM/SR/GLR/e-detectors, Bayesian change-point filters, forecast instability tests, ShiftLab's existing regime diagnostics | **Yes, for the detector object.** CUSUM/SR/GLR and posterior change-state filters already detect regime changes | **Partial.** Must be restricted to released labels and observable history; future loss or synthetic regime truth is prohibited | Only if the observable diagnostic changes a policy decision and yields lower fully charged cost, including classification error and detection delay, against matched detectors | Standard change detectors and sequential model-selection methods coupled to the same fixed decision rule | `NOVELTY_NOT_VERIFIED` |

### Verdict interpretation

- `DISTINCT_MECHANISM_PLAUSIBLE`: reserve for a concretely specified mechanism with an identified,
  unoccupied interaction, before efficacy is known. None of the present descriptions meets that
  bar yet.
- `INCREMENTAL_BUT_TESTABLE`: known core pieces, with a bounded comparison capable of showing a
  genuine interaction effect beyond simple baselines.
- `KNOWN_COMPOSITION`: the current verbal proposal reduces to established modules or existing
  ShiftLab controls; a renamed combination is not novel.
- `NOVELTY_NOT_VERIFIED`: insufficient algorithmic specificity or source coverage to establish
  either a distinct mechanism or an exhaustive negative claim.

These verdicts are scoped to the proposed descriptions above. They are not a claim that all possible
algorithms under the contract have been searched.

## 3. Primary-source review and comparator implications

### Post-promotion monitoring and deterioration detection

1. **Shin, Ramdas & Rinaldo, “E-detectors: A nonparametric framework for sequential change
   detection,” NEJSDS (2024).** The paper defines change detectors by aggregating e-processes
   started at candidate change times. Its SR statistic sums start-specific processes; its CUSUM
   statistic maximizes them. Its guarantees concern its declared pre-change class and detector
   criteria (including ARL/PFA distinctions), not an automatic certificate of negative economic
   value after deploying a challenger. The article identifies the authors' reproduction code:
   [paper](https://nejsds.nestat.org/journal/NEJSDS/article/59/read),
   [author code](https://github.com/shinjaehyeok/e_detector_paper).
2. **Saha & Ramdas, “Non-partitioned e-detectors for nonparametric sequential change detection,”
   arXiv:2607.28322 (2026).** Aggregation over candidate change points and an infimum over possible
   no-change distributions broadens the detector classes and includes Markov-transition changes.
   This rules out generic “restart over possible starts under unknown distribution” as a novelty
   claim. The contract still differs from economic model switching with selectively acquired
   delayed paired losses. [Primary paper](https://arxiv.org/abs/2607.28322).
3. **Banerjee & Veeravalli, “Data-Efficient Quickest Change Detection in Minimax Settings,” IEEE
   TIT 59(10), 2013.** DE-CuSum jointly chooses an on/off observation-control policy and alarm time,
   optimizing worst-case detection delay subject to false-alarm and pre-change observation-cost
   constraints. This is direct prior art against a generic adaptive query-plus-detector claim.
   Its one permanent change, observation-rate constraint and QCD criterion do not instantiate
   ShiftLab's repeated deployment actions and hard total request cap.
   [Primary paper](https://arxiv.org/abs/1211.3729),
   [publication record](https://experts.illinois.edu/en/publications/data-efficient-quickest-change-detection-in-minimax-settings/).
4. **Veeravalli, Fellouris & Moustakides, “Quickest Change Detection with Controlled Sensing,”
   arXiv:2310.17223 (2023).** The WCC procedure adaptively chooses sensing actions based on recent
   observations to maximize estimated KL information while controlling false alarms. This further
   closes “sample more when the detector thinks a change is emerging.”
   [Primary paper](https://arxiv.org/abs/2310.17223).
5. **Lubenia & Banerjee, “Quickest Change Detection with Cost-Constrained Experiment Design,”
   arXiv:2509.14186 (2025).** The paper selects among experiments with different information and
   costs; 2E-CUSUM is proposed for two experiments, with extensions and asymptotic analysis. This
   is an especially close active acquisition baseline for a query-versus-no-query or low/high
   information rule. [Primary paper](https://arxiv.org/abs/2509.14186).
6. **Giacomini & Rossi, “Forecast Comparisons in Unstable Environments,” JAE 25(4), 2010.** The
   Fluctuation and One-Time Reversal tests assess changes in relative forecast performance over a
   historical evaluation sample. They are not sequential delayed-label deployment controllers,
   but they close the claim that late reversals in relative predictive performance are themselves
   a new phenomenon. [Author paper record and manuscript](https://ideas.repec.org/p/duk/dukeec/08-4.html).

### Economic acquisition and reversible action choice

7. **Chick, Forster & Pertile, “A Bayesian decision-theoretic model of sequential experimentation
   with delayed response,” JRSS B 79(5), 2017.** Their Bellman recursion jointly accounts for
   sequential sampling, sampling expense, delayed outcomes still in a pipeline, a maximum sample
   size, and a terminal adoption charge/benefit. This is a precise match for the *stationary,
   one-decision* subproblem. It makes “expected benefit of one more delayed label minus its cost”
   insufficient novelty. It does not provide recurrent reversals or ShiftLab's conditional-null
   anytime promotion guarantee. [Published article](https://rss.onlinelibrary.wiley.com/doi/10.1111/rssb.12225),
   [accepted manuscript with equations](https://eprints.whiterose.ac.uk/110768/1/delaypaperDriver.pdf).
8. **Feit & Berman, “Test & Roll: Profit-Maximizing A/B Tests,” Marketing Science 38(6), 2019.**
   The stopping horizon is selected to trade off opportunity cost of experimentation against the
   harm of a bad rollout; profit maximization rather than a fixed significance threshold is the
   core object. [Author manuscript](https://arxiv.org/abs/1811.00457). A net-benefit threshold by
   itself is therefore not new.
9. **Bayraktar & Ludkovski, “Sequential Tracking of a Hidden Markov Chain Using Point Process
   Observations,” SPA 119(6), 2009.** Posterior-state control jointly values running payoffs and
   recurrent switches with switching costs under a hidden Markov regime. The theorem/model uses
   a specified point-process observation model, not a selectively queried hard label budget or
   conditional-null test. Thus “use belief state + time-to-go + switching penalty” is an established
   control primitive. [Primary paper](https://arxiv.org/abs/0712.0413).
10. **Geng, Bayraktar & Lai, “Bayesian Quickest Change Point Detection with Sampling Right
    Constraints,” arXiv:1309.5396 (2013).** A finite number of sample rights is incorporated in a
    Bayesian sequential stopping recursion. A finite query budget plus an evidence threshold is not
    sufficient novelty. [Primary paper](https://arxiv.org/abs/1309.5396).
11. **Lau & Tay, “Asymptotically Optimal Sampling Policy for Quickest Change Detection with
    Observation-Switching Cost,” IEEE TSP 69, 2021.** The source audit in
    [`switching_observation_switching_qcd_audit_v1.md`](../switching_observation_switching_qcd_audit_v1.md)
    inspected the formal criteria and the open-loop and two-stage sampling policies. Adaptive
    observation choices with switching costs are known; their switches are sampling-mode switches,
    with average costs and an asymptotic permanent-change QCD objective rather than ShiftLab's
    model deployment switching cost.
    [Primary paper](https://ieeexplore.ieee.org/document/9347742),
    [arXiv](https://arxiv.org/abs/1912.11693).
12. **Cheng et al., “Online Learning with Switching Costs and Bandit Feedback,”** and the ShiftLab
    switching audits close generic budgeted acquisition plus switching-cost learning. See
    [`switching_costly_observation_uai26_audit_v1.md`](../switching_costly_observation_uai26_audit_v1.md),
    [`switching_recent_paid_delay_movement_prior_audit_v1.md`](../switching_recent_paid_delay_movement_prior_audit_v1.md),
    [`switching_delayed_comparator_audit_v1.md`](../switching_delayed_comparator_audit_v1.md),
    and [`switching_hidden_markov_optimal_switching_prior_audit_v1.md`](../switching_hidden_markov_optimal_switching_prior_audit_v1.md).
    These audits document the exact mismatches and why they do not, by themselves, prove a novelty
    gap.

## 4. Existing ShiftLab novelty decisions that constrain this proposal

The following records are prior evidence and must not be overwritten or recast as new results:

- [`docs/sprint2/novelty/NOVELTY.md`](../sprint2/novelty/NOVELTY.md) classifies RMM as an
  incremental composition of a restart mixture, continued post-verdict acquisition, host restart
  and alpha split. It found the development gain attributed more to continued acquisition than to
  the restart mixture, and specified matched off-the-shelf e-detector plus acquisition as the
  strongest ablation. The later audit reports that RMM did not significantly beat E_srr on the
  retrospective real late stratum.
- [`docs/sota_sprint/novelty_audit.md`](../sota_sprint/novelty_audit.md) records C1/C2/C5/C6
  (shadow price, pending-label credit, deadline and related acquisition variants), budget reserve,
  rollback and restart mixtures. It says the ingredients are established; only a valid joint risk
  statement or a specific matched economic interaction could raise the contribution beyond
  composition.
- [`docs/scoped_method_research_2026-11-06/BASELINE_FIDELITY.md`](../scoped_method_research_2026-11-06/BASELINE_FIDELITY.md) identifies
  existing E_rb (rollback wrapper), RMM, E_srr, Gated+front, corrected DISCERN-style port, SMCS and
  Xu acquisition-only adapter with their fidelity limitations. E_rb's alpha and start grid are
  material; its horizon gate was non-binding in the reported ablation. Xu acquisition-only is not
  Xu's published certificate.
- [`docs/scoped_method_research_2026-11-06/MECHANISM_ABLATION.md`](../scoped_method_research_2026-11-06/MECHANISM_ABLATION.md) and
  [`docs/scoped_method_research_2026-11-06/CORRECTED_REPLAY_AUDIT.md`](../scoped_method_research_2026-11-06/CORRECTED_REPLAY_AUDIT.md)
  record development evidence: candidate C2/C6 have mixed behavior and no clear real-source
  advantage over Gated+front; no result isolates a new post-promotion policy from alpha/start-grid
  choices. The data are exposed, so they cannot confirm a newly selected method.
- [`docs/switching_hidden_markov_optimal_switching_prior_audit_v1.md`](../switching_hidden_markov_optimal_switching_prior_audit_v1.md)
  contains a tiny exact-enumeration diagnostic where one rollback reduces expected cost in a
  recurrent hidden-Markov cell. The audit explicitly rejects “reversible switching adds value” as
  novelty; the result is a mechanism diagnostic, not a general efficacy or originality result.
- [`docs/switching_delayed_comparator_audit_v1.md`](../switching_delayed_comparator_audit_v1.md)
  gives a direct reduction of the stationary one-switch case to Chick–Forster–Pertile and rejects
  generic delayed Bellman planning as novelty.
- [`docs/switching_markov_state_sensing_cost_audit_v1.md`](../switching_markov_state_sensing_cost_audit_v1.md),
  [`docs/switching_risk_search_active_test_audit_v1.md`](../switching_risk_search_active_test_audit_v1.md),
  [`docs/switching_costly_bandits_two_phase_audit_v1.md`](../switching_costly_bandits_two_phase_audit_v1.md),
  and [`docs/switching_finite_horizon_qcd_budget_delay_audit_v1.md`](../switching_finite_horizon_qcd_budget_delay_audit_v1.md)
  close generic belief-state planning, finite-horizon active testing, cost-aware acquisition and
  hard-cap detector-latency claims as novelty by themselves.

## 5. What could still be a substantive contribution

The only plausible opening is an **interaction claim**, not a component claim:

> Under one explicit delayed-label filtration and pathwise query/switch-cost contract, a predictable
> controller that jointly chooses post-promotion acquisition and rollback achieves lower finite-
> horizon net deployment cost than every matched *separable* construction (strong detector or
> E_rb, plus independently chosen query schedule and economic threshold), while retaining the
> original in-scope promotion-risk bound.

This would need more than observing that an MDP planner can use a richer state. The paper must show
why independent optimization is inadequate, identify the relevant interaction (for example,
remaining-horizon-dependent value of acquiring one more delayed label changes both query timing and
rollback timing), and report a strict advantage against the best matched composition. For a theorem
claim, specify whether the alternative-state value is Bayesian/model-based while the safety event
is worst-case/conditional-null; do not collapse them into one posterior. Prove that pending requests
are charged at issuance and the evidence process remains valid under predictable acquisition.

For late recovery, the exact same novelty burden applies. RMM and post-verdict acquisition already
exist in ShiftLab. The comparator must hold acquisition fixed while exchanging the restart detector,
and hold the detector fixed while exchanging acquisition; otherwise an improvement cannot be
attributed to a distinct joint rule. Disagreement can determine where to sample, but it cannot
identify which model is better without a released outcome.

## 6. Required falsification before any novelty upgrade

The expanded brief's mandatory rollback ablations should be implemented under one frozen protocol:

1. No rollback; existing E_rb; E_rb after alpha/threshold/start-grid tuning; standard two-sided
   CUSUM; SR/e-detector; and full candidate.
2. For each detector/action rule: uniform/fixed post-promotion queries, fixed reserve,
   front-loaded queries, no adaptive acquisition, and candidate adaptive acquisition.
3. Detector followed by fixed economic rule versus joint policy; no economic threshold versus
   matched threshold; rollback detector disabled versus enabled.
4. Match horizon, query budget (including pending labels), label delay, query price, switch price,
   observable information and type-I accounting. Report promotion and rollback error rates only
   under their specified nulls; report detection delay, unnecessary rollback classification,
   label/switch expenditure, predictive loss and net cost separately.
5. On the late-recovery track include corrected Gated+front, corrected DISCERN where applicable,
   SMCS, RMM, conventional SR/CUSUM/e-detectors, relevant gap/Markov-aware approaches and active
   acquisition; label Xu as acquisition-only if the published certificate is not implemented.
6. Freeze the mechanism, claim, comparator set, settings and analysis before untouched confirmation.

If E_rb tuning, a standard two-sided restart, or a fixed/front-loaded acquisition rule reproduces
the apparent effect, classify it as that simpler method and stop the novelty claim. If the full
candidate only improves by spending more labels or changing the in-scope risk, it fails.

## 7. Bounded conclusion

**Current novelty verdict:** no candidate presently earns `DISTINCT_MECHANISM_PLAUSIBLE`. The
descriptive joint-controller proposal is `NOVELTY_NOT_VERIFIED`; adaptive post-promotion acquisition
is `INCREMENTAL_BUT_TESTABLE`; rollback thresholds, generic deterioration detectors and late
restart-plus-acquisition are `KNOWN_COMPOSITION` given prior art and existing ShiftLab work. The
candidate may be reconsidered only after exact matched falsification shows a non-separable effect.

This is a prior-art boundary, not a stop decision for the research objective and not evidence that
all possible methods are known. It protects against relabeling a standard composition as a novel
method while preserving one tightly specified empirical question for the bounded experiment.
