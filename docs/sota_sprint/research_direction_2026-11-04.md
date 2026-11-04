# Research direction checkpoint — 2026-11-04

## Current decision

**Do not promote another method from the current sprint to a novel SOTA claim.** The current best supported output is a scoped benchmark and validity–power study, with an empirical real-data component. The SOTA sprint reports `SOTA_NOT_MET` under its full gate: the fresh synthetic late-improvement result is established only for certificate hosts, while credible real late-improvement relevance is absent. The stronger continuation worktree independently records the same limitation for its candidate method and flags a largely incomplete claim audit. Keep these scopes explicit.

## Evidence we can stand behind (within stated scope)

1. **SOTA sprint (current branch).** Amendment 5 confirms that RMM improves late-change cost against Xu on four registered certificate hosts, but its persistent-null promotion rates are high (`rho=.8`: .12–.18; `rho=.95`: about .71) and reversal costs worsen. Amendment 6, combining restart monitoring with the dependence-robust SUI evidence, did not meet its registered gate: real twin-null validity failed on bike_hour and late benefit was partial. See [execution report](REPORT.md), [Amendment 5](validation/amend5_results.md), and [Amendment 6](merge/merge_results.md).
2. **Archived B3 outcomes (full run-pipeline attribution downgraded).** The saved arrays report `WIN` on weather, spam, and Rialto and `SAFE` on all seven streams. Means, paired comparisons and bootstrap endpoints reproduce to 1e-9 from those arrays. Treat them as retrospective descriptive outcomes: weather/spam have only 3/1 episodes, costs and delays are imposed, and the batch comparator assumes exchangeability. The B1 policy source is separately hash-verified at `041bc26`; however, the recorded full-run runner hash (`d2b7e83e…`) differs from the only committed B3 runner available (`2550728b…` at `475bf474`). A 2026-11-04 scan of all 21 local ICML Git repositories and every tracked version of that runner (including LF/CRLF forms) found no match. The archived rows therefore lack verified runner-to-row attribution. G07 remains unsigned and there is no independent statistical sign-off. See the [claim-to-evidence ledger](claim_to_evidence_ledger_2026-11-04.md) and the provenance notice in the [B3 report](../promising_directions/16_REAL_DATA_RESULTS.md).
3. **Versioned challenger idea.** It passed a 1,000-seed IID null diagnostic. Prior charged chronological comparisons used unpurchased evaluation labels to train v2 and are invalidated. A corrected, exposed five-stream screen beats RMM and the front certificate on mean cost but loses to version-aware Model Picker on all five. Keep exploratory tooling only; see the [corrected provenance report](versioned_real_provenance_fixed_results.md) and [candidate record](versioned_challenger_candidate.md).
4. **Other algorithm leads are closed or negative.** Adaptive RMM/SUI merge failed; profile-denominator likelihood candidate did not improve costs and was much slower; Sethi fixed-gap port was screened as too conservative. The eventwise contextual scout's advantage over its internal rank baselines survives a support-matched review, but it never crossed the threshold against source-matched DR-LIL or DR empirical-Bernstein OPE gates on three fresh 60-seed blocks, nor against the finite-class OPI screen. It remains synthetic and does not establish SOTA; the EB result is detailed in [the frozen gate and comparison](../scout_context_ope_empirical_bernstein_gate_2026-11-04.md) and the [OPE audit](context_scout_ope_comparator_audit_2026-11-04.md).

## Literature boundary

The existing primary-source audit already covers direct sequential risk monitoring, prediction-powered monitoring, model-selection gates, contextual safe policy control, online active model selection, sequential model confidence sets, change detection, and repeated challenger training. In particular, generic anytime-valid monitoring and restart mixtures are not novelty claims. The exact remaining gap has to exceed existing methods under the same null, dependence, delay, label budget, and economic objective. See [novelty audit](novelty_audit.md) and the repo's [closest prior work](../closest_prior_work.md).

## Promising work to do next

An independent audit rejected a proposed twin-role-swap e-process as an algorithmic lead. Role swapping can yield a valid martingale only when acquisition and stopping are role-symmetric, but that randomization null also makes the statistic directionless for a fixed challenger. Randomizing which model serves each eligible event restores directional power under a sharp null, but that is a standard canary randomized trial; delayed-outcome anytime-valid inference already has direct prior work (Lindon & Kallus, ICML 2026). Do not present either construction as a novel fixed-challenger gate.

