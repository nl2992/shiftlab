# RB-DP results (2026-11-13)

Lead: Fable 5.2 (plan, verification). Builders: four Sonnet subagents. Plan: `PLAN.md`. Detailed tables:
`E1_E4_VALIDATION_BASELINES.md`, `E2_E3_SCALING_PREMIUM.md`. All cells synthetic, delay d = 1, two-state HMM
alternative. Nothing committed or pushed.

## The algorithm

RB-DP solves the causal-null-safe budgeted promotion problem by dynamic programming on
(time, alternative belief β, remaining budget n, risk budget w), where w is the worst-case probability of ever
promoting from the current point.

- Continue with budget w' after promoting with private probability π: `π + (1 − π) w' ≤ w`.
- On a query, split w' across the two label values: causal null `max(w0, (w0 + w1)/2) ≤ w'`; IID null
  `(w0 + w1)/2 ≤ w'`. The causal-safety premium is the price of the one extra constraint `w0 ≤ w'`.
- The value is the lower convex hull in w (the learner may randomise between continuation budgets).
- **Dyadic lattice.** For each (t, β, n) the value is convex piecewise linear in w with breakpoints in
  `{k / 2^n}`: the hull keeps only existing breakpoints, a query split is an infimal convolution (breakpoints at
  midpoints of pairs, one extra bit per query), and the cap `w0 ≤ w'` switches regime only at existing
  breakpoints. So a w grid of `2^B + 1` points (refined to contain α) is exact, and the only approximation left is
  linear interpolation in β, which underestimates (the value is concave in β).
- Output: U = cost of the extracted policy evaluated exactly on its own forward tree, with its worst-case risk
  verified by exact backward recursion; L = the lattice DP value.

Code: `src/shiftlab/paper4/risk_budget_dp.py` (first version, uniform w grid, rounded lower bound) and
`src/shiftlab/paper4/risk_budget_dp_fast.py` (`lattice_exact=True`; use this one). Tests: `tests/paper4/` — 83 pass.

## What was measured

| Question | Result | Source |
|---|---|---|
| Does it reproduce certified exact optima? | 190 certified cells (150 existing, 40 fresh random): no bound violated; 186 equal to round-off on the first solver. The two existing cells off by ≤ 2.5e-3 (B = 4, off-lattice grid) are exact in lattice mode (lead rerun: 3.145989478, 5.448796194). Lattice mode vs 60 certified premium cells: max abs ρΓ deviation 4.2e-13 | E1; E3 |
| Does it scale? | Linear in T, about 2^B in B. B = 3: 0.6 s at T = 16, 8.3 s at T = 256. T = 32: 0.2 s (B = 1) to 122 s (B = 8). The exact solver timed out at 3,600 s on B = 3, T = 16 (t = 63/125, e = 3/20); RB-DP solves that cell in 0.4 s with L = U to 12 digits | E2; lead rerun |
| Is IID design safe? | No. Wherever the two optima differ, the IID-optimal policy's true worst-case risk is 2α to 4α (0.2–0.4 at α = 0.1); the RB-DP causal policy sits at exactly α | E3, E4 |
| How much do safe baselines lose? | Fraction of RB-DP's value of information captured, anti-persistent chains without costs: IID + repair 0.47–0.68, fixed-bet e-process gate 0.74–0.96. With costs (c = 1/100, k = 1/20): 0.89–0.92 and 0.72–0.80. Persistent chains: all tie (no premium). No safe baseline exceeds RB-DP in any of 40 cells | E4 |
| What does the premium do at long horizons? | For every B ≤ 6 and t ∈ {2/3, 3/4, 9/10}, ρΓ(T) falls and then flattens at a positive value (table below). This was the open clause of the salvage plan, which the exact solver could only follow to T = 12 | E3 |
| Agreement with theorems | M1 (B = 1) closed form matched to 2e-12 at every T ≤ 200. M4 (B = 2) bound holds; observed limit equals (1 − r)/(3 + r), twice the proved bound (numerical observation). M6–M9 rectangle (r = 1/125, g = 0.49), T ∈ {16, 20, 32}: ρΓ = 0.2470, 0.1975, 0.1645, 0.1409 for B = 3…6 against proved bounds 0.1881, 0.1548, 0.1320, 0.1102 | E3, E3b |

