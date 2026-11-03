# Failure Atlas v2: experiment audit and result-to-claim review (native substitute)

Reviewer: fresh general-purpose subagent, 2026-11-03, commit 68094ff, read-only; own scripts in
`.../scratchpad/review2/audit.py`. Canonical HKUSTDial/ARIS skills are not installed (machine-wide
search and plugin catalog checked); same model family as the author. Recorded in substance.

## Audit

- **(a) Pairing: PASS.** Streams keyed only by (seed base, regime, seed). Every zero-switch row
  equals the never-switch loss for its unit (16,683 frozen, 4,995 strong, 22,238 real rows; 0
  mismatches). `gated+front_only` (frozen) equals `gated_adaptive_range+front` (strong) on all 1300
  rows. The SMCS front-rule fix changed 9 / 8 of 1300 rows; means unchanged. Re-running slices with
  committed code reproduced stored rows exactly (72 synthetic, 64 real).
- **(b) Seeds: PASS synthetic; real streams not fresh.** Validation bases appear in no other
  manifest; frozen hashes match 64ee5a4; QSG logic unchanged afterwards. Caveats: frozen validation
  rows existed on disk ~25 min before Amendment 2 was finalised, so "before reading any validation
  row" is unverifiable (low risk: the amendment tightened the criterion); SMCS front change made
  after frozen rows existed (negligible); `strong_hosts.py` mtime after the strong run (no material
  change on reproduction). The real streams are the same nine caches used in `discovery_real` and
  in `real_repair` (a development run of FLQ/QSG v0), so "not used to develop the repair" is false.
  Real validation used 10 policy seeds, not the contract's 20.
- **(c) Budget / no future access: PASS.** Max 200 labels everywhere; release-before-act, delay >= 1;
  QSG's query rule reads only the disagreement indicator.
- **(d) Recomputation: PASS.** All headline numbers match to 0.1 (primary 6/6, 6/6, 5/6, 5/6,
  strong gated 6/6, strong DISCERN 0/6; certification; QSG head-to-heads; openml_ldpa -15.7
  [-37.8,-0.5]; rialto -3.1 [-3.9,-2.1]). Not stated in the report:
  1. Our variants that pass the strict criterion (gated+QCE .04, DISCERN+QCE .03, Xu+QCE .05) have
     no advantage: best of them vs Xu ties 4/6 stationary regimes, small win V_bursty -3.8
     [-7.0,-0.5], losses V_dep_better_r5 +2.2 [+0.3,+4.5] and V_near +1.3 [+0.2,+2.4].
  2. openml_ldpa is fragile: episode t-test p=.12, Wilcoxon p=.054, 20/32 episodes favour QSG; one
     episode (-290.6) drives it; without it -6.9 [-15.5,+1.6]. Only rialto is robust (p=7e-6, 15/16).
- **(e) Statistics: PARTIAL.** Same-seed comparator selection handled conservatively (intersection-
  union vs all six published: one-sided p <= 2.7e-6 on the five significant stationary regimes).
  Holm over 6 stationary regimes: 5 survive (adj. p <= 2.2e-5), V_near does not (.12); Bonferroni
  over 13 regimes gives the same. No correction across ~35 policies / many pairs. Real episodes are
  consecutive windows of one stream: even episode CIs are optimistic. The ORIGINAL protocol primary
  claim (>= 3 powered real datasets, no null regime above the bound) FAILS; "primary MET" refers only
  to Amendment 1's narrower host-vs-repair outcome, registered after dev showed where front-loading wins.
- **(f) Provenance: PASS with caveat.** All nine hashes match the README; seven byte-identical to B3
  losses; openml_ldpa and uci_occupancy cannot be regenerated from this repo.

## Result-to-claim

Verdict on REPORT section 6 (as of 68094ff): **partially supported**. Unsupported: re-scoping to a
theoretical "pointwise conditional null" class after the registered empirical criterion failed;
"7-48" holds on 5/6 not 6/6; "two powered real streams" is one robust stream plus one outlier-driven
one, neither fresh, and the protocol required three; FLQ and QSG are bundled while the head-to-head
numbers are QSG's.

Claim the reviewer would sign:

> On fresh synthetic seeds under a binding budget, front-loaded acquisition with query-conditional
> evidence lowered net cost relative to the original host for every certified host except the strong
> DISCERN re-port, and QSG beat every published certified-method port by 7-48 per 2000 events on 5 of
> 6 stationary alternatives (Holm-adjusted), at the price of failing the registered false-promotion
> criterion under rho=.8 persistence (.32 vs .094), regressing on late-onset (+8) and reversal (+33)
> regimes, and losing to uncertified methods and the economic-replacement control (+10 to +41).
> Variants that meet the registered criterion are not better than Xu acquisition-only. On real data,
> one previously exposed stream (rialto) shows a small robust gain (-3.1).

SOTA: no meaningful SOTA; the gain is purchased by trading away strong-dependence safety, which is
what certification is for. "Within the certified class" is unfair: under the registered definition
that class contains none of the winning variants. Comparators are ports, not author code.

ICML competitiveness: not competitive. Low novelty (front-loading = DISCERN pi=1; QCE = sequential
sign test on discordant pairs; started mixture ~ e-detectors); the finding is an expected
explore-early trade-off on the author's own Bernoulli simulator. Missing: dependence theory, tuned
non-uniform pacing baselines per host, independent real data, author-code comparators, and any
method that is both certified under persistence and faster than Xu.

Recommendation: **pivot / stop the SOTA framing**; keep the atlas and harness as a benchmark /
negative-result contribution. Most valuable next experiment: one locked, pre-registered fresh-seed
test of a persistence-robust certified variant (block/thinned gap, or a mixture over persistence
levels) against Xu acquisition-only and tuned non-uniform pacing baselines; success = promotion
<= .094 on rho=.8 and .95 nulls and CI < 0 on >= 4/6 stationary alternatives; stop if none exists.

## Author response

Accepted in full. REPORT.md sections 5, 6 and 9 and validation_real.md were revised to the
reviewer's claim and findings; the "not used to develop the repair" statement is corrected.
