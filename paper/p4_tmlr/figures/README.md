# Paper 4 TMLR figures

Style: `style.py`, following the figures4papers conventions (github.com/ChenLiu-1996/figures4papers,
`scientific-figure-making/references/api.md`): its palette, blue = RB-DP, red = baselines, grey/neutral = reference,
top/right spines off, frameless legends, sans-serif, PDF with embedded TrueType fonts, PNG at 300 dpi. Re-implemented,
no code copied. The user chose figures4papers for this paper on 2026-11-21, in place of the PaperBanana default in
`AGENTS.md`.

Regenerate from this folder: `../../../.venv/bin/python <script>.py`. Each script asserts its values against the
paper's tables before saving.

| Figure | Script | Data source | Checks |
|---|---|---|---|
| 1 split | `fig_split.py` | none (conceptual: feasible (w0, w1) under the i.i.d. and adaptive constraints) | n/a |
| 2 premium | `fig_premium.py` | `docs/paper4_continuation/rbdp/results/e2e3_fast_cells.jsonl` (kind E3, e = 1/10, n_beta = 401; 223 cells) | seven Table 2 values to 6e-5 |
| 3 real | `fig_real.py` | (a) `rbdp/real_data/results/phase7_baselines_T16_32/settings.jsonl`; (b) `rbdp/real_data/results/phase9_replay.jsonl` | 35 chains, 31 violated by P3/P4/P5, maxima 4/4/8, safe policies ≤ α; 9,525 windows; pooled means equal Table 4 to 1e-3 |

Notes
- Fig. 3(b) recomputes the window bootstrap (2,000 resamples, seed 20261119). Its intervals match Table 4 to within
  0.006 (the bootstrap draws differ from the original run); means match exactly.
- Fig. 3(b) omits P4c (mean 15.83), which is off the scale; the caption says so.
- Fig. 2 merges end labels of curves that end within 0.01 of each other (e.g. "B=3,6").
