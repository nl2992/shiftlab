# Lemma L: label-time propensity invariance of zero-anchor HT betting (Stage 0, T0.8)

**Recorded 2026-10-28.** This is elementary algebra on the betting framework of Waudby-Smith and
Ramdas and its use for active labelling by Timans et al. (UAI 2025). It is credited, explanatory and
claims no novelty. It is a **pathwise identity, not a validity theorem**. Validity of each arm
comes from its own supermartingale argument (see the T0.7 validity table).

## Setting

Events `t = 1, 2, …` carry a disagreement indicator `D_t ∈ {0,1}` and a paired cost
`Z_t = c(π_t(X_t), Y_t) − c(π_ref(X_t), Y_t)` with `|Z_t| ≤ C`. In the repository `C = 5`.
- On a disagreement, a label is requested with a predictable propensity `q_t ∈ [q_min, 1]`, using a
  coin `U_t` that is conditionally independent of `Z_t`. Let `G_t = D_t 1{U_t < q_t}`.
- Agreements have a known paired cost of zero.
- The gated HT increment is `V_t = G_t Z_t / q_t − ε` on disagreements and `−ε` on agreements. Its
  predictable bound is `B_t = C/q_t + ε` (`gated_monitor_comparison.py:191`).
- The engine is `PredictableBoundMeanEProcess` (`eprocess.py:102–167`). Component `j` multiplies its
  wealth by `1 + c_j V_t / B_t`, where `c_j` is in the fixed grid `(0.05, 0.1, 0.2, 0.4, 0.8)`. The
  e-value is the fixed mixture `Σ_j w_j W_t^{(j)}`.

## Statement

**Lemma L.** Let `ε = 0`. Fix the ordered labelled losses `(Z_(1), …, Z_(n))`, meaning the values of
`Z_t` at the first `n` events with `G_t = 1`. Then, for every predictable propensity sequence
`(q_t)`, and wherever the agreements and unlabelled disagreements fall,
the wealth of component `j` just after the `n`-th label is

    W^{(j)}_(n) = ∏_{k=1}^{n} (1 + c_j Z_(k) / C),

and the mixture e-value is `Σ_j w_j W^{(j)}_(n)`. Both are propensity-free.

**Proof.**
- An agreement gives `V_t = −ε = 0`, so its factor is 1.
- An unqueried disagreement gives `V_t = 0`, so its factor is 1.
- A queried disagreement gives `c_j V_t / B_t = c_j (Z_t/q_t)/(C/q_t) = c_j Z_t / C`.

The product therefore runs over labels only, with factors that do not involve `q`. A fixed convex
mixture of propensity-free products is propensity-free. ∎

## Local ε statement

For `ε > 0` the identity fails. Unlabelled events contribute `log(1 − a)` with `a = c ε q/(C + ε q)`,
and labelled factors become `1 + c (Z − ε q)/(C + ε q)`. For a constant `q`, the expected log-growth
per label is

    g(q) = E log(1 + c (Z − ε q)/(C + ε q)) + ((1 − q)/q) log(1 − a).

Writing the second term as `−((1 − q)/q) a + R`,

    −(1 − q) a² / (2 q (1 − a)) ≤ R ≤ 0.

This bound was proposed by Codex in round 2 and accepted. For the registered `ε = 0.1` and `C = 5`,
`a ≤ c ε/C ≤ 0.016`, so the absolute remainder per label is small. **The relative error can still
be large when net growth is near zero**, for example near the null boundary. The ε remainder must
not be read as negligible there.

## Applicability

| Engine or construction | Lemma L | Reason | Checked by |
|---|---|---|---|
| Zero-anchor HT, single fixed-fraction stake, ε = 0 | **Holds** | Proof above | `test_ht_wealth_is_propensity_free_at_zero_epsilon` |
| HT, fixed-weight stake-grid mixture (default engine), ε = 0 | **Holds** | Mixture of propensity-free products | same test, uniform and non-uniform weights |
| Same, with unlabelled events moved | **Holds** | Unlabelled factors are 1 | `test_ht_wealth_ignores_where_unlabelled_events_fall` |
| HT with ε > 0 (registered ε = 0.1) | **Fails**; bounded remainder above | The `−ε` updates and the bound depend on `q` | `test_positive_epsilon_breaks_propensity_invariance` |
| PPI anchor, bound `(C + ε)(2/q − 1)` | **Fails** | A nonzero anchor updates on unqueried events; an unqueried factor is `1 + c·anchor·q/(C(2 − q))`. With deterministic `Z = C` the per-label growth is `log(1 + c/(2 − q))` | `test_ppi_increment_is_not_propensity_free`, `test_ppi_single_unqueried_factor_matches_closed_form` |
| Empirical Bernstein, GRAPA, plug-in Kelly (adaptive bets) | **Not covered** | Bets depend on calendar history, including zero updates | `test_adaptive_engine_state_moves_on_zero_updates` (empirical Bernstein) |
| Hard reserve stop | Validity preserved (predictable stop); **allocation equivalence lost** | Different `q` schedules exhaust the reserve at different times | — |

## What the lemma explains, and what it does not

- **It explains** why, for HT with fixed-fraction stakes, fixed and paced gating accumulate the same
  evidence *per label*. Their difference is a temporal-allocation effect: which losses get labelled,
  and when.
- **It does not determine calendar-time detection delay.** Delay depends on how labels are spread
  over time relative to onset, and on reserve exhaustion. This is what H-B2 tests.
- **It gives no validity.** Validity under the charter null `E[Z_t − ε | F_{t−1}] ≤ 0` needs the
  supermartingale argument with a predictable `q_t` and a coin independent of the outcome.

## Tests

Run with:

    uv run --no-sync pytest tests/test_lemma_l_propensity_invariance.py -q

7 passed at commit `0a31348`. The tests call the production `gated_increment` and
`PredictableBoundMeanEProcess`, not a reimplementation.
