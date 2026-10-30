# Baseline and branch manifest

- Setup date: 2026-10-29 (America/New_York).
- Repository: https://github.com/nl2992/shiftlab
- Source: origin/research/rpoq-s1-fatal-flaw-audit, fetched during setup.
- Starting SHA: 0b1ce996431763d50b8c22e21dd3eece7c2dcf04.
- Research branch: research/shiftlab-sota-synthetic-search-2026-10-29.
- Independent worktree: C:/Users/nigel/OneDrive/桌面/ICML/shiftlab-sota-synthetic-search-2026-10-29.
- Governing specification: GOAL.md, copied verbatim from the user attachment.
- The user's new branch-specific specification supersedes older scope restrictions where they conflict; scientific validity and provenance safeguards still apply.
- Historical tracked outputs are inventoried by Git object ID in HISTORICAL_OUTPUTS_TREE.txt. Setup verified `git diff --exit-code HEAD -- outputs` passed. All pre-existing tracked files are unchanged by setup.
- main, the RPOQ source ref, and the risk-preserving approximation branch were not changed. The new branch has no upstream to avoid pushing to the source branch accidentally.

## Execution safeguards

Synthetic data only. No CRSP, WRDS, Binance, downloaded benchmarks, real-data holdouts, or protected confirmation data. Preserve historical results, protocols, negative records, and verdicts. Separate development, validation, and final confirmation worlds. Record every attempted configuration, failures included. Verify provenance before reproduction or validity claims.

Before experiments, configure and enforce explicit CPU-time, memory, storage, and run-count limits. No expensive sweep is authorized by an unbounded default. Start with infrastructure inspection and CPU-sized smoke runs. No experiments or CI checks have been run during this setup.

## Completion criteria

Execute the complete GOAL.md programme: matched baseline reproduction, synthetic search and tuning, initial confirmation, mandatory full-archive failure synthesis, no more than three targeted repairs, cross-parent ablations, independent held-out generator validation, theory/novelty assessment, two leaderboards, and frozen real-data handoff. Report an unsuccessful search precisely; discovery is an objective, not a guaranteed result.
