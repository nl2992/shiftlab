# Style spec for illustrated concept / process figures (derived 2026-11-22 from figures4papers)

Sources read: `figure_VIGIL/plot_concept.py`, `figure_Dispersion/plot_idea.py`, `figure_MACL/plot_overview.py`, and the composite
images in `assets/` (VIGIL_teaser, RNAGenScape_teaser and _schematic, Dispersion_motivation and _observation, ImmunoStruct_*).

What they actually do
1. Python-only "concept" plots illustrate the idea with *simulated objects*, not boxes: Gaussian densities with alpha fills,
   KDE contours of sampled point clouds, spline ridges, star markers, dotted guide lines, `<->` gap arrows, a lit 3D-looking
   sphere with sampled points. Big canvases (24 x 6 in) with 24-40 pt fonts, thick axes (3 pt), scaled down in the paper.
2. Composite teasers (assembled outside Python, plot panels made in Python) use a fixed vocabulary:
   - panel letters a, b, c in bold, top-left, outside the panel;
   - a dashed rounded claim banner on top ("X leads to Y.");
   - rows of small rounded cells with a light-to-dark blue gradient, "?" cells for unseen items, monospace row labels;
   - translucent blue zoom cones from a row into a magnified object (the sphere);
   - flat, outlined objects with thin dark outlines and soft fills, never uniform tinted boxes of text;
   - pale callouts (light green / light pink) with 2-3 short lines and *bold coloured keywords*; one red rounded frame to
     highlight the key object; a wide flat block arrow with a light-to-dark blue gradient carrying the takeaway sentence;
   - monospace bold titles for the two compared methods; bold italic dark-red names for named phenomena;
   - real result panels (curves, heatmaps, radar) sitting beside the schematic, with bold in-plot annotations and dashed
     blue trend arrows;
   - dense, tight composition; no large empty areas; palette limited to blue / red / green / gold / greys.

How we apply it
- Every illustrated object is built from our own data or code (tokens = rounds, "?" = pending labels, coloured tiles = regimes,
  dots = streams), not drawn freehand.
- Helpers in `schematic.py`: gradient rounded cells, zoom cone, block arrow, rich text with bold coloured keywords, callouts,
  small flat icons (shield, clock, coin).
