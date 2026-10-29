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

## Immediate next sprint: explain and capture the B=4 adaptive gain

The next sprint is intentionally narrow. It uses the registered T=8, B=4, d=2
low-persistence cell as a diagnostic witness, not as confirmation evidence. The
full decomposed reference is cheaper than the best fixed calendar in two registered
cells, but all tested restricted policies and the finite calendar portfolio miss
that gain. The task is to identify the exact information-dependent decision that
creates the gap, then derive a compact rule with a theorem target before widening
the experiment grid.

### Step 1 — Close the policy-shape audit

- Independently reconstruct the saved reference policy from `t8_b4_policy_shape_v1.json`.
  Check its exact alternative cost and full-history causal-null risk, plus its
  event-by-event query, promotion, rollback and re-promotion behavior.
- Resolve the audit's apparent mismatch between the grouped action probabilities
  and the reported exact risk `1/10`. Trace the implementation's information key,
  action semantics and risk recursion; do not infer the policy structure from
  marginal summaries alone. Preserve the failed first runner and its correction.
- Compare the resulting policy against explicit sequential-testing patterns:
  likelihood-ratio/futility boundaries, alpha spending, delayed group-sequential
  tests, and adaptive sensing. Credit any exact reduction to established methods.
- Deliver a source-grounded policy-shape note and an optimizer-free verifier.
  If the discrepancy is a bug, issue a separately versioned correction and retain
  the original output unchanged.

**Exit gate:** the verifier independently reproduces the reference policy's exact
metrics, and every claimed structural feature is tied to histories and action
probabilities—not just aggregate event counts. If the audit is inconsistent, stop
mechanism design until corrected.

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
