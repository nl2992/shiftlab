# Working plan: risk-preserving approximation for sequential switching

**Mission:** develop a computationally useful approximation to the existing two-law,
finite-horizon switching oracle, with an economic value bound and a worst-case
causal-null promotion-risk guarantee. The governing scope is `RESEARCH_BRIEF.md`.
**Current state (2026-10-29):** reference anchors and exact-risk checks are
reproduced. Several candidate mechanisms have been falsified as main methods or
remain unresolved: query caps lose to the stronger calendar baseline economically (one T=8 recovered-policy tie also shows a small compute reduction); simple
belief grids lack tractable state counts and a closed transfer proof; generic
null-cut and dominance pruning do not reduce the pre-promotion tree; policy-column
generation still lacks a compact pricing oracle. At T=8,B=4,d=2 the exact adaptive
reference beats the best fixed calendar in two cells, but capped/e-process candidates
miss that gain; a finite root-portfolio over calendar risk frontiers also selected
the best single calendar and did not close the gap. No candidate has yet established
the required synthetic and real-data baseline wins. See the append-only ledger.

## Operating contract

The benchmark optimum ranges over nonanticipating policies with a pathwise query
cap. Charge requests immediately; release outcomes only at their declared times.
Compute expected economic costs under the known alternative HMM, and control the
probability of any first promotion uniformly over the full history-adaptive causal
null, which may see pending outcomes. After promotion, continue to account for
rollback, re-promotion, remaining budget and switching costs. A historical
promotion certificate does not certify present profitability after reversal.

Use new branch-local files, registered configurations and distinct outputs. Preserve
historical artifacts and verdicts, avoid reserved holdouts, and never merge the
branch automatically. Keep an append-only record with proof status, negative
results, exact commands, code/data versions and hashes. Classify theorem statements
as PROVED, CONDITIONAL, SKETCHED, CONJECTURED or FALSIFIED. Use small CPU-sized
checks first and reserve new seeds only through the repository's existing process.

## 1. Reconstruct and verify the reference problem

- Read the required notes, solver implementations and tests listed in the brief;
  map the event order, learner/null information, LP variables and continuation DP.
- Check the base manifest against tracked Git blobs. Identify unavailable ignored
  outputs and source caches without rewriting or reconstructing historical files.
- Create a branch-local environment and run the focused decomposition tests. Where
  feasible, reproduce the registered T=6 anchor, the T=7 equality and the T=8
  resource-cap result under their original limits, writing fresh provenance to a
  new location. Record each as verified, unavailable or failed. T=8 does not have
  an independent completed full-oracle comparison.
- Deliver a compact contract and oracle map in `PROBLEM_AND_THEOREM_TARGET.md`,
  including which historical claims have been read versus independently checked.

**Gate:** the reference policy class, risk event, exact-solver limitations and
pending-feedback semantics are explicit. A failed check is investigated and recorded;
no historical protocol or output is changed to make it pass.

## 2. Specify the theorem and examine prior art

- State assumptions, policy class, target optimum, risk criterion, value error,
  computational complexity, closest theorem, missing technical step and a minimal
  instance where the proposed result matters. Identify dependence on T, B, delay,
  approximation accuracy, model size and numerical precision as applicable.
- Start with the existing source audits; check the primary statements and relevant
  proofs for finite-memory POMDP approximation, robust FSC synthesis, one-sided
  partially observed games, constrained/chance-constrained planning and other
  directly relevant work. Extend only where a candidate requires it.
- Compare entire guarantees and their assumptions. Mark a plausible but unchecked
  equivalence `UNRESOLVED — EXACT REDUCTION REQUIRED`, then attempt that reduction.
  Familiar ingredients alone neither establish nor disprove novelty.
- Record the comparison and its evidence in `PRIOR_ART_EQUIVALENCE_AUDIT.md`.

**Gate:** at least one precise, nonvacuous theorem target and unresolved lemma are
identified, with a credible route to useful complexity and a source-matched
comparison. If this fails, document the exact obstacle before substantial coding;
continue to the next candidate rather than abandon the formulation.

## 3. Test candidate mechanisms in priority order

1. **A — risk-preserving state approximation.** Propose a representation retaining
   economic belief, remaining budget, release queue, deployment and enough
   risk-relevant history. Test the existing equal-posterior/different-risk example
   immediately. Derive separate value and worst-case risk errors; quantify memory
   and runtime. Do not assume a scalar risk budget is sufficient.
2. **B — risk-certified approximate optimization.** Separate candidate generation,
   full causal-null certification and any feasibility repair. Prove the repair's
   value cost and whether finding the candidate avoids the original hard problem.
   Distinguish evaluating a fixed policy from optimizing over policies.
3. **C — budget-parameterized structure.** Examine dominance bounds, branch and
   bound, restricted policy families and structural assumptions. Prove any error
   budget and classify complexity accurately as FPT, XP, pseudo-polynomial or an
   empirical speedup. Test any monotone-event restriction for its value loss.

   Current evidence: the registered promotion-dominance rule is safe but removes
   action columns rather than the shared pre-promotion information tree. Its
   measured pruning runs had the same builder-node and continuation-cache counts
   as the reference. Do not repeat that sweep on the same HMM cells; a new C
   candidate must compact pre-promotion histories and preserve the causal-null
   response information, including the posterior-alias counterexample.

