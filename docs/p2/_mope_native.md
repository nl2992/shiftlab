# Native-endpoint gated deployment (exact-grid MOPE CS), 2026-11-09

Author code: n17s/mope @ a4b8584b cloned to `vendor_sota/mope` (git-ignored).

## What changed
- `MopeLowerCS` / `MopeCS` (scripts/promising_directions/sota/competitors/certificate_stops.py) take
  `endpoint="quad"` (default, behaviour unchanged) or `"exact_grid"`: exact log wealth
  `log 0.5 + sum log1p(l1 (w-1) + l2 (w r - v))` on `linspace(0,1,1000)` with the common predictable bet;
  endpoint = first grid value with log wealth < log(1/alpha); same running intersection and bet
  recomputation as before. `GatedDeploymentStop` got an `endpoint` kwarg.
- scripts/p2/comparators.py (new): EXTRA `gated_deployment_native`, `gated_adaptive_range_native`,
  `gated_adaptive_range_native+front` (same hosts, only the endpoint differs); NULL_TESTED = V1.
- scripts/sota_sprint/registry.py `build_extra` imports `comparators`; bench2.NULL_TESTED gets the three names.
- Exact-grid CS is O(1000) per update; the check script is scripts/p2/mope_native_check.py (results JSON: docs/p2/_mope_native.json).

## Parity check (300 iid streams per regime, T=300, alpha=.05, true p in {.35,.5,.65})
| regime | median width native/author | median width quad/author | median / p90 final endpoint gap native vs author | miscoverage author / native / quad |
|---|---|---|---|---|
| full feedback (w=1, wmax=2) | 0.949 | 1.306 | 0.010 / 0.019 | 16 / 15 / 2 |
| IPW (wmax=20, 3 designs) | 1.000 | 1.395 | 0.014 / 0.084 | 6 / 2 / 0 |

Native is close to the author's (not bitwise: endpoints differ by ~1 grid step, and in 94% of IPW
streams at some time by more because bets are path dependent, max gap 0.56 on one stream). The quad port is 1.3-1.4x wider
and nearly never misses (0-2/600) while the native/author CS spends the alpha (about 5% time-uniform
miscoverage in full feedback, within the nominal level). The author code emits a `log1p` NaN warning on some stream(s)
(invalid factor in author's own wealth update); not investigated.

Runtime (standalone CS only, 300 steps, machine heavily loaded by other jobs): native 0.51 s (FF) / 0.85 s (IPW) vs quad 0.46 / 0.76 s,
so ~+10%; the author reference takes 0.11 / 0.23 s. In the episode smoke below, 8 jobs took 33 s on 4 workers (both policies).

## Smoke (F0_better, F5_dep_null_r95; 4 seeds; seed-base 2026110901; `outputs/p2/smoke_native`)
| source | policy | net cost J | promo rate | labels | t_first_deploy |
|---|---|---|---|---|---|
| F0_better | gated_adaptive_range | 417.7 | 0.25 | 198.5 | 1922 |
| F0_better | gated_adaptive_range_native | 398.8 | 0.50 | 171.2 | 1441 |
| F5_dep_null_r95 | gated_adaptive_range | 382.0 | 0.00 | 199.5 | - |
| F5_dep_null_r95 | gated_adaptive_range_native | 381.1 | 0.25 | 176.5 | 1330 |

With n=4 these are smoke only: the native endpoint promotes earlier/more often and saves ~19 net cost on the true-better
regime; on the dependence null one of four episodes promoted (1/4 with a nominally V1-only guarantee is
unsurprising but must be checked at larger n; the V1 null does not cover the F5 dependence).
Implication: the quad port is a materially weaker comparator than the author's, so P2 comparisons should include the
`_native` versions. Nothing committed.
