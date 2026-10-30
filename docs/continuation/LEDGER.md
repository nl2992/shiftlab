# Continuation ledger / mandate-coverage table

Branch `claude/bold-cray-xcy73f`. Legacy `/goal` exit condition: UNMET (unchanged). Sprint verdict: `NO_DEFENSIBLE_METHOD_YET`.

| # | Item | Status | Evidence |
|---|---|---|---|
| 1 | Repo hygiene | DONE | 15 tests pass; ruff/format/mypy clean |
| 2 | Prior-art matrix | PARTIAL: PPRM + Hsu-Shekhar verified from LaTeX; 2605.28533, active RCPS, Einbinder 2025 still open | prior_art_reduction_matrix.md |
| 3 | Faithful baselines (PR, PPRM-style) | PENDING | |
| 4 | Tolerance-matched Brier-null comparison | PENDING | |
| 5 | Decision on H2c contribution | PENDING (provisional: composition) | |
| 6 | Direction-B kill test | PENDING (only if 5 open) | |
| 7 | Tighter valid finite-horizon threshold | PENDING | |
| 8 | Dependence (H3b/H3c) | PENDING | |
| 9 | Delay (outcome-dependent, >=5000 seeds) | PENDING | |
| 10 | Nominal-risk uncertainty | PENDING | |
| 11 | Remaining candidates | PENDING | |
| 12 | Frozen confirmation G7/G8 | PENDING (protocol first) | |
| 13 | Q2/Q3 | PENDING | |
| 14 | Real data | PENDING; NYC TLC `BLOCKED_EXTERNAL_ACCESS` | |
| 15 | Final report | PENDING | |

## Log
- 2026-10-30 it.1: items 1-2 partial done; ledger created.
- it.2: LaTeX sources read for PPRM and Hsu-Shekhar; matrix addendum 1. Next: pull 2605.28533 src, find active-RCPS id, then start item 3.
