# P2-NAD method registry

Code: `scripts/p2/nad.py` (registered in `scripts/sota_sprint/registry.py` through the p2 hook).
Every candidate keeps QSG's decision skeleton: a promotion test, a discard test, a mirrored rollback
test, cycle j at α/2^j, and paced monitoring after a verdict. Each changes the evidence process
and/or the acquisition. Validity statements are in `05_VALIDITY_AUDIT.md`.

| Family | Name pattern | Evidence | Acquisition while undecided | Valid class | Round |
|---|---|---|---|---|---|
| NAD (envelope) | `NAD-m{80,90,95}-g{0,5,10,15,20,40}` | Started relative-edge mixture against u_k = 1/2 + ρ̄^{g}/2·z_{k−1} | Fixed minimum event gap g (g0 = none). A budget guard keeps the spend rate sustainable | M̃(ρ̄) | 1, 3 |
| NAD φ | `NAD-p{80,90}-*` | u_k = 1/2 + ρ̄^{g} (φ-mixing envelope) | as above | Φ(β = ρ̄^g) | 1 |
| NAD rate | `NAD-*-rate`, `-rate2` | as NAD | Gap maximising the planned information rate; rate2 uses a predictable ρ̂ and the budget-sustainable spacing | as NAD | 1, 2 |
| NAD a5b-density | `NAD80-ad` | as NAD | A5b's rule g* = ⌈ln .25 / ln ρ̂⌉ | M̃(.8) | 4 |
| UI bounded | `UI{80,90}-g{0,5,10}`, `-ad` | fam_a MarkovSUI with ρ ≤ ρ̄ (universal inference) | fixed gap / A5b density | M(ρ̄) (stationary) | 2 |
| MIX | `MIX{80,90}-*` | ½ envelope + ½ bounded-ρ UI | fixed gap / rate2 | M(ρ̄) | 2 |
| MIXA | `MIXA80-g{5,10}`, `MIXA80-ad` | ½ envelope(.8) + ½ unbounded-ρ UI (A5b's) | fixed gap / A5b density | M(.8) | 3, 4 |
| PB (payback) | `PB{80,90}-g{5,10}` | Envelope e-processes on a hurdle grid b = 1/2 + h_j; promotion uses the smallest h_j ≥ h(τ) = (c_s + κ)/(2·dis·(T−τ)) | fixed gap | M̃(ρ̄, b(τ)); bounds non-payback promotions | 2 |

## Screen status (dev seeds 2026110901 × 40; see `04_DEVELOPMENT_RESULTS.md`)

| Candidate | Status | Reason |
|---|---|---|
| NAD-m80-g10 | **lead** | Cheapest certificate with in-class null ≤ .025, out-of-class r95 .10, max harm .75 |
| PB80-g10 | **lead (economic-validity arm)** | Zero mean decision harm on all 8 nulls at J +7.5 vs NAD |
| UI80-*, MIX80-* | dropped | Brittle out of class: .90–.95 promotion on ρ=.95 nulls, harm up to 11 |
| UI90-* | dropped | Not cheaper than NAD-m80; .275–.50 on r95 |
| NAD-*-g0, -g40, m95 | dropped | No spacing wastes budget (FA3); g40 is too slow; ρ̄=.95 is near never-switch |
| NAD-*-rate / rate2 | dropped | Planner not better than a fixed g (rate assumes iid alternatives; rate2's ρ̂ is noisy early) |
| NAD φ | parked | Costs more than markov at the same ρ̄; it is the class to report for order-2 nulls |
| MIXA80-g5/g10 | inconclusive | Does not recover A5b's iid efficiency at a fixed gap |
| NAD80-ad, MIXA80-ad | running (dev4) | Tests whether A5b's density rule gives iid efficiency |
