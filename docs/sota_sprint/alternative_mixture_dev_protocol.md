# A5b alternative-persistence mixture development screen

**Status:** exploratory post-result development only. The reweighting uses a proper mixture over the same
alternative Markov models. It leaves A5b's composite-null denominator and validity argument
unchanged. Mixture weighting is established prior art; any contribution would have to be a measured
safe power/cost improvement for this deployment problem, not the weighting operation itself. The
candidate family and parameter values were chosen after inspecting the 2026-11-04 decision-frontier
screen; fresh seeds remove stream reuse but do not remove this selection effect.

## Motivation

The locked synthetic comparison shows that A5b is expensive on persistent alternatives, while its
alternative numerator prior assigns 0.70 mass to rho'=0 and only 0.06 to each of rho'=.5,.8,.9,.95,.98.
Test whether reallocating fixed prior mass toward persistence improves power against registered
dependent alternatives without materially degrading stationary and late-change performance.

## Fixed candidates

* `A5b-rho-balanced`: alternative rho prior `[.30,.14,.14,.14,.14,.14]` on
  `[0,.5,.8,.9,.95,.98]`.
* `A5b-rho-persistent`: alternative rho prior `[.15,.17,.17,.17,.17,.17]` on the same grid.
* Both retain A5b's p' prior, fixed-start prior, adaptive query density, null profile upper bound,
  cycle alpha-spending, and label budget.

## Screen

* Seed base `2026110902`, 50 paired seeds per regime.
* Regimes: `V_late_600`, `W_late_1000`, `V_better_a`, `V_better_b`, `V_better_c`,
  `V_dep_better_r5`, `V_near`, `V_bursty`, `W_better_dep_r7`, `W_better_dep_r9`,
  `V_null_dep_r8`, and `W_null_dep_r95`.
* Compare both candidates with A5b, A1b, Xu, gated adaptive range (front, tuned, and base),
  corrected DISCERN, SMCS+retain-incumbent, and both Choe-Ramdas-style EB ports.
* Contract: T=2000, B=200, c_q=.05, c_s=5, alpha=.05, common paired synthetic streams.
* Primary development outcomes: paired net-cost changes vs A5b and strongest certified published
  port; promotion rates on nulls are diagnostics only.

## Stop/interpretation rule

Retain a candidate only if a dependent-alternative gain is directionally replicated on both
`W_better_dep_r7` and `W_better_dep_r9`, while stationary/late costs do not erase the gain. Any
candidate surviving this screen requires a newly registered confirmation on unseen regime
instances, with at least 1000 fresh seeds per relevant null and a full certified comparator panel.
No result from this 50-seed screen is confirmatory or a SOTA claim.

## Outcome

Both reweightings failed the retention rule. On `W_better_dep_r7`, balanced/persistent deltas
versus A5b were +1.46/+3.24 (higher cost); on `W_better_dep_r9` they were -0.16/-1.52, with
paired 95% intervals spanning zero. On the stationary `V_better_a`, they cost +12.0/+13.8 versus
A5b, and costs also rose on `V_better_b`, `V_better_c`, `V_near`, and `V_bursty`. Late regimes
were effectively unchanged. All candidates had 0/50 promotions on each null, which is only a
development diagnostic. **Stop this prior reweighting.** The fixed mixture reallocation traded away
stationary evidence without a replicated dependent-alternative benefit.

Raw paired records are in the ignored output directory
`outputs/sota_sprint/alt_rho_dev/records.jsonl`; the screen manifest records the seed base and
source hashes. Because the candidates were selected after prior results were inspected, this is
negative development evidence, not a registered comparison.
