# Research Contract: Paper 4 continuation — certified optimisation under full-history causal-null risk

ARIS template: `.aris/upstream/templates/RESEARCH_CONTRACT_TEMPLATE.md`. This file is the session-recovery entry point.
Read it first, then `NEXT_ACTION.md`, `TASK_LEDGER.md` and `THEOREM_REGISTRY.md`.

## Selected Idea

- **Description**: Determine whether ShiftLab supports a fourth contribution. The original two-law problem is fixed:
  minimise alternative-HMM cost subject to full-history causal-null first-promotion risk at most alpha, with a hard
  pathwise query budget, delayed labels, private randomisation and reversible deployment. Three avenues run in
  parallel: (B) learner-side implicit optimisation, (C) the causal-safety premium Gamma = V*_causal - V*_IID, and
  (D) fallback directions.
- **Source**: user directive of 2026-11-10 ("Autonomous Paper 4 research command"). Prior branch state is `8e9366a7`.
- **Selection rationale**: the FCG and antitone-frontier verifier are closed as prior art (`docs/paper4/`). The
  bottleneck is the learner tree, so B is the primary algorithmic question. C is theory-first, and the data already
  shows Gamma > 0 on reversal cells.

## Core Claims (to be established or refuted — none assumed)

1. B: an implicit learner-side optimiser with exact causal safety and a global bound, using less than the full tree.
2. C: primitive-model conditions for Gamma = 0, and a growing family with Gamma > 0 and an explicit lower bound.
3. Scope: two-state HMM alternatives, fixed delay, binary labels.

## Method Summary

The exact references are `FirstPromotionDecomposedGame.solve()` and FCG / FCG-fast (`src/shiftlab/paper4/`).
V*_IID is the IID-only LP optimum, which is FCG iteration 0. V*_causal is the FCG final value, certified to within
4e-14. The theory uses exact rational small-instance computation as a hypothesis generator, followed by proof attempts
and counterexample search.

## Experiment Design

- **Datasets**: synthetic two-state HMM cells only. No real data or holdouts until a method passes.
- **Baselines**: exact decomposed reference, a belief-cached reference, IID+verify, IID+repair, FCG-fast,
  never-promote and calendars. External CPOMDP, FSC and POSG solvers are documented if incompatible.
- **Metrics**: exact risk, exact cost, certified [L, U], wall time split, peak RSS, cuts and iterations.
- **Compute budget**: local CPU only (macOS arm64). No cloud or GPU spend.

## Reviewer infrastructure (verified 2026-11-10)

ARIS review, proof, novelty and claim skills default to a Codex/GPT backend. There is no `.aris/reviewer.json`; the
Claude-host default is Codex MCP, which is not available, and the `claude-review` MCP is not available either.
External cross-family reviews are therefore **BLOCKED** (see `BLOCKERS.md`). Reviews run as fresh-context native
subagents with `review_independence: same-family` and `acceptance_status: provisional`, per the ARIS assurance rule.
HKUSTDial skills (deep-research, idea-evaluator, vibe-research-workflow, tech-paper-template,
pre-submission-reviewer) are invoked natively.

## Key Decisions

- Model routing: Opus plans and verifies; Sonnet/Haiku subagents build. Every built result is re-verified by the lead.
- Push the branch after every completed, verified piece.
- Timing campaigns run only when no other agents are using the CPU.

## Status

See `TASK_LEDGER.md`. Final status lives in `FINAL_DECISION.md`.
