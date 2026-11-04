# Fresh paired decision-frontier development screen

**Status:** exploratory only; regime set was previously studied in the sprint, so this is a
replication/diagnostic, not confirmatory evidence. Raw records are ignored under
`outputs/sota_sprint/decision_frontier_dev/records.jsonl`; manifest seed base `2026110901`.

The common runner generated 50 paired streams for each of ten regimes and replayed ten policies
(A5b/A1b and eight certified published ports). Main comparison uses net deployment cost J; lower is
better. The “best” published baseline below is selected by within-screen regime mean, so contrasts
are descriptive and carry selection optimism.

| Regime | Best certified published port | A5b minus best, mean [paired 95% CI] | A5b promotion |
|---|---|---:|---:|
| V_late_600 | Xu acquisition-only | +15.20 [+8.79,+21.61] | .08 |
| W_late_1000 | Xu acquisition-only | +1.02 [-1.03,+3.08] | .06 |
| V_better_a | Choe-Ramdas EB + front | +1.38 [-4.43,+7.18] | .58 |
| V_better_b | Choe-Ramdas EB + front | +8.92 [+5.87,+11.96] | 1.00 |
| V_better_c | Choe-Ramdas EB + front | +6.69 [-1.50,+14.87] | .86 |
| V_dep_better_r5 | Gated adaptive range + front | +29.48 [+21.59,+37.37] | .46 |
| V_near | SMCS + retain-incumbent | +0.18 [-3.30,+3.65] | .06 |
| V_bursty | Choe-Ramdas EB + front | +5.99 [-3.40,+15.37] | .56 |
| W_better_dep_r7 | Gated adaptive range + tuned pacing | +53.29 [+39.79,+66.79] | .40 |
| W_better_dep_r9 | Gated adaptive range + tuned pacing | +92.60 [+78.88,+106.32] | .20 |

A5b stayed at 0/50 promotions on both tested nulls (V_null_dep_r8 and W_null_dep_r95); this is
too small to support a safety statement. Against Xu on V_late_600, A5b was +15.2 (95% CI
[+8.8,+21.6]) but promoted in only 4/50 versus Xu's 39/50. This sharpens the current P2 trade-off:
the dependence-robust certificate remains conservative in cost and power on these fresh paired
streams, and its strongest case is safety under the declared null family, not broad cost SOTA.

## Research consequence

Two follow-up attempts have not produced a method improvement: finite start-prior changes gave a
post-hoc V-late signal without W-late replication; reallocating alternative Markov-mixture mass
toward persistence gave no replicated W-dependent benefit and raised stationary costs. The next
technical lead is a tighter, certified profile upper bound for the composite Markov null likelihood.
An isolated irregular-gap diagnostic retains one shared nuisance mean while bounding persistence and
was 0.03–0.62 nats tighter than the current factorwise cell bound on the tested 80-observation
sequences. The integrated profile-denominator candidate was subsequently screened and stopped: it
did not improve late-regime cost, produced only a noisy gain on one dependent alternative, and ran
about 63x slower than A5b. A direct Sethi et al. composite-Markov comparator on matched fixed-gap
acquisition was also screened and stopped; it was substantially more conservative in this budget.
These are development results, not safety evidence. Any future advancement requires an anytime-valid
implementation, null simulation at the locked 1000-seed scale, and a fresh comparison against the
strongest certified ports.
