# Working plan: risk-preserving approximation for sequential switching

**Mission:** develop a computationally useful approximation to the existing two-law,
finite-horizon switching oracle, with an economic value bound and a worst-case
causal-null promotion-risk guarantee. The governing scope is `RESEARCH_BRIEF.md`.
**Current state (2026-10-29):** reference anchors and exact-risk checks are
reproduced. Several candidate mechanisms have been falsified as main methods or
remain unresolved: query caps lose to the stronger calendar baseline; simple
belief grids lack tractable state counts and a closed transfer proof; generic
null-cut and dominance pruning do not reduce the pre-promotion tree; policy-column
generation still lacks a compact pricing oracle. No candidate has yet established
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
