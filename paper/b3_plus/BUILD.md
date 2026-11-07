# Building the manuscript

```bash
cd paper/b3_plus
pdflatex -interaction=nonstopmode main.tex
bibtex main
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
```

TeX Live was installed here with `brew install texlive`, which needs no administrator rights
and puts `pdflatex` in `/opt/homebrew/bin`.

The style files (`icml2026.sty`, `icml2026.bst`, `algorithm.sty`, `algorithmic.sty`,
`fancyhdr.sty`) are the official ICML 2026 ones from `media.icml.cc` and are committed beside the
source so the build does not depend on a particular TeX distribution carrying them.

`\usepackage{icml2026}` is the anonymous submission form. Add `[accepted]` only for camera-ready,
which reveals the author block.

## What the build does and does not check

Compiling confirms the document is well formed and tells you the page count, which is the one
thing static checking cannot establish. It does **not** check that the reported numbers are
correct. Those come from `tables/*.tex`, which are generated from saved per-episode records; to
regenerate them, see `docs/promising_directions/B3_PLUS_FIGURES.md` and the table generators.

Build artifacts are gitignored, including `main.pdf`: the source and the generated tables are the
record, and a committed PDF goes stale the moment either changes.