ρΓ at the largest horizon run (T = 100; T = 200 for t = 3/4, B ≤ 5), α = 1/10, e = 1/10, c = k = 0:

| t | B=1 | B=2 | B=3 | B=4 | B=5 | B=6 |
|---|---|---|---|---|---|---|
| 2/3 | 0.3333 | 0.2000 | 0.1429 | 0.1111 | 0.1135 | 0.1404 |
| 3/4 | 0.2500 | 0.1429 | 0.1000 | 0.1379 | 0.2139 | 0.3034 |
| 9/10 | 0.1000 | 0.0526 | 0.1460 | 0.2218 | 0.2688 | 0.2762 |

t = 3/4 also has B = 7: 0.3680 (T = 100) and B = 8: 0.4018 (T = 64, not yet level). The premium is not monotone in
B: it falls for small budgets and rises again for larger ones.

## Caveats

- Delay d = 1 for everything above. A d = 2 solver now exists (`DELAY2.md`, `risk_budget_dp_d2.py`): it matches the
  certified optimum on 166 small cells but has an upper bound only and no lattice theorem. Its long-horizon study
  (`D2_LONG_HORIZON.md`, `DELAY2.md` §6, 81 cells, B ≤ 3 to T = 100) finds a smaller premium than d = 1 in every
  cell: zero for B = 1, zero at T ≥ 32 for B = 2 and 3 except t = 9/10, B = 3, which is level at 0.0399. B = 4
  (`DELAY2.md` §7, 24 cells to T = 100) is level at 0.0331 for t = 3/4 and 0.1229 for t = 9/10, and zero for
  t = 2/3. Values past T = 10 are not certified. d ≥ 3 is not built.
- Two-state alternative; symmetric chains dominate the experiments. Asymmetric chains appear in validation and in
  two baseline groups.
- The exact reduction and the dyadic-lattice property are now proved in `PROOFS.md` (Theorems 1 and 2) and pass
  the stress tests there (`results/proof_stress_v1.json`), but the proofs have not been independently reviewed.
- ρΓ values are point estimates from U; the L/U bracket is at most 7e-4 wide (t = 9/10, B ≥ 5, T = 100, from β
  interpolation at n_beta = 401) and zero to 12 digits in the theorem rectangle.
- E4 baselines were run with the first solver at a coarse grid (n_beta = 201, K = 10), not in lattice mode. The
  e-process gate's risk is a Ville bound, not its exact worst case.
- The fresh random validation grid has only 2 of 40 cells with a positive premium; the 150 existing cells carry the
  premium check.
- Cost is exponential in the label budget B (2^B lattice). B = 8 at T = 32 takes about 2 minutes per mode.
- An independent model-subagent review of the d = 1 proofs (`PROOF_REVIEW.md`) found no wrong claim, added stated
  assumptions and wording fixes (`PROOFS.md` §4), and found one implementation bug (starting belief exactly 1 gave
  L = NaN; fixed 2026-11-16 by removing duplicate belief grid points, regression test added). Earlier results
  with start belief below 1 are unaffected. It also reproduced the exact optimum with its own linear programme on
  10 cells to 1.3e-15 and checked Theorem 2 in exact rational arithmetic on 45,768 rows with no breakpoint off the
  dyadic grid.
- Float64 throughout; U and the risk check are exact evaluations of the policy in floats, not rationals.
- Not run: B = 7, 8 at t = 2/3 and 9/10; T = 200 at B = 6; any real-data stream.

## Reproduce

```bash
uv run --no-sync pytest tests/paper4 -q
uv run --no-sync python scripts/paper4_continuation/rbdp/e1_1_wpM.py
uv run --no-sync python scripts/paper4_continuation/rbdp/e1_2_fresh.py
uv run --no-sync python scripts/paper4_continuation/rbdp/e4_baselines.py
```

The E2/E3 commands are listed at the end of `E2_E3_SCALING_PREMIUM.md`.
