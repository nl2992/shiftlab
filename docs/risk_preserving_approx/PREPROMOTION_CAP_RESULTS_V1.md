# Pre-promotion query cap: development results v1

2026-10-29. **Status:** a promising computational tradeoff on small known-HMM
cells; no general approximation rate, novel method, or synthetic/real-data policy
superiority established. This is a restricted policy class, not a replacement for
the original oracle.

## Construction and guarantee

`src/shiftlab/dive/prepromotion_cap.py` adapts the existing exact first-promotion
solver. It permits at most m queries before or at first promotion, while preserving
the original pathwise total B and all remaining query choices after promotion,
including rollback and re-promotion. Requests count immediately; the cap depends
only on public request/action history. The original full causal-null response
and delayed HMM continuation remain in place.

As registered in `PREPROMOTION_CAP_PROTOCOL_V1.md`, for the full optimum V* and
restricted optimum V_m,

    0 <= V_m - V* <= T P_alt_pi*(more than m requests before/on first promotion),

where pi* is a full optimal policy (or use a limiting near-optimal sequence). The
upper bound follows by coupling pi* until the first excess request, then staying
with the incumbent and never querying or promoting. The replacement never adds a
null promotion and its remaining decision loss is at most T; original future
costs are nonnegative. This bound is conditional on an unknown probability and
is not a practical general approximation rate. An independently verified full
lower bound plus the exact cost of a safe capped policy gives an a-posteriori
instance-specific bound. Standard budget splits, dynamic programming and safe
truncation are prior art; no novelty is asserted for this restriction.

## Correctness and first screen

`uv run --no-sync pytest tests/test_prepromotion_cap.py -q`: 6 passed. The tests
cover a zero budget, unobserved labels, delay two, the full-cap equality with the
original reference, invalid caps, and continued access to the total B budget
after promotion and rollback. They do not establish every invariant in every
model. The registered 20-cell screen (`PREPROMOTION_CAP_PROTOCOL_V1.md`, raw
`prepromotion_cap_screen_v1.json`) completed without failures. Numerical master
objectives were nonincreasing as m increased, and m=B matched the unrestricted
reference in all four horizons. The original executed runner is preserved in
`screen_prepromotion_cap_executed_source_v1.txt`; the tracked runnable runner
only changes the adjacent-pair iteration to satisfy lint.

At m=2, the recovered safe T=6 cost was `461083/160000`; T=7 cost was
`1349103/400000 = 3.3727575`; T=8 recovered `24735833/6400000`, equal to the
unrestricted decomposed solver's recovered policy on that cell. All three had
exact causal-null promotion risk 1/10. The T=8 equality is a numerical
recovered-policy comparison, not a completed independent full-oracle certificate.

## T=7 exact full-oracle and capped-policy certificates

Under `FULL_T7_CERT_PROTOCOL_V1.md`, a new full decomposed-LP lower certificate
was built with exact objective coefficients. The numerical opponent dual proposal
was converted into an exact feasible null sequence flow, making the free-column
dual equations exact. Rational learner duals and a residual correction using
realization weights <=1 yield a rigorous lower bound. The optimizer-free
`scripts/research_risk_approx/verify_full_t7_certificate.py` checks the saved
`full_t7_certificate_v1.json`, including exact free equations, dual signs,
residuals, full-policy cost and risk. The resulting bracket for V* is

    3.371289687498436... <= V* <= 10788127/3200000 = 3.3712896875,

with exact gap below 1.564e-12. The full certificate's executed source is
preserved byte-for-byte in `full_t7_executed_source_v1.txt`; the runnable source
only receives subsequent lint fixes. The verifier uses shared model and
coefficient helpers, so it is optimizer-independent but not a second independent
implementation of the HMM.

A saved m=2 behavior policy in `precap2_t7_witness_v1.json` was separately
reconstructed and checked by `verify_precap2_witness.py` without an optimizer.
Its exact risk bound is 1/10 and its cost is `1349103/400000`. Relative to the
full-oracle lower certificate, its rigorously verified suboptimality is less than
`0.001467812502`. This is a bound for this recovered policy in this one cell,
not an upper bound on a general approximation rate or a real-data claim.

## Repeated resource comparison

The follow-up `PRECAP_RESOURCE_PROTOCOL_V1.md` fixed five fresh-process runs per
algorithm for each T=6,7,8, alternating execution order. All 30 runs completed;
each reported a unique worker PID and exact safe-risk bound 1/10. Median total
below is build plus the solver call plus a separate policy/risk evaluation; the
solver call itself also evaluates its recovered policy. Peak memory is each actual
worker's Windows `psutil.Process().memory_info().peak_wset`, including Python and
library overhead. Full raw values and hashes are in
`precap_resource_comparison_v1.json`.

| T | Reference median total | m=2 median total | Reference / m=2 median peak working set | Reference / m=2 builder nodes | m=2 versus full recovered cost |
|---|---:|---:|---:|---:|---:|
| 6 | 0.2326 s | 0.1063 s | 165.84 / 164.05 MiB | 1799 / 574 | equal; certified gap < 2e-12 |
| 7 | 0.5679 s | 0.2564 s | 168.47 / 165.10 MiB | 3334 / 884 | +0.0014678125; certified gap < 0.001467812502 |
| 8 | 1.4668 s | 0.5130 s | 171.95 / 166.93 MiB | 5700 / 1290 | equal recovered cost; no full-oracle certificate |

The measured median time reductions are about 54%, 55%, and 65% for these cells.
These are machine-specific small-instance observations, not a polynomial-time or
FPT claim. Peak-memory differences are modest and include the interpreter. The
cap can lose value: m=2 at T=7 is strictly costlier than the full feasible
reference, and the unknown-probability bound does not prove a useful worst-case
rate. The run did not evaluate published robust-FSC or sequential-test baselines,
new synthetic configurations, or real data.

## Next gate

This is a useful computational candidate for deeper investigation because it
produces exact-safe policies with a checked small-cell gap and fewer nodes, but
it has not met the user's requested endpoint. Audit fixed-budget split / bounded
sequential-design prior art at the theorem level; compare with strong
source-matched policies, establish whether a nonvacuous bound or adaptive cap
selection can be computed without the full oracle, and test registered synthetic
families before a frozen exploratory replay on eligible pulled real data. Preserve
the existing no-go evidence and do not treat the cost/compute tradeoff as a claim
of improved economic cost over the unrestricted optimum.
