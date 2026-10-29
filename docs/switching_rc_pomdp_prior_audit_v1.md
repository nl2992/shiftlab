# Recursive constraints and the switching-risk memory gap

**Date:** 2026-10-29. **Status:** primary-source audit and candidate rejection; no algorithm or novelty claim.

## What the closest recursive-constraint method establishes

Ho et al., *Recursively-Constrained Partially Observable Markov Decision Processes* (UAI 2024), start from a standard C-POMDP: expected reward is optimized subject to expected cumulative costs under one POMDP model. A global expected-cost constraint can violate Bellman's principle because a branch may overspend locally while low-cost branches compensate it at the initial belief. Their RC-POMDP changes the problem by imposing a history-dependent cumulative-cost bound at every reachable history. It augments belief with the remaining admissible cost, proves deterministic optimality and Bellman recursion, and gives ARCS with soundness and epsilon-optimality if the algorithm terminates. The paper states ARCS is incomplete and may fail to terminate.

This closes a proposed generic contribution of “add a remaining risk budget to the belief state to restore dynamic programming.” The history-dependent budget augmentation and recursive-constraint principle are established. Khonji et al.'s constant-horizon C/CC-POMDP FPTAS also covers a fixed single-kernel reward/constraint problem, but it assumes the horizon is constant and does not supply a polynomial-in-horizon result for this task. Robust finite-memory policy gradients for hidden-model POMDPs optimize a worst-case objective over a finite model set, but use local policy-gradient search and do not give the separate known-alternative objective plus causal-null reachability constraint used here.

## Contract mismatch that remains

ShiftLab's finite objective is

\[
\min_\pi \;\mathbb E_{P_{\rm alt}}[C(\pi)]
\quad\text{subject to}\quad
\sup_{\nu\in\mathcal N_{\rm causal}}\Pr_\nu\{\text{ever promote}\}\leq\alpha,
\]

with a hard request-time query cap and delayed labels. The alternative HMM determines economic value; the null's conditional response is selected adversarially after each full event history, including pending outcomes hidden from the learner. The generic two-law sequence-form LP already represents this contract exactly, but its tree can grow exponentially.

RC-POMDP's remaining-cost state is updated along the agent's belief history under one fixed transition/observation model. A direct transfer would need to allocate risk across causal-null histories that Nature sees but the policy cannot distinguish while a label is pending, and then tie the same policy to a different alternative-HMM objective. Giving the controller Nature's hidden history would change its information; averaging the two laws would change the null event. The source does not establish a compact state or an approximation bound for these obligations. This is a precise limitation of that reduction, not evidence that the residual is novel.

The existing exact alias counterexample shows why the alternative posterior alone is insufficient. A scalar risk budget can encode history if its update is allowed to retain arbitrary information, so it is not a compression theorem without a proved finite representation and a bound against the full-history oracle. The current candidate therefore fails its next G2 gate.

## Decision and next gate

Do not implement a generic RC-POMDP wrapper, a scalar risk-budget planner, or a finite-memory controller on this basis; do not launch an efficacy sweep. The next admissible theory question is narrower: under the current delayed information structure, can causal-null risk allocation be represented by a sub-exponential policy-sufficient state while preserving the shared-policy alternative utility and the exact global false-promotion constraint? Require either a construction with a value bound or a growing-family lower bound before code. If the sufficient state has exponential size or its guarantee is only within a restricted controller class, close G1 for this route and change the research hypothesis.

Current-regime evidence remains separate from the false-promotion constraint: old likelihood-ratio wealth does not certify benefit after a reversal. Any later algorithm needs distinct promotion-risk and current-value states, with rollback evaluated under post-reversal evidence and its delay cost.

## Sources

- Ho et al., [*Recursively-Constrained Partially Observable Markov Decision Processes*](https://proceedings.mlr.press/v244/ho24a.html), UAI 2024. Full primary PDF downloaded from the PMLR record and inspected through Sections 2–5, Proposition 2, Theorems 1–4 and ARCS; source hash is in `switching_source_manifest_v24.json`.
- Khonji et al., [*Approximability of Constant-horizon Constrained POMDP*](https://ijcai.org/proceedings/2019/775), IJCAI 2019; detailed primary-source audit is recorded in `switching_source_manifest_v23.json` and `switching_belief_compression_candidate_audit_v1.md`.
- [*Robust Finite-Memory Policy Gradients for Hidden-Model POMDPs*](https://ijcai.org/proceedings/2025/947), IJCAI 2025. Its model-set worst-case objective and local FSC optimization are a nearby baseline, not the two-law constrained objective above.
