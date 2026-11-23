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
- In fig. mechanism the dotted "shield's check" is the shield's internal functional `_I(t)` after round t (the quantity that W_t in Section 3 compares with R ; delta = 0, so no confidence width); the in-transit reserve is shown as the pending count P_t in panel (b), not as a separate band in panel (a).
- Calibrated comparators (calib_summary.json) are not used; all figures use the registered, tuned comparators.

## Added 2026-11-22 (schematic and process figures, in the style of the figures4papers "miscellaneous" set)

`schematic.py` holds the drawing helpers (tinted rounded boxes, dashed claim banners, flow arrows, panel letters, inset
data panels), all matplotlib in inch coordinates.

| Figure | Script | Content | Data |
|---|---|---|---|
| overview (Fig. 1) | `fig_overview.py` | (a) decision problem timeline with delayed labels and fees, (b) the shield's check W_t as a stacked bar, (c) worst-regime exceedance per arm | (c) from `results/riskbudget/confirm_summary.json`, asserted against `tables/numbers.tex` |
| pipeline (Sec. 5) | `fig_pipeline.py` | four evaluation stages and what each shows | every count read from `tables/numbers.tex` and `tables/screen_numbers.tex` |

Also changed in this round: Fig. 2 (violations) condition order matches Table 9, larger labels, rotated counts dropped; Fig. 3
(cost tail) labels de-overlapped, y-axis truncation stated in the caption; Fig. 4 (regime map) threshold labels moved above
the band. `fig_violations.py` and `exposure_ratio_test.py` honour `real_streams.EXCLUDED`.

## Update 2026-11-23: hand-assembled composites (the figures4papers "miscellaneous" approach)

`fig_overview` and `fig_pipeline` are no longer drawn in matplotlib. The illustrated scenes (characters, cards, zoom wedge, block arrows, text) were generated with Codex native image generation from the briefs `assets_raw/overview_prompt.txt` and `assets_raw/pipeline_prompt.txt` (outputs `overview_gen1.png`, `pipeline_gen1.png`), checked by eye for text errors, and the data panels drawn in Python (`fig_panels.py`: exceedance bars, 30 regime tiles, stop-loss margin line, 12 per-stream bars, 100 stream dots; all read from the result files) are pasted into reserved areas by `compose_composites.py`. The earlier matplotlib versions are kept as `old_matplotlib_*.py`. The Gemini PaperBanana route needs `GEMINI_API_KEY`, which is not set.


## 2026-11-23 (later): decluttering pass
Main-text figures now carry one message each; full-detail versions are appendix figures (`*_full`).
- `fig_mechanism`: two harm curves, budget line, two numbered callouts (frame `assets_raw/mechanism_gen2.png`, prompt `mechanism_prompt2.txt`); data in `mech_data.py`; `fig_mechanism_full.py` keeps the check line, labels in transit and deployed bars.
- `fig_violations`: strip plot (one dot per regime) plus real-stream percentages; `fig_violations_full.py` keeps the heatmap and five-arm counts (data in `viol_data.py`).
- `fig_cost_tail`: R=20 panel only; `fig_cost_tail_full.py` keeps R=12 (ablations) and R=30.
- `fig_regime_map`: bin medians plus paced IQR; `fig_regime_map_full.py` keeps every point.
