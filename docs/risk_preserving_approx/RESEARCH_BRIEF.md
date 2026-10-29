# SHIFT LAB — NEW METHODOLOGICAL RESEARCH BRANCH

## Mission: Risk-Preserving Approximation for Budget-Constrained Sequential Switching

You are acting as a senior ML theory researcher, optimization researcher and research software engineer.

Repository: `https://github.com/nl2992/shiftlab`

**Primary goal:** Develop a genuinely novel, computationally tractable algorithm for approximating the optimal acquisition-and-switching policy under a hard observation budget, delayed feedback, and an adversarial false-promotion risk constraint.

This is an ICML-level methodological research program, not a benchmark paper, systems paper, or exercise in combining existing algorithms.

Your job is to investigate the mathematical structure already uncovered in ShiftLab, identify an actual missing theoretical or algorithmic result, derive a candidate solution, implement it, and test it against the strongest applicable alternatives.

Do not abandon the current research formulation without a rigorous mathematical reason.

Do not label an algorithm novel merely because its ingredients appear in a new application.

Equally importantly, do not prematurely reject an algorithm merely because it uses familiar ingredients.

The object of novelty is the **algorithm, theorem, computational advantage or irreducible mathematical guarantee**, not necessarily every component individually.

---

# PHASE 0 — ISOLATE THE RESEARCH BRANCH

Before conducting research, inspect the Git state.

Fetch the latest remote branches and identify the current `origin/main` SHA.

Create a separate branch named:

`research/risk-preserving-switching-approx-2026-10-29`

Prefer a completely separate Git worktree:

```bash
git fetch origin
git rev-parse origin/main

git worktree add \
  -b research/risk-preserving-switching-approx-2026-10-29 \
  ../shiftlab-risk-approx-2026-10-29 \
  origin/main
```

If the requested branch or worktree already exists, inspect it and continue safely when appropriate. Otherwise choose a new unique suffix. Do not overwrite an existing branch or worktree.

Conduct all implementation, research documentation, simulation and commits in this new worktree.

## Non-negotiable preservation rules

1. Never rewrite, delete, truncate, regenerate or silently replace historical ShiftLab research results.
2. Never alter historical experiment protocols, frozen seed registries, confirmation artifacts, output hashes or previous no-go verdicts to make a new method appear successful.
3. Never force-push, hard-reset or clean another worktree.
4. Do not cherry-pick speculative experiments into `main`.
5. Do not automatically merge this branch.
6. Do not open any reserved real-data holdouts.
7. Preserve all existing mathematical counterexamples, exact certificates, empirical failures, source audits and reproducibility records.
8. Maintain clear provenance for every newly generated artifact.
9. If a historical artifact contains an error, create a separately versioned correction with evidence. Preserve the original and document the discrepancy.
10. Do not alter existing source code when an independent implementation or adapter would suffice.

The purpose of this branch is **additive methodological research**, not replacing the historical project.

Commit the initial research plan and a manifest recording the base SHA and preserved reference artifacts.

---

# PHASE 1 — RECONSTRUCT THE EXISTING MATHEMATICAL PROBLEM

Read the relevant existing work before inventing a mechanism.

At minimum, inspect:

- `docs/budgeted_switching_research_goals.md`
- `docs/switching_problem_v1.md`
- `docs/switching_first_promotion_decomposition_v1.md`
- `docs/switching_first_promotion_scaling_protocol_v1.md`
- `docs/switching_causal_game_results_v1.md`
- `docs/switching_reversal_lp_certificate_v1.md`
- `docs/switching_lagrangian_posg_reduction_v1.md`
- `docs/switching_two_law_game_duality_v1.md`
- `docs/switching_alt_belief_risk_alias_counterexample_v1.md`
- `docs/switching_finite_memory_approximation_prior_audit_v1.md`
- `docs/switching_paired_copy_compact_screen_v1.md`
- `docs/switching_robust_fsc_reduction_audit_v1.md`
- `docs/switching_novelty_delta_v1.md`
- `src/shiftlab/dive/causal_switching_game.py`
- `src/shiftlab/dive/first_promotion_decomposition.py`
- Relevant tests, including `tests/test_first_promotion_decomposition.py`

Read related files as necessary. Do not assume an existing claim is validated merely because it appears in a research note.

## Mathematical contract

Retain the existing finite-horizon switching formulation.