For each candidate, preserve its formal assumptions, counterexamples, nearest
prior art, proof status and continue/narrow/stop decision in the ledger. Move to
implementation only for a candidate that survives the theorem and equivalence
screen; retain failed constructions where useful for reproduction.

**Gate:** a selected mechanism has explicit assumptions and nonvacuous proposed
risk/value/complexity bounds, with a proof or a sharply identified lemma and no
established decisive counterexample or complete source-matched equivalence.

## 4. Implement and validate against exact references

- Register a bounded development protocol before executing it: instances,
  parameters, metrics, resource limits, comparisons and any seed allocations.
- Implement the chosen method and adapters in new files. Preserve the exact solver
  and provide a way to independently evaluate returned policies.
- Test budget on every path, request-time charges, chronology and hidden pending
  labels, full-history null access, switching charges and continuation behavior.
  Include B=0, uninformative or terminally delayed labels, immediate/late
  promotion, reversal/rollback/re-promotion, risk boundaries and posterior aliasing.
- Compare with both exact solvers whenever available, robust FSC or constrained
  POMDP competitors where faithfully reproducible, and a source-matched sequential
  test plus delayed economic planner. Identify missing competitors as limitations.
- Record cost, absolute/relative oracle gap, worst-case null risk and certificate,
  maximum queries, controller/state size, nodes, runtime, peak memory, solver
  tolerances and assumptions. Independently reconstruct policy metrics and use
  exact-rational checks where tractable.

**Gate:** invariant tests pass; the risk guarantee is mathematically justified;
small-instance results match the exact oracle or satisfy a proved bound. Keep
numerical calibration separate from worst-case certification.

## 5. Scale, assess and decide

- Freeze a scaling protocol before runs across horizon, budget, delay, switching
  cost, risk level and regime persistence. Compare at matched information and
  constraints; log resource limits and failed runs. Keep development and any later
  confirmatory seeds distinct, and do not open reserved real-data holdouts.
- Verify theorem boundary cases and adversarial examples, and check observed
  scaling against predictions without inferring general complexity from a plot.
- Separate computational gains, economic gains and methodological novelty. Build
  a claim-to-proof-and-artifact map and assess source-matched alternatives.
- Deliver `SCALING_PROTOCOL.md`, `SCALING_RESULTS.md` and a final assessment only
  when supported by actual work; include the defensible continue, narrow, change
  approximation strategy or stop decision. Do not create empty placeholders.

## Checkpoint cadence and tools

Commit each completed checkpoint and push only the designated research branch.
Use Ponytail for implementation discipline, HKUSTDial skills for research and
source-grounded evaluation, and the installed ARIS skills when their workflows fit;
read the applicable skill before use. Tool availability does not authorize a
separate overnight schedule, remote computation or notification. Update the ledger
with the commit, checks, failures and next research decision at every checkpoint.

## Checkpoint: B=4 adaptive policy understood; no novelty claim

The completed audit uses the registered T=8, B=4, d=2
low-persistence cell as a diagnostic witness, not as confirmation evidence. The
full decomposed reference is cheaper than the best fixed calendar in two registered
cells, but all tested restricted policies and the finite calendar portfolio miss
that gain. The task is to identify the exact information-dependent decision that
creates the gap, then derive a compact rule with a theorem target before widening
the experiment grid.

### Step 1 — Close the policy-shape audit

- Independently reconstruct the saved reference policy from `t8_b4_policy_shape_v1.json`.
  Verify the full-history causal-null risk from saved behavior and trace its
  event-by-event query and first-promotion behavior. The optimizer-recorded
  alternative cost is cross-referenced to the registered calendar comparison;
  the risk verifier does not independently recompute post-promotion continuation.
- Resolve the apparent `1/8` versus `1/10` risk mismatch from the exact histories:
  it is a mixture of promotion after three positives and after four positives,
  with probabilities `3/5` and `2/5` at a released-label boundary. Preserve the
  failed first runner and its correction.
- Compare the resulting policy against explicit sequential-testing patterns:
  likelihood-ratio/futility boundaries, alpha spending, delayed group-sequential
  tests, and adaptive sensing. Credit any exact reduction to established methods.
- Deliver a source-grounded policy-shape note and an optimizer-free verifier.
  If the discrepancy is a bug, issue a separately versioned correction and retain
  the original output unchanged.

**Exit gate:** the verifier independently reproduces exact causal-null and IID
risk from saved policy behavior, and every structural claim is tied to histories
and action probabilities—not aggregate event counts. Record the economic-cost
verification scope separately. If the audit is inconsistent, stop mechanism design
until corrected.

**Outcome:** this gate passed. The exact adaptive branch is a finite randomized
sample-size/futility pattern with delayed feedback. Its source-matched prior-art
equivalence remains a serious objection, so it is retained as a baseline and does
not count as a candidate method or pass G1.

The branchwise monotonicity follow-up also passed: both deterministic components
are monotone on every potential-label tape, their exact robust risks are `1/8` and
`1/16`, and their `3/5`–`2/5` mixture reproduces the oracle cost and risk `1/10`.
This improves the verified synthetic comparator but remains oracle-extracted
standard sequential testing. It does not establish an efficient optimizer over
this class or a value bound against the unrestricted policy class.

### Step 2 — State one candidate theorem before coding