The highest-value next step is an evidence-completion package for the P2 validity–power trade-off, rather than another gate or likelihood-bound tweak:

1. Reconcile the current sprint, B3 real-data evidence, and retrospective audit into one claim-to-evidence ledger. Recompute metrics only from archived row-level artifacts; label every result by source branch/commit, seed exposure, data exposure, validity status, and exact estimand.
2. Have an independent reviewer verify the B3 source-to-row path and the conditional-null argument for P3b. Keep the empirical synthetic/real-stream cost result separate from the certification null. Do not call a retrospective conditional-null monitor “marginal-null safe.”
3. If the paper claims the value of anytime certification over batch selection, verify a fixed-sample paired comparator under the same null and identical budget/delay/economic contract. Distinguish P6 versions: the exact 5.3876% boundary-null counterexample concerns an archived repeated `n=25` mean-threshold rule, while B3's current P6 code runs one exact-binomial test after up to 50 labels. The current code is sign-blind, but budget exhaustion can make its terminal count depend on later query availability. The written P3b fixed-delay null does not yet prove validity conditional on that complete selection path; see [`b3_p6_validity_scope_2026-11-04.md`](b3_p6_validity_scope_2026-11-04.md). Deterministic real streams do not instantiate a stochastic null.
4. Run the new method only if a specific theorem-level gap survives this audit. Any new empirical claim requires a new registered protocol, a disjoint seed/data block, and no parameter selection on that block.

**No method lead currently survives.** In particular, the hard-budget, delay-aware acquisition idea is closed as a current lead: the registered A5b+C6 composition lost its frozen cost gate by about `+4.620` per event over the four delayed/late targets, while prior scheduler screens also failed to establish an advantage. Active inference, active testing, and delayed-feedback scheduling are established adjacent areas; another pacing heuristic would not close the gap. The twin-role-swap idea is also closed.

The fresh-seed rollback stress screen also rejects the versioned dual-monitor extension for now: its unreserved policy spent almost the full cap with little rollback sensitivity, while a reserved policy reduced false promotions at the cost of substantial missed improvements and still did not detect degradation. See [the stress screen](versioned_stress_screen_2026-11-04.md). Do not treat rollback as the current method lead.

The registered 30-seed development pilot combining C6 deadline-value acquisition with A5b's
gap-aware Markov SUI evidence also fails its cost gate. Its equal-cell mean paired cost increase
is about `+4.620` per event across the four delayed/late targets, with only one target cell
favoring the treatment. Close this composition without tuning or a validation run; see the
[protocol](a5b_c6_deadline_dev_protocol_2026-11-04.md) and [result](a5b_c6_deadline_dev_results_2026-11-04.md).

This package can make a paper more defensible, but it does not itself create a novel algorithm. A new algorithm is retained only if it beats the strongest valid same-contract baseline on a disjoint confirmation and the result survives an independent result-to-claim review.

## Theory screen: finite-refresh bound closed

The current information bound is the only plausible route to a substantive new result, and it is a
theory contribution rather than a method lead. A decision-value corollary in
[`unknown_persistence_information_bound.md`](unknown_persistence_information_bound.md) proves that
at `rho=1`, under a marginal-null promotion constraint and a common observation channel, no
adaptive-query policy can close a calculable fraction of the gap to a fixed challenger oracle: for
`alpha=.05`, `delta=.05`, `T=2000`, `c_s=5`, it bounds the policy at 109.725 units against an oracle
at 195, a gap of at least 85.275 deployment-loss units. The straightforward finite-refresh coupling
extension is valid but becomes vacuous by `rho=.9999`. An independent O(T^2)-cell path-type
relaxation also fails to give a useful finite-refresh regret bound: at `rho=.95` and `.8`, its
gross-gain ceilings are about 231 and 510, both above the fixed challenger oracle's net 195.
Computing the sharper joint distribution of likelihood ratio and offline switching reward would
require an unproven state compression; the obvious exact state space is too large at `T=2000`.
Close this theory route for current method development. Retain the `rho=1` result as a scoped
boundary observation only. Reopen theory work only if a new structural argument yields a useful,
certified bound under the registered finite-refresh objective; do not restart algorithm
development without a source-level gap.

