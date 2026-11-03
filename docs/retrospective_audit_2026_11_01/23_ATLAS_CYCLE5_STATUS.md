# Atlas cycle 5 located — 2026-11-01

The study exists in ignored local `shift-research-starter/outputs/failure_atlas_v1_cycle5/`: exact_cov/results.json plus its summary, family3/archive.jsonl/state.json/summary.md and analogous family4 outputs. It must not be described as never executed because outputs are absent from Git.

`python -B scripts/retrospective_audit/audit_atlas_cycle5.py` exits 0. The exact_cov aggregate has 144 cells, zero skipped, declared 5,000 seeds per cell, source commit 9a6c63ecd0b98975296573a002f0c4d4afa3c079. CoV, RC, best_safe gap, risk monotonicity and registered majority decision agree with the aggregate's own values within 1e-9. RC>CoV in 0/144 cells: the registered majority rule does not reopen the small-horizon attribution on that criterion. No extrapolation to T1000 follows.

This is aggregate arithmetic verification, not an independent LP solve, raw seed replay, solver certificate review, or complete protocol-coverage review. Neither source code parity nor dirty-run provenance has been resolved. Family 3/4 outputs exist but their contents and declared predictions are not yet independently reconciled. The local family3 report itself lists hard-budget pacing as missing in one limitation while listing it among loaded baselines: a current-scope contradiction candidate requiring implementation/output inspection, not an established omission.

Exact source hash and meta are saved in ATLAS_CYCLE5_ARITHMETIC.json. W09 and G09 remain incomplete. Reviewer: lead INTERNAL_ONLY.
