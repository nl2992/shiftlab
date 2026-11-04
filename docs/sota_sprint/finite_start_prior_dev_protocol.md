# A5b finite start-prior development screen

**Status:** exploratory development only; not a validation protocol or SOTA claim. Registered before
the runs below. This candidate was proposed after reviewing existing validation results, so the
tested regimes are already known and any apparent gain requires confirmation on new regime
instances.

## Candidate

`A5b-finite-start-uniform` uses the same gap-indexed Markov SUI evidence, composite-null upper bound,
adaptive query density, rho shrinkage, cycle alpha spending, and fixed delay as A5b. It changes only
the prior over sparse SUI start points. With a hard label budget `B` and start stride 10, the maximum
number of starts in one test segment is `M = max(1, floor((B-1)/10)+1)`. The prior assigns 0.5 to the
first start and spreads 0.5 uniformly across the remaining `M-1` starts (or assigns 1 to the only
start when `M=1`). It is fixed before observing labels, sums to one, and every component retains the
same per-start validity argument. No prior novelty claim is made: mixtures over start times are
established; the hypothesis is a finite-budget allocation that may improve late-change utility.

## Screen

* Fresh exploratory seed base: `2026110801`, 20 paired seeds per regime.
* Regimes: `V_late_600`, `W_late_1000`, `V_better_a`, `V_null_dep_r8`, `W_null_dep_r95`.
* Policies: `A5b-finite-start-uniform`, `A5b`, `A1b`, `CONTROL_never_switch`.
* Contract: frozen SOTA sprint contract (`T=2000`, `B=200`, `c_q=.05`, `c_s=5`, `alpha=.05`,
  release-before-act, registered regime delays).
* Outcomes: paired net-cost difference versus A5b, promotion rate on null regimes, first-promotion
  time, label use, and switch count. Twenty-seed null rates are diagnostics only, not safety evidence.
* Stop interpretation: kill the candidate if it shows no directional cost gain on either late
  regime, or if the gains require materially worse stationary cost. Any development signal must be
  re-registered and tested on fresh regime instances and at least 500 null seeds before supporting a
  claim.

## Amendment A (after reading the first screen)

The first screen showed a directional but inconclusive `V_late_600` cost change (−11.2 vs A5b,
95% normal paired interval [−23.3,+0.9]), no change on `W_late_1000`, a small inconclusive stationary
change (−1.9 on `V_better_a`), and identical promotion counts on the two nulls (0/20 each). To check
whether the late signal depends on allocating too much mass to the first start, one additional
variant sets first-start weight to .25 and spreads the remaining .75 uniformly across the other
budget-feasible starts. This amendment is post-result development tuning, not confirmation.

* Fresh exploratory seed base: `2026110802`, 20 paired seeds per regime.
* Same five regimes and contract as above.
* Policies: `A5b-finite-start-late`, `A5b-finite-start-uniform`, `A5b`, `A1b`,
  `CONTROL_never_switch`.
* The same stop interpretation applies. Any gain selected from this amendment requires new, unseen
  regime instances for confirmation.

## Amendment A outcome (development only)

On seed base `2026110802` (20 paired seeds), `A5b-finite-start-late` reduced mean net cost on
`V_late_600` by 13.2 versus A5b (paired SD 27.1; approximate paired 95% t interval [-25.9, -0.5]).
It was identical on `W_late_1000`, and cost 10.3 more on `V_better_a` (interval [-7.6, 28.2]).
The uniform variant reduced `V_late_600` cost by 9.8 (interval [-21.4, 1.8]), was effectively
identical on W late and stationary regimes. Both candidates had 0/20 promotions on each tested
null; A5b also had 0/20. The `.25` variant promoted on 7/20 V-late episodes versus 2/20 for A5b,
but the 20-seed null screen is not safety evidence.

This is a narrow, post-result-tuned signal on one V-late regime, with no gain on W-late and a
stationary cost trade-off. **Do not promote this as a paper contribution or claim SOTA.** Retain only
as a development lead. Any follow-up must compare against the strongest certified published
baseline and test on newly registered late-change and stationary regimes, plus at least 500 fresh
seeds on each relevant null; the start-mixture weighting itself is established prior art.

