# Failure Atlas v2, FLQ/QCE line (parallel record)

Two independent Failure Atlas v2 executions were run on 2026-11-03 from the same starting point
(merge commit `96d053b`). Both are kept; neither overwrites the other.

| line | code | docs | repair | final verdict |
|---|---|---|---|---|
| RMM/LRMD | `scripts/failure_atlas_v2/` | `docs/failure_atlas_v2_*.md`, `docs/failure_atlas_v2_results/` | restart-mixture label-clock e-detector (RMM attachable, LRMD standalone) | registered synthetic criteria met for RMM; claim review "partial"; no real-data advantage |
| FLQ/QCE (this folder) | `scripts/failure_atlas_v2_flq/` | `docs/failure_atlas_v2_flq/` | front-loaded acquisition + query-conditional evidence (FLQ), QSG | final audit: numbers reproduce, not SOTA; gains come with failing rho=.8 dependence safety |

This line was developed on branch `claude/dazzling-wilbur-a3e951` (head `f81fbd8`) and moved
here unchanged except for path rewrites (`scripts/failure_atlas_v2/` ->
`scripts/failure_atlas_v2_flq/`, `docs/failure_atlas_v2/` -> `docs/failure_atlas_v2_flq/results/`,
its protocol -> `protocol.md`). Its raw outputs, like the RMM line's, live under the git-ignored
`outputs/failure_atlas_v2/`; the two lines used different seed bases and run directories.

The two lines agree on the main finding: error-controlled certificate methods are
over-conservative under a label budget, and the faster fixes (front-loading, label-clock or
query-conditional evidence) buy speed partly by losing false-promotion control under Markov
dependence.

Shared-code change from this line: the DISCERN-style PrPl-EB CS in
`scripts/promising_directions/sota/competitors/certificate_stops.py` restores the `/4` in
`psi_E` (Waudby-Smith & Ramdas). The RMM/LRMD runs predate this fix; see the correction note in
[../failure_atlas_v2_report.md](../failure_atlas_v2_report.md).
