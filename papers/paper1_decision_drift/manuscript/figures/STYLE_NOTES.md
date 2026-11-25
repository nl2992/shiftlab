# Paper 1 figure style (from the ten figures4papers "Miscellaneous" examples, read 2026-11-23)

Examples studied (github.com/ChenLiu-1996/figures4papers, assets/): VIGIL_teaser, RNAGenScape_schematic and _teaser,
Dispersion_motivation, _observation, _observation_distillation, ImmunoStruct_schematic, _contrastive, _results_IEDB, _results_CEDAR.

What they do, and where we use it
1. Draw the domain objects (robots, scales, document cards, medals, spheres, manifold surfaces): `glyphs.py` robot / scales / doc / purse.
2. Contrast = the same scene twice, only the cause changes; grey dashed = blocked, X / check marks as outcome: `compose_teaser.py`, `compose_pacing2.py`.
3. Semantic colour system, constant across panels: deployed orange, reference blue, label coin gold, paired cost green, uniform red, gated (ours) blue, harm dark red.
4. Takeaway as structure: dashed grey "problem" banner + blue "fix" banner; full-width block-arrow banner; pale rounded note; curly brace + note.
5. Bold annotation drawn on the data ("detectable", "alarm at event N", "equal detection"), direct end-of-line labels, ours bold in legends and baselines pale.
6. Formulas in stacked coloured boxes under a curly brace, changed terms in magenta: `compose_growth2.py`.
7. Uneven mosaic panels (a large scene above small data panels): `compose_pacing2.py`.
Each figure uses a different composition on purpose: teaser = banners + scene twice; growth = formula stack + bars; pacing = scene twice + mosaic; map = heatmap with frontier + direct-labelled lines.

Build: Python writes SVG via `svgkit.py` (copied from the Paper 4 figures), Chrome headless exports PDF/PNG; Python-made plots are inlined as vector SVG.
All plotted values come from the repository's replay code or `outputs/r7_sweep` and are asserted in the scripts. PaperBanana was unavailable.
Superseded: fig_overview1, fig_growth, fig_growth_c, fig_pacing, fig_pacing_c, fig_map, fig_map_c, fig_overview (earlier templates).
