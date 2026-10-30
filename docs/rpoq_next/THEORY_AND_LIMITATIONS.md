# Theory status and limitations

| Statement | Status | Basis |
|---|---|---|
| `E[X²\|x] = 2Hμ − H² + r/q` for `X = H + Q(Y−H)/q` | PROVED (algebra) | Simulation test in `tests/rpoq_next/test_growth_alloc.py` |
| With one common bet, growth-optimal allocation equals Neyman (to second order) | CONDITIONAL | Quadratic approximation; derivation in `METHOD_DESIGN.md` |
| With per-context Kelly bets and no proxy, the growth-optimal allocation is bang-bang on `μ²/r` | CONDITIONAL | Same approximation; observed in A1 (`q = 0.66` on one context) |
| Null validity of any predictable allocation and bet | CONDITIONAL (inherited) | `delayed_event_prefix_validity.md`; not newly proved; null crossing ≤ 0.031 in simulation |
| A finite-sample power or regret guarantee for learned growth allocation | CONJECTURED, not attempted | No theorem |
| Approximation bound to the exact RPOQ oracle | Not attempted (Candidate C) | — |
| "Growth-aware allocation beats equally equipped baselines" | **FALSIFIED as a general claim** | Holds only in stationary heterogeneous-SNR synthetic settings (A3); negative on CRSP exploratory replay (R1: −1.15, −3.21) |
| "A pre-test stability check protects against the favourite flipping" | **FALSIFIED on CRSP** | R0 reported ρ = 0.74 val→cal; the favourite still lost its signal in the test period |

**Limitations that matter.** Second-order approximation; grid-search allocator; learned moments from small burn-in; per-context bets are essential to the effect and make it sensitive to context definition; contexts must be observable and stable; no tests of random or informative delay, proxy misspecification or strong dependence; real-data evidence is exploratory on an exposed test period with imposed clocks and costs and anti-conservative intervals.
