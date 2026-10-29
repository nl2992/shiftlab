# Budget-aware, anytime-valid switching: research goals

**Decision date:** 2026-10-28. **Status:** active research objective; no new algorithm,
novelty, theorem, or advantage has been validated. ICML is the methodological standard sought,
not a publication prediction. Starting revision: `7ea6923fbc784aab81e4821a03268fa683b04238`.

## Direction and precedence

The user has selected a methodological research programme: one new acquisition-and-switching
mechanism, a defensible theoretical contribution, and empirical evidence explaining its value.
ShiftGuard is the preserved experimental platform. Stop routine retrospective manuscript
polishing. Q1 monitoring, Q2 certification, and Q3 resource allocation remain motivation, not
three contributions to be packaged as a new system.

This decision supersedes the *future-work direction* in `papers/shiftguard_unified/research_goal.md`,
`publication_scope_decision_v1.md`, the 2026-10-26 decision gate, and
`docs/research_refinement_v1/FINAL_RESEARCH_PROPOSAL.md`. Their negative evidence and scoped
no-go conclusions remain intact. Reopening a narrower problem does not reverse a failed test
or validate an old mechanism. Historical protocols, results, manuscript drafts and hashes stay
unchanged. The charter's scientific and data safeguards continue to apply.

## Evidence already available

- `papers/shiftguard_unified/integrated_efficacy_confirmation_results_v1.md`: late harm is
  missed, selection/certification consumes useful time, reversal incurs loss, and the controller
  ablation makes the same decisions. These motivate questions; they do not imply novelty.
- `docs/algorithm_search_exit_ledger.md`: stratification equals established composition;
  evidence-driven intensity and the anchor failed their screens. Disagreement gating is credited
  to prior work. Temporal budget allocation was identified as Paper 3, not a new monitor.
- `docs/research_refinement_v1/PRIOR_ART_AND_NOVELTY_MATRIX.md` and
  `NOVELTY_DOSSIER_B2.md`: reuse existing source reads and equivalence objections. Do not redo
  a broad literature inventory when a precise missing theorem comparison will suffice.
- `src/shiftlab/dive/integrated_pipeline.py`, `hard_budget.py`, `delayed_feedback.py`, and
  `docs/streaming_decision_contract.md`: starting implementation and timing contracts to inspect
  before a new runnable slice. No research-code changes are authorized by this planning record alone
  beyond the user's continuing research scope; register the new experiment before running it.
- Existing EIA, Upworthy, CRSP and OBD audits constrain real-data claims. CRSP is a retrospective
  stress test; a finance motivation does not establish publication clocks or trading utility.

## Goal sequence and acceptance gates

| Goal | Concrete deliverable | Acceptance / exit rule | Initial state |
|---|---|---|---|
| G0 Preserve platform | Platform manifest with code revision, relevant protocol/output hashes, verifier commands, reusable components and known failures | Preserve results and oracle boundary; separate new development artifacts and seeds from historical confirmation | Complete for selected ShiftGuard integrated confirmation anchors; not a full artifact archive |
| G1 Fix one information structure | Mathematical problem and source-level novelty delta | Explicit feedback, risk event, comparator and nontrivial feasible assumptions; published methods do not already provide the claimed result | Next |
| G2 Derive one mechanism | Acquisition/action pseudocode, derivation, proof or counterexample, and equivalence audit | One substantive acquisition-switching coupling and a proved new result or separation; a standard combination or heuristic alone fails | Blocked on G1 |
| G3 Build falsifiable prototype | Runnable simulator slice, matched baselines, registered development protocol and results | Hard budget and chronology verified; useful gain over strongest equally equipped baseline under a declared test family | Blocked on G2 |
| G4 Independently confirm | Frozen code/config/seeds, powered synthetic comparison and real-data timing audit/evaluation | Primary practical gain with uncertainty, safety calibration and ablations; eligible real task supports scoped relevance | Blocked on G3 |
| G5 Paper decision | Claim-to-proof/artifact map and continue/pivot/stop record | New algorithm + defensible theory + meaningful empirical evidence all pass before full manuscript effort | Blocked on G4 |

“Blocked on” denotes a dependency, not a claim that user input is required.

### G1: immediate continuation

Begin with two frozen policies and bounded paired decision losses identifiable from a queried
common outcome. Start with a known finite horizon, a hard label budget, query costs, positive
switching costs and explicit label delays; justify any minimum dwell time or piecewise-stationary
assumptions. Do not assume arbitrary nonstationarity permits both safety and low regret.

Write the event order: covariates and available feedback, predictable query/action choices,
budget reservation for pending queries, label release, evidence update, switch/reversal.
State whether delays are bounded, independent or informative and whether out-of-order outcomes
may update evidence. State what is observable before querying and whether query affects arrival.
Charge every query at a declared time and never exceed the hard budget, including pending work.

Define net utility as realized decision utility minus query and switching costs. Define regret
against a specific switching comparator with the same action set and declared switching penalty
and variation constraint. Distinguish evaluator clairvoyance from a feasible learner's information;
charge comparator costs explicitly. State the false-switch event precisely: e.g. promotion of a
candidate whose specified conditional benefit fails its economic hurdle. Specify the horizon over
which a one-time cost is amortized, repeated candidates/switches, alpha accounting, and the
difference between evidence of past benefit and a promise about future regimes. Rollback safety
and accumulated loss require separate definitions; anytime validity alone bounds neither.

Inspect primary methods, assumptions, theorem statements and relevant proofs for the user-named
Gafni et al. (PMLR v306/gafni26a), Digalakis et al. (arXiv:2512.18390), Drift2Act
(arXiv:2603.08578), Lindon–Kallus (PMLR v306/lindon26a), and Prabhu et al. (IEEE TIT 2022,
sequential controlled sensing with false-detection and sensing-switch costs). Verify identities and versions;
these are audit targets, not accepted bibliographic or theorem claims. Extend the existing audit
to active sequential testing, label-efficient switching/change-point regret and delayed-feedback
learning only as needed. Record exact source/theorem, information access, budget type, comparator,
delay assumptions, guarantee, and whether a reduction or combination already proves our target.
An inaccessible proof leaves the novelty gate unresolved.

**Deliver first:** `switching_problem_v1.md`, `switching_novelty_delta_v1.md`, and a dated
continue/pivot/stop entry. A negative audit is a valid outcome. Do not code a generic controller
while this gate is unresolved.

### G2: mechanism and theory

Investigate an acquisition rule driven by the expected reduction in *costed switching-decision
loss*, accounting for pending evidence and remaining useful regime duration, rather than evidence
growth alone. This is a search hypothesis, not a selected algorithm. Derive the rule in the G1
model before naming it. One mechanism should address one demonstrated failure first.

Seek a time-uniform false-switch guarantee, a finite-budget performance bound and an explicit
delay contribution. These are targets; do not promise all three are jointly feasible. State
constants, assumptions and vacuous regimes. Establish a nontrivial advantage or separation from
the strongest applicable established rule; an inherited e-process guarantee is supporting theory,
not the novel theorem. Use indistinguishable-instance counterexamples to check whether unobserved
late changes, exhausted budgets or long delays make the desired guarantee impossible. If so,
revise assumptions or the target before proceeding. Audit repeated selection and reversal proofs.

### G3–G4: empirical contract

Reuse controlled synthetic infrastructure first: stationary/benign controls, late onset, costly
selection/certification, post-switch reversal, recurrence, budget exhaustion, and delay stress.
Keep oracle changes and expected utilities evaluator-only. Compare no-switch, fixed/periodic
switching, strongest compatible published method and the best simpler pipeline under identical
candidate access, label/compute budgets, delay clocks and switching/query charges. Credit adaptations
and do not describe incompatible feedback tasks as faithful published-method reproductions.

Primary endpoint: cumulative net decision regret/cost against the G1 comparator. Report safety
violations, query spend and pending queries, switch count, losses before reversal and delays with
nondetections included. Ablate acquisition versus uniform/paced/gated querying, pending-feedback
accounting and switching logic separately. Use paired streams and dependence-appropriate intervals.
Before confirmation, freeze the practical improvement threshold, primary contrast, familywise
testing plan, seed allocation, sample size/power rationale and stop rule using development only.
No cherry-picked scenario win or lower label spend alone establishes methodological success.

Audit existing real datasets before acquisition: paired outcome identifiability, feature and label
availability, chronological untouched evaluation, cost interpretation and licensing. Use a real
task only if it supports the mechanism's contract; clearly label imposed timing/costs and narrow
claims. If no task qualifies, record the exact missing information and a data-plan dependency.
Do not substitute retrospective finance results for verified delayed observation timing.

## Continuation discipline

### Checkpoint 2026-10-28: feasibility work started

- Prior turn: progress (governing direction and active goal recorded).
- G0: selected platform sources, protocols and evidence anchors are existence/hash recorded in
  `switching_platform_manifest_v1.json`. This is not a full output release or a fresh verification
  of historical results. Historical artifacts and research code were not modified.
- G1: `switching_problem_v1.md` fixes an initial common-outcome two-policy contract, separates
  global-null false promotion from future economic certification, and proves an elementary
  delayed-loss obstruction. `switching_novelty_delta_v1.md` records verified source access,
  a direct ICML 2023 budget/switching comparator and unresolved full-text/proof reads.
- Decision: continue G1; no algorithm selected, no novelty established, no experiments run.
  Next: retrieve missing proofs and test standard budgeted-learning/delay reductions against
  the proposed future-value acquisition target. G2–G5 remain open.

### Checkpoint 2026-10-28: source access and elementary mechanism screen

- Downloaded and checksummed seven primary PDFs; selected theorem/proof passages inspected.
  `switching_source_audit_v2.md` records exact scope and corrections. The source manifest is
  `switching_source_manifest_v1.json`; third-party PDFs remain in ignored outputs.
- Cheng's hard-budget switching theorem is an immediate comparator; Lindon–Kallus's displayed
  intervals are asymptotic. Challenger's meta-regret theorem does not need a parametric power-law
  curve. MLDemon already supplies sample-age drift correction. These prevent overstated gaps.
- `switching_mechanism_screen_v1.md` derives a valid restricted batch certificate, its optimal
  statistical/age sample count and its economic-vacuity condition. The elementary composition
  is rejected as a standalone contribution. A separate counterexample demonstrates why global
  switching costs cannot be bounded by summing switches inside interleaved delayed learners.
- Decision: G1 remains open; continue with direct delayed-switching and constrained sequential
  design comparisons, then derive one coupled mechanism. No efficacy run or new method claim.

Complete one gate at a time. Each research checkpoint records assumptions, sources, artifacts,
verification commands, failed predictions and a continue/pivot/stop decision. Start CPU-sized;
do not rerun frozen confirmations or launch factorial sweeps to populate a paper. Keep previous
failed mechanisms as explicit exclusions unless a changed information structure yields a precise
new derivation. If novelty, theory or practical gain fails, revise the hypothesis explicitly;
benchmark polishing is not the fallback objective. This goal creates no recurring automation.

### Checkpoint 2026-10-28: direct delayed comparators and runnable reference

`switching_delayed_comparator_audit_v1.md` adds Yang et al.'s multi-batched delay reduction,
Quanrud–Khashabi's direct delayed updates and Chick–Forster–Pertile's economic delayed
experimentation model. These further exclude generic batching, pending-outcome awareness and
Bellman optimization as standalone contributions. Extended hashes are preserved in manifest v2.

Under `switching_reference_protocol_v1.md`, an established-ingredient reference now has a
request/availability-separated implementation and a derived fixed-comparator cost bound.
Correctness checks include exact short-stream expectation calculations and independent query/
deployment randomness. This is comparator engineering, not a new method nomination, safety
calibration or efficacy evidence. The original dynamic-regret, statistical-safety and real-data
requirements remain open. Next derive or reject a concrete jointly adaptive acquisition rule;
its proof must handle the dependence that action-conditioned sampling creates in switch coupling.

Validation: 27 targeted tests passed, including exact expected-cost checks; Ruff and formatting
checks passed for the new files and Git whitespace checks passed. The reference protocol now
records a coupling-preserving route for evidence-adaptive acquisition that keeps deployment
randomness private, and an exact counterexample for action-conditioned querying. This is a
derivation constraint and supporting identity, not the missing novel algorithm or theorem.

### Checkpoint 2026-10-28: hard-budget safety and transient regimes

`switching_budget_delay_lower_bound_v1.md` proves an explicit finite-horizon regret obstruction
jointly involving B, d, pulse duration and the global false-promotion constraint. The argument
covers adaptive randomized query policies and counts missed regimes. The registered exact
checker passed 67,578 cases. This adds a feasibility boundary, not the required novel theorem.

Primary-source inspection found the underlying null-trace coverage argument in Chandar–
Tchamkerten's Lemma 1 (arXiv:1501.05930v5, whose title differs from its older transient-detection
version). Multiphase scout/confirm acquisition is also established there. Geng–Bayraktar–Lai
already solve a finite-rights Bayesian detection problem. These are new explicit comparator
obligations, with hashes in manifest v3. Neither the supporting lower bound nor classical
scout/confirm is nominated as the contribution. G1 remains open; derive a specific economic
acquisition advantage against these methods before proceeding to efficacy runs.

### Checkpoint 2026-10-28: one-step economic acquisition rejected exactly

`switching_economic_acquisition_screen_v1.md` registered and executed an exact three-label,
two-round-delay counterexample. One-step VOI with pending-label integration bought no labels
and cost 10. The equally equipped likelihood-gated Bellman policy cost 539/64=8.421875;
its null promotion probability was 1/64<=1/10. Independent forward law-specific occupancy
calculations reproduced the backward value; no simulation seeds or real data were used.

Decision: reject one-step economic VOI. The screen also derives a fixed-look-ahead failure
family and a certificate-reachability pruning rule, both supporting facts without novelty claims.
Next derive an efficient acquisition rule that values certificate-reaching sequences, pending
evidence and later reversals, and test its delta against the audited Bellman/multiphase methods.
G1 is still not passed; this is an analytical mechanism rejection, not a new method nomination
or G3 efficacy run. The full novel-algorithm/theory/empirical objective remains active.

### Checkpoint 2026-10-28: threshold-reaching batch planning is standard rollout

