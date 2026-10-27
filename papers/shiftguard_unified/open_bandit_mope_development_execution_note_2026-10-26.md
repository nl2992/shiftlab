# OBD MOPE development replay execution note — 2026-10-26

The frozen protocol in `open_bandit_mope_development_protocol_v1.md` was first attempted using the pinned author implementation. The initial replay did not finish: `wealth_lb_gd` performs a convex optimization for each event, making a full eventwise pass over the position-1 evaluation stream impractical in this environment. That process was stopped before it produced a summary or output directory.

**Initial attempt status:** incomplete; that attempt produced no policy-value result, MOPE path, comparison, or confirmation. The source data and acquisition manifest were not modified. The attempt itself supplies no evidence.

This does not invalidate the completed synthetic MOPE comparison in `mope_obd_applicability_audit.md` and `opi_mope_matched_results_v1.md`. That comparison is the usable MOPE benchmark result for the current decision gate. The OBD estimator development results in `open_bandit_ope_development_results.md` remain point-estimation diagnostics and do not become sequential evidence by this attempt.

The full working-tree test run completed afterward with 1,552 passed, 1 skipped, and 0 failures. Configured Ruff and Mypy checks passed. These software checks did not resolve the initial computational limitation.

## Completed follow-up with exact optimizer

The follow-up preserves the pinned MOPE confidence-sequence recursion, the
official 10,000-point grid, the seven-day data split, and the frozen item
policy. It replaces only the per-event CVXPY solution of a two-dimensional
concave quadratic program with exact enumeration of its stationary point,
edge optima, and polygon vertices. On 250 randomized QPs the maximum objective
difference from the pinned CVXPY reference was `1.48e-13`; the maximum
coordinate difference was `8.32e-7`. Four complete 75-event confidence paths
matched exactly. On the actual OBD stream, the original CVXPY implementation
and exact optimizer also produced identical lower and upper paths through the
first 1,000 evaluation events, including the first empty set at event 866.

The full run completed on CPU in 190.9 seconds for 274,737 position-1
evaluation records. Its aggregate output is independently reconstructed and
verified by `scripts/verify_open_bandit_mope_development.py`; the passing QP
and path validation is stored in
`outputs/shiftguard_unified/sota_reproductions/mope_fast_solver_validation_v2/`.
The result remains exploratory retrospective development, not a guarantee or
confirmation: OBD's IID/dependence, slate, feature-availability, and
click-release assumptions remain unresolved. See
`outputs/shiftguard_unified/real_data_development/open_bandit_mope_v1/` and
`papers/shiftguard_unified/real_data_development_results.md`.


**Current-worktree verifier rerun (2026-10-26):** `uv run --no-sync python scripts/verify_open_bandit_mope_development.py` independently reconstructed the complete 274,737-event path, candidate, metrics, and output hashes. It confirmed item 41, first empty set at event 866, no promotion, and matching recorded artifact hashes. The verifier now supplies identity/no-op import shims only when optional Numba, CVXPY, or tqdm packages are absent; its run replaces the QP solver with the separately validated exact optimizer and uses the pinned recursion, so none of those optional packages is invoked. The default environment can therefore reproduce the audit without modifying `uv.lock`.