## Reproduction pointers

- Current checkout: `git rev-parse HEAD` is `de9aaaa3fa46a16944f5078234b3588a73e80fef`; `origin/main` is the same commit as of 2026-11-04.
- SOTA sprint source and raw outputs: `scripts/sota_sprint/`, `outputs/sota_sprint/` (ignored/local), and `docs/sota_sprint/`.
- Historical B3 code/results: audit worktree `shiftlab-retrospective-audit-2026-11-01`, protocol commit `19f1090`, implementation commit `041bc26`, result commit `475bf47`; artifacts include row-level episode JSONL, paired seed arrays, manifests, and recomputation files.
- The audit worktree's summary is not a clean independent sign-off: `CLAIM_LEDGER_COVERAGE.md` says the bounded ledger covers 33 rows, leaves 9 not yet audited and 24 partial/inconclusive, and G01 remains unsigned.

## Stop / advance rule

- **Advance the evidence package** if every headline result reconciles to raw rows, the source-to-claim audit resolves, and a same-null batch comparator can be validity-calibrated without changing the estimand.
- **Stop method novelty** if the strongest valid batch/active baseline matches the candidate or if no admissible real stream has measurable switching headroom. Retain the benchmark and negative results with precise scope.
- **Advance a new method** only after a written proof delta, a frozen protocol, and a disjoint confirmation all pass. Synthetic significance or a larger search grid alone does not meet this rule.

## Continuation update — 2026-11-04

The current branch has no upstream commits to integrate: after `git fetch origin`, `HEAD` and
`origin/main` both resolve to `de9aaaa3fa46a16944f5078234b3588a73e80fef`. The working tree contains
local research changes; these remain uncommitted and were preserved.

The newly registered gap-conditioned evidence screen is now complete and **neither candidate
passes its advance rule**. `gap_envelope_rho08` is cheaper than the Markov-LR comparator on 11/11
eligible alternative cells (mean paired difference `-0.0347`), but it misses both mandatory
adverse-cost guards. `gap_envelope_rho95` is essentially tied overall (`+0.0035`) and also misses
both guards. The full pointwise null table and raw rows remain in the protocol's output directory;
this result closes the screen, not the underlying broad goal. Do not add adaptive acquisition to
this candidate. See [the frozen protocol](../failure_atlas_gap_envelope_development_protocol_v1.md)
and [the result](../failure_atlas_gap_envelope_development_results_v1.md).

The lower-level primary-source review also confirms that *Which LLM to pick? Online Active Model
Selection for Large Language Models* (arXiv:2610.01592, submitted 2026-10-01) is an important
acquisition baseline: its streaming query rule combines hypothetical loss variance and posterior
entropy, with exponential-weights updates. The paper's objective is identification/regret and its
experiments match average annotation counts; it does not establish pathwise hard-budget delayed
promotion safety. The repository already contains an explicitly adapted `OnlineLLMPicker` and
hard-budget delayed Online LLM Picker and CAMS adapters. Reimplementing those methods, or adding a
generic remaining-budget/deadline heuristic, is therefore not the next contribution. Existing
repository audits already reduce generic deadline-aware acquisition to finite-horizon belief-state
control and enumerate the relevant delayed-feedback precedents.

**Research decision:** no algorithmic lead currently survives the result and novelty audits. Keep
the corrected versioned-challenger result and the gap-envelope result as evidence, not method
claims. The immediate useful work is source-to-claim completion (especially B3 run-source identity)
and an independent result review. Reopen empirical method development only when a source-audited
structural difference or a real stream with observed release times and a matching decision contract
is identified. A new synthetic grid or scheduler-only tweak does not satisfy that condition.