`switching_certificate_burst_screen_v1.md` and its exact script evaluated the registered
16-cell stationary development grid. The rule improved over one-step VOI in all cells, matched
Bellman in 12, and lost in four. Independent law-specific forward occupancy calculations
reproduced all Bayes costs, query counts and null promotion probabilities. A local decision
discrepancy identifies the missing value of contingent acquisition with early cancellation.

Decision: no-go for this rule as the contribution; it is standard multistep rollout, now an
explicit matched reference. Stop enlarging the stationary toy grid. Next derive a substantive
allocation mechanism for nonstationary repeated switching that prices contingent certificate
attainment, pending evidence and future reversal opportunities. No method nomination, dynamic
regret theorem, eligible real-data evaluation or ICML-level contribution has yet passed its gate.

### Checkpoint 2026-10-28: nonstationary information state and risk boundary

`switching_nonstationary_contract_v1.md` now specifies a recurrent two-state working model,
learner-visible delayed feedback, hard request accounting, exact filtering and a separate
composite global-null betting guarantee. The new information-layer implementation never accepts
hidden regime states. Its research clock is explicitly distinct from the existing platform API;
no direct replay compatibility is assumed.

The combined targeted suite passed 50 checks, including hidden-path posterior enumeration,
adaptive-query short-null enumeration and a reversal diagnostic. The diagnostic confirms that
large historical evidence can coexist with a current forecast favoring the incumbent: global
false-promotion control does not certify current benefit or prompt rollback. These are supporting
standard ingredients with precise scope, not the required novel mechanism or theorem. Next derive
the economically relevant acquisition/action coupling on this nonstationary information structure
and audit its advantage beyond standard constrained planning. All final contribution gates remain open.

### Checkpoint 2026-10-28: acquisition and reversal evaluated jointly

`switching_nonstationary_reserve_screen_v1.md` registered and completed two recurrent-model
delay cells. One delayed observation held for after promotion improved over frontloading, but
the best fixed wait changed with delay and neither schedule reached the exact planner. At
d=2, the planner's final advantage was purely conditional query cancellation (0.278 fewer
requests), rather than improved decision loss or switching charges. The full decomposition
prevents attributing all gains to rollback.

Both cells used the same hard cap, costs, model information and global-null gate. Exact
null promotion probabilities were 1/16 for promoting policies. A separate explicit-hidden-state
forward weighting reproduced all six metrics for all ten combinations; hidden states never
entered policy decisions. Planner counts stayed below the registered 100,000-state limit.
These are scoped development results and a strong known-model reference, not the new algorithm,
theory, dynamic-oracle regret evidence or real-data validation. Next derive or reject an efficient
contingent allocation mechanism; fixed reserves and ordinary Bellman planning are not nominated.

### Checkpoint 2026-10-28: actual statistical risk frontier corrected

`switching_risk_frontier_audit_v1.md` and its exact checker establish a stronger comparator
obligation. A calibrated one-label randomized policy satisfies the same composite global-null
false-promotion bound while costing 9.562 versus 10 for a specific predictive-product gate
that cannot permit promotion with up to five labels. Its optional query uses at most one right
on every path; no expected-budget substitution occurs. It also has a valid e-process
representation, so this is a critique of a frozen engine, not of testing by betting.

The gate-constrained Bellman screens remain valid but do not define the entire alpha-safe
frontier. Their cold-start/finite-depth findings cannot be described as universal statistical
label requirements. Notices now qualify those files. The general budget/delay lower bounds
covering all adaptive policies remain intact. The contemplated shadow-price experiment was
held before execution because its gap could otherwise be a chosen-engine artifact.

Next mechanism target: jointly optimize acquisition and statistical decision design under
the actual error constraint, rather than freeze one sufficient e-statistic. Include calibrated
randomization or explicitly justify any restriction; do not exclude it to rescue a candidate.
Risk-constrained sequential/POMDP planning and randomized testing are established approaches,
so the new rule still needs a narrow audited technical delta and a new performance result.
G1 remains open. No methodological paper, novel algorithm, final theory or real-data evidence
is claimed complete.

### Checkpoint 2026-10-28: optimized test design added as a reference

`switching_economic_test_frontier_v1.md` and its exact solver completed the registered B=0,...,6
calculation. The reference jointly selects an upfront cohort lottery and a randomized terminal
test under the composite conditional null; each path respects the hard request cap. Its optimum
is scoped to this class, not all adaptive policies. At B=1 it reproduces cost 9.562; at B=4 it
mixes three- and four-query plans, demonstrating why fixing a test or cohort can weaken a baseline.

Six independent word-level optimizations and 33 conditional-null threshold recursions agreed
exactly; Ruff passed. No efficacy, new theorem or novel mechanism is claimed. Stop enlarging
this stationary reference. Next deliver a precise contingent-acquisition/test/action candidate
and an equivalence audit against constrained sequential design, with the same statistical null,
randomization permissions and delayed information for all comparators. Reject the candidate
before empirical expansion if ordinary constrained planning already supplies its claimed result.
G1 remains open; G2-G5 retain their original theory, confirmation and real-data requirements.

### Checkpoint 2026-10-28: contingent planner validity and another close comparator

`switching_causal_risk_planner_audit_v1.md` adds primary-source reads of Prudent-Banker
(2026) and Osogami's robust POMDP method (ICML 2015), with PDF hashes in source manifest v4.
Delay-aware safety thresholds and robust belief planning are established; neither is nominated
as our method. Their information/safety contracts differ from the current hard-query-cap,
paired-outcome, false-promotion contract and cannot be silently equated.

The registered exact checker distinguishes unsafe IID-only calibration from a conservative
arrival-time adversary that can see future private coins. It checks 16 binary rejection rules
against eight causal null strategies each and 80 future-coin cases; all passed. The examples
show risk 1/10 becoming 1/5 under a legitimate conditional null, and risk 1/10 being overstated
as 3/20 by the enlarged arrival-time null. These are supporting semantics checks, not novelty.

Decision: reject a generic risk-budget Bellman planner as the contribution. Keep event-time
causality and future-coin independence explicit in any contingent acquisition/test/action rule;
use enlarged-null planning only as a labeled conservative reference. Do not launch more toy
grids to rescue the planner. Next deliver an audited computational or decision-regret advantage
beyond established constrained design and delayed safe learning. G1 and all final gates remain open.

### Checkpoint 2026-10-28: a concrete acquisition/switching mechanism rejected

`switching_transport_acquisition_candidate_v1.md` derives query-stratified recoupling and a
movement-compatible channel rule, with an exact two-slot implementation. Conditional marginal
identities, an explicit switching-cost formula and a supporting delayed static-comparator bound
make the mechanism concrete. Maximal coupling itself is classical, not the proposed novelty.

The decisive continuation-state comparison rejects it before efficacy: independently sample
the same marginal query location and couple deployment maximally. This preserves the joint
future information/action state and expected decision losses, with no greater switching cost.
The apparent local score gain relies on rewarding discarded old-action distinctions and is
not economic evidence. The dominance statement is scoped to the candidate's oblivious paired-
loss, expectation-cost contract; it does not preserve unspecified path-dependent safety events.

Ten targeted tests passed, including exact enumeration of 625 query/target/prior configurations,
independent feasible-coupling bounds, vertex/grid comparisons, propensity identities, and the
dominance comparison. Ruff passed. No efficacy grid or new real-data evaluation was run.

Decision: no-go for movement-compatible channel selection as the contribution. Retain the
reference kernel and counterfactual proof. The proposed query-dependent deployment-marginal
follow-up is already represented in the causal full-policy reference's action space; it is not a
novelty direction by itself. Any replacement must survive equivalence auditing and prove a
substantive performance result with its risk contract. G1 and the full
methodological/theory/empirical objective remain open.

### Checkpoint 2026-10-28: causal full-policy reference made runnable

`switching_causal_game_reference_v1.md` registers a classical sequence-form reference permitting
joint randomized querying, deployment and rollback, with no fixed evidence gate or equal-target
query-stratum restriction. Learner information sets share unreleased outcomes; the statistical
opponent chooses outcomes at event time, before future private coins. A hard cap includes pending
requests. Exact recovered-policy best response verifies the composite global-null event, rather
than relying on IID calibration or solver success. It remains a finite known-model reference.

The one registered recurrent-model cell completed within limits. Cost was 184103/78125=2.3565184
versus continue cost 5/2, with worst causal-null risk 1/10 and no calibration adjustment. The
post-solve simplification in `switching_causal_game_results_v1.md` matches a standard randomized
two-label cohort rule, including all cost/count components. Thus no adaptive-acquisition or
rollback advantage is inferred. Independent enumeration of 2,048 hidden state/outcome worlds
reproduced all metrics. Eleven targeted tests and Ruff passed.

The 1996 source URL timed out; primary fallback Koller-Pfeffer (IJCAI 1995), Section 4, was
read for sequence form and flow constraints, with provenance in source manifest v5. Classical
game optimization is not nominated as new. Retain the reference and stop this cell. Next
derive a source-audited advantage for contingent acquisition/action coupling beyond optimized
cohort testing and constrained planning before registering further efficacy comparisons.
The original new-method, new-theory, synthetic-confirmation and eligible-real-data gates remain open.


### Checkpoint 2026-10-28: paid-observation switching comparator closes the broad premise

`switching_paid_observation_audit_v1.md` records a source-level read of Gong and Zhang, ICML
2026. Their paid-observation contextual bandit explicitly encodes switching cost by charging
for observing any action other than the previously selected action. They also analyze a hard
cumulative free-observation allowance, lower-bound phase transition, near-optimal regret controller,
and an oracle-efficient stochastic model. Thus the broad “budgeted acquisition plus switching
cost” premise is already directly covered; it cannot be our novelty claim. Primary PDF provenance
is preserved in `switching_source_manifest_v6.json`.

The paper's round outcomes are available immediately after the action/observation choice and it
does not state the target's time-uniform false-promotion constraint. These differences motivate a
possible narrower question, but they do not establish a gap. The exact query cap and budget semantics
also differ. Next compare the precise delayed-release, paired-loss, causal-risk contract against the
paid-observation reduction and the separately-valid-test baseline; require a theorem, counterexample,
or strict frontier separation before nominating an algorithm. No more toy expansion of the causal
game cell. G1's broad premise is closed as occupied; a narrower G1 delta, G2-G5, and the overall
method/theory/evidence goal remain open.


### Checkpoint 2026-10-28: sampling control with observation-switching cost is established

`switching_observation_control_prior_v1.md` records a primary-text read of Lau and Tay (IEEE
TSP 2021). Their quickest-change method jointly designs sampling and a switching-costed sensing
policy under false-alarm and long-run average observation-switching constraints, with an asymptotic
ARL–WADD guarantee. The paper discusses processing latency as motivation, though its formal model
does not queue delayed labels. It makes clear that joint sensing/switching/change detection is a
broad established problem family. Its one-time irreversible stop, ARL criterion and average sensing
cost differ from repeated reversible model deployment with a pathwise query cap and finite-sample
causal false-promotion control; these distinctions still do not establish novelty. Provenance is in
`switching_source_manifest_v7.json`.

The research hypothesis now has two strong neighboring results: ICML 2026 paid-observation
contextual learning explicitly reduces switching costs to observation costs and treats a hard
free-observation budget; Lau–Tay jointly controls sensing switches and quickest detection under
ARL/AOSC. Before any new algorithm, G1 must show a theorem-level separation from both, as well as
from standard delayed online learning and constrained sequential design. The remaining candidate
is repeated reversible deployment under fixed delayed paired labels, pathwise total query cap,
anytime global false-promotion risk and explicit dynamic economic comparator. This is a candidate
contract, not a novelty claim. If a routine composition yields the desired guarantee, revise/stop
the method premise instead of building a broad system around it.

### Checkpoint 2026-10-28: safety guarantee composes; economic guarantee remains open

`switching_safe_test_baseline_v1.md` formalizes a direct baseline: use any predictable query
schedule obeying the pathwise cap, update a nonnegative constant-bet test only on fixed-delay,
order-preserving releases, gate every promotion on an episode-specific threshold, and spend a
summable alpha sequence across re-promotion episodes. Under a full event-time conditional null
also conditioning on current covariates and query choice, Ville plus a union bound gives the
global anytime false-promotion guarantee. Each episode must test only queries initiated after
that episode begins; carrying pending pre-episode labels into a reset test would be unjustified.

This resolves the safety part of the composition question: delay and the hard query cap do not
by themselves require a new test construction under this strong null and fixed release order.
It does not deliver a dynamic-comparator regret or net-utility guarantee, optimize acquisition,
or establish useful detection delay. Thus a method that merely attaches an e-process to a
budgeted delayed online learner is not a sufficient contribution. G1 now requires a quantitative
economic advantage that survives the alpha gate and delayed-feedback lower bound, against this
safe composition and the strongest budgeted switching comparator. G2-G5 remain open.


### Checkpoint 2026-10-28: dynamic indicator switching regret is already established

`switching_dynamic_indicator_regret_audit_v1.md` records a primary-text review of arXiv
2609.30556 (2026). Its multiscale lazy-FTRL method gives strongly adaptive regret and expected
dynamic-regret-plus-indicator-switching guarantees against piecewise-constant comparators, with
model deployment named as an application. Affine losses over two policies fall inside its convex
full-information model. Theorem-level details and PDF provenance are recorded; source manifest v8
preserves the hash. Thus neither a dynamic comparator nor an indicator deployment cost is the
methodological gap. The exact paper requires full loss feedback each round and supplies neither a
pathwise query cap/delayed paired-label queue nor the global false-promotion constraint. Those
differences define an open comparison obligation, not a novelty result.

The remaining candidate contribution is a new attainable utility/regret frontier from the joint
interaction of selective delayed paired feedback, hard query budget, reversible switching and
finite-sample global risk. G1 now requires a minimax lower bound and a matched upper bound (or a
substantive separation) under one explicit regime, checked against paid-observation and delayed
full-information reductions. If these reductions already match the frontier, revise the hypothesis.
No new efficacy experiment is authorized by this checkpoint.


### Checkpoint 2026-10-28: delayed switching-cost optimization is also established

