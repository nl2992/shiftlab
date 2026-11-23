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
| 3 real | `fig_real.py` | (a) `rbdp/real_data/results/phase7_baselines_T16_32/settings.jsonl` + `phase10_baselines/settings.jsonl` + `phase10c_baselines/settings.jsonl`; (b) `rbdp/real_data/results/phase9_replay.jsonl` | 44 chains (= len(make_tables.ORDER) = tally), 40 violated by P3/P4/P5, maxima 4/8/8, all read from `phase10c_baselines/tally.json`, safe policies ≤ α; 9,525 windows; pooled means equal Table 4 to 1e-3 |
| overview (Fig. 1) | `compose_overview.py` (+ `overview_assets.py`, `svgkit.py`) | (a) schematic, except the label strip, which is the rollout's real labels; (b) schematic; (c) value of information C0 - W(t=1, beta, n=3, w), adaptive and i.i.d., from the lattice solver via `lattice_data.py` (same cell as Fig. 3: T=6, B=3), plus one policy rollout; (d) `real_data/results/phase10c_baselines/tally.json` (key `new` = 44 chains: max_ratio, iid_break_datasets, dearer/cheaper/tie, settings) | gap iid >= adaptive everywhere; rollout makes T rounds and B queries; P3-P5 > alpha, P1/P2/P6/P7 <= alpha, dearer = 0, chains = len(make_tables.ORDER); needs `PYTHONPATH=src` |
| lattice (Fig. 3) | `fig_lattice.py` | computed live (via `lattice_data.py`) by `src/shiftlab/paper4/risk_budget_dp_fast.py` (`lattice_exact=True`, T=6, B=3, transitions 19/20, e=1/50, alpha=1/10, n_beta=401), i.i.d. and adaptive modes, n=1,2,3 at t=1, beta_1=1/2 | every kink lies on {k/2^n}; N=80; same C0 in both modes. Needs `PYTHONPATH=src` |
| screen (Fig. 5) | `compose_screen.py` | `rbdp/real_data/LEDGER_PHASE10.md` (every count is parsed from the Counts block at build time; currently 84 screened: 9 positive, 1 excluded (Frisian), 21 null, 8 short, 31 fit rejected, 13 unavailable, 1 duplicate), `REAL_CHAINS.md` (white-noise control 2/24 vs 13/150), `paper/p4_tmlr/make_tables.py` ORDER + `attempts*.jsonl` (44 supporting: 23/5/4/12), baseline settings files (3,696 = 44x12x7 records), `phase9_replay.jsonl` (9,525 windows) | all asserted in the script. Nothing is hard-coded: the totals come from the ledger and `make_tables.ORDER`, so the figure updates with the ledger and fails loudly if the files disagree |

Notes
- Figure numbers above are in order of appearance in the paper. `fig_lattice.py`, `compose_overview.py` and `compose_screen.py` import from `src` / `make_tables.py`; run with `PYTHONPATH=src`.
- Not made: a solver-scaling figure. The E2 timings are already in Table 3 and a plot would repeat them.
- Fig. 3(b) recomputes the window bootstrap (2,000 resamples, seed 20261119). Its intervals match Table 4 to within
  0.006 (the bootstrap draws differ from the original run); means match exactly.
- Fig. 3(b) omits P4c (mean 15.83), which is off the scale; the caption says so.
- Fig. 2 merges end labels of curves that end within 0.01 of each other (e.g. "B=3,6").

