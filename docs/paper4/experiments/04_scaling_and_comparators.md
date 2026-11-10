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

| Cell | IID+repair `U0` | FCG `U` = exact `V*` | Saving | Cuts |
|---|---|---|---|---|
| C2 (T5 B2 d1, tr 9/10, em 1/10, 9/10) | 765659/312500 | 76309/31250 | 0.0082 (0.34%) | 8 |
| C3 (T6 B3 d1, tr 3/4, em 1/20, 19/20) | 4757803/1600000 | 118361/40000 | 0.0146 (0.49%) | 13 |
| C6 (T8 B3 d1, tr 3/4, em 1/20, 19/20) | 6357803/1600000 | 39589/10000 | 0.0147 (0.37%) | 22 |

On every other cell, including all T=10 cells, the IID optimum was already causal-safe, so `U0 = U`.

## Compute: end-to-end seconds

| Cell | Reference | FCG v1 (exact loop) | FCG-fast (float loop, exact final certificate) | Cuts | Reference opponent sequences |
|---|---|---|---|---|---|
| C6 (T=8) | 1.93 | 6.82 | 2.26 | 22 | 1,193 |
| S1 (T=10 B4 d2, tr 1/10, em 1/50, 49/50) | 69.45 (56.7 in run 1) | — | **37.58** | 0 | 13,791 |
| S2 (T=10, tr 3/4, em 1/50, 49/50) | 71.02 | — | **53.79** | 0 | 13,791 |
| S3 (T=10, tr 3/4, em 1/20, 19/20), Addendum A | 65.34 | — | **44.35** | 0 | 13,791 |

- At T=10, FCG-fast is **1.3–1.85× faster** than the reference on all three cells.
- **Run-to-run noise:** the reference took 56.7 s on S1 in one run and 69.45 s in the other, about 20%. The S2 ratio
  (1.32×) is therefore weak evidence from a single repetition. S1 and S3 are clearer.
- **Where the win comes from:** FCG-fast's time is 98% or more tree build (36.9 / 50.9 / 43.4 s). It wins only by not
  building the 13,791-sequence null tree. The cutting mechanism did **no** work at T=10, because no cell needed a
  cut. The registered S2 premise failed, and so did the Addendum A cell S3.
- **Where cuts fire (T ≤ 8):** FCG is slower than the reference. FCG-fast is 17% slower on C6, and v1 is 2–4.5× slower.

**Mechanism attribution.** The T=10 speed-up is the IID-relaxation-plus-exact-verification route, which is
the repo's Candidate B. Here it is engineered faster: a float build, a belief cache keyed by learner information (848
distinct beliefs instead of 4,544 recomputations at T=8), and exact certification once at the end. The earlier
Candidate B implementation took 114.8 s on S1.

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