Use the audit to propose one history compression or allocation rule that captures
the adaptive timing gain while preserving the full causal-null information. Specify
the candidate's state, update rule, policy class, assumptions, exact risk certificate,
economic approximation bound, and runtime/memory dependence on `T`, `B`, delay,
state resolution and numerical precision. State the closest established theorem and
the precise missing lemma. Test the existing alternative-posterior/risk-alias example
against the proposed state immediately.

No scalar risk budget, root lottery, likelihood threshold, or finite-memory policy
is treated as a contribution by itself. The method must either provide a proved
nonvacuous value/risk/complexity guarantee or be clearly labeled conjectural with
one sharply isolated proof obligation. If a source-matched prior method already
provides the guarantee, record the equivalence and move to the next mathematically
justified candidate without changing the problem formulation.

**Exit gate:** a precise algorithm and theorem statement, a minimal instance where
it matters, and a source-level novelty delta survive counterexample and prior-art
checks. Otherwise record a no-go and select the next candidate in A/B/C order.

**Next candidate test:** Candidate B's hidden-root pricing belief must retain enough
state to evaluate each fixed active null response. The audit in
`CANDIDATE_B_PRICING_STATE_COUNTEREXAMPLE_V1.md` falsifies belief-only merging under
the unrestricted history-adaptive null. Continue only if a bounded response
automaton or a response-continuation quotient can be derived with a state bound
smaller than the learner sequence form. Otherwise close this pricing route and
advance to a structurally different Candidate C mechanism; do not implement a
belief-only pricing DP.

Candidate C's branchwise-monotone class now has an exact risk certificate on this
cell, but no approximation theorem or efficient policy-generation procedure. The
next G1 test is to identify a constructible subclass with a nonvacuous value bound
against the full two-law oracle. If the only route is enumerating arbitrary
deterministic plans or using standard group-sequential optimization, record the
equivalence and move on; do not call the oracle-extracted mixture the candidate.

### Step 3 — Register a bounded, paired development comparison

Only after Step 2 passes, register a new protocol and unique output paths. Start with
the two B=4 cells where the full reference beats calendars, then include matched
control cells from the existing six-cell grid. Compare under identical budgets,
delays, costs and risk level against the decomposed reference, best fixed calendar,
finite calendar portfolio, m=3 cap, and the strongest faithfully implementable
sequential-test or robust-controller baseline. Do not rerun completed screens or
expand to a factorial sweep without a theorem-driven reason.

Report exact worst-case null risk, alternative cost and oracle gap, maximum pathwise
queries, policy/controller size, builder nodes, runtime and memory. Independently
reconstruct candidate behavior and exact metrics wherever tractable. Register
development versus confirmation seeds through existing repository mechanisms; do
not use development outcomes as confirmation.

**Exit gate:** invariant and independent-verification checks pass, the candidate
meets its proved risk guarantee, and it improves on the strongest matched baseline
in at least one predeclared meaningful dimension without a disqualifying value loss.
Compute savings alone do not pass the methodological or efficacy gate.

### Step 4 — Apply the upstream research gates

G1 (novelty delta), G2 (mechanism and theory), and G3 (matched synthetic utility)
must pass in order. Until then, keep CRSP and all reserved real-data holdouts closed;
do not schedule or launch overnight/remote jobs or notifications as an implied part
of this plan. After G3, separately audit eligible real data for paired outcomes,
chronology, delay semantics, costs, provenance and licensing before requesting or
running any real-data evaluation. Freeze a distinct confirmation protocol before
confirmation data are touched. A failed gate is a recorded decision point, not a
reason to broaden the benchmark or publication scope.

### Overnight execution boundary

If this plan is later run unattended, the bounded unit is one preregistered sprint
at a time: execute only the registered checks, stop on a failed invariant, preserve
all partial logs and outputs, append a ledger entry, and leave the branch unmerged.
No new data access, confirmation-seed allocation, remote workload or automatic
notification is implied. Before any tool-driven workflow is described as active,
verify that Ponytail, HKUSTDial and ARIS are actually available in the environment
and follow their installed instructions; this plan does not claim an unavailable
integration has been installed or launched.

### Checkpoint: IID-relaxation candidate screened on synthetic cases

The Candidate B IID-relaxation / exact-null-verification pipeline was compared
against the five remaining cells in the frozen T=8 grid; the sixth had already
been run. Across all six, every returned policy exactly matches the robust
reference cost, has full causal-null risk at or below `1/10`, and has a rational
dual lower bound within roughly `1e-12` of its feasible upper cost. It beats the
best calendar and the cap/gate baselines in the registered low-persistence cells,
and ties calendars in controls. It does not improve on the exact robust reference.

On a preregistered T=10 stress cell, it also beats all 163 fixed calendars by
`0.03587776397` with a certified value interval about `1.52e-11` wide. A
branchwise verifier split the recovered policy's sole 3/5–2/5 lottery; both
deterministic promotion events were monotone over 1,024 tapes, with exact robust
branch risks `1/8` and `1/16`. This gives a direct finite-instance causal-null
certificate by monotone coupling.

The method is **not** a compute win: T=8 complete runtimes were about 9.4–10.4s
versus 5.1–5.4s for the robust reference. At T=10 it used fewer builder nodes
(10,813 versus 58,806) but took 114.84s versus 58.01s and had no measured memory
advantage. A reporting bug in the T=10 aggregate elapsed field is preserved and
corrected in `IID_RELAXATION_T10_STRESS_CORRECTION_V1.md`. A first branchwise
verifier attempt omitted post-promotion continuation; its failure is retained,
and the corrected verifier passes.

