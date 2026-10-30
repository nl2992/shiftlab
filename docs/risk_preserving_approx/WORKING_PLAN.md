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
