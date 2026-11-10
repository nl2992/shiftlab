# 02 — Symbolic causal-risk verification (WP2): gate-limited deliverable

**Date:** 2026-11-10. **Status:** WP2 stopped at its scoping gate. A full symbolic (BDD/ADD) verifier was not
built. Directive §12, §15 and Deliverable 2 ("if the candidate fails early, deliver the bounded counterexample and
mathematical diagnostic instead of building an unnecessary full system") justify this.

## Why no BDD verifier

1. **Prior art.** For a fixed deterministic policy, worst-case causal risk is a bottom-up pass over the reduced
   ordered decision diagram of the promotion event in event order:
   `v(node) = max{v(lo), (v(lo) + v(hi)) / 2}`. Residual subfunctions are exactly Myhill–Nerode classes.
   This is the robust Bellman evaluator of Krale et al. (NeurIPS 2025, Theorem 3 and Definition 3) on a compressed
   graph, which §15 lists as non-qualifying.
2. **No leverage.** The existing exact product-state verifier already needs only 56 (T=8) and 72 (T=10)
   states (`theory/01` §3). Verification is not the bottleneck.

## Verifier actually delivered and used

| Component | Supports | Exactness | Tests |
|---|---|---|---|
| `CausalSwitchingGame.null_risk` (repo) | Behavioural policies with adaptive queries, fixed delay, pending labels visible to the null, hard budget | Exact `Fraction` | Repo tests; `tests/paper4` |
| `paper4.frontier_cuts.best_response_null` | Same; also returns the argmax endpoint strategy (the inversion frontier) | Exact | Equals `null_risk` (`tests/paper4/test_frontier_cuts.py`) |
| `paper4.frontier_cuts.risk_row_for_null` | Linear risk row for any fixed pure null strategy, keyed by full outcomes | Exact | IID strategy row equals the independent IID row |
| `scripts/research_risk_approx/check_negative_influence_identity.py` | Boolean events at T ≤ 3; randomisation example | Exact; three independent routes | 276/276 events |

**Correctness theorem.** Lemmas 1–2 in `theory/01` §4: risk is linear for a fixed null strategy, and
the supremum over strategies is attained at deterministic endpoint strategies.

**Complexity.** For a fixed behavioural policy, the cost is O(number of reachable generated histories). In the
product form it is O(controller states × pending-queue states × budget × T).

## Treatment of randomisation (WP2.3)

| Kind | Treatment | Status |
|---|---|---|
| Deterministic pure plans | Event-level recursion | Exact |
| Behavioural randomisation with public actions | The null conditions on realised public actions (Kuhn / sequence form) | Exact (Lemma 2) |
| Private root mixture | Linear in the realization plan; the null sees only public consequences | Exact via realization-space mixing |
| Marginal-average promotion function | **Unsound.** The two-branch example has true risk 3/4 against a certificate of 1/2 | FALSIFIED as a certificate |

The independent sequence-form LP check of the randomisation example is built in
`tests/paper4/test_counterexample_library.py`, test E.

## Known failure modes

- The repo helper `mix_with_never_promote` is defined for deterministic plans. On stochastic policies with
  activation < 1 it produces a different behavioural policy, as found during FCG v1. FCG uses
  realization-space mixing instead.
- Exact dual bounds can exceed Python's 4,300-digit integer-to-string limit. The runners lift the limit.
- The verifier cost grows with reachable generated histories. It is polynomial only for finite-memory policies.
