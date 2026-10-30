# Candidate J exact-controller risk verifier benchmark protocol

**Registered before benchmark execution:** 2026-10-30. **Type:** bounded
synthetic correctness and verifier-complexity diagnostic; not policy efficacy.

## Frozen instance and policy

- Horizon `T=18`, hard pathwise query budget `B=18`, fixed label delay `d=2`.
- The deterministic learner queries at every event while its budget remains.
  It promotes at the first event after observing four consecutive positive
  queried labels; it otherwise retains the incumbent. Its controller memory is
  the current positive-run length in `{0,1,2,3}`.
- The null may choose each query's conditional positive probability in
  `[0,1/2]` after seeing the complete generated history, including the one
  queried outcome that can still be pending to the learner.
- Compare the new product-state Bellman risk verifier against the existing
  `CausalSwitchingGame.null_risk` full-history recursion on this exact same
  deterministic policy. Both must return the exact same rational risk.

## Frozen metrics and limits

Record exact risk; distinct product states; full-history recursion states
(counted by unique policy-history evaluations); wall time and Python-traced
peak memory for each verifier; controller/source/protocol hashes; and the exact
command. Single local-process run, 120-second wall limit for the reference
recursion. Do not tune `T`, `B`, `d`, or run repeated warm-cache timings.

**Diagnostic pass:** risks agree exactly, product-state count is at least 10x
smaller, and product-state wall time is at least 2x faster. A pass establishes
only a verifier advantage for this fixed controller. It does not establish an
optimizer, a value gap, novelty, G1–G3, or eligibility for real data. A failed
threshold closes this verifier-efficiency hypothesis without altering the
correctness theorem or rerunning the cell.

**Command:**

```powershell
uv run --no-sync python scripts/research_risk_approx/benchmark_candidate_j_controller_risk.py
```

Output path: `docs/risk_preserving_approx/candidate_j_controller_risk_benchmark_v1.json`.
No external data, seed registry, holdout, or remote compute is involved.
