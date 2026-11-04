# A5b profile-denominator development screen

**Status:** exploratory development only. This is an attempt to tighten the composite-null
likelihood upper bound used by A5b. It does not change the null family, alpha spending, alternative
mixture, or query policy. It has no prior-art novelty claim; the potential contribution, if any, is a
deployable safe-power/cost improvement enabled by a tighter sequential universal-inference bound.

## Candidate and validity construction

`A5b-profile-first` changes only the denominator for the earliest started evidence component. Every
10 queried outcomes it computes a branch-and-bound upper bound on that component's full prefix
likelihood over `p in [0,.5]` and `rho in [0,1]`, conditioning on the previous sign when the segment
does not start at the first observation. Between checkpoints, it multiplies the cached prefix upper
bound by the existing factorwise upper bound on the short suffix. For any fixed null parameter,
`L(prefix) * L(suffix) <= sup L(prefix) * sup L(suffix)`, so this remains an upper bound. Other
started components use the existing bound. The profile routine relaxes persistence per transition
within each rho interval, maximizes the resulting concave p profile using a tangent upper bound, and
bisects rho intervals until the requested likelihood tolerance is reached.

## Paired screen

* Fresh seed base: `2026110903`; 20 paired seeds per regime.
* Regimes: `V_late_600`, `W_late_1000`, `V_better_a`, `V_better_b`, `V_dep_better_r5`,
  `W_better_dep_r7`, `W_better_dep_r9`, `V_null_dep_r8`, `W_null_dep_r95`.
* Policies: `A5b-profile-first`, `A5b`, `A1b`, `xu_acquisition_only`,
  `gated_adaptive_range+pace_tuned`, `discern_style`.
* Contract: T=2000, B=200, c_q=.05, c_s=5, alpha=.05.
* Outcomes: paired net-cost differences and promotion rates. Development null counts are not safety
  evidence. The primary screen does not claim superiority over the selected-in-screen best baseline.

## Retention rule

Retain only if it shows a directional cost improvement over A5b on both late regimes or both
dependent regimes, without a material cost regression on stationary alternatives. Otherwise stop.
Any retained variant requires fresh parameterized regimes, the full certified comparator panel, a
registered test, and at least 1000 seeds per relevant null before a validity/power or SOTA claim.

## Outcome

The candidate did not meet the retention rule. Versus A5b, paired cost changes were 0.0 on both
late regimes; +2.30 [-0.01,+4.61] on V_better_a; +1.10 [-0.81,+3.01] on V_better_b; -5.45
[-12.75,+1.85] on W_better_dep_r7; and -0.40 [-1.24,+0.44] on W_better_dep_r9. It promoted in
7/20 on W_better_dep_r7 versus 5/20 for A5b; on the two nulls both were 0/20 (diagnostic only).
Against the best certified port selected within this panel, costs were higher by 27.89
[16.38,39.40] on V_late_600, 5.14 [0.49,9.78] on W_late_1000, 59.44 [41.64,77.24] on
W_better_dep_r7, and 76.53 [49.13,103.94] on W_better_dep_r9.

The profile calculation did not improve the actual late-regime cost and only showed a noisy gain
on one dependent alternative. Mean policy runtime was 14.44 seconds per episode (median 13.70,
max 30.45) versus 0.23 seconds for A5b. **Stop this integrated variant.** A tighter denominator
alone did not translate into SOTA cost/power and the current implementation is too slow for this
deployment loop. Raw records and the run manifest are under ignored `outputs/sota_sprint/`.