The source-matched audit now classifies relaxation, exact verification, dual
bounding and mixture repair as established generic ingredients. Candidate B
remains a useful generator and a-posteriori certificate, but it does not pass G1
or establish methodological novelty. The fixed synthetic grid shows economic
gains over restricted baselines, but no end-to-end computational advantage and
no pulled-real-data evaluation. G2 and the full G3 gate remain open; CRSP and
reserved real-data holdouts stay closed.

**Next decision:** stop tuning this standard pipeline as the lead method. The
posterior-only, continuation-grid, and belief-only pricing variants of Candidate A
already have explicit counterexamples or no-compute-gain results; do not repeat
them. Preserve those no-go records and move to a structurally distinct Candidate
C: seek a compact causal-null response-continuation quotient that retains pending
outcomes and exact public-history dependence. State an equivalence relation and
prove or bound its impact on both alternative cost and robust risk before coding;
test it against the existing posterior-alias and arbitrary signed-future-value
counterexamples. If the quotient has no bound smaller than the full learner
sequence form, record that result and move to a new mechanism rather than repeat
dominance, generic null cuts, or monotone-event screens. Preserve Candidate B as
the strongest current synthetic comparator. Real-data work starts only after the
novelty, mechanism/theory and matched-synthetic gates pass and the eligible-data
audit authorizes the particular task.

### Checkpoint: universal response-state quotient screened

The exact response-state quotient was tested before implementation. At a common
event, query count, deployment, empty pending queue and uninformative alternative
belief, the full-history causal null can still choose different next-query
probabilities for different public query-time transcripts. For `q` prior
requests among `T-2` events, this gives `binom(T-2,q)` pairwise distinguishable
histories and a uniform conditional-kernel approximation floor of `1/4` for any
strategy-independent quotient that merges a pair. The proof and its quantifiers
are recorded in `CANDIDATE_C_RESPONSE_QUOTIENT_LOWER_BOUND_V1.md`.

This closes only universal null-response-kernel quotienting; it is not a lower
bound against policy-specific risk/value approximation or implicit optimization.
Do not implement this quotient. Continue by identifying a policy-side or
implicit-optimization mechanism that preserves the unrestricted causal null,
then state its value/risk/runtime theorem and compare it with the full-history
oracle on a bounded synthetic case. The posterior-alias and signed-future-value
counterexamples remain mandatory checks. Preserve the synthetic/real-data gates;
no holdout is opened by this checkpoint.

### Active working plan: Candidate D model-match and bounded pilot

This section supersedes the prior “continue by identifying” instruction above:
Candidate D is the current next test. It is a scalarized one-sided POSG (OS-POSG)
solver with exact worst-case risk verification and two-policy multiplier-bracket
recovery. The recovery lemma is conditional and is not itself a novelty claim.
The universal response-kernel quotient no-go remains in force; it does not rule
out this policy-search route.

**Objective.** Determine whether finite-horizon OS-POSG value approximation can
produce a risk-bracketing pair with a certified cost gap and an end-to-end
resource advantage over the exact decomposed sequence-form oracle, while
preserving the original two-law information structure and unrestricted causal
null. Do not open real data or claim novelty during this test.

**Gate D1 — source and model match (documentation/proof only).** Before coding,
write a source-matched reduction covering: finite-horizon-to-discounted or
finite-horizon OS-POSG conversion; state augmentation for hidden root, HMM state,
pending-label queue/release times, remaining query budget, deployment, promotion,
and time; learner and null observations/actions at each event; bounded payoff
representing the scalarized objective; and strategy-gadget/perfect-recall
extraction. Map the precise assumptions of the cited HSVI theorem to this game.
The output must identify which side controls each transition and show that
first-promotion risk—not a different discounted or expected surrogate—is what
the scalarized payoff charges. Check both the posterior-alias and
signed-future-value counterexamples. If this reduction fails or only works by
restoring the full sequence-form tree, stop Candidate D and record why.

**D1 outcome (2026-10-29):** the exact model mapping passes, using two
microstages per event because the null responds after observing the learner's
request. Finite-horizon payoffs can be embedded into discounted OS-POSG rewards
by time-indexed rescaling and an absorbing terminal state. This is exact for
each fixed finite instance, but the rescaled reward range can worsen numerical
bounds, and the source theorem gives no useful complexity bound for this family.
The alias and signed-reversal counterexamples remain covered only if full
learner information and post-promotion alternative continuation are preserved.
See `CANDIDATE_D_MODEL_MATCH_AUDIT_V1.md`. D1 therefore does not by itself
authorize an efficacy sweep or imply a compute win.

**Gate D2 — theorem and prior-art audit.** Validate the finite-LP strong-duality
conditions, multiplier range, recovery inequality, and root-mixture risk bound
against the exact model. For approximate risk endpoints, require rigorous bounds
that establish the bracket; empirical estimates do not count. Compare the whole
solver-plus-recovery guarantee and complexity with the closest OS-POSG,
constrained-POMDP, robust-controller, and existing ShiftLab results. Treat the
method as established composition unless a precise source-level delta remains.
Do not proceed to an efficacy sweep if there is no plausible state/strategy
representation with a resource advantage.

