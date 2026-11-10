# 04 — Scaling and comparators (FCG)

**Date:** 2026-11-10. Results are development screens on synthetic cells. Every timing is from a separate
fresh process, one repetition each. Configurations, hashes and per-iteration data are in the JSON files
cited below. The reference is the exact first-promotion decomposed sequence-form solve
(`FirstPromotionDecomposedGame.solve()`, `calibrated_total_cost`).

## Correctness (all cells): PASS

Every FCG and FCG-fast run returns `U` equal to the reference cost as an exact `Fraction`. Exact robust
risk is `1/10`, and the certified gap `U - L` is at most `4e-14`.

## Accuracy: FCG against the IID+repair shortcut

These are the cells where the IID optimum is causal-unsafe, with robust risk 1/5 against alpha 1/10.

| Cell | IID+repair `U0` | FCG `U` (= `V_ref`; `V*` in `[L, U]`, gap ≤ 4e-14) | Saving | Cuts (rows incl. IID) |
|---|---|---|---|---|
| C2 (T5 B2 d1, tr 9/10, em 1/10, 9/10) | 765659/312500 | 76309/31250 | 0.0082 (0.34%) | 7 (8) |
| C3 (T6 B3 d1, tr 3/4, em 1/20, 19/20) | 4757803/1600000 | 118361/40000 | 0.0146 (0.49%) | 12 (13) |
| C6 (T8 B3 d1, tr 3/4, em 1/20, 19/20) | 6357803/1600000 | 39589/10000 | 0.0147 (0.37%) | 21 (22) |

On every other cell, including all T=10 cells, the IID optimum was already causal-safe, so `U0 = U`.

## Compute: end-to-end seconds

| Cell | Reference | FCG v1 (exact loop) | FCG-fast (float loop, exact final certificate) | Cuts | Reference opponent sequences |
|---|---|---|---|---|---|
| C6 (T=8) | 1.93 | 6.82 | 2.26 | 21 | 1,193 |
| S1 (T=10 B4 d2, tr 1/10, em 1/50, 49/50) | 69.45 (56.7 in run 1) | — | **37.58** | 0 | 13,791 |
| S2 (T=10, tr 3/4, em 1/50, 49/50) | 71.02 | — | **53.79** | 0 | 13,791 |
| S3 (T=10, tr 3/4, em 1/20, 19/20), Addendum A | 65.34 | — | **44.35** | 0 | 13,791 |

- At T=10, FCG-fast is **1.3–1.85× faster** than the reference on all three cells.
- **Run-to-run noise:** the reference took 56.7 s on S1 in one run and 69.45 s in the other, about 20%. The S2 ratio
  (1.32×) is therefore weak evidence from a single repetition. S1 and S3 are clearer.
- **Where the win comes from (unattributed).** Tree build is 95–98% of FCG-fast's time (36.9 / 50.9 / 43.4 s). The
  cutting mechanism did **no** work at T=10, because no cell needed a cut: the registered S2 premise failed, and so
  did Addendum A's S3. Three changes are confounded in the gain:
  1. skipping the 13,791-sequence null tree;
  2. a belief cache keyed by learner information, which the reference lacks (848 distinct beliefs against 4,544
     recomputations at T=8, per the builder's profile; no saved artifact);
  3. a float build.
  The reference records no time split, so the share of each is **not measured**. A fair comparison needs a
  belief-cached reference and repeated runs.
- **Where cuts fire (T ≤ 8):** FCG is slower than the reference. FCG-fast is 17% slower on C6, and v1 is 3.9–4.9×
  slower on the cut cells C2, C3 and C6 (dev run).

**Mechanism attribution.** The T=10 gain belongs to the IID-relaxation-plus-exact-verification route (the repo's
Candidate B), engineered as above. The earlier Candidate B implementation took 114.8 s on S1.

**Errata against registered protocols** (the protocols are left unedited, as the directive requires):
- FCG_SCALE_PROTOCOL_V2 Addendum A calls S3 "the T=10 counterpart of C6". It also changes delay (1 → 2) and budget
  (3 → 4). Cuts fired only at d=1, so "cuts not exercised at T=10" is confounded with delay. No T=10, d=1 cell was
  tested.
- V2 describes an alternative stop condition ("float LP violation below 1e-9 with exact risk ≤ alpha"). The code
  does not implement it; it raises if the float violation is ≤ 1e-9 while exact risk > alpha. This never triggered.
- Timing noise: the C6 reference took 1.40 s in the dev run and 1.93 s in the scale run (38%). The S1 reference took
  56.7 s and 69.45 s (about 20%). The S2 ratio (1.32×) is inside this noise.

**Run 1 failure, preserved.** FCG-fast completed on S1 and S2 but could not be serialised. The exact dual
bound exceeded Python's 4,300-digit integer-to-string limit. The run is kept as
`results/fcg_scale_v2_run1_serialization_failure.json`. The runners now call
`sys.set_int_max_str_digits(0)`.

## Comparators not run (directive WP4.4)

The following were not run in this screen:
- calendar and sequential-test baselines (earlier repo runs exist);
- constrained-POMDP column generation;
- robust FSC synthesis;
- one-sided POSG solvers;
- BDD risk evaluation. It is unnecessary: the verifier is not the bottleneck (56–72 states).

No claim is made against them.

## Files

- `results/fcg_dev_v1.json`
- `results/fcg_scale_v2.json`
- `results/fcg_scale_v2_run1_serialization_failure.json`
- `results/fcg_scale_v2_addendumA_s3.json`

Commands:
```bash
uv run --no-sync python scripts/paper4/run_fcg_dev.py
uv run --no-sync python scripts/paper4/run_fcg_scale_all.py
uv run --no-sync python scripts/paper4/run_fcg_scale.py --cell S3 --method ref
uv run --no-sync python scripts/paper4/run_fcg_scale.py --cell S3 --method fast
uv run --no-sync pytest tests/paper4 -q
```
