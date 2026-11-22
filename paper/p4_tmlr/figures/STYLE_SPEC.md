# figures4papers style spec (from the repo's code and its "Miscellaneous" schematics)

Sources studied (copies in the session scratchpad `f4p/`): README "Miscellaneous" assets (ImmunoStruct_schematic,
RNAGenScape_schematic, RNAGenScape_teaser, Dispersion_motivation), `scientific-figure-making/references/design-theory.md`,
`figure_Dispersion/plot_idea.py`.

## What their schematics do (copy this)
1. **Draw the objects, not text cards.** Each stage is a glyph: trapezoids for encoders/models (pastel fill, black
   outline, calligraphic math inside, e.g. F_seq), thin tall rectangles for embeddings/state vectors (concatenated
   vectors are one bar with coloured segments), monospace letter-spaced token strips (`S I L V A G K D V`, Courier bold)
   for sequences, node-link graphs (circles with dark outline + straight edges), shaded spheres (imshow lighting, see
   plot_idea.py), 3D surfaces (plot_surface, pale blue to pale red, alpha), tiny neural nets.
2. **Sparse labels.** A stage has a 1-3 word bold title placed above/beside the glyph, coloured in a darker shade of the
   glyph's fill (e.g. dark sage title over a sage trapezoid). Lists only as short "➤ item" lines in a pastel note box.
   No paragraphs inside stages. No numbered circles. No grey background cards around stages.
3. **Arrows.** Between stages: chunky block arrows with a light gradient tinted to the stream's colour. Inside a module:
   thin black arrows with small heads, orthogonal routing. Feedback, losses, constraints: dashed dark-red (#8B1E1E /
   #B64342) lines with an italic dark-red label ("Reconstruction", "L_Pred").
4. **Emphasis.** One key phrase in bold (italic) dark red #B64342; optionally a dark-red rounded frame around the one
   element that matters. A soft pastel rounded callout (pale pink or pale green fill, thin or no border) for the
   takeaway/question, with a few words in bold.
5. **Colour semantics.** Pastel fills: sage #DDE5C8 / green_1 #DDF3DE, light blue #CFE3F6, butter #FCEFC7, lavender
   #E6DAEE, pink red_1 #F6CFCB. Strong: blue_main #0F4D92, blue_secondary #3775BA, red_strong #B64342, greens #8BCF8B.
   Neutrals #CFCECE #767676 #4D4D4D #272727. Blue = our method; red/pink = the alternative or the adversary.
6. **Panels** lettered a, b, c: bold lowercase, large (~28pt at 300 dpi canvas), top-left. Generous whitespace.
7. **Type.** Helvetica/Arial; math via LaTeX/mathtext (calligraphic where it names an operator); monospace for symbol
   streams and code-like labels.

## Data plots (from design-theory.md)
rcParams: font Helvetica/Arial, font.size 16 (24 for big bars), axes.linewidth 2-3, top/right spines off, frameless
legends, svg.fonttype none. Lines 2-3 pt, 2-4 curves per axis, fill_between for gaps. Bars: black edges 1.5-3 pt,
value printed above/at the end of each bar, hide redundant ticks. `fig.tight_layout(pad=2)`, `dpi=300`.

## What to avoid (the "AI-generated" look the user rejected)
Rounded grey cards per step, numbered black circles, explanatory paragraphs in boxes, uniform box grid, equal weight on
every element, text doing the work the drawing should do.

## Composed schematics
Observations from the "Miscellaneous: figures not made end-to-end in Python" assets (RNAGenScape_schematic/teaser, ImmunoStruct_schematic/contrastive,
Dispersion_motivation/observation, VIGIL_teaser), read on 2026-11-23. The earlier flat matplotlib diagrams missed these things:
1. **A rendered 3D asset is the centre of the story.** RNAGenScape draws one shaded plot_surface landscape (pale blue valleys to pale red peaks, thin white mesh
   lines, soft light) with a trajectory of small green points z, z1, z2 ... zn on it, labelled in italic with subscripts. The teaser repeats the same landscape twice
   (standard vs ours) with a thick grey path. Dispersion uses lit grey spheres with dashed spokes, ImmunoStruct uses ribbon proteins and surface renders. The asset
   is a picture, not a drawn shape; everything else is composed around it.
2. **Light cones link a small module to the asset.** A green gradient wedge fans from a thin embedding bar (or a pale blue wedge from the embedding row in
   Dispersion) to the region of the surface it acts on. It is translucent and fades away from the source.
3. **Pastel module glyphs.** Trapezoid encoders/decoders with calligraphic letters inside (E, D, F_seq), thin tall embedding bars (coloured segments when
   concatenated), rounded pill boxes for modalities, pale note boxes with "➤" bullets (Biochemical Properties, Properties in RNAGenScape b).
4. **Dashed rounded group boxes with a coloured bold title** sitting on the border ("Organized autoencoder", dashed boxes in ImmunoStruct d).
5. **Shaded block arrows** (white to tint gradient, thin dark outline, soft drop shadow) between stages; thin black orthogonal connectors inside a module with small
   arrowheads; dashed dark-red arrows with an italic dark-red label for losses or feedback (L_Recon, L_Pred, Reconstruction, L_similarity).
6. **Small icons as legend**: snowflake = frozen, flame = trainable, in a dashed legend box; a sugar bag, scales, robot, check/cross marks (VIGIL) as meaning carriers.
7. **Standard vs ours side by side** (teaser, VIGIL a, Dispersion): the same drawing twice, a bold monospace title above each, the failure named by a bold red phrase
   ("Leaves the manifold and comes back."), the fix by a bold dark-red phrase and a pale green callout with a few bold words.
8. **Density and mixed panel sizes**: panels a-e of different widths packed tightly with little whitespace, equations rendered in a serif/calligraphic face next to
   Helvetica text, monospace for tokens and titles, shadows on boxes. Nothing is a uniform grid.
How the P4 figures follow this (compose_overview.py, compose_screen.py): the 3D asset is a real value surface from the solver with a real policy rollout; spheres,
trapezoids, coins, shield and die icons are SVG glyphs with gradients and a `<filter>` drop shadow; a green gradient cone runs from the state bar to the surface;
group boxes are dashed with the title on the border; panel (d) is the standard-vs-ours pair with a red phrase and a green callout.