**D2 outcome (2026-10-29):** finite-LP duality and the conditional risk-bracket
recovery argument survive model matching. Horák et al.'s OS-POSG HSVI, its
strategy extraction, constrained-POMDP optimization, and exact robust
verification are established prior art; this scalarization-plus-recovery
composition has no identified novelty delta. A bounded test remains worthwhile
only as an established-algorithm baseline because point-based belief search may
avoid the explicit learner tree on these finite models. The pinned Julia
implementation currently exposes value bounds but not the required learner
strategy gadget; a faithful adapter and independent controller verifier are
needed before any ShiftLab efficacy run. See
`CANDIDATE_D_IMPLEMENTATION_FEASIBILITY_V1.md`. Do not call Candidate D a novel
lead unless a new theorem or computational mechanism emerges beyond that source.
The public MIT Julia implementation's own suite completed with 53 passed and
1 failed: its 60-second solve on a 143-state game returned gap `33.75048`
instead of `<1`. This weakens the efficiency hypothesis but does not falsify
performance on the smaller finite-horizon switching game. Keep any pilot
strictly bounded and stop if the extracted strategy or exact verification erases
the measured gain.

**Gate D3 — preregistered pilot.** If D1–D2 survive, add a versioned protocol
before execution, with a fresh output path and source/config hashes. Use one
small instance where both exact oracles finish, then at most one matched stress
instance selected from already registered synthetic settings. Fix multiplier
search points, HSVI tolerances, stopping limits, random seeds, and peak-memory
measurement in advance. Compare end-to-end wall time, peak memory, solver nodes
or belief points, controller memory, scalarized gap, exact alternative cost,
and exact full-history causal-null risk. Include strategy extraction, endpoint
verification, multiplier search, and mixture recovery in resource totals. Retain
all failed runs. An independently implemented policy evaluator must check query
budget on every path, delayed-release chronology, null access to pending labels,
first-promotion risk, and post-promotion rollback/re-promotion economics.

**Gate D4 — decision.** Continue only if the recovered policy satisfies the
proved risk guarantee, its observed cost is within the preregistered certified
gap, and it demonstrates a meaningful end-to-end resource improvement against
the strongest matched baseline without a disqualifying value loss. A cheaper
scalarized subproblem that loses its advantage during strategy extraction or
exact verification is a no-go. If successful, expand only under a new frozen
synthetic scaling protocol and then revisit G1 (novelty), G2 (mechanism/theory),
and G3 (matched synthetic utility) in order. CRSP and reserved real-data
holdouts remain closed until all three gates pass; any later real-data use needs
its own eligible-data, provenance, chronology, licensing, and confirmation
protocol audit.

**Checkpoint discipline.** Keep all work in this branch/worktree. Record the
exact command, source/data/config hashes, checks, failures, and decision in the
append-only ledger. Commit and push completed checkpoints to the designated
branch only. Do not schedule a recurring, remote, or unattended job or send
notifications as part of this plan; any bounded local run must finish with
preserved logs and an explicit stop condition.

## Candidate D adapter checkpoint (2026-10-29)

The first D3 prerequisite passed on the frozen one-action-opponent toy: the
HSVI/gadget adapter attained the exact value 0.44 with a reported gap below
`1e-4`, residual below `1e-7`, and the expected signal-conditioned controller.
See `CANDIDATE_D_GADGET_ADAPTER_RESULTS_V1.md` and its append-only ledger row.
This is adapter validation only. It does not show a strategy-security guarantee
against an active opponent and does not establish a ShiftLab value or compute
advantage. No ShiftLab efficacy pilot or real-data run is authorized by this
result. The immediate next step is an adversarial toy plus independent maximin
controller evaluation; separately, D3 still needs a scalable, certifiable rule
for bracketing the optimal multiplier without relying on the exact benchmark LP.

The follow-on two-stage adversarial development toy now passes an independent
statewise maximin evaluation after either observation generated by the
opponent's first action. The extracted controller has five nodes, a solver gap
of `1.77e-7`, and maximum gadget residual `7.96e-8`; see
`CANDIDATE_D_SEQUENTIAL_ADVERSARIAL_GADGET_RESULTS_V1.md`. To retain opponent-
reachable observation branches, recursive extraction uses full-support
opponent action weights solely to choose the posterior used for gadget
tie-breaking. This small game does not qualify Candidate D for the ShiftLab
pilot. Proceed next with a source-faithful audit of the adapter against the
published strategy-extraction theorem, then decide whether a useful benchmark
conversion and multiplier-bracketing procedure can be implemented without
solving the exact reference problem.

The source audit and stronger end-to-end toy verifier are now recorded in
`CANDIDATE_D_EXTRACTION_THEOREM_AUDIT_V1.md`. A finite-horizon induction proves
the full-support reference-belief extension under componentwise gadget
feasibility, full legal-action support and complete recursive branch coverage;
this is a finite form of established max-justification, not a novelty claim.
The run checks every solved LP constraint and the full discounted two-stage
security value. The ShiftLab finite-horizon conversion, transformed numerical
error, multiplier recovery, and end-to-end baseline advantage remain open.

## Immediate execution plan: Candidate D T=2 compiler gate (2026-10-29)

This is the next bounded task under the mission above; it does not change the
research objective or authorize an overnight run. Work only in the isolated
research worktree and preserve the frozen T=2 protocol and all failed outputs.

