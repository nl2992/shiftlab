# G6 (partial): label release times (checkpoint B; `src/shiftlab/sota_search/g6.py`, `outputs/h2c_next/g6_delay_budget.json`)
Cost-null e-processes re-implemented with **per-event release times** (the label of step s becomes available at s + d_s; moments use labels released by t−1; the wealth factor for step s is applied at its release; discounting runs on the release-time axis). 400 seeds, G1 null stream and concept δ=2 abrupt (t0 = 700), threshold 1/α, base delay 5. Null FA / harm power:
| delay model | labels | pooled (C0-like) | discounted (C1) | H2c |
|---|---|---|---|---|
| fixed 5 | 10% | .010 / .275 | .015 / .388 | .010 / .590 |
| independent uniform +0..20 | 10% | .010 / .265 | .015 / .362 | .007 / .593 |
| zero-cost outcomes late (+30) | 10% | .025 / .278 | .030 / .347 | .010 / .618 |
| costly outcomes late (+30) | 10% | .003 / .230 | .005 / .365 | .005 / .547 |
| fixed 5 | 20% | .010 / .647 | .005 / .787 | .015 / .900 |
| independent | 20% | .015 / .610 | .007 / .762 | .013 / .897 |
| zero-cost late | 20% | **.043** / .557 | **.045** / .710 | .025 / .882 |
| costly late | 20% | .003 / .615 | .000 / .760 | .003 / .858 |
**Validity matrix.** Independent random delay: PROVED for this construction (release independent of X; each factor has conditional mean ≤ 1 given the released past), and the simulation agrees (null FA ≤ .015). Outcome-dependent delay: NOT covered by the theorem. The predicted anti-conservative direction (good outcomes late, so released labels over-represent costly outcomes) moves null FA toward the level (.043–.045 for non-guided methods at 20% labels vs 0.05) but does not exceed it at 400 seeds, so the evidence is "no violation detected, direction as predicted, margin thin"; 400 seeds cannot separate .045 from .05. The opposite direction (costly late) is conservative and costs 0–0.08 power. H2c is less affected than the cost-only methods (null FA .025 vs .043–.045 in the worst case). Dependence for the cost-null methods was **not** re-run here (the earlier Brier-method result — strong autocorrelation breaks all e-processes — is the only dependence evidence); clustered losses and regime-dependent availability not implemented.