The learner chooses acquisition decisions and which model to deploy, while respecting:

- Pathwise observation budget `B`, charged when queries are requested.
- Delayed revelation of queried outcomes.
- Acquisition costs.
- Deployment and switching costs.
- A nonanticipating learner information filtration.
- A known working alternative model for economic-value calculations.
- A potentially history-adaptive causal null, with access to pending outcomes unavailable to the learner.
- Global control of the probability of ever promoting the challenger.

The constrained problem is

\[
V^*(T,B,\alpha)
=
\inf_{\pi\in\Pi_B}
C_{\mathrm{alt}}(\pi)
\]

subject to

\[
R_{\mathrm{null}}(\pi)
=
\sup_{\nu\in\mathcal N}
P_\nu(\tau_{\mathrm{first\ promotion}}\le T)
\le\alpha.
\]

Here, `Π_B` contains nonanticipating policies satisfying the hard query budget on every realization.

The false-promotion risk is an event probability under the entire causal-null family, not an average risk computed solely under the alternative HMM.

Preserve the important distinction:

**A historically valid first-promotion decision does not certify the challenger's current profitability following a regime reversal.**

Rollback and re-promotion are economically relevant continuation decisions, even though the original any-promotion risk event is already determined.

Do not simplify this distinction away.

---

# PHASE 2 — START FROM THE EXISTING EXACT SOLVER

ShiftLab already contains an exact first-promotion decomposition.

This is the principal starting point.

The decomposition separates:

1. A robust risk-constrained pre-promotion problem.
2. A post-promotion delayed-HMM continuation problem under the working alternative model.

The existing implementation uses exact belief-state dynamic programming for continuation and a sequence-form optimization for the risk-constrained pre-promotion component.

## Existing reference results

For `T=6`, `B=3`, `d=1`:

- Full solver: 15,693 learner realization variables.
- Decomposed solver: 705 learner realization variables.
- Full builder: 21,733 nodes.
- Decomposed builder: 1,799 nodes.
- Exact recovered cost: `461083/160000`.
- Exact worst-case promotion risk: `1/10`.

At `T=7`, the exact solvers also agree on the optimal value.

At `T=8`, the full reference builder exceeds its registered 200,000-node cap, while the decomposed solver finishes with 5,700 builder nodes.

Do not claim independent full-oracle optimality certification at `T=8`, since the generic reference did not finish there.

These results are reference anchors, not your claimed novelty.

## Critical observation

The exact decomposition makes the problem smaller but does not eliminate exponential growth in the query budget.

It is polynomial in horizon under fixed-budget assumptions of the existing history enumeration, but that is not a uniform polynomial-time or fixed-parameter tractability result.

The objective of this branch is to determine whether additional structure can yield a substantially more efficient algorithm while preserving rigorous risk and value guarantees.

---

# PHASE 3 — FORMULATE THE CENTRAL RESEARCH QUESTION

The working question is:

**Can we construct a compact, computationally tractable approximation to the optimal two-law switching policy, with explicit guarantees on both economic optimality loss and worst-case causal-null promotion risk?**

An ideal result would construct a policy `π̂` satisfying

\[
R_{\mathrm{null}}(\widehat\pi)\le\alpha
\]

and

\[
C_{\mathrm{alt}}(\widehat\pi)-V^*
\le\varepsilon_V,
\]

with a demonstrable computational advantage over the generic sequence-form reference and the strongest applicable existing algorithms.

Alternative formulations may permit a rigorously certified risk slack,

\[
R_{\mathrm{null}}(\widehat\pi)
\le\alpha+\varepsilon_R,
\]

but risk approximation error must be explicit and justified.

Prefer exact safety whenever feasible, for example by combining approximation with a conservative risk certificate or safety mechanism.

Do not confuse empirical risk calibration with a mathematical worst-case certificate.

Your first deliverable is a written theorem specification containing:

1. Exact assumptions.
2. The policy class.
3. The optimization target.
4. The statistical risk criterion.
5. An economic approximation guarantee.
6. A runtime or memory complexity bound.
7. The closest established theorem.
8. The precise technical obstacle not covered by that theorem.
9. A minimal instance in which the proposed result matters.

If no compelling theorem shape can be identified, report that before investing in a large implementation.

---

# PHASE 4 — INVESTIGATE THREE SPECIFIC ALGORITHMIC DIRECTIONS

These are candidate directions, not predetermined successful contributions.