`switching_delayed_nonlinear_cost_prior_v1.md` records a focused primary-source read of Pan
et al. (arXiv:2111.00095). Their iROBD result covers delayed feedback and nonlinear multi-step
switching costs under strongly convex/smooth hitting costs, with a competitive-ratio theorem and
matching delay-dependence lower bounds. It does not cover paid selective queries, pathwise query
budget, paired policy labels or anytime risk. This closes the broad “delay + switching cost”
framing; source provenance is recorded in manifest v9.

Across the audited sources, the candidate must now be justified specifically by the joint
information/evidence constraint: paid paired outcomes, a pathwise total budget, release delay, and
finite-sample false-promotion risk interacting with repeated economic switching. A novel theorem
about only delay, only switching, or only observation cost is insufficient. The next proof attempt
should either derive a new risk-regret frontier with an explicit rate and matching lower bound, or
show by reduction that existing methods attain it and revise the hypothesis.


### Checkpoint 2026-10-28: historical test wealth is not current-regime value

`switching_current_regime_evidence_v1.md` formalizes the annotated limitation. Two environments
can share the complete observed history at a decision time, including arbitrarily strong evidence
from a formerly beneficial regime, then have opposite deterministic gains afterward. Their
future switch values have opposite signs whenever `H Delta > k`; any history-based sign decision
has error at least 1/2 in one environment. This elementary nonidentifiability result is not a
novel theorem, but it prevents interpreting the global-null e-process guarantee as a current or
future economic certificate.

The research contract must report separately (i) time-uniform promotion validity under a declared
null, (ii) current-regime evidence from post-change data or a forecast model, and (iii) future
economic value under explicit persistence/dwell/drift assumptions. Reversible deployment under
arbitrary changes instead needs a dynamic-regret target that includes the unavoidable delay loss.
Algorithm selection remains on hold; this clarification does not justify another efficacy sweep.


### Checkpoint 2026-10-28: ShiftGuard preservation gate verified

Completed G0 for the selected integrated ShiftGuard platform anchors. The manifest now records
the source revision, 18 selected files and hashes, reusable modules, the registered failure
evidence, preservation rules, known limits, and a read-only verifier. Running
`python scripts/verify_switching_platform_manifest.py` checked 24 unique files against their
recorded SHA256 values, including all saved source, raw-output and analysis-output hashes in the
independent confirmation verification record. It confirmed status `passed`, 7,200 metric rows,
72 profile-method cells, 23.04 million learner and evaluator rows each, maximum label use 640,
and 22 primary contrasts. The historical confirmation itself was not rerun or modified.

The preserved failure evidence is late-window misses, selection/certification opportunity cost,
negative reversal utility before rollback, and identical decisions with/without the registered
controller. The run used synthetic immediate feedback, so it does not validate the new delayed
method or any real-data claim. G0 is complete only for these selected anchors; G1 remains open and
the full algorithm/theory/evidence objective remains active.


### Checkpoint 2026-10-28: Cheng's hard-budget switching theorem audited

`switching_cheng_audit_v1.md` records a primary-text read of Cheng, Zhou and Ji (ICML 2023),
including Section 4, Theorem 2, Algorithm 1, Proposition 2 and Appendix C. Their result is a
mandatory neighboring baseline: hard total budget on individual action-loss observations,
switching-costed actions, and soft-Theta(T sqrt(K/B)) minimax expected regret against the best
fixed action. Their batched full-information Shrinking Dartboard instantiation has an
O(T sqrt(K log K/B)) bound. For two policies a paired query maps to two action observations.

This closes the broad hard-budget-plus-switching premise. Their protocol has immediate feedback,
free observations, a fixed-action comparator and no time-uniform false-promotion event, so it does
not prove the ShiftLab target. Those differences are not themselves a novelty result. Include the
converted Cheng method as a matched-budget baseline; G1 still needs a risk-regret theorem or
separation against it and the separately-valid-test composition. No algorithm or efficacy sweep
is selected by this source audit.


### Checkpoint 2026-10-28: real-data eligibility boundary recorded

`switching_real_data_eligibility_v1.md` compares the available CRSP, Criteo Attribution,
CriteoPrivateAds, Open Bandit and WILDS tasks against paired outcomes, delayed availability,
switch utility and prior test exposure. No current source supports an untouched real confirmation
of the full claim. CRSP is retained as a possible exploratory paired predictive-loss replay under
an explicitly retrospective one-event delay; its 2020–2025 test period is exposed and its
close-time availability and economic costs are not verified. Criteo Attribution is too short for
informative within-stream querying under the assumed 30-day maturity (3.31% mature before stream
end) and its full sequence was scanned. CriteoPrivateAds and OBD lack the required observed paired
verified release timing and application-grounded action utility; WILDS is offline. Predictive
losses on a common observed click label could be paired for CriteoPrivateAds or OBD, but their
unknown/assumed maturity clocks and missing decision-cost contracts still limit them to development
diagnostics.

G4's dependency is now concrete: a new untouched chronological period with point-in-time features,
an auditable label-release contract, identifiable paired losses, and grounded costs for any
economic claim. A CRSP replay can support only scoped real-sequence development after G1–G3 pass;
it cannot count as confirmation. No real-data run was started. Continue G1 theory and keep the
full objective active.


### Checkpoint 2026-10-28: close controlled-sensing prior audited

`switching_sequential_safety_prior_v1.md` records inspection of the full 53-page primary source and selected model, theorem and proof passages from
Prabhu et al. (IEEE TIT 2022), including the stationary vector-exponential-family model, terminal
false-detection constraint, sensing-switch cost, Proposition 1 information lower bound,
Proposition 6 admissibility proof route, Proposition 7 achievability proof route and Theorem 4. Under their
continuous-selection and regularity assumptions, their modified-GLR policy attains the
information lower-bound slope for expected stopping-time-plus-sensing-switch cost as the target
error vanishes. This closes generic "active sampling + sequential error control + switching
cost" as a novelty premise.

Their cost is switching among sensing arms, their outcomes are observed immediately, and they
have no pathwise total query cap, pending-label queue, nonstationary regimes or repeated model
deployment. These dimensions define a narrower comparison requirement, not an open gap by
themselves. Add their method as a mandatory stationary terminal-decision reduction baseline; derive
a theorem-level risk-regret separation in the paired delayed hard-cap contract before selecting a
new algorithm. No efficacy experiment was run; G1 remains open.

### Checkpoint 2026-10-28: constrained partially observed control is established

`switching_constrained_control_prior_v1.md` records a relevant-section audit of the full 42-page
Helmeczi, Kavaklioglu and Cevik source, covering its finite-horizon constrained POMDP formulation,
and the abstract-level check of Wen, Guo and Xia's partially observed terminal probability-risk
criterion. Belief-state planning with costs/resource budgets and terminal probability-risk control are established
families. The former's formal budget is expected cumulative resource use, and the latter's
accessible description is a terminal model-based profit-risk objective; neither establishes the
exact ShiftLab guarantee by itself. These are contract differences, not an inferred gap.

G1 now requires a finite-sample separation from standard constrained planning where applicable,
the anytime-test plus delayed hard-budget switching composition, and the small exact causal-game
reference. The target remains a scalable, pathwise-budgeted delayed acquisition/reversible-switch
rule with worst-case anytime null safety and a nontrivial utility/regret advantage. No new efficacy
experiment is authorized by this checkpoint. The risk-probability source remains abstract-only;
its full assumptions and proof are an open source-audit item. G1-G5 and the full objective remain
active.


### Checkpoint 2026-10-28: noisy delay-budget-safety lower bound derived

`switching_noisy_information_lower_bound_v1.md` derives a finite-horizon lower bound for a
Bernoulli regime improvement. At relative round `j`, at most
`min(B,(j-d+1)_+)` informative labels can have arrived. Adaptive KL chain rule bounds the
learner-transcript divergence by this count times the per-label KL; binary data processing and
the alpha false-promotion constraint then bound promotion power by the upper binary-KL inverse.
Summing missed decision loss yields a joint finite-budget, delay and risk floor. The proof uses
standard information-theoretic inequalities, so no novelty is claimed; the noiseless pulse result
and Prabhu's controlled-sensing converse remain relevant prior comparisons.

This sharpens G2's feasibility gate and gives a quantitative check for future parameter cells,
but supplies neither a matching upper bound nor an acquisition rule. G1/G2 remain open; do not
start efficacy experiments until a candidate beats an equally equipped safe switching method
above this floor. G3-G5 and the full methodological goal remain active.

### Checkpoint 2026-10-28: partially observed probability-risk games audited

`switching_partial_observation_risk_game_prior_v1.md` records the full-source audit of Wen,
Xia and Yu (arXiv:2508.17791). Their finite-horizon partially observed zero-sum semi-Markov game
uses a probability that accumulated reward reaches a terminal goal, and establishes a belief/goal
state reduction, Shapley equation and equilibrium. Therefore a partially observed adversary,
terminal probability-risk optimization, or belief augmentation alone is already established.

The precise mismatch is now clearer: both players in that paper condition on the same observable
history and belief, while our causal-null environment can use pending outcomes hidden from the
learner; our objective is expected alternative utility subject to worst-case anytime null risk,
with a pathwise query cap, delay and repeated deployment costs. Those differences are obligations,
not proof of novelty. The full source must be a common-information reduction baseline, and the
small causal-game LP remains the stronger oracle for finite-instance policy evaluation. G1 remains
open; no efficacy experiment or method claim follows. The 2024 risk-probability decision paper is
still abstract-only. G2-G5 and the full methodological objective remain active.

### Checkpoint 2026-10-28: late-change evidence mixture is prior art

`switching_change_point_safe_baseline_v1.md` records a primary-source audit of Shin, Ramdas and
Rinaldo's e-detectors. Their tests start at consecutive candidate onsets and combine e-processes;
weighted starts with total mass at most one give a probability-of-any-false-alarm guarantee.
For the Bernoulli ShiftLab cell, the current predictable bet with `lambda=2*epsilon` is exactly
the null-to-alternative likelihood ratio. Under fixed ordered label delay, predictable querying
and a pathwise budget preserve the event-time Ville argument. This yields a safe all-onset mixture
baseline that addresses fixed-window detector misses, while leaving query allocation, economic
switching, rollback loss and dynamic regret unresolved.

Thus neither a likelihood-ratio bet, restarting across candidate change times, nor mixing their
anytime evidence is a novel contribution. Compare the new method to this baseline under identical
query schedules and costs. The e-detector paper's likelihood-ratio delay theorem supplies a
standard delay benchmark in its iid post-change regime. G1/G2 remain open; no efficacy experiment
or method claim follows. G3-G5 and the full objective remain active.


### Checkpoint 2026-10-28: current-regime evidence separated from null validity

The annotated likelihood-ratio concern is now explicit in switching_current_regime_evidence_v1.md: the gate may control false promotion under its declared fixed null, while historical evidence cannot certify value after an unobserved regime reversal. Candidate prototypes must expose separate objects for promotion validity and evidence/forecasts tied to the current regime. No method is selected by this clarification. The immediate next step remains the G1 theorem-level comparison: reduce Cheng's immediate-feedback hard observation-budget baseline into the paired-query contract where possible, with B=2 B_q, and determine whether standard delayed switching plus the all-onset anytime test already attains the lower-bound frontier. If so, pivot; otherwise formulate the exact residual theorem without treating contract mismatch as novelty. Hold G2-G4 experiments until this gate passes.

### Checkpoint 2026-10-28: uniform query plus all-onset mixture is too weak

`switching_uniform_safe_baseline_v1.md` derives a finite-horizon concentration bound for a
standard uniform all-onset likelihood-ratio mixture under a fixed, pathwise-budgeted schedule,
then evaluates a registered `T=120, nu=61, B=20, epsilon=.10, alpha=.05` cell. Even the
all-positive component log likelihood is below `log(T/alpha)` for delays 1, 5 and 20, so this
composition cannot promote and incurs the full gross post-change gap of 12. This is a useful
rejection of a naive safe-test-plus-uniform-acquisition baseline, not evidence against optimized
mixture weights, sequential design, calibrated randomization or constrained planning. G1 remains
open; no novel algorithm or efficacy experiment follows. The next comparison must optimize
acquisition and test design under the same null and hard-cap timing before claiming any advantage.

### Checkpoint 2026-10-28: cost-adaptive observation prior extended

The UAI 2026 primary-source audit in `switching_costly_observation_uai26_audit_v1.md` confirms
that adaptive observation-set selection, per-round observation economics, and gap-dependent
allocation have recent minimax/instance-dependent treatments. Any new acquisition contribution
must survive comparison to this family and cannot rely on a generic conversion from average cost
to a pathwise query cap. The required comparison must preserve fixed delays, paired-query units,
repeated deployment switches, and the false-promotion contract. This narrows G1 but does not pass
it; G2-G5 and the full goal remain active.

### Checkpoint 2026-10-28: contingent acquisition/reversal diagnostic rejected

The registered `T=6,B=3,d=1` sequence-form comparison and follow-up fixed-cohort/no-rollback LPs
are documented in `switching_reversal_diagnostic_v1.md`; compact policies exactly reproduce the
recovered metrics and conditional-null risk. Early stopping after negative labels saves
`0.00919` total cost over the optimal fixed cohort, entirely through fewer queries. One post-
promotion maintenance query and rollback adds only `0.000430625` over the adaptive no-rollback
policy. These are classical sequential-sampling and rollback effects under a known Markov model,
not a novelty result; the small cell has no real-data or confirmatory meaning. Stop this generic
mechanism search rather than scaling the oracle win into an empirical claim. G1/G2 remain open:
any continuation must state a sharper regime/information structure and prove a distinct guarantee
against active testing and constrained planning before experiments.

### Checkpoint 2026-10-28: active sequential testing prior added

The primary-source audit in `switching_active_sequential_two_sample_audit_v1.md` verifies that
Li et al. (TMLR 2024) already combine adaptive label selection, a finite label cap, online
classifier updates, and an anytime-valid Type-I guarantee (Theorem 5.1; proof in Appendix A.2).
This rules out treating an active query policy plus an anytime test as the method delta. The
remaining comparison is specific: establish whether that test composed with a standard economic
switching rule can be reduced to the common-outcome, delayed, pending-label contract, including
switch costs and reversal. The theorem differences do not establish novelty. G1 remains open;
keep algorithm selection and efficacy runs on hold until the reduction or a strict separation is
proved.

### Checkpoint 2026-10-28: known-onset sequential-test reference computed

