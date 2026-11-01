# Computational results (`outputs/hg_v2/runtime_profile.csv`)
1000 streams × 2000 steps, single core, vectorised NumPy, warm run, delay 5, 10% labels. Peak RSS is the process high-water mark and therefore only monotone across rows (the first rows include the 1000×2000×1 stream, `mixture8` allocates k=8 copies).
| arm | seconds |
|---|---|
| ONS | 0.18 |
| F2 gated ONS hard200 | 0.41 |
| F1 H2c | 0.57 |
| parent (pprm_tight) | 0.65 |
| F3 gated ONS multi | 1.06 |
| HG_unifcap | 1.12 |
| mixture of 8 bets | 2.25 (peak RSS 833 MB) |
All finalists run in roughly 0.2–1.1 s per million stream-steps; the Python step loop of ONS/gated ONS (2000 iterations, vectorised across streams) is cheaper than the cumulative-sum implementations because it avoids large temporary arrays. This is a single-run timing on a shared machine, not a scaling study; there is no claim of a system-level speed-up, and online (streaming, bounded-memory) implementations were not built.