Primary source for the active-selector update: [arXiv:2610.01592](https://arxiv.org/abs/2610.01592).

## Continuation audit — uniform-propensity scout attribution, 2026-11-04

A source-level audit found that the eventwise scout confirmations use uniform query probability
`q_t=b` but the shared candidate-fitting code charges global-bound methods using `q_min=b/2`.
For uniform querying, replacing the generic floor with the known actual propensity makes the
eventwise and global scout certification bounds identical. The full Markov and temporal manifests
also confirm uniform querying and the same four method arms. Their registered improvements over
pooled-rank/nested-volume therefore combine contextual policy selection with a twofold looseness in
the global support bound; they do not isolate an eventwise-bound advantage. The old result files
remain faithful to the frozen code and are not deleted or rewritten. See the
[source audit](eventwise_scout_known_uniform_propensity_audit_2026-11-04.md).

The saved paired Markov (43,200) and temporal (19,200) rows verify identical selected candidate
IDs, scout gains, query counts, and processed-event counts between the two scout arms. The
eventwise arm's process bound is about half as large, and it promotes 3,570 vs 1,631 Markov rows
and 1,018 vs 240 temporal rows. This directly localizes the uniform-grid contrast to certification
bound tightness rather than a change in contextual selection.

**Development result:** a new 60-seed, 108-cell CPU run applied the exact known uniform floor to all
four arms on disjoint seeds `21,510,000–21,510,059`. The corrected eventwise and minimum-bound scout
arms had identical expected utility and promotion decisions. The contextual scout exceeded pooled
rank by `+9.7148` (descriptive 95% seed-cluster interval `[+6.7629,+12.6908]`) and nested
context-volume by `+8.0688` (`[+5.4444,+10.7045]`) over the positive-signal cells. The 2,160
zero-signal scout rows had 11 promotions; these are diagnostics, not calibration. See the
[frozen development protocol](../scout_context_known_uniform_markov_development_protocol_v1.md)
and [artifacts](../../outputs/scout_context_known_uniform_markov_development_v1/).

A separate 1,000-seed-per-cell Markov null calibration passed on disjoint seeds
`21,600,000–21,600,999`: 95 false promotions over 36,000 rows, zero cap violations, and maximum
simultaneous cellwise upper limit `0.02051`. It applies only to its registered conditional-mean
synthetic null, Markov contexts, uniform query rule, and exact floor. See the
[calibration protocol](../scout_context_known_uniform_markov_null_protocol_v1.md) and
[artifacts](../../outputs/scout_context_known_uniform_markov_null_v1/).

**Confirmation result:** the frozen 600-seed run passed on disjoint seeds
`21,700,000–21,700,599`: the contextual scout exceeded pooled rank by `+8.5961` (familywise
one-sided lower limit `+7.6906`) and nested context-volume by `+7.4721` (lower limit `+6.6029`).
All 172,800 expected rows are present, with zero cap violations. Under the exact propensity floor,
eventwise and minimum-bound scout arms match on candidate selections, query counts, promotions, and
expected utility. See the [confirmation protocol](../scout_context_known_uniform_markov_confirmation_protocol_v1.md)
and [artifacts](../../outputs/scout_context_known_uniform_markov_confirmation_v1/).

This is a confirmed synthetic result against the repository's internal baselines, not yet an
improvement over SOTA. The source literature raises a direct comparator: [Waudby-Smith et al.'s
anytime-valid OPE confidence sequences](https://arxiv.org/abs/2210.10768) cover time-varying policy
values, adaptive logging, arbitrary stopping, and dependent contexts; [Karampatziakis et
al.](https://proceedings.mlr.press/v139/karampatziakis21a.html)
provide an earlier nonasymptotic off-policy CS and gated deployment application. The 2026 PPAI
method of [Sargent et al.](https://proceedings.mlr.press/v306/sargent26a.html) addresses adaptive
contextual-bandit inference and pretrained predictions but gives asymptotic normality rather than
an anytime certificate, so it is an efficiency reference, not the primary safety comparator.

The source DR-LIL and empirical-Bernstein DR comparators are now both implemented on matched
fresh development blocks. EB narrowed the mean final interval width from `0.1709` to `0.1286`, but
neither OPE gate crossed its positive-net-value threshold in 6,480 streams. On the EB block, the
fixed-mixture gate promoted `8.80%` of positive rows, with mean evaluator-known future net utility
`14.28`; both OPE gates deployed zero times. This closes the contextual scout as a demonstrated
improvement over these published anytime OPE methods under the tested budget/horizon design. It
does not establish that fixed mixture improves on SOTA. See the [frozen EB protocol and findings](../scout_context_ope_empirical_bernstein_gate_2026-11-04.md).

**Next research step:** leave this synthetic comparator branch closed and identify a different
structural gap or obtain an aligned real stream with release times, labeling costs, and deployment
outcomes. Any new lead still needs strongest source-matched baselines, independent null calibration,
confirmation, and a credible deployment transport argument before novelty/SOTA language.

An independent primary-source review also screened the suggested paired-e-process value-of-
information acquisition idea. Do not start another acquisition sweep from that heuristic: Cao's
2026 monitor already has growth-optimal e-factors and predictable covariate-dependent audit
propensities; cost-constrained quickest-change detection already allocates observations by
information and cost; delayed-response policies already use decision-value formulations; and
delayed-outcome anytime inference is established. The residual gap is only the joint contract of
paired model differences, promotion plus rollback, delayed releases, a pathwise hard cap, and a
nonasymptotic validity guarantee. This is a theorem question, not yet a method or novelty claim.
Before another experiment, specify the null, target estimand, pending-label filtration, rollback
reset rule, and a nontrivial performance bound that is not a restatement of known active-testing or
optimal-control policies. See [Cao et al.](https://arxiv.org/html/2611.00576), [Lubenia and
Banerjee](https://arxiv.org/abs/2509.14186), and [Lindon and Kallus](https://proceedings.mlr.press/v306/lindon26a.html).

The 2026-11-04 primary-source search additionally reconfirmed that hard query budgets, active
sampling for valid inference, and delayed-feedback scheduling are established neighboring areas:
[Active Statistical Inference](https://proceedings.mlr.press/v235/zrnic24a.html),
[Confidence-Budget Matching](https://proceedings.mlr.press/v139/efroni21a.html), and
[Bayesian Optimization under Stochastic Delayed Feedback](https://proceedings.mlr.press/v162/verma22a.html).
These sources do not settle the project's exact combined contract, but they raise the bar: novelty
would need a verified difference in anytime promotion safety, serial dependence, hard cap, and
arrival deadline together—not just a new budget heuristic.

## Continuation audit — exact-gap SUI transfer, 2026-11-04

The fixed-calendar exact-gap Markov SUI transfer was implemented as a separate Atlas comparator
with a conservative rectangular likelihood bound and conditioned starts. The first registered
screen (20 paired seeds) had zero false promotions across eight null cells but lost to Markov LR
on equal-cell cost (`+0.0102`, paired 95% CI `[+0.0041,+0.0162]`) and had a large mandatory
adverse-cell regression (`+0.2406` vs episode_front). A separately registered sparse-eight-start
screen on disjoint seeds narrowed, but did not reverse, the difference (`+0.0059`, CI
`[+0.0004,+0.0114]` vs Markov LR); its mandatory adverse regression was `+0.2459`. Both screens
fail their frozen advance criteria. Their small null samples do not establish calibration.

**Decision:** close this exact-gap SUI transfer before adding acquisition or tuning the mesh on
either seed block. The fixed uniform-calendar gaps offer no measured advantage over the existing
Markov gate, while the broader gap envelope was already cheaper on the corresponding screen.
Maintain the protocol/results as negative evidence and keep the wide objective open. The method
novelty audit still shows no surviving algorithmic lead; the next useful action remains source-to-
claim completion and an independent result audit, unless a new structural gap or aligned real
stream is found.

Artifacts: [dense-start protocol](../failure_atlas_gap_markov_sui_development_protocol_v1.md),
[dense-start results](../failure_atlas_gap_markov_sui_development_results_v1.md),
[sparse-start protocol](../failure_atlas_gap_markov_sui_sparse_development_protocol_v1.md), and
[sparse-start results](../failure_atlas_gap_markov_sui_sparse_development_results_v1.md).

## Continuation audit — conditional-null and P6 review

A lower-cost independent code review confirms that P3b's written one-shot argument is conditional,
not marginal: it assumes fixed delay, label-independent query randomization, predictable
propensities/bets, and `E[D_t | H_{t+d-1}^{(-t)}] <= 0`, conditioning on all learner-visible side
information through release except the current label. The review also notes that repeated
promote/rollback resets do not inherit one global alpha bound without spending. This does not
change the documented `20.8%` persistent-regime marginal-null failure.

The review corrected a comparator conflation. Current B3 P6 code makes one fixed-sample exact
binomial test at up to 50 released disagreement labels, then never tests again. The 5.3876% exact
counterexample applies to a different archived repeated `n=25` mean-threshold rule. Current query
decisions and the 50-label cap do not inspect label signs. However, budget exhaustion makes the
terminal count depend on episode query/disagreement availability, and the written P3b fixed-delay
null does not establish validity conditional on that complete selection path. The B3 protocol only
states exchangeability; deterministic real streams do not instantiate a stochastic null. See the
[focused P6 scope audit](b3_p6_validity_scope_2026-11-04.md). Keep B3 outcomes descriptive until a
selection/stopping proof under a declared null is supplied and the original runner-to-row provenance
is resolved.

The corresponding claim-ledger row and evidence-package action were corrected. This leaves a
valid-comparator proof and provenance audit as useful evidence work, but it does not create a new
algorithmic lead or reverse the method-screen results.

## Continuation audit — 2026-11-04

A fresh fetch leaves `HEAD` and `origin/main` at `de9aaaa3fa46a16944f5078234b3588a73e80fef`.
The B3 runner recovery check was widened across all 21 local ICML Git repositories and found no
tracked source matching the recorded run SHA, including after checking line-ending variants. This
closes the local recovery avenue. The full research goal remains open. Reopen algorithm development
only against a new, source-audited structural gap or a real stream with observed outcome-release
times and an aligned deployment contract; otherwise continue the P2 result review and report its
scope as empirical benchmark evidence rather than a new algorithm.

### OPE comparator correction — 2026-11-04

A source audit rejected the initial `Q_t R_t/q_t`-as-reward mapping: it can exceed one and violates the bounded raw-reward interface in `anytime_policy_identification.py`. A valid source-matched encoding is now specified in `context_scout_ope_comparator_audit_2026-11-04.md`: two actions (skip/query), target policy always queries, bounded query reward equal to normalized net decision gain including only the applicable switching charge, source DR truncation with fixed `k`, and the source LIL CS against threshold 1/2. This is supported by Waudby-Smith et al., Section 3, Theorem 2 and Proposition 3, for predictable logging and time-varying average conditional values. Implementation, fresh-seed comparison, and any future-value transport assumption remain open; the earlier error is documented rather than silently reused.


### OPE LIL comparator implementation and development — 2026-11-04

The bounded two-action query/skip mapping was implemented alongside the exact-floor eventwise scout and compared on two fresh, disjoint 60-seed × 108-cell blocks. The first used constant reward prediction; the second used a context-specific reward predictor trained from the fully labeled validation slice before certification. Both used source DR truncation `k=1`, alpha `.05`, the source LIL boundary, identical query uniforms and hard-cap prefixes, and the same scout-selected context mapping as the fixed-mixture gate. Both runs completed with 25,920 rows and zero cap violations. Across 6,480 eventwise streams per run, the OPE LIL lower bound never crossed `.5`; mean final lower bounds were `.417–.421`, widths `.165–.167`. The matched fixed-mixture gate promoted about 7.6–8.0% of positive rows, with mean expected future net utility about 12.7–12.9; zero-signal promotions were 0/2,160 per run, which is only diagnostic. Paired seed-cluster intervals favored fixed-mixture because the OPE gate never deployed. The validation-trained predictor did not materially tighten the CS.

This negative result closes the proposed contextual-scout-over-OPE-LIL lead on this design. It does not show fixed-mixture is better than SOTA, and no OPE null calibration or future-value transport guarantee was established. The source-matched implementation, protocols, raw rows, and analysis are retained at `docs/sota_sprint/context_scout_ope_comparator_audit_2026-11-04.md`, `docs/scout_context_ope_markov_development_protocol_v1.md`, `docs/scout_context_ope_markov_development_protocol_v2.md`, `outputs/scout_context_ope_markov_development_v1/`, `outputs/scout_context_ope_markov_development_v2/`, and `outputs/scout_context_ope_markov_comparison_audit/`. Do not tune on these blocks. Only test a different published boundary if its assumptions map directly and a new protocol/seed block is frozen first.

### Prior-art update: anytime-valid optimal policy identification — 2026-11-04

The June 2026 Molitor preprint `Anytime-valid Optimal Policy Identification` (https://arxiv.org/abs/2606.17515) is a direct finite-class policy-selection comparator already reproduced locally. It builds on the same Waudby-Smith confidence sequences, but its theorem assumes each policy's conditional value is time-invariant; persistent Markov context profiles violate that premise in general. Its fixed-value result should therefore not be blindly applied to this experiment. At rho=0, a matched OPI run on a finite class is viable. For Markov context drift, a prefix-average optimal-policy set might follow from simultaneous time-varying CSs, but that target and its deployment transport need separate formulation. The SOTA audit now treats generic anytime finite-class policy identification as prior art, not a novelty claim.

### Finite-class OPI comparator update — 2026-11-04

The first OPI adapter (protocol v1, seeds `22,000,000–22,000,059`) is withdrawn and excluded: it did not use a common logger/reward process across target policies. The corrected v2 finite-class bandit adapter is documented in `scout_opi_iid_development_protocol_v2.md` and screened on seeds `22,100,000–22,100,059`, with 6,480 matched rows and no hard-cap violations. On its 1,440 positive-signal scout rows, OPI uniquely identified no policy; fixed mixture promoted 7.08%, with mean evaluator-known gain 10.17 versus OPI 0. Its lower-bound CS is consequently too conservative to demonstrate competitive policy selection at these budgets. The 720 zero-signal rows are descriptive diagnostics only, not calibration. This closes this particular finite-class OPI implementation/design as a promising performance lead; it does not establish scout superiority or a SOTA comparison. See `outputs/scout_opi_iid_comparison_audit/report.md` and the raw v2 manifest/rows.

## Delayed-release extension gate (2026-11-04)

A new operational-filtration audit records an out-of-order two-label counterexample. It confirms the limitation already stated in the P3b theory note: issue-time conditional validity alone does not justify release-order wealth when labels can arrive out of order. The current fixed common-delay, order-preserving result is not refuted. Do not treat arbitrary release order as a surviving novelty lead; first establish a release-filtration null that preserves the paired-gain estimand, then show a quantitative advantage over matched delayed-inference methods. See [the audit](out_of_order_release_filtration_audit_2026-11-04.md).

### Next acquisition hypothesis: restart-mixture warning gate — 2026-11-04

The latest P7s/Cao development comparison suggests that P7s's main reversal deficit is low acquisition while the recent signed mean still reflects the stable period. A model-specific unknown-onset likelihood mixture gives an anytime false-wake bound under the IID synthetic stable regime, but a screening calculation shows the current `.05` audit floor likely supplies too few post-change labels. This is a development hypothesis only: it uses a stronger `.30` sign-probability null than the paired rollback certificate, and restarting e-processes/controlled sensing are established methods. See [the feasibility and prior-art gate](../promising_directions/B3_PLUS_RESTART_MIXTURE_AUDIT_GATE_2026-11-04.md). Do not claim novelty or start confirmation; first freeze the model-specific controller and compare it on disjoint development seeds against both Cao adapters.

### Restart-mixture acquisition pilot closed — 2026-11-04

The disjoint 200-seed-per-scenario P7s-RM development pilot reduced P7s's reversal cost by `9.096` but still lost to Cao-L and Cao-Hybrid by `+2.578` and `+2.736` mean paired cost, with 33–36 event longer rollback RMST. It also raised stable-state cost over P7s. The registered gate failed; do not tune or confirm this candidate. The results and limited model-specific false-wake interpretation are in [the findings](../promising_directions/B3_PLUS_RESTART_MIXTURE_DEVELOPMENT_FINDINGS_2026-11-04.md), with the frozen protocol [here](../promising_directions/B3_PLUS_RESTART_MIXTURE_DEVELOPMENT_PROTOCOL_2026-11-04.md). No current method lead survives this comparator.

## Continuation frontier — current worktree review

The newer B3+ comparator and attribution records do not reopen the single-pair method claim:
P7s and its sentinel still lose the reversal-cost gate to the Cao adapters, while the real-stream
attribution only covers three selected streams and does not establish performance against a full
source-matched deployment suite. The exact-gap Markov-SUI and contextual OPE/OPI directions also
remain closed under their recorded development gates. Preserve their raw records and negative
decisions; do not resweep those blocks.

The previous continuation scan incorrectly nominated sequential replacement from a **fixed library**
of classifiers. The local Lane B Phase E already evaluated that structure and closed it: shared-label
disagreement querying is covered by IWAL / Model Picker, while standard multiplicity control handles
the familywise error. Do not reopen it. The remaining recorded theory candidate is C1-E: whether a
belief-dependent HMM query policy yields a nontrivial label-budget/detection-rate advantage under
fixed delay, a hard query cap, and the model-conditional promotion-risk gate. This must be compared
with burst calendars and an optimal belief-state sensing policy. The candidate need not beat the
optimal DP; it needs a useful certified gap to that oracle and a source-level rate result beyond
standard belief-state sensing. Beating calendars alone would not establish a contribution. See the [corrected research frontier](research_opportunity_scan_multi_challenger_2026-11-04.md),
[C1 theory targets](../switching_theory_targets_c1_c2_v1.md), and [C1 proof record](../switching_c1_upper_bound_proofs_v1.md).

### C1-E exact-screen disposition and project pivot — 2026-11-08

The exact finite-cell calculation is now recorded in [the frozen protocol](switching_c1e_information_dp_protocol_v1.md)
and [results](switching_c1e_information_dp_results_v1.md). Adaptive optimal sensing gains 3.92%
transcript KL over the best fixed calendar in the registered HMM cell, but the best calendar beats
the contiguous burst and the adaptive DP itself is routine belief-state control. The source check
found established HMM sensor-scheduling DP, active sequential hypothesis testing, and active
quickest detection under sampling control. The result does not isolate a non-compositional hard-cap,
delay, and promotion-risk rate theorem. **Close C1-E as an algorithm lead**; retain the calculation
as negative/diagnostic evidence and do not expand it into a sweep.

The current empirical leads are also below the SOTA bar: P7s saves labels on three audited streams
but loses the matched reversal cost/delay comparison, while the contextual scout did not beat the
source-matched OPE/OPI controls. New prior art further narrows generic drift-monitoring claims:
[Cao (2026)](https://arxiv.org/abs/2611.00576) proves a label-history delay lower bound for
budgeted risk monitoring and studies free-covariate triggers; [Drift2Act (ICLR CAO Workshop
2026)](https://openreview.net/pdf?id=tcUgT2jE5W) combines delayed active risk certificates with
cost-aware drift interventions. These do not erase the paired replacement contract difference,
but make broad claims about budgeted monitoring or cost-aware intervention untenable.

Next, require an aligned stream with event and release timestamps, paired losses of two frozen
models, and a stated hard label and switching budget. Freeze the estimand and strongest matched
baseline before new algorithm work. If no such stream is available in the current evidence package,
prioritize a source-level theorem search rather than another synthetic variant sweep. The updated
frontier and SOTA boundaries are in [the opportunity scan](research_opportunity_scan_multi_challenger_2026-11-04.md).

### New direct model-replacement prior art and data feasibility — 2026-11-08

The source review added Digalakis Jr. et al., [*The Challenger* (arXiv:2512.18390v2)](https://arxiv.org/html/2512.18390).
It already formalizes economic model switching with learning-curve dynamics and gives oracle-regret
results, so broad claims to cost-aware sequential model replacement are closed. Its growing-challenger
retraining setting differs from our fixed-pair, selectively labeled, delayed-monitoring contract; that
difference needs a source-matched method result before it can support a contribution.

One plausible stream for a feasibility audit is the Criteo Attribution dataset. The dataset publisher
documents 16.5M timestamp-sorted impressions, conversion outcomes over a 30-day horizon, and a
`conversion_timestamp` for observed conversions; it is released under CC BY-NC-SA 4.0. See the
[dataset card](https://huggingface.co/datasets/criteo/criteo-attribution-dataset). Positive event
times plus 30-day negative-label maturation could define a **derived** delayed-label replay, but this
is not an observed label-ingestion log. The cost and cost-per-order fields are transformed, not real
prices, and repeated user/conversion records create dependence. Treat it only as a possible
chronological benchmark, with cluster-aware uncertainty and descriptive limits; do not call it an
actual annotation-delay deployment trace or use it to claim calibrated promotion risk. Before method
work, audit timeline integrity, target semantics, maturity censoring, user-level overlap, and whether
the available variables support two frozen models with a defensible prospective split.

The publisher file has now been downloaded and fully streamed through a structural audit: all
16,468,027 impression timestamps are ordered; all positive conversion times are within the 30-day
window; but 370,386 rows repeat an already-seen positive conversion ID. The last fact makes
impression-row independence untenable without a conversion/user-level model. The detailed audit,
dataset digest, and next pre-run gates are in [the feasibility note](criteo_delayed_outcome_feasibility_2026-11-08.md).