Investigate them in priority order, while allowing a better mechanism to emerge from the analysis.

## Candidate A: Risk-Preserving Belief-State Approximation

The first hypothesis is that the economic belief state can be approximated without losing the information required to control causal-null promotion risk.

The challenge is that the alternative-HMM posterior is not generally sufficient for the robust risk-constrained problem.

Existing ShiftLab counterexamples explicitly demonstrate this.

Develop a candidate state representation incorporating, as necessary:

- Approximate economic posterior.
- Remaining query budget.
- Pending feedback and release timing.
- Relevant deployment state.
- Accumulated risk evidence or a risk certificate.
- Information required by the adversarial null.

Do not assume that appending a scalar risk budget automatically creates a sufficient state.

Investigate whether finite-memory aggregation, quantization, state abstraction or a finite-state controller can produce a usable guarantee of the form

\[
0\le
C_{\mathrm{alt}}(\widehat\pi)-V^*
\le f(T,B,d,\delta)
\]

and

\[
R_{\mathrm{null}}(\widehat\pi)
\le\alpha+g(T,B,d,\delta),
\]

where `δ` is a defined approximation parameter.

Both functions must be derived and meaningful.

A numerical upper bound that exceeds the maximum possible cost or a risk guarantee exceeding one is not useful.

Compare specifically against Kara–Yüksel finite-memory POMDP approximation and robust finite-state-controller synthesis.

The contribution cannot simply be belief truncation plus standard POMDP planning.

## Candidate B: Risk-Certified Approximate Policy Optimization

Investigate whether approximate optimization and exact or conservative risk verification can be separated.

For example:

1. Generate a candidate acquisition-and-switching controller using an approximate economic planner.
2. Compute or upper-bound its worst-case promotion risk under the full causal-null family.
3. Modify or reject unsafe decisions using a mathematically justified feasibility-preserving procedure.
4. Bound the economic loss introduced by the restriction.

The difficult question is whether this can avoid solving the original exponentially large optimization problem.

A generic post-hoc risk check is not novel.

An interesting result would be a risk-certificate-guided optimization algorithm with:

- A provable worst-case feasibility guarantee.
- A quantified value bound.
- Better computational scaling.
- A clear distinction from existing constrained-POMDP, robust-control and chance-constrained-planning methods.

Examine whether a compact certificate can be updated recursively without storing the entire learner history.

Be particularly careful about the difference between verifying a fixed controller and finding an approximately optimal controller.

Those are not equivalent problems.

## Candidate C: Budget-Parameterized Structural Approximation

Investigate whether the hard query cap creates exploitable structure.

The existing exact solver has complexity exponential in `B`.

Do not assume this dependence is unavoidable without a lower bound.

Explore whether useful assumptions about regime transitions, observation informativeness, risk structure or switching costs permit:

- Improved parameter dependence.
- Approximation schemes with explicit value and risk bounds.
- Dominance pruning with a proven error budget.
- Certified upper and lower bounds for partial optimization.
- A practical policy family that approaches the unrestricted oracle.

Potential results might include a parameterized approximation theorem, a certified branch-and-bound algorithm, or a structural restriction that is provably approximately optimal.

Distinguish carefully between fixed-parameter tractability, XP algorithms, pseudo-polynomial algorithms and empirical speedups.

Do not claim an FPT result if the exponent of `T` depends on `B`.

---

# PHASE 5 — AUDIT THE STRONGEST PRIOR ART

Conduct a focused, source-level novelty audit.

The objective is not to accumulate references or produce another extensive literature inventory.

For each candidate, determine whether a published algorithm or theorem already achieves essentially the same guarantee under comparable assumptions.

At minimum, assess relevant results on:

- One-sided partially observed stochastic games.
- Constrained and robust POMDPs.
- Finite-state-controller optimization.
- Robust optimal stopping.
- Approximate dynamic programming.
- Risk-constrained reinforcement learning.
- Partial-observation belief compression.
- Chance-constrained planning.
- Sequential experimental design.
- Anytime-valid sequential testing.
- Delayed-feedback control.
- Parameterized algorithms and approximation schemes for finite stochastic games.

Start from the source audits already in the repository. Verify important mathematical statements using primary papers rather than relying on summaries.

## Revised novelty-rejection standard

Do **not** reject a candidate merely because its implementation includes standard components.

Reject its novelty claim when one of the following is established:

1. The complete proposed guarantee follows directly from existing results.
2. A source-matched existing algorithm achieves the same result under comparable assumptions.
3. The claimed structural advantage is mathematically false.
4. A decisive counterexample invalidates the proposed theorem.
5. The resulting method offers no defensible theoretical or algorithmic distinction from existing techniques.

If the issue is merely that a result *might* follow from standard methods, mark it:

`UNRESOLVED — EXACT REDUCTION REQUIRED`

Then attempt the reduction.

Do not treat absence of a published result as proof of novelty either.

For each serious candidate, build a comparison table identifying:

- Our theorem or proposed theorem.
- The closest existing result.
- Assumptions shared by both.
- Assumptions that differ.
- Whether the difference is technically essential.
- Whether the existing proof can be adapted.
- What additional lemma or construction our method requires.
- Status: proved equivalent, proved distinct, unresolved, or falsified.

The goal is mathematical discrimination, not optimistic novelty claims or reflexive rejection.

---

# PHASE 6 — IMPLEMENT ONLY AFTER THE THEORY IS SPECIFIED

Once a candidate survives the initial theorem and prior-art screens, implement it in new files.

Suggested locations:

```text
src/shiftlab/dive/risk_preserving_approx.py
scripts/research_risk_approx/
tests/test_risk_preserving_approx.py
docs/risk_preserving_approx/
outputs/risk_preserving_approx/
```

Use names that reflect the actual selected mechanism.

Do not modify the original exact reference solver unless necessary to correct a demonstrated defect, and never silently change its semantics.

Create adapters to compare the new method with existing references.

## Mandatory invariants

Every returned policy must respect:

- Query budget on every sample path.
- Query costs at request time.
- Nonanticipating action decisions.
- Correct release timing.
- Null-adversary access to the required hidden history.
- Appropriate treatment of pending outcomes.
- Switching-cost accounting.
- The distinction between promotion validity and future economic value.

Write automated property tests for these invariants.

Test edge cases including:

- `B=0`.
- No informative observations.
- All labels delayed past the terminal horizon.
- Immediate and late promotion.
- Promotion followed by reversal and rollback.
- Re-promotion after rollback.
- Boundary risk levels.
- Distinct learner histories that share an economic posterior but have different risk implications.

The last case is especially important because it has already invalidated simplistic compression arguments.

---

# PHASE 7 — EXACT-ORACLE AND STRONG-BASELINE EVALUATION

Before examining larger simulations, evaluate the proposed method on small instances where exact references are available.

Use the existing exact solver as the ground truth whenever it completes.

## Required comparisons

1. Full sequence-form oracle.
2. Exact first-promotion decomposed oracle.
3. The new approximation algorithm.
4. Appropriate robust finite-state-controller or constrained-POMDP competitors.
5. A source-matched sequential-test plus delayed economic-planner composition.
6. Relevant naive or ablated versions, clearly identified as diagnostic rather than principal baselines.

If a strong published competitor cannot be implemented faithfully, document the limitation. Do not declare superiority over an unimplemented method.

## Required metrics

Record:

- Expected economic cost.
- Absolute and relative optimality gap.
- Worst-case causal-null promotion risk.
- Risk certificate or certified upper bound.
- Maximum pathwise queries.
- Number of state variables and stored controller states.
- Builder/search nodes.
- Runtime.
- Peak memory.
- Numerical solver tolerances.
- Proof assumptions satisfied by each experiment.

Use independently reconstructed policy metrics and exact-rational checks where tractable.

The existing exact results must continue to reproduce.

The algorithm should be evaluated across varying horizon, budget, label delay, switching cost, risk level and regime persistence.

Do not tune on the final confirmation seeds.

Register experimental parameters and seed allocations before executing a new confirmatory grid.

---

# PHASE 8 — SCALING AND THEOREM VALIDATION

After verifying exact small-instance agreement or bounded approximation error, test scalability.

Distinguish:

**Computational improvement:** fewer nodes, less memory or shorter execution time.

**Statistical improvement:** lower economic cost at comparable risk and budget.

**Methodological contribution:** a new algorithm with a defensible property or theorem beyond applicable prior work.

A computational improvement alone is useful, but does not automatically satisfy the project's ICML objective.

## Theorem validation

For every proposed theorem:

