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

## A2 (protocol [`SYNTHETIC_PROTOCOL_A2.md`](SYNTHETIC_PROTOCOL_A2.md)): allocation from learned moments

1,000 seeds, burn-in 400 events / 100 labels counted against the cap, per-context Kelly bets. Artifacts: `outputs/rpoq_next/screen_a2/results.json`. Null crossing ≤ 0.031 for every arm (limit 0.07), spend ≤ 398 of 400.

Power, `ρ = 0 / 0.6`:

| Setting | uniform | neyman-est | rasi-est | growth-fixed | growth-online |
|---|---|---|---|---|---|
| null | 0.017 / 0.015 | 0.018 / 0.018 | 0.015 / 0.016 | 0.031 / 0.031 | 0.011 / 0.009 |
| const | 0.227 / 0.245 | 0.227 / 0.253 | 0.232 / 0.237 | 0.347 / 0.349 | 0.145 / 0.163 |
| hom | 0.240 / 0.255 | 0.215 / 0.225 | 0.219 / 0.225 | 0.388 / 0.395 | 0.150 / 0.163 |
| het | 0.256 / 0.262 | 0.310 / 0.296 | 0.284 / 0.279 | 0.523 / 0.516 | 0.254 / 0.301 |
| anti | 0.170 / 0.177 | 0.265 / 0.252 | 0.200 / 0.206 | 0.365 / 0.367 | 0.161 / 0.181 |

**Registered verdict: NOT PASSED.** Primary contrast (max of the growth arms minus the best of uniform/neyman/rasi, het): +0.239 [0.204, 0.275] at `ρ=0` and +0.265 [0.228, 0.302] at `ρ=0.6`, which meets that part. The tie control fails: `growth-online − neyman` in const is −0.082 [−0.109, −0.054] and −0.090 [−0.119, −0.063]. Reported as a fail. Observations: the sequential learner (`growth-online`) is **worse than uniform** in most settings (re-estimating from noisy data hurts), and `growth-fixed` beats Neyman in const by +0.120 [0.086, 0.153] where there is nothing to find, which prompted A2b.

## A2b (protocol [`SYNTHETIC_PROTOCOL_A2B.md`](SYNTHETIC_PROTOCOL_A2B.md)): placebo and fair-bet diagnostic

1,000 seeds. Artifacts: `outputs/rpoq_next/screen_a2b/results.json`. Null crossing ≤ 0.031.

| Quantity (95% CI) | `ρ=0` | `ρ=0.6` |
|---|---|---|
| het: growth-fixed (best bet) − best baseline (best bet, incl. placebo) | +0.213 [0.176, 0.252] | +0.210 [0.172, 0.246] |
| het: growth-fixed − random_conc (ctx bets) | +0.222 [0.183, 0.261] | +0.210 [0.173, 0.246] |
| const: growth-fixed − random_conc (ctx bets) | +0.083 [0.051, 0.116] | +0.084 [0.051, 0.116] |
| const: growth-fixed (best bet) − best baseline (best bet) | +0.022 [−0.014, 0.059] | +0.020 [−0.015, 0.054] |

**Registered verdict: INCONCLUSIVE.** "Concentration explains the effect" is not triggered (het gap to the placebo ≈ +0.21). "Growth-aware selection adds value" requires the const gap to the placebo within ±0.03; it is +0.083. Reading: random concentration plus per-context bets is itself a handicapped arm (0.264 vs 0.325 for uniform with a pooled bet), and growth-aware selection merely recovers the level of the best pooled baseline in const (+0.02, not significant). In het, where signal differs across contexts, it is far ahead (+0.21) even against a fair best-bet baseline.

**What is and is not established.** In this stationary generator with heterogeneous signal-to-noise and a stratified null, learned growth-aware concentration beats equally equipped baselines, calibrated and cap-respecting. Not established: robustness to nonstationary alternatives (concentrating on a burn-in favourite is exactly what fails when signal arrives later or moves), whether the gain is more than known active-subgroup/e-PS-style allocation, or any real-data effect. A3 tests the first.

## A3 (protocol [`SYNTHETIC_PROTOCOL_A3.md`](SYNTHETIC_PROTOCOL_A3.md)): confirmatory screen, fair baselines, nonstationary alternatives

1,000 fresh seeds (base 2026), `scripts/rpoq_next/analyze_a3.py` applied to `outputs/rpoq_next/screen_a3/results.json`. `Δ = growth_fixed(best bet) − max{uniform, neyman, rasi, random_conc}(best bet)` in power, paired bootstrap 95% interval.

| Setting | best-baseline power | growth_fixed (best bet) | Δ [95% CI] |
|---|---|---|---|
| null (`ρ=0.6`) | 0.029 | 0.028 | −0.001 [−0.013, +0.011] |
| const `ρ=0` | 0.343 | 0.347 | +0.004 [−0.031, +0.039] |
| const `ρ=0.6` | 0.345 | 0.354 | +0.009 [−0.028, +0.046] |
| het `ρ=0` | 0.290 | 0.505 | **+0.215 [+0.177, +0.253]** |
| het `ρ=0.6` | 0.298 | 0.514 | **+0.216 [+0.177, +0.255]** |
| het_onset `ρ=0.6` | 0.055 | 0.084 | +0.029 [+0.010, +0.049] |
| het_flip `ρ=0.6` | 0.342 | 0.222 | **−0.120 [−0.157, −0.082]** |

Rule 1 (validity) pass: null crossing at most 0.029 for every arm; spend at most 398 of 400. Rule 2 (tie) pass. Rule 3 (primary) pass. Rule 4 (robustness): `het_onset` passes (but all arms have power ≤ 0.084, so it is nearly uninformative), `het_flip` **fails**.

### Registered verdict: SUPPORTED WITH RESTRICTION (as a synthetic screen only)

Growth-aware, learned-moment concentration with per-context bets beats equally equipped baselines, including the random-concentration placebo and each baseline's better bet type, **when the alternative is heterogeneous across observable contexts and stays put after the burn-in**. It is calibrated and respects the hard cap. It is **materially worse** when the signal moves after the burn-in: in `het_flip` the placebo that concentrates on a random context (0.342) beats the informed allocator (0.222), and so does plain uniform with per-context bets (0.279).

### Failure condition (to be stated in any claim)
The method bets on the burn-in's favourite context. If the favourite loses its signal, the allocator spends the budget in the wrong place and is worse than not trying. The sequential re-estimating variant (`growth_online`) did not fix this and was worse than uniform in most settings in A2.

### What this is, and is not
- It is a restricted, calibrated advantage in a stratified-null, heterogeneous-SNR, stationary-after-burn-in family. That is essentially active subgroup selection, a known idea family (e-PS-style allocation by estimated growth; unresolved against the two unread 2026 preprints).
- It is not evidence for the general thesis that growth-aware allocation beats variance-based allocation: with a common bet the two coincide (derivation), and the advantage here comes from per-context bets plus concentration.
- Nothing here is real-data evidence.