The registered finite occupancy LP in `switching_known_onset_sequential_test_v1.md` optimizes
promotion stopping within a fixed consecutive cohort, with onset revealed, a pathwise cap of 20,
fixed delays, and the original conditional-null false-promotion level. The recovered numerical
rule is monotone over every `2^20` label word and passes independent null/alternative forward
recursions. Net excess is `10.211`, `10.383`, and `11.004` for delays 1, 5, and 20, versus lower
bounds `8.329`, `8.558`, and `9.416`. This narrows the earlier randomization baseline but does not
characterize adaptive querying, unknown-onset performance, or an attainable frontier; the
restricted-class gap cannot diagnose tightness of the all-policy lower bound. It also assumes
persistent benefit and gives no post-reversal guarantee. G1 stays open. Next compare the exact
unknown-onset information structure to established sequential testing with adaptive query timing,
or derive the fixed-cohort stopping frontier analytically, before proposing an algorithm.

### Checkpoint 2026-10-28: randomized alpha-spending baseline remains far from the bound

`switching_randomized_alpha_baseline_v1.md` now records the exact fixed-cell calculation for an
even query schedule with fresh randomized one-label promotion tests. Its conditional-null risk is
`0.04883` at level `0.05`; net excess ranges from `11.651` to `11.687` for delays 1, 5 and 20,
versus noisy-information net lower bounds from `8.329` to `9.416`. This valid comparator improves
on the inert uniform-mixture test, but its gap is not a frontier: the lower-bound relaxation and
the weak test may both explain it. Historical evidence also does not establish post-reversal
benefit. Keep G1 open, do not proceed to efficacy experiments, and next seek a sharper lower-bound
argument or source-level equivalence result for an optimized fixed-budget sequential test under
the same causal-null and delay contract.

### Checkpoint 2026-10-28: safe-test composition boundary derived

`switching_safe_composition_boundary_v1.md` derives the standard likelihood-ratio e-detector
composition under the paired Bernoulli conditional null. Predictable query skipping, a pathwise
cap, fixed ordered delay, and an unknown-onset mixture preserve false-promotion control; repeated
attempts require fresh post-start evidence and summable episode alpha. This closes safety
feasibility without a new method. The same construction supplies no economic acquisition rule or
dynamic-regret guarantee, and historical wealth does not certify post-reversal benefit. G1 now
requires a performance improvement beyond the safe-test plus costed-switching composition under
an explicit persistence/dwell or drift model, or a revision if standard controlled sequential
design already achieves it. G2-G4 remain held.

### Correction 2026-10-28: full-mixture noncrossing bound verified

The earlier uniform-mixture checkpoint cited only the onset-specific component's all-positive
log likelihood, which alone does not rule out a crossing by the full mixture because earlier
components include pre-change labels. `switching_uniform_safe_baseline_v1.md` and its evaluator
now compute the exact pathwise maximum of the complete mixture over all queried label sequences.
For delays 1, 5, and 20 it is `11.1996`, `10.8952`, and `9.5011`, each below the crossing
threshold 20. This closes the proof gap and verifies the same conclusion: the registered fixed
schedule cannot promote on any path and has gross regret exactly 12. It remains a weak baseline,
not a separation from optimized acquisition or calibrated tests; G1 stays open.

### Checkpoint 2026-10-28: safe detector plus threshold controller benchmark defined

`switching_threshold_controller_decomposition_v1.md` gives the exact net-cost identity for a
standard one-switch threshold-and-hold controller under a persistent Bernoulli alternative:
loss gap times expected calendar crossing delay, plus query charges, minus the comparator's
switch charge on paths that never cross. The e-process controls false promotion, but does not
bound crossing delay, query count, or noncross probability. This makes the baseline objective
explicit without claiming a performance theorem. The unresolved G1 delta is a proved improvement
to one of those terms over constrained sequential testing under identical risk, budget, delay, and
switching costs; arbitrary reversals additionally require fresh current-regime evidence and
rollback-delay accounting. G2-G4 remain held.

### Checkpoint 2026-10-28: joint unknown-onset KL reduction did not sharpen the floor

`switching_unknown_onset_mixture_lower_bound_v1.md` registered and evaluated a uniform-onset
mixture KL/data-processing lower bound in the fixed `T=120, B=20, epsilon=.10, alpha=.05`
cell. The result is weaker than averaging the existing per-onset bounds by `0.0666`, `0.1296`,
and `0.2978` gross regret for delays 1, 5, and 20. This checked non-result rules out that simple
convexification as the next theoretical advance; no prior or parameter tuning is warranted.
Continue G1 with the source-level active sequential-test reduction into the paired, delayed,
global-conditional-null contract. Require the same pathwise pending-query cap and switch-cost
accounting, then compare its attainable stopping/promotion frontier with the existing exact
fixed-cohort and lower-bound references. If the reduction closes the gap, revise the hypothesis;
otherwise state the residual theorem precisely. G2-G4 remain held, and the likelihood-ratio safety
claim remains separate from current-regime evidence after reversal.

### Audit closure: active two-sample test does not reduce to the ShiftLab null

The saved primary-source audit in `switching_active_sequential_two_sample_audit_v1.md` closes
the proposed direct reduction: with a constant feature, Li et al.'s feature-label independence
null holds for every Bernoulli label mean, including the ShiftLab positive-gain alternative.
Making time/onset part of the feature instead destroys their IID feature-label premise. Their
Theorem 5.1 therefore cannot be imported as a test of the conditional-mean null here. This is a
precise theorem-scope obstruction, not a claim that no adapted active-testing algorithm can work.
The next G1 comparison must start from the valid paired-outcome e-process already proved for our
conditional null and ask whether any adaptive acquisition policy has a provable advantage over
the exact constrained-planning and fixed-cohort references under identical risk, delay and cap.
All method/forecast contracts must keep promotion validity separate from evidence about the
current regime after reversal, as recorded in `switching_current_regime_evidence_v1.md`.

### Audit extension: controlled-sensing channel allocation collapses for paired outcomes

`switching_ucb_controlled_sensing_audit_v1.md` records the source-level scope of Huang et al.'s
2026 UCB-CuSum preprint. Its adaptive value comes from choosing among channels with different
post-change information rates. In the paired ShiftLab cell, one queried common outcome scores
both policies and its law is action-independent, so there is only one sensing channel and that
allocation gain vanishes. Their immediate-observation, mean-time-to-false-alarm theorem also does
not meet our delayed, pathwise-cap, global finite-horizon risk and costed-deployment contract.
This is prior-art narrowing, not a novelty claim.

This checkpoint initially narrowed G1 to one-stream sampling timing. The subsequent audits below
show that finite sampling-right timing and delayed one-shot economic adoption already have direct
prior-art coverage. Treat that earlier next-step statement as superseded. Do not carry forward
channel-allocation terminology that the paired observation model does not support.

### Prior-art boundary: single-stream finite sampling rights already have optimal timing rules

`switching_sampling_rights_qcd_audit_v1.md` records the model and theorem audit of Geng,
Bayraktar and Lai. Their Bayesian quickest-detection problem has one stream, a finite number of
sampling rights, posterior-dependent sampling intervals, and threshold stopping. This closes the
generic single-stream “adaptive query timing plus sequential stopping” premise. The one-shot
delayed economic adoption reduction below further narrows the remaining contract delta to
recurrent reversible decisions under robust finite-horizon conditional-null risk, with pathwise
request accounting. These are comparison obligations, not a novelty argument.

Do not proceed from this prior-art difference directly to a new controller. The delayed pipeline
itself is already present in the one-shot economic adoption prior below. The residual question is
whether recurrent reversible decisions under robust conditional-null risk admit a scalable rule
with a finite-sample performance advantage over the best scalable episode-wise sequential-design
composition, together with a computational or approximation guarantee relative to the exact
causal planner on small instances. The planner is an oracle bound, not a beatable comparator. The
G1 contract should continue to keep historical evidence for promotion validity separate from
current-regime forecasts and future value after reversal.

### Contract reduction: delayed one-shot economic adoption is also prior art

The cached Chick–Forster–Pertile primary source has a direct model-class reduction to the
stationary, one-switch ShiftLab special case: their paired normal net benefit is our paired
loss difference; their maximum sample size is the hard query cap; their fixed arrival lag is the
label delay; their sampling and adoption costs are query and switch costs; and their post-trial
population supplies the hold horizon. Their model tracks outcomes in the pipeline while recruiting
continues and waits for all pending outcomes before adoption. The exact mapping is now recorded in
`switching_delayed_comparator_audit_v1.md` and the prior-art matrix. This closes delayed one-shot
economic acquisition as a standalone contribution, subject to the model's Bayesian stationary
assumptions. A viable target must earn its difference from this prior through repeated reversible
decisions and the robust anytime risk contract; merely adding a delayed queue or e-process is
insufficient.

### Acceptance-criterion correction: the exact planner is an oracle, not a beatable baseline

The sequence-form causal planner optimizes over the full feasible policy class for its registered
finite model. Requiring a candidate to show a strict advantage over that exact planner is therefore
impossible under an identical objective and contract. Use the planner as an oracle upper bound on
utility (lower bound on cost), and compare candidate performance with the best scalable, non-oracle
methods. In small instances, require a source-audited computational or approximation guarantee
relative to the oracle, not empirical superiority to it. The recovered HiGHS policy is only a
numerical feasible solution until a certified bound/gap is reported, so its observed cost is not
itself the oracle value. G1/G2 should require a theoretical separation from scalable established
compositions, meaningful approximation to the robust oracle, and a finite-sample risk/performance
guarantee under recurrent reversals. G3-G4 stay held until those conditions are derived.

### Checkpoint 2026-10-28: fixed-delay capacity scheduling added to the baseline audit

`switching_delay_capacity_audit_v1.md` records a focused primary-source audit of Ryabchenko,
Attias and Roy (arXiv:2503.19856). Their fixed-delay batch-representative method has a pathwise
concurrent tracking capacity and a minimax regret characterization; this is a mandatory close
baseline for paired queries once capacity is matched. Its concurrent-capacity constraint is
distinct from ShiftLab's total query cap, and the work has neither switching economics nor a
false-promotion constraint. Setting `b=ceil(T/B)` maps its full-information guarantee to
`12 sqrt(T b log 2)+3 sqrt(Td log 2)` for two paired-loss actions; adding query and switching
charges costs at most `(c+k)B`. This is a fixed-comparator, oblivious-loss bound, not a safe dynamic
regret theorem. The audit does not establish novelty from those differences.

This also resolves the stale follow-up to the rejected transport-coupling candidate: query-
dependent deployment marginals are already permitted by the finite causal oracle, so they do not
define a contribution. The exact causal LP remains only a small-instance oracle; recovered
numerical policy values are not certified optima. Continue G1 only toward a scalable theorem-level
separation from risk-valid batch/switching compositions and sequential design. G2-G5 remain open;
no efficacy experiment was run. If the separation cannot be stated and proved, revise or stop the
method hypothesis rather than proceed to empirical expansion.

### Checkpoint 2026-10-28: Detection Augmented Learning closes the generic restart-combination claim

`switching_dal_prior_audit_v1.md` records a primary-source audit of Gerogiannis et al.,
arXiv:2610.25782v1. Their Theorem III.9 already gives piecewise-stationary dynamic regret for a
detector, forced-exploration schedule and restarted stationary learner, under horizon-logarithmic
detection and minimum change-separation assumptions. This directly closes a generic
detector-plus-exploration-plus-restart contribution. Their theorem uses immediate bandit or
structured feedback, no paid pathwise total-query budget or deployment-switch charge, and a
segmentwise sub-Gaussian false-alarm model rather than ShiftLab's robust conditional-null risk.
Those are residual comparison obligations, not a novelty claim. Compare a risk-valid DAL adaptation
where possible; do not revive the ShiftGuard architecture as the method. G1 remains open, and
G2-G5 stay held until the paired-label/delay/budget/economic interaction yields a theorem-level
separation. No efficacy experiment was run.

### Checkpoint 2026-10-28: DAL translation screened, direct regret transfer rejected

`switching_dal_translation_screen_v1.md` defines a contract-matched comparator: query the paired
loss difference on a deterministic calendar with spacing `L=ceil(T/B)`, use a directional change
monitor, and keep an anytime-valid e-process as a separate global-null promotion gate. This gives
pathwise query use at most `B` and converts a detector window of `m_D+ell_D` samples to calendar
time at most `(m_D+ell_D+1)L+d`. DAL's Theorem III.9 does not transfer: its immediate feedback,
forced-action observation histories, separated detector/learner analysis and ungated action
sequence differ. A complete risk-regret bound for this comparator is still missing. It is a
baseline derivation task, not a contribution; G1 remains open and no experiment was run.

### Checkpoint 2026-10-28: fixed-calendar unknown-onset detection bound derived

`switching_fixed_calendar_e_detector_bound_v1.md` gives a finite-sample detection-delay bound
for the contract-matched scheduled-query baseline under a persistent Bernoulli gain segment.
For onset weight `w_nu`, the fresh onset likelihood ratio crosses with probability at least
`1-delta` once `n K - R sqrt((n/2) log(1/delta)) >= log(1/(alpha w_nu))`; the calendar delay is
at most `n ceil(T/B)+d`. This quantifies the budget-spacing and unknown-onset penalties without
using historical evidence as current-regime evidence. It is not a recurrent-switch regret bound:
rollback, segment economics, and multiple false-promotion episodes remain unbounded here. G1 stays
open; this closes a baseline term, not a method gap. No experiments were run and G2-G4 remain held.

### Checkpoint 2026-10-28: registered weak-baseline headroom quantified

`switching_uniform_baseline_headroom_v1.md` combines the exact pathwise-inert uniform-mixture
baseline with the universal noisy-information lower bound in its registered `T=120, nu=61,
B=20, epsilon=.10, alpha=.05` cell. Gross decision-loss improvement over that baseline is at
most 3.5711, 3.3421, and 2.4836 units for delays 1, 5, and 20, even if the lower bound were
attainable. This is a ceiling, not an expected method gain; the query-cost lower bound needed to
make a net-cost claim is absent. The calculation confirms this cell is a poor demonstration
target and reinforces that failure against the inert mixture says little about acquisition novelty.
No experiment was run; G1 stays open and G2-G4 remain held.

### Checkpoint 2026-10-28: adaptive acquisition plus detection prior audited