1. State the result precisely.
2. Give a complete proof or identify the exact unresolved lemma.
3. Check boundary cases.
4. Construct adversarial or counterexample instances.
5. Test whether numerical experiments agree with the predicted scaling.
6. Determine if the result survives comparison with existing theory.
7. Classify each statement as PROVED, CONDITIONAL, SKETCHED, CONJECTURED or FALSIFIED.

Do not label a proof complete while a material step remains conjectural.

Do not infer a general complexity rate from a small finite scaling plot.

Whenever possible, include an independent verifier for mathematical certificates.

---

# PHASE 9 — PRESERVE EVERY RESULT, INCLUDING FAILURES

Maintain an append-only research ledger inside the new branch.

Suggested document:

`docs/risk_preserving_approx/RESEARCH_LEDGER.md`

For every research iteration, record:

- Date and commit.
- Candidate hypothesis.
- Exact novelty claim being tested.
- Closest applicable prior art.
- Proof progress.
- Implemented code.
- Tests executed.
- Registered experiment parameters.
- Result paths and hashes.
- Successful findings.
- Negative findings.
- Remaining uncertainty.
- Decision and justification.

If a candidate fails, preserve its implementation, minimal counterexample and failure explanation where useful for reproducibility.

Do not overwrite results with a better-looking rerun.

Preserve the seed registry. Allocate new unique development and confirmation blocks using existing repository mechanisms.

Any external dataset must retain the relevant provenance, permissions and timestamp assumptions.

Do not open historical holdouts or treat development results as independent confirmation.

---

# PHASE 10 — CONCRETE DELIVERABLES

Work toward the following branch-local artifacts:

```text
docs/risk_preserving_approx/
    BASELINE_MANIFEST.md
    PROBLEM_AND_THEOREM_TARGET.md
    PRIOR_ART_EQUIVALENCE_AUDIT.md
    ALGORITHM_DESIGN.md
    THEORY_AND_PROOFS.md
    EXACT_ORACLE_COMPARISON.md
    SCALING_PROTOCOL.md
    SCALING_RESULTS.md
    RESEARCH_LEDGER.md
    FINAL_RESEARCH_ASSESSMENT.md
```

Create only documents justified by actual work; do not fill the directory with speculative placeholders.

Implement tested research code and experiment runners as the investigation warrants.

Each completed research checkpoint should be committed separately with a meaningful message.

Push only the designated research branch when remote access and permissions allow it.

Do not merge into `main` without explicit user authorization.

## Final assessment format

At the end of the current research session, report:

### 1. Research outcome
- Novel algorithm established?
- New theorem established?
- Existing theorem equivalence?
- Unresolved technical gap?
- Negative or inconclusive result?

### 2. Mathematical contribution
Give the exact theorem statement, assumptions and proof status.

### 3. Algorithmic contribution
Describe the procedure, its computational complexity and its distinction from established alternatives.

### 4. Empirical evidence
Report exact-oracle gaps, risk validity, computational scaling and strongest-comparator results.

### 5. Preservation verification
Confirm the historical reference results remain intact, identify the base SHA, and provide any relevant hashes or regression-test results.

### 6. Next research decision
Give a defensible recommendation: continue, narrow, change approximation strategy or stop a particular hypothesis.

Do not predict ICML acceptance.

Do not present an ordinary composition as a new method.

Do not convert this research into a benchmark paper just because methodological results are difficult to obtain.

---

# PRIORITY AND AUTONOMY

Begin immediately.

Do not spend the first iteration writing a manuscript.

Prioritize the following sequence:

**First:** Preserve the baseline and establish the mathematical theorem targets.

**Second:** Audit the strongest prior art and test the precise equivalence objections.

**Third:** Construct or falsify a candidate risk-preserving approximation mechanism.

**Fourth:** Implement the candidate and independently validate it against exact oracles.

**Fifth:** Test scaling and economic performance with matched constraints.

**Finally:** Report the strongest defensible methodological result, including failures and unresolved questions.

Work autonomously within this isolated branch. Make engineering and research decisions using the existing repository context, and document them.

If a candidate fails, retain the evidence and investigate the next mathematically justified candidate within this same research program.

Do not pivot to unrelated problems, new datasets, trading strategies, benchmark competitions or alternative publication objectives merely because an initial algorithm fails.

**Central objective: Find a provably useful, computationally efficient, risk-preserving approximation algorithm for ShiftLab's existing two-law switching problem, while leaving every prior result reproducible and scientifically intact.**