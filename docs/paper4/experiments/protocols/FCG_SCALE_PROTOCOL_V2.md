# FCG scaling screen v2 (float inner loop, exact final certificate)

**Registered:** 2026-11-09, after the v1 development results (`../results/fcg_dev_v1.json`) and before any
v2 code exists. Development-only; synthetic; no holdouts or real data.

## Why v2

Under v1, FCG is correct on all six cells and recovers the exact `V*` on the anti-persistent cells.
It is 2–4.5× slower than the exact decomposed reference at T ≤ 8, confirmed in separate fresh processes.
Most v1 time goes to exact-arithmetic coefficient construction (build 2.4–2.7 s at T=8, against a 1.4–1.8 s
total for the reference) and to exact repair at every iteration. Neither is needed until termination.

## Variant FCG-fast

- Build the learner tree, cost vector and risk rows in floating point.
- Iterate: LP; recover the policy; exact best response (the product verifier, already small); add the
  cut. No per-iteration repair and no exact dual.
- Stop when the exact robust risk of the recovered policy is `<= alpha`, or when the float LP
  violation is below `1e-9` with exact risk `<= alpha`.
- **At termination only:** build the exact cost vector and the exact rows for the final `K`. Compute the exact
  rationalised dual lower bound `L`, the exact repaired policy and its exact cost `U`, and verify exact robust
  risk `<= alpha`. The certificate is therefore identical in kind to v1.

## Cells (prior 1/2, alpha 1/10, query 1/100, switch 1/10)

| id | T | B | d | transition | emissions | role |
|---|---|---|---|---|---|---|
| S1 | 10 | 4 | 2 | 1/10 | (1/50, 49/50) | the registered T=10 stress cell (persistent control) |
| S2 | 10 | 4 | 2 | 3/4 | (1/50, 49/50) | anti-persistent counterpart |
| C6 | 8 | 3 | 1 | 3/4 | (1/20, 19/20) | v1 cell, re-timed with FCG-fast for comparison |

Each method runs in its **own fresh process**: the reference (`FirstPromotionDecomposedGame.solve()`),
FCG-fast, and v1 FCG (C6 only). The reference node limit is 200,000, and every run has a 20-minute
wall-clock cap.

## Gates (lax)

- **G-correct (required):** exact robust risk `<= alpha`, `U = V_ref` within `1e-6` where the reference
  completes, and `U - L <= 1e-6 * max(1, |U|)`.
- **G-compute (headline, reported):** FCG-fast end-to-end seconds against the reference end-to-end seconds,
  per cell. A computational-advantage claim is made only for cells where FCG-fast is faster.
- Report `|K|` against reference opponent sequences, and the time split (build / LP / verify / final certificate).

## Decision rule

- If FCG-fast is faster than the reference on S2, where the null side is largest and cuts are needed,
  then FCG becomes a CONDITIONAL GO computational candidate. That would still be pending a source-level
  check against sequence-form double-oracle prior art.
- Otherwise record **NO-GO — computational feasibility** for FCG on this game family. FCG is retained as an
  exact anytime alternative to the reference, not as a contribution.