`switching_observation_switching_qcd_audit_v1.md` records a primary-source audit of Lau and
Tay's 2021 quickest-change method. They jointly choose sampling and GLR-CuSum detection under
observation-switching costs, prove asymptotic optimality for the permanent single-change setting,
and give an observation-dependent two-stage design. This closes the broad acquisition-plus-
detection claim. The remaining differences are a hard total label cap, delayed releases, repeated
reversible deployment economics and robust finite-horizon conditional-null risk; those are
comparison obligations only. The source PDF provenance is in manifest v18. G1 remains open and
must now produce a specific finite-sample theorem or approximation separation in the recurrent
contract, or revise the hypothesis. No experiments were run; G2-G4 remain held.

### Checkpoint 2026-10-28: generic chance-constrained planning approximation audited

`switching_ccpomdp_approximation_audit_v1.md` records the primary-source scope of the IJCAI
2019 CC-POMDP FPTAS. It assumes one fixed stochastic model and a constant planning horizon; its
runtime is polynomial in the expanded sequence tree, not in a variable long horizon. The ShiftLab
oracle's risk is a worst case over causal conditional-null strategies. Endpoint reduction gives a
finite but exponentially large family of null kernels, hence an exponentially large family of
chance constraints. The cited FPTAS does not provide a guarantee for that robust family. This
closes generic finite-horizon planning/approximation as novelty but leaves open a genuine
robust-game approximation result. G1 remains open, and no algorithm or experiment was selected.

### Checkpoint 2026-10-28: exact risk compression condition identified

`switching_monotone_promotion_reduction_v1.md` proves that if each deterministic policy's
ever-promotion event is coordinatewise increasing in the full potential-outcome tape, then its
worst causal conditional-null risk equals its risk under IID `Ber(1/2)`. The result holds even
when query timing is adaptive and nonmonotone; the exact outcome-tape coupling is independent of
release delay. The existing nonmonotone contingent-query example still has IID risk `1/4` versus
causal risk `1/2`, confirming the condition cannot be dropped. `scripts/check_switching_monotone_promotion_reduction.py`
enumerates every Boolean event through horizon 3 and checks the equality for all monotone tables,
plus both examples. This may collapse the risk adversary for a restricted acquisition class, but
does not show that the restriction preserves optimal economic value or yields a scalable solver.
G1 remains open; no new algorithm or efficacy experiment is claimed.

### Checkpoint 2026-10-28: monotone-policy cost is zero on the registered cell

The explicit monotone mixture in `switching_monotone_promotion_reduction_v1.md` matches the
unrestricted recovered policy on the registered recurrent `T=5, B=2, d=2` cell: activate with
probability `2/5`, query the first two events, and promote only if both labels are positive.
`verification.json` independently enumerates 2,048 worlds and reports exact agreement on all
five expected metrics, robust risk `1/10`, and pathwise query cap two; total cost is `184103/78125`.
This is zero observed restriction cost against that recovered policy, not an exact optimality
claim because no rational LP dual certificate exists. It does not test adaptive query timing or
generalize across parameters. G1 remains open; develop a compact monotone policy class and compare
its regret to the robust oracle before any efficacy run.

`screen_monotone_switching_policy_cost.py` then exhaustively optimized the full monotone pure-plan
mixture class in the analytic two-round static-regime cell (`T=2, B=1, d=1`). All 15 of 16 pure
plans had monotone promotion events; the restricted LP's exact optimum was `987/1000`, with
causal risk `1/10`, and matched the unrestricted solver's recovered value and the registered
analytic benchmark. This verifies the single-boundary-risk LP reduction on that finite policy
class. It remains a two-round calculation and does not establish a scalable optimizer, a cost
bound for longer adaptive policies, or new empirical efficacy.


The exhaustive unrestricted T=2 pure-plan LP now also carries a rational dual certificate (
u=1,
mu=13/100 on one null response), proving its exact optimum is 987/1000. Thus the monotone
restriction has zero optimality cost in this toy extensive form, rather than merely matching the
numerical causal-game solver. This does not certify the T=5 optimum or generalize beyond this cell.


### Checkpoint 2026-10-28: monotone-event utility preservation falsified

switching_monotone_class_separation_v1.md gives an exact two-label counterexample: the best
coordinatewise-monotone promotion event has alternative net value zero, while a nonmonotone event
with the same hard budget and delayed release has robust causal-null risk 1/2 and value 19/40;
upfront activation at 1/5 meets alpha=1/10 and yields safe value 19/200. The result holds with
free queries and a positive switch charge, so the loss comes from signed future value/reversal
evidence rather than acquisition pricing. All 16 Boolean events were checked exactly by
check_switching_monotone_class_separation.py. This rules out a universal positive-factor
approximation based on monotone promotion events absent additional alternative assumptions; it
does not identify a defensible assumption or novel method. G1 remains open; next source-level step
is to determine whether a robust-risk representation that admits nonmonotone events has a
structure exploitable beyond generic finite-horizon constrained planning. No efficacy study is
authorized by this result alone.


### Checkpoint 2026-10-28: generic risk-search plus cost-aware acquisition rejected

switching_risk_search_active_test_audit_v1.md records source-level inspection of RAO* (AAAI
2016) and active sequential testing with non-homogeneous costs (arXiv:2509.11632): finite-horizon
risk-constrained search and discrimination-per-cost acquisition are established. Their protocols
omit parts of the ShiftLab contract, but those differences do not establish novelty. Along with
the exact monotone-event utility separation, the generic combined mechanism fails G1. This is a
negative result for the current candidate, not completion or abandonment of the user's full goal.
Continue G1 only on a narrower, explicit alternative/information class with a source-level
reduction test; otherwise revise the research hypothesis. No prototype efficacy sweep or real-data
evaluation follows before that gate passes. G2-G5 remain open.


### Checkpoint 2026-10-28: partial-feedback switching baseline added

The source audit now includes Rangi and Franceschetti (AISTATS 2019), whose feedback-graph
EXP3 methods jointly handle partial feedback and deployment switching costs with regret/switch
bounds. That closes another generic construction. Their feedback is free and action-induced, with a
best-fixed-action comparator; paid hard-cap labels, delayed release and false-promotion risk remain
unmatched. A proposed joint query/action transport rule therefore needs a specific theorem that
beats a faithful feedback-graph/controlled-sensing composition under identical information and
costs. No such theorem is currently derived; G1 remains open and experiments remain held.


### Checkpoint 2026-10-28: finite-horizon utility-driven sensing prior audited

switching_finite_horizon_sensing_prior_audit_v1.md records a primary-source audit of Ferrari,
Zhao and Scaglione (arXiv:1705.05960v1). Their finite-horizon POMDP jointly selects sensing
resources, when to stop sensing and whether to exploit, with time-varying posterior thresholds and
an optimal sensing-resource rule. This closes generic remaining-horizon-aware VOI and posterior-threshold
acquisition as novelty. Their static immediate-observation model omits the causal conditional-null
risk, pending delayed labels, hard total query cap and recurrent reversible deployment. The
remaining gate is only whether this interaction yields a scalable theorem beyond sequential sensing,
robust planning and delayed-learning compositions. No algorithm selected; experiments remain held.
### Checkpoint 2026-10-28: two-round persistent-HMM structural screen

Extended the two-round monotone-promotion LP screen analytically to a symmetric persistent
hidden Markov regime with emissions 1/10 and 9/10, equal prior, one queried label, delay one,
alpha=1/10, query cost 1/100 and switch cost 1/10. At transition probabilities 0, 1/10,
1/4 and 2/5, the monotone-event restriction and unrestricted causal-null policy LP had the
same optimum total costs: 0.9480, 0.9608, 0.9800 and 0.9992 respectively. The unrestricted LP
enumerated all endpoint causal null response tables; the monotone LP used the fair-coin risk
reduction. Alternative costs used the HMM posterior after the first label and one-step predictive
emission for round two.

This is a small two-round screen, not a theorem or a source novelty result. It supplies no
positive separation and does not rule out a separation at longer horizons, with pending labels,
multiple purchases or asymmetric regime dynamics. It also does not validate a current-regime
safety certificate. The structural conjecture is not established, and no efficacy study is
unblocked. Continue by either extending the constrained-vs-unrestricted exact comparison to a
small delayed-label horizon where reversal is possible, or rejecting monotone promotion as a
promising algorithmic restriction if the next screen also shows no advantage. Maintain separate
objects for regime-predictive utility and global-null false-promotion risk.
### Checkpoint 2026-10-28: six-round delayed-reversal oracle policy screen

Reused the registered exact causal-game model (T=6, hard budget 3, delay 1, alpha=1/10,
query cost 1/100, switch cost 1/10) to inspect the recovered risk-constrained LP policy under
three symmetric persistent HMM alternatives: emissions (1/10,9/10) with transition 1/5;
(1/20,19/20) with transition 1/4; and (1/10,9/10) with transition 2/5. For each returned
behavioral policy, enumerated all 64 full potential-label tapes and computed its promotion
probability under that tape by forward recursion through the policy's randomized query/action
choices and fixed delay. Every coordinatewise cover comparison was nondecreasing in all three
cells (zero violations); each recovered causal-null risk was 1/10.

This establishes that the numerically recovered unrestricted optimizer is representable by a
monotone promotion-probability function in these registered cells. Therefore a restriction to
such policies has no cost gap in these instances. It is still not an exact restricted-LP versus
unrestricted-LP optimal-value comparison, a general structural theorem, or a certificate that the
HMM posterior forecasts current-regime utility after every possible reversal. The sequence-form LP
is floating-point optimized and its recovered policy is rationalized for evaluation, so report the
screen as numerical. It does not establish novelty or efficacy, and G1 remains open. Next, form a
constrained sequence-form LP whose promotion probability on each full potential tape obeys the
cover inequalities, then compare its primal/dual bounds to the unrestricted robust LP on T=4/5
cells; keep the predictive alternative cost and causal-null risk calculations separate.
### Checkpoint 2026-10-28: constrained sequence-form monotonicity LP implemented

Added an exact-in-form sequence realization constraint: for every full binary potential-label
tape and each coordinatewise cover edge, the realization-weight sum of first-promotion action
sequences on the lower tape must not exceed that on its upper neighbor. Promotion probabilities
are linear in learner realization weights because the tape fixes queried outcomes while the
learner's randomized action/query branches remain disjoint sequences. These inequalities are
added to the learner side of the existing robust causal-risk LP; alternative HMM expected cost
and the adversarial null-risk constraints remain separate. Implementation is in
src/shiftlab/dive/causal_switching_game.py (`promotion_tape_matrix` and
`solve(monotone_promotion=True)`).

For symmetric transition 1/4, emissions (1/10,9/10), prior 1/2, budget 2, delay 1, query cost
1/100, switch cost 1/10 and alpha 1/10, restricted and unrestricted floating-point LP objectives
matched at T=3 (1.4604), T=4 (1.9472), and T=5 (2.4352). At T=3, independent forward evaluation
of the restricted policy confirmed monotonicity over all potential tapes and causal risk 1/10;
a regression test now checks this against the unrestricted solver objective. Targeted suite:
12 tests passed; Ruff and `git diff --check` passed.

This is meaningful negative evidence against a utility gap from monotonicity in these cells, but
not yet an exact primal/dual certificate: HiGHS uses floating point and the test does not certify
the LP optimal values rationally. It is not a novel algorithm or theorem, and the restriction
itself has no observed advantage. Next try a reversal-shaped HMM/utility setup with delay 2 and
larger T, compare restricted/unrestricted bounds, and abandon monotone promotion as a candidate
if no separation or structural benefit emerges. Keep current-regime forecast utility distinct
from global-null risk throughout.
### Checkpoint 2026-10-28: monotone-promotion candidate rejected

The constrained sequence-form LP was compared with the unrestricted causal-risk oracle under
delay 2 and a strong HMM signal. With transition 1/4, emissions (1/50,49/50), T=6, B=3,
alpha=1/10, query cost 1/100 and switch cost 1/10, both objectives were 2.955693376. At
transition 9/20 both were 3.0, with no promotion in the recovered optimum. Across prior delay-1
T=3/4/5 cells the objectives also matched. The result is numerical, not a rational certificate.

The source audit in `switching_monotone_delayed_stress_audit_v1.md` finds the MLR/TP2 monotone
POMDP route established in Lovejoy (1987) and standard two-state POMDP threshold results. Our
robust tape-level constraint is not identical to those theorems, but it yields no measured planner
advantage and has no new mechanism. Reject it as the candidate contribution; retain code only as
a diagnostic. G1 remains open; do not treat this work as passing any manuscript gate.
### Checkpoint 2026-10-28: response-adaptive switching-cost prior audited

`switching_response_adaptive_switching_prior_audit_v1.md` records a full primary-source read of
Hardwick and Stout (JSPI 2007), including their posterior-state dynamic programs for arbitrary
terminal objectives under allocation-switch constraints/costs and their adaptive hyperopic rule.
This closes generic “adaptive sampling + switching cost” as a novelty claim. The allocation switch
is not the same as deployment switching, and their Bayesian fixed-sample objective has no delayed
pending-label process or robust false-promotion constraint. Those differences are a precise
comparison obligation, not a gap claim. The author-hosted PDF and SHA256 are in source manifest
v20. G1 remains open; no method or efficacy study is selected.
### Checkpoint 2026-10-28: episode-wise safe composition nearly matches finite oracle

`switching_episode_composition_comparator_v1.md` and its exact script compare all 15 fixed query
calendars under geometric, equal and frontloaded episode alpha spending in T=6,B=3,d=2. The
frontloaded schedule (1,3,4) has cost 2.959836896 and exact worst causal-null risk 1/10; the
recovered unrestricted sequence-form policy has cost 2.955693376 at the same risk. Expected
queries are 2/5 versus 1. The 0.00414352 gap is only to the numerically recovered policy (no dual
certificate), and the comparator class is narrow. It signals little headroom in this cell, not a
general bound. The proof uses the randomized positive-only test for false-promotion control and
uses HMM forecasts only for economic action/rollback decisions. Exact risk and cost calculations,
all calendars, and code hashes are saved. The composition is a stronger established baseline, not
a new method; G1 remains open. Targeted causal-game suite (12 tests), Ruff and whitespace checks
pass. No broad efficacy or real-data evaluation follows.
### Checkpoint 2026-10-28: episode-composition sensitivity across six recurrent cells

