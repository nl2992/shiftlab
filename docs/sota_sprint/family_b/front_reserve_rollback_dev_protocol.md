# Front-loaded certified host with rollback reserve: development screen

**Status:** exploratory candidate screen only. This is a mechanism-composition lead, not a novelty
claim or confirmatory validation.

## Question

Family B found that rollback helps on reversals only after a promotion, while front-loading can
bring certified decisions forward but may spend the hard label budget before recovery evidence is
available. Does reserving 20% of the label budget for the post-decision monitor let a front-loaded
certified host improve reversal cost while retaining its late-improvement advantage?

## Candidate

`B7-front-reserve-rollback` wraps `gated_adaptive_range+front` in the existing restart monitor,
reserves 20% of the budget before the host's first verdict, and enables the existing post-promotion
rollback detector. The base host and restart monitor each receive alpha/2 as in the registered B
family. The rollback alarm remains a cost-control mechanism; this experiment makes no claim of
anytime-valid rollback or robustness to serial dependence.

## Screen

* T=2000, B=200, c_q=.05, c_s=5, delay according to the registered regime.
* Fresh paired development seeds, base `2026110905`, 50 seeds per regime.
* Regimes: `V_reversal_1000`, `W_reversal_700`, `V_late_600`, `W_late_1000`, `V_better_a`,
  `V_null`.
* Candidate panel: `B7-front-reserve-rollback`, its parent `rmm:gated_adaptive_range+RMM`,
  `B2`, `gated_adaptive_range+front`, `Choe-Ramdas EB + front`, `CONTROL_never_switch`, and
  `A5b`.
* Primary outcome: paired net deployment cost. Also record promotions, rollbacks and label use.
  Development null counts are diagnostics only.

## Retention rule

Retain only if B7 beats both its RMM parent and the strongest published certified comparator on
both reversal regimes, while its mean cost is no worse than the best applicable baseline on both
late regimes and does not materially regress on the stationary alternative. Otherwise stop this
candidate. Any retained result requires an independent implementation audit, fresh parameterized
regimes and seeds, and the registered-scale null analysis before any validity or SOTA claim.

## Outcome

The candidate failed the retention rule. It was more costly than its RMM parent on both late
regimes: +24.26 [13.22,35.30] on `V_late_600` and +16.62 [9.47,23.77] on `W_late_1000`.
On the two reversals it was +6.74 [-1.24,14.72] and +3.68 [-8.01,15.37] versus that parent,
so there is no evidence of reversal improvement. It also lost to B2 on both reversals (+18.86
[10.66,27.06] and +9.52 [-0.07,19.11]). Mean promotions on the late regimes were .22 and .02,
versus .88 and .52 for the parent. **Stop B7.** Front loading consumed the reserved opportunity
cost through delayed promotion and did not yield a useful recovery gain. On `V_null`, it promoted
1/50 times; this is a small diagnostic, not validity evidence. Raw records are under ignored
`outputs/sota_sprint/front_reserve_rollback_dev/`.