1. **Confirm the starting state.** Record branch, commit, modified/untracked
   files, pinned Julia package commit, and whether any prior solver process is
   still running. Do not restart or overwrite an active run.
2. **Validate the compiled game.** Parse the already compiled T=2 OS-POSG with
   the pinned upstream Julia package. Capture stdout/stderr and exit status to a
   fresh ignored run directory. Check parser counts and the exact model hash
   against `CANDIDATE_D_OSPOSG_CONVERSION_T2_PROTOCOL_V1.md`.
3. **Run the frozen comparison once.** Solve the compiled game under the
   registered 30-second limit and compare its root interval to the independent
   scalarized sequence-form LP value. Pass only if the LP is optimal, the
   interval contains that value, and the interval width is at most `1e-4`.
   Preserve timing, tolerances, solver output and generated model unchanged.
4. **Stop or diagnose without moving the gate.** A parser/model mismatch,
   timeout, non-containing interval or excess width is a recorded no-go for
   this registered conversion. Preserve it first; any debugging changes must be
   versioned separately and cannot alter the frozen result or threshold.
5. **If T=2 passes, audit the remaining theorem steps.** Prove/verify reward
   scaling under discounting, hidden-root scalarization, bounded-payoff error,
   multiplier search and risk-bracket recovery, including exact endpoint risk
   certificates. Compare total computation, including extraction and exact
   verification, with both decomposed and full exact oracles where available.
6. **Only then prepare a ShiftLab pilot.** Register one small exact-solvable
   instance before running HSVI on it; preregister any single stress instance
   separately. Include independent policy reconstruction and all delayed-label,
   query-budget, null-information and post-promotion continuation invariants.
   Proceed only if a mathematically justified risk/value guarantee survives and
   end-to-end resources can plausibly beat the strongest matched baseline.
7. **Reassess the research gates in order.** G1 novelty delta, G2 mechanism and
   theory, then G3 matched synthetic utility. Candidate D currently has no
   identified novelty delta and remains an established-algorithm baseline
   unless new mathematics or a defensible computational mechanism appears.
   Keep real-data and reserved holdouts closed until all gates pass and the
   particular data source has a separate provenance/eligibility audit.

At every completed checkpoint, append results and decision to
`RESEARCH_LEDGER.md`, hash new outputs, run only relevant checks, and commit the
checkpoint on this branch. The active converter protocol is
`CANDIDATE_D_OSPOSG_CONVERSION_T2_PROTOCOL_V1.md`; its outputs belong under
`.aris/runs/candidate_d_osposg_conversion_t2/`. Verify Ponytail, HKUSTDial and
ARIS availability and their installed instructions before describing any of
them as part of the execution workflow. No scheduled automation, remote run,
notification, real-data access or merge is implied by this plan.

## Candidate D T=2 compiler checkpoint (2026-10-29)

The frozen v1 conversion test failed because its serializer omitted an explicit
zero reward required by the pinned package; preserve that v1 NO-GO and its model.
A separately registered v2 compiler now passes independent structural checks
for all 101 legal state/action triples. HSVI reports the exact scalarized
sequence-LP value `-1.0` with zero interval width after 18.16 seconds. The Julia
harness exited after convergence because its final print expression used
unexported helper names; this post-solve reporting defect is retained and the
captured final solver row establishes the v2 interval. See the v1/v2 protocol
and result records for hashes and limitations.

**Next gate:** do not expand to T=6 yet. First close the model-level theory and
output gap: prove the finite-game reward scaling and error correspondence for
the actual `gamma=0.9`, inspect whether the upstream Recorder's stored bounds
are sufficient to recover the required strategy gadget, and map a certified
multiplier bracket to exact worst-case risks without using the exact oracle to
select policies. If strategy extraction, endpoint certification, and the full
policy evaluator cannot be independently implemented, stop Candidate D as an
established value-computation baseline. If they can, preregister one exact-
solvable ShiftLab pilot before any HSVI solve and measure all extraction and
verification costs against the decomposed/full oracles and Candidate B. Real
data remain gated on G1–G3.

## Candidate D T=2 extraction checkpoint (2026-10-29)

The extraction/gadget adapter now passes an exact-rational T=2 check: it
reconstructs a four-node, no-query/never-promote policy with cost `1`, causal
null risk `0`, and scalarized value `1`, matching the exact lambda-one LP.
Local gadget residual is `4.45e-16`. This validates only extraction and
verification plumbing; it is not an economic or computational improvement.
The next possible test is a preregistered fixed multiplier set with an exact
constrained-oracle audit of risk bracketing and the multiplier-location
condition. If that does not produce a useful policy pair, stop Candidate D and
resume the remaining candidate search. See
`CANDIDATE_D_T2_EXTRACTION_RESULTS_V1.md`.

## Candidate D recovery decision (2026-10-29)

The preregistered T=2 multiplier pair brackets alpha and its root mixture exactly
matches the constrained sequence-form optimum (`124/125`, risk upper bound
`1/10`). This is a useful correctness check. It is not a promising lead: the
only conditional cost bound uses multiplier width `0.99`, end-to-end HSVI
solve/extraction takes `28.092s` versus `0.00538s` for the exact LP, and the
composition has no novelty delta. Stop Candidate D as a lead while retaining
its converter, extractor and verifier as comparators. The next step is to state
and discriminate a new policy-side or implicit-search mechanism against the
known posterior-alias and signed-future-value counterexamples before coding.
See `CANDIDATE_D_T2_RECOVERY_RESULTS_V1.md` and the append-only ledger.