The frozen protocol in `switching_episode_composition_grid_protocol_v1.md` evaluated all fixed
calendars and three alpha allocations under six HMM cells. The best composition matched the
recovered LP policy at transition 1/4 with emissions (1/10,9/10), and was within 0.00414 at
emissions (1/50,49/50). Gaps were 0.0551 and 0.1064 in the two more-persistent transition-1/10
cells; both transition-9/20 cells preferred no switch. All candidate schedules met exact causal
risk and pathwise cap checks. The no-switch results indicate no exploitable signal for those
working models, while the persistent-cell gaps are only headroom against a narrow model-aware
calendar baseline and a floating-point LP policy, not certified method gains. Results and code
hashes are recorded under `outputs/switching_episode_composition_grid_v1/results.json`.

This sensitivity screen is useful for choosing future theory assumptions, not a confirmatory
synthetic study. It suggests any future candidate must target persistent/recurrent models and
beat optimized episode alpha spending; gains will likely be small. G1 remains open; no new method,
theorem, eligible real-data analysis or paper gate has passed.
### Checkpoint 2026-10-28: adaptive query timing showed no value in the six-cell decomposition

`decompose_switching_calendar_gap.py` compared the unrestricted causal game to 15 fixed query-
opportunity calendars in each predeclared HMM cell. The best fixed-calendar robust planner matched
the unrestricted recovered-policy cost exactly in all six cells; the selected opportunity dates
were (1,2,3) for signal-bearing models and no queries for transition 9/20. Since the calendar
planner still chooses queries vs. skips, actions and randomized tests adaptively at calendar dates,
this only removes access to query times outside the selected calendar. It shows no measured value
from fully adaptive timing in these cells. The episode policy's residual gap lies in its more
restricted test/action rule. Numerical LPs have no dual certificate, so equal recovered values do
not prove general equality of optima. Pivot the next theorem search toward robust test/action
policy structure, with a fresh prior-art audit; do not revive adaptive timing alone as novelty.

Reproduce the six-cell decomposition with `PYTHONPATH=src python
scripts/decompose_switching_calendar_gap.py`; results and hashes are in
`outputs/switching_calendar_gap_decomposition_v1/results.json`. Ruff and `git diff --check` passed.
### Checkpoint 2026-10-28: an arbitrary fixed-cohort test closes most episode-policy gap

The registered fixed cohort (query 1,2,3; decide at round 5) was optimized over all eight
randomized promotion probabilities under 128 endpoint causal-null kernels in the transition-1/10,
emissions-(1/50,49/50) cell. The recovered test promotes with probability 4/5 only after tape
111. Exact worst null risk is 1/10 and the pathwise request count is three. Exact alternative cost
is 2.7233173602304, compared with 2.8196795680256 for the best simple episode composition and
2.7133173602304 for the recovered unrestricted causal-game policy. The terminal test reduces the
episode-policy gap to 0.01 from the causal-game recovered policy. This shows that most of that
cell's apparent improvement opportunity was already addressed by ordinary test/action design,
not adaptive query timing.

The recovered test and its risk/cost arithmetic are exact after rationalization, but the LP has
no dual certificate, so its optimizer is numerical; the dynamic reference is also uncertified.
This is a fixed-cohort diagnostic within classical risk-constrained test design, not a new method
or theorem. Source/protocol/results are recorded in `switching_fixed_cohort_random_test_protocol_v1.md`
and its output directory. G1 remains open; matched efficacy and real-data gates stay held.

### Checkpoint 2026-10-28: rollback has a small reversal-specific value, but is covered by optimal switching

The registered one-way-versus-recurrent pair in `switching_rollback_value_pair_protocol_v1.md`
kept the query clock, delay, budget and robust promotion-risk rule fixed. The optimal promotion
test was the same in both cells: promote with probability 2/5 only after the two early labels are
both 1, with exact worst-case promotion risk 1/10. In the recurrent HMM, one rollback opportunity
reduced expected cost by exactly 27114503/1953125000 (~0.0138826); in the one-way no-reversal
control it had zero value. Reoptimizing the test after enabling rollback added no value. Exact
hidden-world enumeration independently matched the posterior-recursion costs for 8,192 worlds
per controller/model cell; the LP remains numerical without a dual certificate. Targeted causal
switching tests pass (12 passed), Ruff and `git diff --check` pass.

The primary-source audit `switching_hidden_markov_optimal_switching_prior_audit_v1.md` finds that
Bayraktar and Ludkovski already solve finite-horizon economic switching with Bayesian filtering,
recurrent hidden Markov states, running rewards and switching costs. The observed small reversal
effect is therefore a diagnostic, not a methodological contribution. Keep current-regime
economic forecasts separate from robust null evidence: prior promotion evidence does not certify
continued benefit after a reversal. G1 remains open; do not start broad efficacy or real-data runs.

### Checkpoint 2026-10-28: finite-horizon adaptive sensing and stopping is direct prior art

`switching_usage_constrained_sequential_testing_prior_audit_v1.md` records a primary-source read
of Li et al. (arXiv:1601.06447): their finite-horizon Bayes DP already selects sensing actions
from the current posterior, jointly chooses when to stop, and enforces terminal error and
per-realization maximum-sample constraints. Their per-sensor usage constraints are in expectation.
This closes generic adaptive sensing plus stopping as the contribution. The added source-table
entry in `switching_novelty_delta_v1.md` makes it a mandatory baseline for one-shot certification.
Known stationary hypotheses, immediate independent observations and no economic deployment
switches leave a contract mismatch, not an open-gap claim. G1 remains open; no efficacy or
real-data study follows without a theorem-level separation.

### Checkpoint 2026-10-28: exact reduction succeeds for one-shot switching and fails at the full contract

`switching_reduction_boundary_v1.md` maps the stationary, immediate-feedback, one-promotion
subproblem exactly to finite-horizon usage-constrained sequential testing: a hard maximum of B
samples, Bayesian terminal adoption/rejection loss, query cost and optional error constraints.
It records the specific failure points for the full target: history-dependent conditional-null
risk, labels pending across the action clock, and repeated regime-dependent economic switches.
This means those extra features cannot be treated as an automatic novelty delta. Delayed robust
planning already has a standard extensive-form representation, so a viable contribution must
exploit structure for a scalable algorithm with a bound against that oracle, then show a strict
advance over composed established baselines. G1 remains open and empirical work stays gated.

### Checkpoint 2026-10-28: robust finite-memory control supplies a representation, not the needed compression

The primary-source read and model mapping in `switching_robust_fsc_reduction_audit_v1.md`
shows that the finite-horizon causal-null safety branch can be encoded as a robust partially
observed model by storing full event history, pending outcomes, budget, time and promotion state.
This corrects any claim that the null is unrepresentable in a robust POMDP. The exact state is
history-sized, and the audited robust-FSC method returns locally optimized policies for a single
uncertain model; it supplies neither a compact representation nor a bound for the shared-policy,
two-kernel economic objective. The next gate is therefore an actual compression/approximation
theorem against the full-history oracle. Generic state augmentation/FSC/SCP remains disallowed as
the contribution. G1 is still open; empirical work remains gated.

### Checkpoint 2026-10-28: static null mixtures understate causal risk on a delayed nonmonotone event

The exact check in `switching_static_null_mixture_separation_v1.md` uses two labels, B=2 and
fixed delay 2. For the promotion event `Y1 != Y2`, the worst history-adaptive conditional-null
risk is exactly 3/4, while every fixed nonadaptive Bernoulli kernel and every mixture of such
kernels has risk at most 1/2. The endpoint script checked all 8 causal profiles and 4 fixed
product kernels; its rational output and hash are saved under
`outputs/switching_static_null_mixture_separation_v1/`. This rejects static-mixture risk
calibration for nonmonotone events, but does not imply that a compact dynamic risk state is
impossible or novel. The compression/approximation theorem gate remains open; no efficacy study.

### Checkpoint 2026-10-28: finite-state risk recursion preserves signed delayed events

`switching_fsc_risk_compression_v1.md` derives the exact conditional-null reachability recursion
for a fixed deterministic FSC over time, controller memory, action, remaining rights and pending
labels. A two-label XOR controller with delay 2 yields compact risk 3/4, matching enumeration
over all 8 full-history causal endpoint profiles. The script and rational results are preserved
under `outputs/switching_fsc_delayed_risk_compression_v1/`. This supplies an exact verifier for
nonmonotone events; robust FSC verification is established prior art (the source audit is linked
in the note), so it is not a new algorithm or theorem. What remains is optimizing one controller
for alternative economic cost under this null-risk constraint and proving a useful approximation
to the full oracle. G1/G2 remain open; empirical studies stay gated.

### Checkpoint 2026-10-28: fixed two-mode controller exactly distills one recovered oracle cell

The exact one-variable mixture LP in `switching_two_component_fsc_lp_v1.md` uses a fixed
rollback controller graph and a root activation lottery. On the registered delayed-reversal
cell, the active component has cost `173083/64000` and causal-null promotion risk `1/4`; mixing
it with the no-query incumbent at probability `2/5` yields risk `1/10` and total cost
`461083/160000`, exactly matching all reported metrics from the saved unrestricted numerical
sequence-form LP. This is post-hoc distillation, not independent evidence; the reference LP has
no exact dual certificate. Root randomization under one linear risk constraint is standard LP
structure, so this does not resolve G1 or establish a method. Targeted tests pass (11 passed),
Ruff and `git diff --check` pass. G1/G2 remain open; empirical efficacy and real-data gates stay
held.

### Checkpoint 2026-10-28: registered six-round oracle value now has a rational certificate

The numerical caveat on the `T=6, B=3, d=1` recurrent-HMM sequence-form benchmark is closed for
that instance. `switching_reversal_lp_certificate_v1.md` records an exact rational dual lower
bound and an exact feasible-policy upper bound; the bracket is at most `4.5e-11`. The checker
rebuilds alternative-cost coefficients with rational arithmetic, rationalizes the numerical dual,
then checks all free-column equalities exactly and accounts for inequality residuals using the
sequence-flow bound that each learner realization weight is at most one. The feasible upper
policy has exact causal-null risk `1/10` and respects the hard cap. This strengthens the small
oracle used for future comparisons; it does not advance novelty or justify efficacy sweeps.
The saved dual vectors were then checked by a separate verifier that does not call an optimizer;
it reconstructed the LP and confirmed the bound bracket and certificate hash. Targeted causal-game
tests (11 passed), Ruff, and `git diff --check` pass. G1/G2 remain open;
continue only by finding a source-audited structural separation beyond this finite oracle and the
existing delayed-learning, sequential-design, and robust-planning baselines. G3/G4 stay held.

### Checkpoint 2026-10-28: belief-grid plus exact-risk FSC is not yet a valid novelty candidate

`switching_belief_compression_candidate_audit_v1.md` screens a possible way to compress the
known alternative HMM while verifying the original causal-null promotion event exactly. Primary
sources already cover POMDP belief-grid value bounds (Lovejoy), robust belief planning (Osogami),
finite-controller reachability verification (Cubuktepe et al.), and fixed-kernel constant-horizon
chance-constrained approximation (Khonji et al.). None directly supplies an approximation for the
two-kernel objective in this contract, but combining those ingredients is not itself a novelty
claim. The unresolved technical step is a utility-gap bound to the full-history robust oracle that
also preserves global causal-null risk for nonmonotone promotion policies. No such theorem is
derived, so this candidate remains screened rather than selected; no experiment was run. G1/G2
remain open, and G3/G4 stay gated.

### Checkpoint 2026-10-28: exact counterexample rejects alternative-posterior-only compression

`switching_alt_belief_risk_alias_counterexample_v1.md` gives a two-label, delay-one case where
alternative histories `11` and `01` have the same current HMM posterior, but their alternative
probabilities differ. A full-history controller can spend the causal-null risk allowance on the
more likely history and obtain exact net value `128/125`; a policy whose state is only the current
alternative posterior is bounded by `14/25` at the same `alpha=1/10` and the same fixed query
calendar. The exact checker passes
and records the values under `outputs/switching_alt_belief_risk_alias_v1/`. This is a targeted
counterexample to posterior-only compression, not a new algorithm or a lower bound against FSCs:
one extra memory bit repairs this cell. The exact alpha sweep retains a positive gap for all
`0<alpha<9/20` in this fixed model. This still does not bound memory beyond two labels. The next
theorem question is how risk-relevant memory must scale with horizon, budget and delay, and whether
any compression can approximate the full-history oracle. G1/G2 remain open; no efficacy grid was
run and G3/G4 remain held.

### Checkpoint 2026-10-28: one-bit compression does not scale from current evidence

Rechecked the posterior-alias counterexample, six-round exact oracle certificate, post-hoc two-mode
controller, and fixed-FSC causal-risk recursion. The one-bit memory repairs only the two-label
alias cell. The six-round controller's promotion and rollback evidence are separate, and the
controller was distilled from the same oracle cell; the exact oracle bracket is instance-specific.
This does not establish a memory bound or an approximation guarantee. The belief-compression
candidate is rejected at its current G2 step: no generalization to an efficacy grid. To reopen it,
state an explicit growing family and prove either a risk-preserving construction with utility gap to
the full-history oracle or a memory lower bound, then audit it against robust FSC and constrained
POMDP prior work. Promotion safety under the causal null remains distinct from current-regime
benefit and rollback evidence after reversal. The exact alias checker, independent rational LP
certificate verifier, and delayed-FSC risk checker pass; these validate only the scoped results.
G1/G2 remain open; G3/G4 remain gated.

### Checkpoint 2026-10-28: two-threshold reward/detection control added to prior-art boundary

The primary-source audit in `switching_reward_detection_control_prior_audit_v1.md` inspected
Banerjee, Liu and How (arXiv:1609.06757v2, ACC 2017). Their two-threshold policy already moves
between reward-optimal and information-maximizing control, switches to a post-change policy at an
upper evidence threshold, returns to reward-optimal control when evidence falls, and discusses
repeating detection across sufficiently separated changes. This rejects generic reward/detection
thresholding as a contribution. The source does not cover ShiftLab's pathwise paid query cap,
delayed releases, switching fee or finite-horizon conditional-null false-promotion probability;
these remain obligations rather than a novelty claim. The paired-outcome setting has one common
observation stream, so any surviving acquisition mechanism must prove value from when to spend a
query right, under delayed releases and reversible economics, beyond this controller and the
strongest sequential-design composition. Do not run efficacy experiments until that mechanism and
theory clear G1/G2. G1/G2 remain open; G3/G4 remain gated.