## Style analysis
Techniques reused from the figures4papers references (ImmunoStruct_schematic, RNAGenScape_schematic/teaser, Dispersion_motivation, plot_idea.py, design-theory.md):
1. Objects instead of cards: label strip, spheres, a segmented state bar, a small tree, a number line; no grey boxes, no numbered circles (ImmunoStruct a).
2. Monospace letter-spaced token strips with pastel cells and black outlines for bit streams (the `S I L V A G K D V` strip).
3. Shaded spheres by surface normals and a top-left light (`plot_idea.py`) for the two hidden states.
4. One thin tall bar split into colour segments for the concatenated state (ImmunoStruct embedding bar).
5. Chunky block arrows with a white-to-tint gradient between stages; thin black arrows inside a module (ImmunoStruct, Dispersion).
6. Dashed dark-red arc and bold italic dark-red label for the one constraint (the "Reconstruction" arrow, RNAGenScape).
7. Short bold coloured titles in a darker shade of the stage colour; grey one-line captions; no paragraphs.
8. Soft pastel rounded callout without border for the takeaway (Dispersion_motivation, RNAGenScape_teaser).
9. Trapezoids for the two models, funnels as sieve gates, pale fills from the palette (ImmunoStruct F_seq trapezoids).
10. Data panels: design-theory rcParams at half scale (font 16 -> 8 pt, axes 2.5 -> 1.25 pt), black-edged bars with values at the bar ends, blue_main/neutral/red_2, frameless legends, bold lowercase panel letters.
Snippets in fig_screen (a) are illustrative glyphs, but their bits use the pipeline's rules, read from `run_phase5.py` (HYDRO = IVLFCMA), `run_phase6.py` (LATIN_BASE vowels) and `run_phase10b.py` (interval > median) and asserted. Gate counts (84, 62, 31, 10, 10, +35, 44, 528) come from the files and are asserted.

## Composed schematics (Fig. 1 and Fig. 5a): build and export
These two figures are composed as SVG (Python writes the SVG; `svgkit.py` has the gradient block arrows, `<filter>` drop shadows, dashed group boxes, lit spheres,
coins, shield and die icons). Python-rendered assets are embedded: the 3D landscape is a matplotlib `plot_surface` rendered to a transparent 600-dpi PNG
(`_build/landscape.png`, cropped), and Fig. 5 (b, c) are matplotlib bars (`svg.fonttype none`) inlined as nested SVG so their text stays text. Text is Helvetica,
math is italic Times with sub/superscripts; all text stays `<text>`, so the PDF keeps selectable text (checked with `pdftotext`/`pdffonts`).
One unit of the SVG viewBox is one CSS pixel and the figure is 624 units = 6.5 in wide, so 1 unit = 0.75 pt and the minimum text size (9.4 units) is 7 pt in the paper.

```sh
cd paper/p4_tmlr/figures
PYTHONPATH=../../../src OPENBLAS_NUM_THREADS=1 ../../../.venv/bin/python compose_overview.py   # fig_overview.{svg,png,pdf}
PYTHONPATH=../../../src OPENBLAS_NUM_THREADS=1 ../../../.venv/bin/python compose_screen.py     # fig_screen.{svg,png,pdf}
```
`svgkit.Svg.save` does the Chrome export itself (equivalent shell commands, with the HTML wrapper written to `_build/<name>.html`, which holds the inline SVG
and `@page { size: 624px Hpx; margin: 0 }`):
```sh
CH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
"$CH" --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=4 --window-size=624,H --screenshot=fig_overview.png file://$PWD/_build/fig_overview.html
"$CH" --headless=new --disable-gpu --no-pdf-header-footer --print-to-pdf=fig_overview.pdf file://$PWD/_build/fig_overview.html
```
The PDF page is exactly the figure (468 pt wide), so it crops tightly. Chrome is used instead of cairosvg because cairosvg ignores the shadow filters.

Fig. 1 (c) does a real rollout, not kink lines. `overview_assets.rollout` runs the stored adaptive-mode policy of the solver
(`risk_budget_dp_fast._Evaluator._decide`, with the same branching as `_Evaluator._vertex`: randomise between the two hull vertices of the budget, query or not, split the
budget into w0 and w1 = 2v - w0, draw the label from the model's predictive probability, update the belief). The seed is the first one in 0..499 whose run buys all B
labels over the T rounds and visits at least four distinct (beta, w) points (seed 1; the choice is cosmetic and is not tuned to a result). The path
points (beta_t, w_t) are drawn on the t=1, n=B surface at their own (beta, w); the n at later rounds is smaller, so they are a projection onto that surface, as the caption says.
The i.i.d. surface is the translucent layer above the adaptive one (value of information is larger without the cap).
Previous (flat matplotlib) versions are in `_prev/`.