## E-process maximum-wealth boundary screen (2026-10-29)

The preregistered threshold-eight screen on the six exposed `T=6` development
cells passed exact null-risk, alternative-cost and root-mixture verification,
but did not improve the lead. It ties the exact oracle and strongest calendar
on two cells while threshold four is cheaper; on two other cells it loses to
threshold four, calendar and oracle; the final two remain no-query ties. Its
state counts are unchanged and runtime is 0.010–0.045 seconds. Stop all
threshold-only variants. Preserve the protocol and result as a comparator, and
resume with a mathematically distinct policy-side or implicit-search mechanism
that addresses the known aliasing and signed-future-value counterexamples.
G1–G3 remain open and real data/holdouts stay closed.

## Candidate E safe-history pruning checkpoint (2026-10-29)

Forcing a safe incumbent continuation at selected pre-promotion public histories
has a simple conditional guarantee: it can only remove first-promotion paths,
and if every feasible policy reaches the selected set with alternative
probability at most `epsilon`, exact restricted optimization loses at most
`L*T*epsilon`. The T=10 feasibility screen did not find enough pruning under
small explicit loss budgets: its best reduction was 4.10% of pre-promotion
realization columns at a 0.05 cost bound, below the registered 5% continue gate.
The exact likelihood-envelope pass itself traversed 10,813 alternative nodes,
matching Candidate B's builder count. RAO* risk-based branch pruning and POMDP
hypothesis-pruning loss bounds also cover the generic ingredients. Candidate E
is closed without implementation or novelty claim. Next, search for a mechanism
that reduces optimization work before/during tree construction; keep the full
causal-null model and all data gates unchanged. See its theorem note, protocol,
runner and exact feasibility output.

## Candidate F adaptive delayed betting gate audit (2026-10-29)

A predictable stake can be attached to each query and applied on ordered label
release. Under the conditional causal-null mean bound and fixed feedback delay,
the capital process is a nonnegative supermartingale and its threshold has a
Ville risk guarantee. The proof does not solve the unrestricted two-law economic
optimization. Recent anytime-valid testing work already gives wealth/time
Bellman control and a complete class of predictable affine betting processes;
controlled sensing with costs is also established. The proposed ShiftLab planner
would be a direct composition without a cost-loss or resource theorem, so do not
implement it as the lead. Continue searching for a candidate that reduces
optimization complexity and has a defensible value guarantee. See
`CANDIDATE_F_ADAPTIVE_BET_GATE_AUDIT_V1.md`.

## Candidate G exact IID-belief compression screen (2026-10-29)

An exact rational hidden-root belief graph for the IID relaxation reproduced all
4,867 public-history states on the registered T=10 case; it did not merge any
histories. The screen took 0.340 seconds and generated 4,866 transitions, but
failed the preregistered 50% compression gate. Stop exact belief-state compression.
A separate idea—Lagrangian backward induction over the same graph instead of the
13,420-variable LP—may still reduce solve time, but it is the standard constrained
POMDP dynamic-programming reduction. Audit its exact source equivalence before
implementation and do not claim novelty without a remaining theorem or resource
advantage. See the Candidate G protocol and result.

## Active execution plan after Candidate G (2026-10-29)

This section is the current run order and supersedes earlier “next step” notes
that predate the E–G screens. The governing objective and preservation rules in
`RESEARCH_BRIEF.md` remain unchanged. The branch is still in discovery: no
candidate has passed G1 (novelty), G2 (theorem/mechanism), or G3 (matched
synthetic utility). The existing IID-relaxation result is a useful synthetic
comparison, not a qualifying contribution. Keep all real-data work, reserved
holdouts, confirmation seeds, remote jobs and notifications closed.

### Work package 1 — close the Candidate G Bellman-DP question

1. Compare the proposed scalarized Bellman recurrence, state, terminal rewards,
   policy recovery and dual bound line by line against the existing IID
   relaxation and primary constrained-POMDP sources. Include request-time budget
   charges, label release order, hidden root mode, pending outcomes, first
   promotion, post-promotion alternative continuation and exact full-null
   verification in the reduction.
2. Record whether the reduction is exactly standard constrained-POMDP
   Lagrangian DP. If so, close it as an established-algorithm comparator unless
   a concrete, source-supported end-to-end resource advantage remains after
   policy extraction, exact risk verification and safety repair. Do not build a
   DP merely because its recurrence is available.
3. If such an engineering comparison is justified, register one bounded
   development protocol first: same T=10/B=4/d=2 instance, fixed multiplier
   grid, same cost/risk metrics, a 60-second local CPU cap per solve, and exact
   checks against the existing IID LP and full causal-null verifier. No new
   seeds or broader sweep. This can establish a baseline implementation
   comparison, not novelty by itself.

**Exit:** commit an exact reduction/equivalence note and a continue/close
decision. A standard-equivalence finding closes this search branch and does not
count as a setback to the overarching formulation.

### Work package 2 — identify a structurally different optimization mechanism

Resume from the demonstrated bottleneck: methods that first traverse essentially
the same public-history tree (E and G) do not reduce construction effort enough;
the IID root-belief graph also has no state compression. Candidate D remains a
comparator, while F’s betting gate and ordinary sequential tests lack an
unrestricted economic approximation theorem. Search for a compact
representation or implicit optimization method that reduces work before or
during tree/LP construction while retaining the causal null’s access to pending
outcomes.