### Checkpoint 2026-10-28: conditional risk recycling is a baseline, not a method

`switching_two_episode_risk_recycling_v1.md` gives an exact two-look calculation under the
full-history conditional null. For positive-only randomized tests, worst-case familywise risk is
`1-(1-a1)(1-a2)`, where `a_i` are the conditional per-attempt error levels. Conditional-error
allocation can use the risk cap more fully than Bonferroni; at alpha 0.1 and stationary q=0.9,
the example raises promotion probability from `1719/10000` to `837/4750` at the same expected
query count `191/100`. The exact Fraction check enumerating the four null endpoint pairs passed.
Posch and Bauer's primary two-stage adaptive-design source confirms conditional-error reassessment
is established practice. This is standard sequential testing, stationary, and has no rollback; it
does not clear G1. Retain it as a calibration baseline for any future adaptive risk allocation.
G1/G2 remain open; do not start broad efficacy or real-data work from this toy advantage.

### Checkpoint 2026-10-28: monotone terminal tests survive a bounded recurrent-HMM screen

The exploratory fixed-cohort screen in `switching_hmm_monotone_terminal_test_screen_v1.md`
compared unrestricted causal-null terminal tests with monotone tests across 26,112 two-state HMM
cells. HMM tape/payoff coefficients were formed exactly, and each policy-class LP used all eight
causal endpoint nulls; HiGHS optimized both LPs numerically. Across 11,062 cells with positive
unrestricted value, no monotone-class gap exceeded `1e-7`. This is limited finite-grid evidence,
not an exact theorem or efficacy result. The next analytical step is to derive a checkable HMM
condition for which the boundary-IID fractional-knapsack test is monotone and hence exactly
optimal under the causal null, or to find an exact counterexample. Even if proved, the fixed
terminal test is only a subroutine; adaptive acquisition, rollback, a performance theorem against
scalable sequential design, and eligible real-data evidence remain open. G1/G2 stay open; G3/G4
remain gated.

### Checkpoint 2026-10-28: monotone promotion preserves the certified delayed-reversal oracle cell

The existing `T=6, B=3, d=1` recurrent-HMM cell was re-solved with `monotone_promotion=True`
using the same full causal conditional-null LP. This restriction applies to first-promotion
probability over potential label tapes and leaves adaptive queries and rollback available. The
constrained solve recovered the same exact feasible policy as the unrestricted solve: activate
with probability `2/5`, query at event 2 only after a positive first label, promote after two
positives, query once while deployed, and roll back after a negative maintenance label. Both
recovered policies have exact cost `461083/160000` and causal-null risk `1/10`. The independent
rational certificate places the unrestricted optimum in `[576353749991/200000000000,
461083/160000]`; hence the monotone class loses at most `9/200000000000` on this cell. The
reproducible comparison is `switching_monotone_adaptive_oracle_cell_v1.md` and its output JSON.
This is one instance, not a general theorem or novelty claim, and does not compare against the
strongest scalable sequential-design baseline. G1/G2 remain open; G3/G4 remain gated.


### Checkpoint 2026-10-28: asymmetric-HMM monotone-adaptive screen finds no recovered-cost separation

The reproducible 576-cell screen in `switching_asymmetric_hmm_monotone_adaptive_screen_v1.md`
varied asymmetric transition rates and priors, emission strength, horizon/budget/delay, alpha,
and query/switch fees. All unrestricted and monotone-constrained numerically recovered policies
had equal rationally evaluated costs; this is not an optimum certificate. Together with the prior
exact signed-future-value counterexample, the evidence rejects monotonicity as a general value
approximation route. It remains an optional tractability restriction only when separately
certified. Stop broad grid searches for a monotone gap. Return to G1's specified future-value
acquisition target under an explicit persistence/drift contract and perform a proof-level reduction
against costed POMDP and sequential experimental design. No algorithm, novelty, theorem or efficacy
claim is validated; G1/G2 remain open and G3/G4 remain held.


### Checkpoint 2026-10-28: exact fixed-cohort separation under the full causal-null contract

The registered matched comparison in `switching_fixed_cohort_vs_adaptive_protocol_v1.md`
correctly shares null conditional probabilities across cohort branches until their public query
histories diverge. A rational primal-dual certificate proves the best randomized fixed-cohort
terminal test has cost `4626223/1600000`; the full adaptive oracle's certified upper cost is
`461083/160000`, yielding a strict gap of at least `15393/1600000`. The safe fixed-cohort policy
uses three early labels with probability `4/5`, promotes only on `111`, and otherwise does nothing.
The full oracle's recovered policy instead conditions its second query, promotes earlier after two
positives, and can use fresh maintenance evidence to roll back. Both use the same costs, hard cap,
delay, alternative HMM and global conditional-null risk; exact forward cost and risk recursions
independently match the fixed-cohort certificate.

This proves a finite class separation, not novelty: it does not isolate the source of the gap and
does not beat the composed active sequential-testing / delayed-experimentation / hidden-Markov
control baseline. Continue G1 by auditing that exact composition against this registered game; do
not promote the finite-oracle policy to a method or open G3/G4. Keep promotion risk distinct from
current-regime belief and post-reversal future utility.

### Checkpoint 2026-10-28: fixed-cohort gap does not clear the composed-prior boundary

`switching_composed_prior_boundary_v1.md` maps the exact fixed-cohort separation against the
closest audited methods: delayed economic experimentation/adoption, controlled sequential testing
with sensing-switch cost, utility-driven finite-horizon sensing, chance-constrained POMDP planning,
and robust finite-memory POMDPs. A focused primary-source check also located budgeted observation-
capability design; its publisher PDF was inaccessible, so only the public-record scope is noted.
The sources cover the individual ingredients but none of the audited theorems directly matches
the asymmetric-information two-kernel objective with delayed paired labels, a pathwise cap and
repeated deployment rollback. That is an unresolved equivalence audit, not evidence of novelty.
The exact finite sequence-form LP is generic and does not scale.

G1 remains open. Next compare a faithful, resource-matched composition against the exact causal
oracle on a growing registered family, or prove a growing-family separation from that composition.
Do not promote the one-cell fixed-cohort gap into a method claim or advance to G3/G4.

### Checkpoint 2026-10-28: exact small-family separation from deterministic query calendars

`switching_fixed_calendar_action_oracle_protocol_v1.md` compares the unrestricted causal game
against every deterministic query calendar on three registered cells `(T,B)=(4,2),(5,2),(6,3)`.
Each calendar receives a fully optimized action policy, including promotion, rollback and repeated
switching, under the same delay, pathwise cap, HMM alternative, switching/query fees, and
history-adaptive conditional-null risk. Rational dual lower bounds for all 44 calendars were
verified independently without an optimizer; recovered policy costs and risks were also checked.
The best deterministic-calendar class is worse than a feasible adaptive policy by exactly `7/500`
in the first two cells and by more than `1562/100000` in the six-round cell. This strengthens the
finite fixed-cohort evidence, but it is still not a growing-family theorem and excludes randomized
calendar mixtures and adaptive controlled-sensing compositions. It does not identify the source of
the gap or establish novelty. G1/G2 remain open; G3/G4 remain held. Next include the stronger
randomized-calendar/controlled-sensing class under the same shared-null information structure, or
derive a theorem that isolates an acquisition effect from action timing and rollback.

### Checkpoint 2026-10-28: full action control does not improve the two-calendar lottery

`switching_randomized_calendar_action_protocol_v1.md` jointly optimizes a private lottery between
no queries and the early three-query calendar, with unrestricted branch action policies and the
shared causal-null risk budget. The branch split is valid because the first-round query choice
reveals the branch to the null adversary. The exact optimum is `4626223/1600000`: choose no query
with probability `1/5`, or query events 1, 2 and 3 with probability `4/5` and promote only after
`111`. The early branch has conditional robust-null risk `1/8`, yielding total risk `1/10`.
Rational primal-dual verification brackets the value within `3e-12`; an independent full-game
recursion matches policy cost and risk without an optimizer. This exactly matches the previous
fixed-cohort terminal-test value despite allowing rollback/re-promotion, so those action freedoms
add no value in this cell. The adaptive oracle's feasible policy remains better by at least
`0.009620624997`. This is a precise two-calendar class separation, not the full randomized
calendar class and not a new algorithm. G1/G2 remain open; G3/G4 remain held. Next isolate
label-contingent acquisition from action-timing freedoms or solve a wider shared-null randomized
calendar class, then compare against the strongest adaptive controlled-sensing composition.

### Checkpoint 2026-10-28: action-matched acquisition gap is certified, but the rule is classical futility stopping

`switching_action_matched_adaptive_acquisition_v1.md` locks every policy to the same terminal-only
deployment action and compares adaptive acquisition against all 26 deterministic calendars in the
`T=6, B=3, d=1` recurrent-HMM cell. An explicit rule enters at event 3 with probability `4/5`,
queries again only along the positive-label prefix, and promotes at event 6 only after `111`. Its
exact expected cost is `1179063/400000`, expected query count `1481/1000`, and causal-null risk
`1/10`. All 26 fixed-calendar policies have optimizer-free verified rational dual lower bounds;
their minimum is approximately `2.962847499999693`. The explicit adaptive policy therefore
certifies a gap of at least `0.015189999999693` from the deterministic-calendar class while
holding action timing fixed. A coupled static lottery over no-query and calendar `(3,4,5)` has
cost `1182739/400000`, risk `1/10`, and `12/5` expected labels; positive-prefix futility saves
`919/1000` expected labels and `919/100000` cost in this cell. Exact forward recursion verifies
that the explicit rule matches the adaptive LP's recovered metric tuple. The static lottery is a
feasible baseline, not an optimization over every randomized cohort/test policy.

This yields a finite structural separation, not a scalable algorithm or novelty result. The
positive-prefix coupling is established early-futility/group-sequential logic, and delayed-response
group-sequential testing is also prior art (Brown and Rutemiller 1971; Gould and Pecore 1982;
Hampson and Jennison 2013; the source-level scope audit is in
`switching_positive_prefix_prior_art_audit_v1.md`). The risk result is
false-promotion control under the endpoint causal null; it does not show benefit in a current
regime after reversal. G1/G2 remain open and G3/G4 remain held. Next perform the proof-level
equivalence audit for this exact cost-saving coupling against delayed controlled sequential tests
and costed sensing, then seek a non-classical contribution in recurrent switching economics,
current-regime forecasts and delayed risk accounting rather than relabeling futility stopping.

### Checkpoint 2026-10-28: exact-game/POSG equivalence boundary

`switching_posg_equivalence_audit_v1.md` makes the information structure explicit as a finite
imperfect-private-monitoring stochastic game: the learner's alternative-HMM utility and the
history-adaptive conditional-null reachability risk are separate probability models; pending labels,
request-time budget reservation, deployment state and the absorbing any-promotion event must be
represented. The small-cell sequence-form LP is an exact generic solver, not a method contribution.
A standard belief-state POMDP is insufficient without representing the null player's hidden history.

Primary-source audit confirms substantial overlap with robust partially observable control
(Rasouli–Saghafian, Theorems 3–4), chance-constrained POMDP planning (RAO*, abstract/record only
in this pass), finite-horizon adaptive sensing and stopping (Li et al., including a finite maximum
sample horizon), and delayed group-sequential designs (Hampson–Jennison). These sources block
broad novelty claims but do not establish full theorem equivalence. The POSG state augmentation
may reproduce the exact objective generically; the audited evidence does not yet show whether an
existing algorithm solves the same constrained information structure or supplies the desired
scalable guarantee. Regime belief/current expected utility remains distinct from global
false-promotion control, including after a reversal.

Decision: continue G1, no method selected, and do not open G2–G5. Next conduct the required
proof-level equivalence audit on a growing family, first checking whether robust POSG dynamic
programming can express the same asymmetric null information and separate constrained objective;
then identify whether any scalable structure remains beyond generic exponential planning. If no
nontrivial scalable advantage survives, revise or stop this method hypothesis instead of polishing
the finite benchmark. Source limitation: RAO* full text/proof not inspected in this pass.

### Checkpoint 2026-10-28: source-level POSG boundary

- Read the full primary HTML source for Wen, Xia and Yu (2025), including model assumptions and
  Theorem 3, plus the primary RSS source for Carr et al. (2021). They close broad claims about
  probability-criterion partially observed games and reward-plus-safety POSGs respectively.
- They do not directly establish the constrained two-law objective here: alternative-HMM expected
  economic cost and worst-case null reachability are evaluated under separate laws for the same
  learner policy; the null adversary sees pending outcomes hidden from the learner; and query budget
  is pathwise at request time. Conversely, generic finite-game representability proves no novelty
  or tractability.
- `switching_posg_reduction_boundary_v2.md` records the scalarized formulation and the exact
  preservation obligations for a valid reduction. G1 remains open; no new algorithm or theorem is
  claimed, and G2–G5 remain held. Continue by proving the reduction on a growing finite family or
  identify a structural restriction that yields a compact recursion and a risk/error guarantee.

### Checkpoint 2026-10-28: two-law constrained-game reduction

- Inspected the existing reference implementation and its information sets: alternative and null
  traversals share the same learner realization variables; pending labels are hidden from the
  learner; the null opponent sees them; budget is removed at request time; and first promotion is
  the absorbing risk event. The focused semantic suite passes: `uv run pytest -q
  tests/test_causal_switching_game.py tests/test_causal_switching_game_reversal.py` (12 passed).
- `switching_two_law_game_duality_v1.md` gives the finite constrained sequence-form formulation
  and Lagrangian zero-sum game reduction. Perfect recall, endpoint maximization of the rectangular
  causal null, and convex Slater duality for alpha>0 establish the representation. Sequence form
  is standard and linear in the expanded game tree, which may still be exponential in horizon.
