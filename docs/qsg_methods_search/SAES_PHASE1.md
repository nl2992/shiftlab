# SAES (signal-assisted economic switching): Phase 1 information audit

Pivot directive of 2026-11-08: before building a signal-to-action controller, establish whether
genuinely observable unlabeled signals carry information about relative model advantage beyond
the label history. Development data only. **Verdict: FAIL. No signal family carries enough
information to justify Phase 2.** Per the directive, the SAES algorithm search stops here.

## Data (exposed streams only; nothing sealed was touched)

`scripts/qsg_methods_search/saes_dev_build.py` rebuilds feature-bearing development streams and
stores, per event, what a deployed system sees before any label: both models' scores `s0, s1`,
and a train-standardised feature-drift statistic. Losses `l0, l1` are evaluator-side.
Output: `data/saes_dev/` (gitignored).

- **Sprint streams** (metro, beijing_pm25, bike_hour, appliances, household_power) use the exact
  `fresh_real.py` recipe. All five reproduce the archived `array_content_sha256` byte for byte,
  and the raw-zip SHA256s match `data/sprint_fresh_losses/README.md`.
- **B3 sources** (airlines first 200k rows, weather, spam, bank, rialto, elec2) use the uniform
  recipe: incumbent LR on train-old, challenger HGB on train-new, train-only preprocessing. These
  pairs differ from the archived B3 pairs. They are development streams, not reproductions.

Total: 11 streams, 198 episodes. Audit `saes_phase1.py`; outputs
`outputs/qsg_methods_search/saes_phase1.txt` and `saes_phase1_proxy.txt`.

## A. Per-event information (confidence gap on disagreements)

| stream | AUC of g=\|s1−.5\|−\|s0−.5\| for "challenger correct" | cross-fitted ρ² of calibrated proxy | effective label multiplier 1/(1−ρ²) |
|---|---|---|---|
| airlines | .565 | .011 | 1.01 |
| appliances | .636 | .058 | 1.06 |
| bank | .502 | .000 | 1.00 |
| beijing_pm25 | .606 | .028 | 1.03 |
| bike_hour | .744 | .114 | 1.13 |
| elec2 | .561 | .010 | 1.01 |
| household_power | .595 | .020 | 1.02 |
| metro | .743 | .064 | 1.07 |
| rialto | .776 | .084 | 1.09 |
| spam | .715 | .047 | 1.05 |
| weather | .610 | .039 | 1.04 |

**Price of information** (synthetic family, tuned Wald, decision cost excluding query spend,
40 dev seeds): budget 200 → 344.70; 300 → 340.89; 400 → 339.41 (λ re-tuned per budget). So
+50% free labels is worth 3.8 units and +100% is worth 5.3. A prediction-powered proxy worth
1.00–1.13× labels (median 1.04) is bounded at **≤0.7 units, typically ≈0.2**. Proxy-evidence
SAES: **STOP**.

## B. Staleness information (do signal changes predict the upcoming advantage change?)

The target is the advantage change, mean z on [t, t+300) minus mean z on [t−300, t), using the
**full** label history, which is generous to the label-only baseline. The predictors are
recent-vs-reference changes in the confidence-gap mean, the disagreement rate, the feature
drift and the score gap, plus the current confidence-gap level. Pooled over 2,447 checkpoints:
all |r| ≤ .08 (disagreement-rate change −.05 [−.09, −.01]; drift change −.08 [−.17, +.02]).

Per stream the largest effects are:
- rialto, disagreement-rate change: −.24;
- beijing_pm25: −.13 / −.12;
- bike_hour and metro, current-gap level: −.31 and −.15. These mainly reflect mean reversion
  of the noisy past window, not staleness.

Signs are inconsistent across streams. R² ≤ 6% even at the best stream. Drift-, rate- and
score-triggered SAES: **STOP**.

Do real streams change at all? Relative advantage varies beyond binomial noise on several
streams (variance ratio of window-to-window change 3–52 on openml_ldpa, uci_occupancy, appliances,
household_power, beijing_pm25, rialto). Part of that is serial dependence, not regime change
(M5). So there *is* movement to track, but the unlabeled signals do not anticipate it.

## C. Synthetic mechanism evidence (already on record)

The S-family run (NEXT_METHOD_LEDGER.md, Candidate S) is the directive's Phase 3 contrast:

| signal type | regimes | result |
|---|---|---|
| informative | 5 regimes, disagreement rate shifts exactly at the performance change | −2 to −4 per regime |
| misleading | 3 false-alarm regimes | small losses |
| uninformative | 2 silent regimes plus the original 14 | small losses (+1.2 on the original 14) |

So even a perfectly timed signal of moderate size bought little, because detecting a rate shift
takes about as long as the labels. Real signals are much weaker than that synthetic one.

## Conclusion

The new-information hypothesis was the right question: the oracle diagnostic shows change
timing is worth 11.7 units. The answer on development data is negative. The observable
signals tested are model confidence, score-distribution change, disagreement intensity and
feature drift. They carry at most a few percent of a label's worth of per-event information
and essentially no advance warning of advantage changes. No sealed seed or dataset was used.