For each new idea, write a one-page candidate card before coding. It must specify:

- the exact policy class and a constructive policy-generation algorithm;
- a state/response representation and bound on its size relative to the
  sequence-form reference;
- exact or bounded worst-case causal-null risk, not risk under the alternative
  or IID surrogate alone;
- a nonvacuous economic loss bound against the unrestricted two-law optimum;
- runtime and memory including preprocessing, pricing, extraction, verification
  and repair;
- the closest primary theorem/source and an explicit reduction attempt;
- a minimal counterexample test covering posterior aliasing, signed future
  continuation value, hidden pending outcomes, and rollback/re-promotion.

Do not rerun closed screens with parameter tweaks. Record each failed candidate
with its counterexample or measured bottleneck. A plausible but uncertain
prior-art match remains `UNRESOLVED — EXACT REDUCTION REQUIRED` until the
reduction is attempted.

**G1 gate:** continue only if the source audit leaves a precise algorithmic,
theoretical or end-to-end computational delta. A familiar ingredient is neither
an automatic rejection nor a novelty claim.

### Work package 3 — theory before implementation

For the first surviving candidate, write and audit the full theorem statement:
assumptions; nonanticipating hard-budget policy class; alternative expected
cost; full-history causal-null promotion event; risk guarantee; economic value
gap; complexity in T, B, delay, resolution/model size and precision; and all
failure conditions. Prove the smallest instance and boundary cases first. State
the unresolved lemma narrowly enough that a counterexample or proof attempt can
settle it. Use exact rational arithmetic wherever the finite model permits.

**G2 gate:** no implementation beyond a minimal proof-checking prototype until
the guarantee is proved or one sharply isolated conditional lemma remains, and
all known counterexamples have been tested. A conjecture may motivate a bounded
diagnostic, but its output remains exploratory and cannot be called a guarantee.

### Work package 4 — registered synthetic test and strongest baselines

Only after G1 and G2, register a paired development protocol on the smallest
exactly solvable instances where the candidate predicts an advantage. Compare
against the decomposed and full exact references when available, the best fixed
calendar, the strongest adaptive/sequential baseline, Candidate B’s IID
relaxation plus exact verifier, and any faithfully implementable robust-FSC or
constrained-POMDP comparator. Match the pathwise query budget, delay, costs and
risk level. Include controls and known counterexamples; freeze metrics and
resource limits before execution.

Report alternative cost and oracle gap, exact worst-case causal-null risk and
certificate, maximum pathwise queries, policy size, construction nodes, wall
time, peak memory, and extraction/verification/repair costs. Independently
reconstruct returned policies. Use development results only to decide whether
to register a separate confirmation protocol; do not relabel them as
confirmation.

**G3 gate:** the candidate must satisfy its proved risk/value statement and
beat the strongest matched baseline on a preregistered meaningful utility or
complexity criterion without unacceptable loss on controls. Compute savings
alone are insufficient if they do not support the methodological claim.

### Work package 5 — real-data eligibility, only after G3

After a synthetic pass, select a source only if its chronology, point-in-time
features, paired outcomes, label availability, utility/cost definition,
provenance and licensing support the switching estimand. Keep reserved holdouts
closed until a separate protocol is frozen and handled under the existing
repository process. If observational data cannot identify causal promotion
risk, use them only for the explicitly supported economic component and do not
claim real-world null-risk validation.

### Tool and checkpoint discipline

The isolated toolkit is already present in this worktree: Ponytail for focused
implementation/review habits, HKUSTDial Supervisor-Skills for research
evaluation and evidence-grounded writing, and ARIS for experiment/review
orchestration. Before applying a skill, read its installed instructions and
record the exact workflow used. These tools support this plan; they do not
authorize scheduled overnight loops, cloud/remote compute, paid jobs,
notifications, publication or external data access. Keep runs local and bounded
unless the user separately requests a specific action.

At every checkpoint, append the hypothesis, protocol, exact command, commit,
artifact hashes, checks, proof status, negative evidence and next decision to
`RESEARCH_LEDGER.md`. Use a unique output path; preserve prior failures and
historical artifacts. Commit each completed checkpoint to this branch and push
only the designated branch. Never merge automatically.

## Candidate H finite-response-automaton pricing audit (2026-10-30)

For each fixed active null response, a finite deterministic transducer lets the
pricing Bellman recursion preserve public-history dependence exactly. This
resolves the known belief-only aliasing example, but gives no uniform state-size
advantage: transducer size can grow with the response history tree, and distinct
public observations can still induce distinct pricing beliefs. The recurrence
is standard constrained-POMDP policy-column generation; the old cut-generation
screen had no end-to-end gain and did not retain response vectors for a
retrospective automaton-size count. Close this route as a lead; do not rerun
those cells to recover missing artifacts. Exact assumptions, conditional
theorem, complexity boundary, counterexample and sources are in
`CANDIDATE_H_AUTOMATON_PRICING_AUDIT_V1.md`.

**Next:** search for a structurally different optimization method whose
complexity reduction is accompanied by a nonvacuous value and full causal-null
risk guarantee. Do not replace the full history with another generic controller
state absent an explicit bound. G1–G3 remain open; real data and reserved
holdouts remain closed.