- Decision: **no-go** for presenting the generic two-law constrained game, its scalarization, or
  the small exact LP as the methodological contribution. This closes that version of G1 rather
  than claiming the full research goal is achieved. Keep the overall goal active and G2–G5 held;
  only reopen G1 for a concrete structural family that admits a sub-exponential policy
  representation/approximation preserving causal-null risk and a value bound against the full
  oracle. Posterior-only belief compression is already counterexample-screened, so the next
  hypothesis must state which extra risk-relevant memory it retains before any broad experiment.

### Checkpoint 2026-10-28: bounded-memory testing prior

- Inspected Managoli and Prabhakaran (2026 preprint), including its adaptive adversary/FSM
  information structure, Theorem 1, Corollary 1, Theorem 2 and proof sections. It already gives
  memory-dependent minimax error bounds for adversarial testing with a randomized finite-state
  machine.
- Its theorem controls asymptotic average classification error for a sample arriving every step.
  It does not give finite-horizon probability of any false promotion, paid/pathwise-budgeted query
  acquisition, delayed releases, reversible deployment costs or alternative-HMM decision regret.
  `switching_finite_memory_adversarial_testing_prior_audit_v1.md` records that boundary. A generic
  finite-memory detector/controller is now also closed as a novelty claim.
- The posterior-belief compression candidate remains rejected. No algorithm has passed the current
  novelty gate. The next admissible hypothesis must prove a finite-horizon acquisition-and-switch
  cost/regret improvement under the original causal risk and delay contract, beyond a sum of
  established memory, sensing, switching and delay bounds. G2–G5 remain held; do not run a broad
  efficacy grid until that theorem target and comparator are concrete. Promotion validity and
  post-reversal current-value evidence remain separate.

### Checkpoint 2026-10-29: recursive constrained-POMDP prior

- Read Ho et al.'s primary UAI 2024 paper through Sections 2–5, Proposition 2, Theorems 1–4 and
  the ARCS algorithm. RC-POMDP already augments belief with a history-dependent admissible-cost
  budget, restores Bellman structure, proves deterministic optimality, and gives sound/
  epsilon-optimal output when ARCS terminates; ARCS is incomplete. This closes the generic
  “remaining risk budget as state” / dynamic-programming idea.
- Its guarantee applies to expected cumulative costs under a single POMDP law. ShiftLab instead
  scores economic cost under an alternative HMM and constrains any-promotion probability under a
  separate history-adaptive causal null that sees pending labels hidden from the learner. A direct
  RC-POMDP transfer would have to preserve that asymmetric information and shared policy; the
  generic two-law sequence-form reference does so only with potentially exponential tree size.
  `switching_rc_pomdp_prior_audit_v1.md` records the scope boundary and primary-source hash.
- Decision: reject a generic RC-POMDP wrapper or scalar risk-budget planner as the method. No
  algorithm or theorem passed G1/G2. Next require a sub-exponential, policy-sufficient risk-memory
  construction with a value bound to the full-history oracle, or a growing-family lower bound that
  forces a hypothesis change. No broad experiment is authorized by this checkpoint. Promotion
  validity remains separate from current-regime benefit and rollback evidence after reversal.

### Checkpoint 2026-10-29: memory lower-bound gate after source audit

- PR #8 merged the recursive constrained-POMDP audit and source manifest at `1fb33d6` after the
  full CI suite passed. The active main checkout is clean. This closes the generic remaining-risk-
  budget recursion as a novelty route; it does not close the overall research goal.
- The available exact alias result only rules out alternative-posterior-only state. Its one-bit
  repair, the robust-FSC history augmentation, and the exact two-law sequence-form oracle do not
  establish how much memory is required as horizon grows. Exponential oracle size is not itself a
  lower bound on a useful controller.
- Next G1 gate: formulate a growing family of promotion events over delayed queried tapes for
  which (i) worst full-history causal-null probability is computed exactly, (ii) alternative-HMM
  value is explicit, and (iii) any policy with at most `M` controller states has a proved value
  gap from the full-history safe oracle for a stated scaling of `M`, horizon, budget and delay.
  First screen candidate event languages with the exact causal-null backward recursion and a
  distinguishability argument for the finite controller; the learner must never see pending
  outcomes. A numerical separation or hard instance alone does not satisfy this gate.
- If the family fails because a small statistic suffices, record that statistic and test its
  policy-sufficiency for the shared alternative-value / causal-null-risk objective. If no growing
  lower bound or compact risk-preserving construction survives comparison with robust-FSC and
  RC-POMDP prior work, stop this memory-compression route and revise G1. G2–G5 remain held; no broad
  efficacy sweep or holdout opening follows from this checkpoint.
- Preserve the separate evidence contract: a promotion-risk state controls the declared null;
  current-regime benefit requires post-change evidence or an explicit persistence model. Historical
  likelihood-ratio wealth cannot certify value after reversal, and rollback delay loss remains a
  separate outcome.

### Checkpoint 2026-10-29: cost-aware bandit two-phase prior

- Audited Schur, Lago and Fiez (UAI 2026) from the official PMLR PDF, including the proof of their
  two-phase policy reduction. Under stationary independent reward noise, action-dependent
  observation prices and correlated actions, they show that an arbitrary policy is uniformly
  dominated in regret by one that observes only in an initial phase and commits afterward. Their
  cost-adjusted information-gain guarantees further close generic costly-acquisition rules.
- The reduction does not preserve recurrent hidden regimes, delayed paired feedback, request-time
  hard budgets with pending labels, reversible switching, or the causal-null any-promotion event.
  `switching_costly_bandits_two_phase_audit_v1.md` records the exact theorem boundary and source
  hash. Assumption mismatch alone does not establish a novel method.
- Decision: retain the current method goal only if a theorem exploits the interaction of those
  ShiftLab-specific elements and beats a fully state-aware costed-sensing baseline under the same
  contract. The query-stratum-dependent `p_j` movement-coupling idea remains unvalidated and must
  account for actual continuation utility, not arbitrary scores. No efficacy grid or holdout access
  is authorized before that comparison passes G1/G2.

### Checkpoint 2026-10-29: Markov state-sensing planner prior

- Audited Kapoor and Nair (AISTATS 2026) from the official PMLR PDF, including the hidden-state
  sensing protocol, SPI, and Theorems 4.1, 4.2 and 4.4. They already formulate Markov control with
  recurring state-sensing costs, blind action sequences, and a computable truncation/suboptimality
  guarantee. `switching_markov_state_sensing_cost_audit_v1.md` records the theorem boundary and
  source hash.
- Their sensing action reveals the latent state under a single discounted law. It does not preserve
  ShiftLab's delayed noisy paired labels, pathwise total query cap, reversible deployment costs, or
  separate causal-null any-promotion constraint. Merely augmenting this planner with queue, budget
  and risk variables is not a methodological result.
- Decision: a surviving theorem must compare against both stationary cost-aware bandits and Markov
  state-sensing control, and exploit the exact two-law, delayed, reversible contract. No method has
  passed G1. Hold G2–G5 and keep promotion validity separate from post-reversal current value.

### Continuation checkpoint 2026-10-29: exact oracle and next G1 screen

- Independently reran `scripts/verify_switching_reversal_lp_certificate.py` without an optimizer.
  The saved rational certificate verifies the registered `T=6, B=3, d=1` full-history oracle in
  `[576353749991/200000000000, 461083/160000]`, a width of `9/200000000000`. This confirms the
  finite reference value, not a scalable controller or a method-versus-baseline result; its
  feasible upper policy was fitted on the same cell.
- The fixed-calendar/action-oracle study already supplies a small exact adaptive-timing separation,
  while episode composition and adaptive stopping explain most of the simple acquisition gap. The
  remaining memory-compression direction therefore needs a theorem rather than another small-cell
  sweep.
- Immediate next G1 screen: define a growing delayed-label family and its full-history safe oracle;
  then either prove an `M`-state value lower bound under the same causal-null anytime risk, or
  construct a compact risk state with an explicit oracle gap. Start with a simple IID subfamily to
  test candidate distinguishability arguments, but retain a one-step release queue and request-time
  budget accounting. A failed lower-bound attempt should be recorded as a counterexample/pivot, not
  turned into an empirical novelty claim.
- Promotion-risk validity remains a separate guarantee from current-regime benefit: after an
  unobserved reversal, pre-reversal likelihood-ratio wealth does not certify that the challenger
  remains valuable. Any continuation-value claim must use post-change evidence or state a defensible
  persistence/predictive-signal assumption. G1 remains open; G2–G5 remain held, with no efficacy
  grid or real-data confirmation authorized by this checkpoint.

### G1 screen 2026-10-29: IID delayed terminal testing is insufficient

- `switching_iid_delayed_terminal_test_screen_v1.md` analyzes a growing family with a pathwise
  budget, one-step label release, and the original history-adaptive causal null. For monotone tests,
  common-uniform coupling reduces worst-null risk exactly to IID `Bernoulli(1/2)`. The known IID
  alternative then gives a Neyman–Pearson randomized upper-tail test on the positive-label count.
  Every robust-feasible test is feasible under the boundary null, and the most-powerful upper-tail
  test is itself causally safe, so it is optimal for the full robust terminal-test class. A count,
  one-label queue and public clock give a polynomial-size exact controller; there is no memory lower
  bound or oracle gap for this family.
- Decision: reject this as the target method. Fixed-schedule terminal testing is classical and
  adaptive finite-horizon testing with a maximum sample count is already audited. This kills the
  simplest growing-family route, but does not resolve the full objective.
- Next G1 screen must retain the interaction removed here: repeated/reversible deployment before
  all delayed outcomes clear, recurring economic regimes, and the separate global causal-null
  promotion event. Compare any compact state against the full-history two-law oracle on that family.
  G1 remains open; do not launch an efficacy grid. Current-regime benefit after reversal still
  requires post-change evidence or a declared persistence/predictive-signal model.

### G1 source boundary 2026-10-29: delayed belief and queue are established

- Audited Subramanian et al. (JMLR 2022), Theorem 5 and its proof plus the delayed-POMDP example in
  Section 2.4, from the official PDF. Their exact information-state dynamic program already covers
  delayed observations using the delayed-state belief and recent controls. With finite ShiftLab
  delays, augmenting an HMM belief by pending outcomes/release clocks, query budget and deployed
  action is ordinary single-law POMDP state construction, not the algorithmic contribution.
  `switching_delayed_pomdp_information_state_audit_v1.md` records the scope and hash (manifest v27).
- The theorem does not cover the separate history-adaptive causal-null reachability criterion: the
  null sees pending labels hidden from the learner, and alternative-posterior aliases can have
  distinct continuation risk. Thus it closes the economic-belief/queue compression claim but not
  the two-law objective.
- Next G1 work must focus on the risk-preserving information state itself and compare it with the
  full-history two-law oracle, or prove a growing memory lower bound. A generic risk-budget state is
  also prior art. No method has passed G1; G2–G5 remain held.

### G1 scaling screen 2026-10-29: posterior-alias witness does not grow

- Tried extending the two-label posterior-alias example by appending labels from the deterministic
  favorable HMM state. `switching_alias_family_scaling_screen_v1.md` gives the exact safe-test
  comparison: the full-history prefix test has power `(9/10) min(1, alpha*2^B)`, but a one-bit
  suffix-positive trigger has power `min(1, alpha*2^(B-1))` at the same query cost. At
  `alpha=0.1`, the latter reaches power one by `B=5` with causal-null risk `1/16`. The proposed
  growing family therefore has no asymptotic memory gap; the newest labels provide a compact,
  safer trigger.
- Decision: reject this extension as a lower-bound family. Future memory screens must optimize over
  all later triggers and compact event summaries, and preserve the pending-feedback/reversible
  decision interaction. G1 remains open; no efficacy sweep follows.

### G1 source boundary 2026-10-29: adaptive robust sequential tests are established

- Audited Saha and Ramdas, arXiv:2408.14015, from the official arXiv PDF: adaptive conditional
  contamination under composite nulls, Corollary 3.4, Section 4.2, and Theorem 4.6. Their robust
  likelihood-ratio and predictable plug-in constructions already give
  test-supermartingale/anytime risk control under history-adaptive conditional null laws.
  `switching_robust_sequential_testing_prior_audit_v1.md` records the theorem scope and source hash
  (manifest v28).
- Consequently, an e-process gate, composite-null likelihood ratio, or predictable safe-factor
  product is not the methodological contribution. Predictable acquisition, finite stopping, and
  delayed label release appear reducible to event-time filtration bookkeeping; formalize that
  reduction before making it a proof claim.
- The robust-test audit now gives the exact fixed-delay reduction: the visible wealth at event `t`
  is the event-time product through `t-d`; Ville then controls every visible threshold crossing,
  including adaptive stopping at a hard request cap. This depends on fixed ordered releases and
  does not justify multiplying only revealed factors under outcome-dependent/out-of-order delay.
- Residual G1 must concern the interaction between a global any-promotion risk constraint, limited
  delayed observations, and recurring reversible economic switching, compared against an exact or
  provably strong resource-matched controller. Promotion evidence remains distinct from current
  challenger value after regime reversal. G1 remains open; G2–G5 stay held.

### G1 growing-family screen 2026-10-29: paired-copy labels admit compact safe testing

- Constructed a growing finite-state alternative emitting adjacent copied Bernoulli bits, with
  fixed one-round feedback delay and the original full-history causal null. If `Z_i` marks a pair
  of positive labels, then its conditional null probability is at most `1/4`, while it is `1/2`
  under the alternative. Therefore the exact worst-null promotion risk for a count threshold is
  the `Binomial(m,1/4)` tail; alternative power is the `Binomial(m,1/2)` tail.
- `switching_paired_copy_compact_screen_v1.md` gives the finite-state count controller, exact
  test, Hoeffding scaling, and a coarse additive value bound against the full-history oracle. An
  exact rational screen at `alpha=.1` reaches power at least `.99` with 50 pairs, 100 pathwise
  queries, 206 controller states and relative gap upper bound about `.0078` at 10,000 reward
  rounds. The full oracle itself was not solved in this growing family.
- Decision: this refutes a blanket finite-memory lower-bound strategy based only on longer delayed
  tapes. The pair-success statistic is an ordinary Bernoulli test, and fixed-sample testing plus
  a compact counter are established ingredients; reject it as the new algorithm. A future lower
  bound must survive compact sufficient event statistics and compare against the strongest
  resource-matched safe test. G1 remains open; G2–G5 stay held. Promotion validity still does not
  certify current value after reversal.
