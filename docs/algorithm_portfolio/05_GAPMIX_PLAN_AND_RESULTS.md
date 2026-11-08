# Track B: Gap-Mix+ (dependence-aware evidence with evidence-adaptive querying)

Full record: branch `research/methods-recovery-2026-11-07`, `docs/methods_recovery/`:
- preregistration: `00_PREREG_GAPMIX_PLUS.md` (`1fc3a300`);
- tuning: `10_TUNING.md`;
- Amendment A1: `01_AMENDMENT_A1.md` (`b74a1fc3`, frozen neighbour pacing `17dd261b`);
- results: `20_GAPMIX_PLUS_RESULTS.md`.

**Design.** Gap-Mix evidence (exact-gap Markov LR, 4-start restart mixture, declared ρ̄=.8) with a
3-parameter querying governor driven by evidence distance-to-threshold, gap, budget, horizon,
pending labels and delay.

**Arms.**

| Arm | Evidence and acquisition |
|---|---|
| 1 | Markov-LR evidence, DSS acquisition |
| 2 | Gap-Mix evidence, DSS acquisition |
| 3 | Gap-Mix evidence, PAVE acquisition |
| 4 | Gap-Mix+ |
| 5 | Gap-Mix evidence, tuned fixed pacing |
| 4a | Gap-Mix+ with its evidence term frozen (ablation) |

Extra comparators: QSG envelope, gap-10 thinning, `episode_front`, uniform.

**Data.** 48 target cells and 64 neighbour cells × 60 eval seeds; null grid of 18 cells × 500
streams.

| registered criterion | value | pass |
|---|---|---|
| 1. ≥3% better than the strongest valid comparator | **−3.97% [−4.66, −3.27]** (Arm 4 is worse) | no |
| 2. attribution vs Arm 4a | 1.19% [0.74, 1.66] better | yes |
| 3. beats Arms 2, 5 and 3 (pooled and gate-on) | 1.66%, 0.79% and 1.73% pooled; gate-on vs Arm 3 0.65% [−0.61, 2.01] | no |
| 4. null validity (UCB ≤ .1, ρ ≤ .8) | worst .060 | yes |
| 5. neighbours within 3% | ρ=0: −7.0%; d=50: −3.6%; B/T=.5: −12.7% | no |

**Verdict: STOP (directive §5.7: it cannot beat the strongest valid simple comparator).** The
valid gap-10 thinning is 2.6% cheaper than Gap-Mix+. The evidence-adaptive governor contributes
about 1%, which is real but too small and smaller than the evidence choice.

**Kept (scoped) finding.** Gap-Mix is valid at declared ρ̄=.8. It is 13.6% cheaper than the
valid Markov-LR evidence in this run (14.7% in GAVE-R) and 9.5% cheaper than the QSG envelope.
It is an evidence-construction result, not a new acquisition algorithm, and its novelty against
Markov sequential-testing priors (Sethi et al. overlap, `docs/gaver/40_PRIOR_ART_CHECK.md`) is
unresolved.
