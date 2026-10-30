# Synthetic results

## A1: necessary-condition screen for Candidate A (protocol: [`SYNTHETIC_PROTOCOL.md`](SYNTHETIC_PROTOCOL.md))

**Run:** 2026-10-30, 2,000 seeds per setting, commit with `screen_a.py` at the A1 checkpoint. Artifacts: `outputs/rpoq_next/screen_a1/results.json`. Exploratory, synthetic. **Claim level: none.**

### Registered quantities

Power (fraction of seeds crossing `1/α = 20` through the resolved prefix), `ρ = 0` / `ρ = 0.6`, all arms with per-context bets unless stated:

| Setting | uniform+ctx | neyman+ctx | growth+ctx | growth+common | primary: growth+ctx − best(uniform, neyman)+ctx |
|---|---|---|---|---|---|
| null (calibration) | 0.015 / 0.015 | 0.018 / 0.018 | 0.019 / 0.019 | 0.001 / 0.002 | — |
| hom | 0.256 / 0.263 | 0.212 / 0.223 | 0.927 / 0.925 | 0.019 / 0.021 | +0.671 [0.648, 0.693] / +0.662 [0.640, 0.684] |
| het | 0.257 / 0.276 | 0.311 / 0.318 | 0.979 / 0.977 | 0.042 / 0.055 | +0.668 [0.647, 0.689] / +0.659 [0.637, 0.680] |
| anti | 0.184 / 0.188 | 0.287 / 0.295 | 0.679 / 0.670 | 0.028 / 0.035 | +0.392 [0.365, 0.419] / +0.376 [0.347, 0.402] |

All arms hold the hard cap (mean spend 392 of 400) and cross under the null at ≤ 2% (limit 7%).

### Registered verdict: **NOT PASSED**

The pass rule required the primary contrast ≥ +0.05 with a positive lower bound in `het` (met: +0.668 and +0.659) **and** `|growth+ctx − neyman+ctx| ≤ 0.02` in `hom`. The second condition is violated by a wide margin (0.927 vs 0.212). By the protocol, that is a fail. It is reported as one.

### What the failure shows (diagnosis, not a rescue)

1. **The tie prediction in the method design was wrong.** P1 said allocation ties when the signal is constant. The correct tie condition is constant *signal-to-noise ratio* `μ_k²/r_k`. In `hom` the signal is constant but `σ_k` varies, so SNR varies from 0.059 to 0.004 across contexts.
2. **The allocator concentrates labels in one context.** In `hom`, `q = (0.66, 0.02, 0.02, …)`: all spare labels go to the lowest-noise context. In `het` the same happens to the highest-SNR context (`q = 0.66`, the rest at the 0.02 floor). Neyman instead spreads labels over every context (`q` from 0.04 to 0.14). This is the bang-bang optimum derived for `c = 0`, observed.
3. **So the gain is oracle subgroup selection.** The allocator is handed the exact `μ_k` and `r_k`, so it knows in advance which context to test, and testing one good subgroup is far more powerful than testing everywhere. The null is valid (calibration passes), but the comparison is *not* a like-for-like allocation improvement. It reflects the repository's known caveat: stratified or subgroup monitoring changes which alternative is being detected (an intersection-null test with a chosen stratum).
4. **The common-bet arm collapses** (power ≤ 0.055): when labels concentrate in one context, a pooled bet is mis-scaled for it. So the per-context bet is essential to the effect, consistent with the derivation.
5. **Precedent.** Allocating samples by estimated e-value growth among strata/hypotheses is the idea in e-PS (arXiv:2609.26651, `REPO-AUDIT`), and the myopic version exists in this repo. With exact knowledge there is no novelty here. The open question is whether it survives *learning* `μ_k, r_k` from the same hard budget.

### Consequence

Candidate A is **not falsified** and **not supported**: A1 shows an oracle-knowledge upper effect, not a method result. The stop rule in the protocol would send us to the fallback, but the stop was triggered by a mis-specified control, not by the mechanism failing. A2 (below) is registered as a *new* protocol and does not edit A1.

## A2 (to be registered): does it survive estimation?
Needs: an SNR-constant control for the tie test; moments **learned** from burn-in labels counted against the same hard budget; equally equipped comparators (Neyman and the Robust-ASI path with estimated `r̂`; a sequential growth-learning allocator in the e-PS spirit); misspecification (wrong-sign `μ̂`); nonstationary alternatives.
