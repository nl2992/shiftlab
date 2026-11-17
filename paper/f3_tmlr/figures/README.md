# F3 TMLR figures

Style: `style.py` (figures4papers house style re-implemented: blue = shield, red = baselines, top/right spines off,
frameless legends, Helvetica/Arial fallback DejaVu, PDF with embedded TrueType fonts, PNG 300 dpi).
Regenerate any figure from the worktree root:

    PYTHONPATH=src OPENBLAS_NUM_THREADS=1 .venv/bin/python paper/f3_tmlr/figures/<script>.py

| Figure | Script | Output | Data source |
|---|---|---|---|
| mechanism | `fig_mechanism.py` | `fig_mechanism.{pdf,png,tex}` | computed by running `RiskBudgetShield(AlwaysChallenger(), R=20, delta=0.0)` and `StopLossPlugin(AlwaysChallenger(), 20)` through `run_policy` on a hand-built tape (T=60, d=5, k=3, Z=+1 for 10 rounds then -1); harm from `metrics.harm_path`; shield bound from the shield's `_I(t)` read after each act (read-only wrapper); pending count from `RunRecord.q/release_t` (asserted equal to the shield's `P`). Deterministic, no seeds. |
| regime_map | `fig_regime_map.py` | `fig_regime_map.{pdf,png,tex}` | `results/riskbudget/exposure_ratio_test.json` rows; bin medians recomputed and asserted equal to the file's `summary.bins`. |
| violations | `fig_violations.py` | `fig_violations.{pdf,png,tex}` | (a) `confirm_summary.json` C3 (five comparators), C1 `f3_pi1_R20`, C2 `f3v2d_R20`, per-regime rates; stress regimes from `configs/paper3/regimes_f3_v1.json`. (b) raw `outputs/paper3/riskbudget/real/<condition>/*.json`, counts of `sup_harm > 24` pooled over 14 streams (4,600 runs per arm). Arms: wald_cut, cusum_rb_h8, stoploss_h14, f3_pi1_h14, f3v2d_h14. |
| cost_tail | `fig_cost_tail.py` | `fig_cost_tail.{pdf,png,tex}` | `confirm_summary.json` `descriptive` (J, sup_q99) for all 18 arms. |

Notes and limits
- Real-stream counts match `real_tables.md` (clean: Wald 475, stop-loss 311, CUSUM rollback 517 at R=24).
- "CUSUM rollback" is `cusum_rb_h8` (as in the paper's C3 set); `cusum_rb_h4` is not plotted in fig. violations.
- Fig. cost_tail uses q99 of sup-harm pooled over all regimes and seeds, taken from the summary (not recomputed).
- In fig. mechanism the "verified bound" is the shield's invariant functional I_t (delta = 0, so no confidence width); the in-transit reserve is shown as the pending count P_t in panel (b), not as a separate band in panel (a).
- Calibrated comparators (calib_summary.json) are not used; all figures use the registered, tuned comparators.
