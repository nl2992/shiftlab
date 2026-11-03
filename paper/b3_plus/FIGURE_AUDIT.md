# Figure audit (2026-11-02)

Two figures exist. Both were inspected visually, not described from memory.

## Severity summary
**2 CRITICAL, 3 MAJOR, 2 MINOR.**

Top three actions: export vector; fix the Figure 1 arrow semantics; fix the one wrong
value label in Figure 2.

## Figure 1 — Solution Overview (`fig1_method.png`)

Paradigm is correct: a staged pipeline on a time axis, which is the right form for a
per-event loop whose whole point is *when* information becomes available. A flowchart
without the timeline would lose the delay, which is the paper's central constraint.

| # | Finding | Severity |
|---|---|---|
| 1 | **Raster PNG.** ICML camera-ready wants vector; text in a raster diagram goes soft in print and cannot be searched or scaled. | CRITICAL |
| 2 | **The \textsc{settled} state carries a green upward arrow although acquisition falls there.** Colour and direction both signal "increase" while the adjacent text says the rate drops to the propensity floor. A reader who trusts the icon over the text takes away the opposite of the method. | MAJOR |
| 3 | Box labels ("ISSUE", "RELEASE", "DECIDE") match the three stages named in Section 3, so the figure and prose use one vocabulary. | pass |
| 4 | Caption states the finding in its first sentence. | pass |
| 5 | No chartjunk, no 3D, legible at full width (`figure*`). | pass |

## Figure 2 — Experimental Results (`fig2_netcost.png`)

Grouped bars are the right chart type for multi-method comparison across datasets.

| # | Finding | Severity |
|---|---|---|
| 1 | **Raster PNG**, as above. | CRITICAL |
| 2 | **Was placed at `\columnwidth`.** Five groups of four bars plus twenty value labels inside a 3.25-inch column would put every label far below the 8pt floor. Fixed: promoted to a full-width `figure*`. | MAJOR (fixed) |
| 3 | **Palette is not deuteranope-safe.** `P6` green sits directly beside `P7s` crimson, and series identity in the legend is carried by colour alone. Partly mitigated because every bar is numerically labelled, so no reading depends only on hue. Dual-encode with hatching, or move to a ColorBrewer-safe set. | MAJOR |
| 4 | **`spam` `P0` is labelled 850; the record is 849.0.** One wrong number in twenty. | MAJOR |
| 5 | On `uci_occupancy`, `P3b` (177.63) and `P7s` (176.62) both render as 177, so that case's effect is invisible at this precision. Consider a companion panel of paired differences. | MINOR |
| 6 | Low-power datasets starred with the footnote "K<5, seed-level bootstrap", and no error bars drawn, so seed-level uncertainty is not presented as episode-level. This was the check that mattered most and it passes. | pass |
| 7 | **Y axis starts at zero**, so bar lengths are proportional and no difference is visually exaggerated. | pass |
| 8 | Caption states the finding first, including that `P6` wins on `weather`. | pass |
| 9 | Configuration box ("T=2000, B=200, c_q=0.05, c_s=5") makes the panel self-contained. | MINOR (redundant with caption, harmless) |

## Not yet assessable

Figures 3 and 4 do not exist; generation is blocked on the Google Cloud billing error recorded in
`B3_PLUS_FIGURES.md`. The vector export and the Figure 1 arrow fix are blocked on the same thing,
since regeneration needs the same API.
