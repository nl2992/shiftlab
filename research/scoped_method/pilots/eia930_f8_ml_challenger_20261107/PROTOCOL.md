# EIA-930 F8 model-pair discovery: trained challenger

**Status:** prospective development profile screen. It is not a method evaluation or confirmation.
The initial EIA persistence/day-ahead pair has already been screened and did not match F8; its
records remain untouched in `eia930_f8_development_20261107/`. This is a new challenger trained
only on the 2021 training year. Development evaluation is limited to 2022–2023. No 2024–2025
outcomes or method costs will be opened in this screen.

## Dataset and feedback contract

Use the frozen EIA-930 respondents `PJM`, `ERCO`, and `CISO`, the six official balance CSVs and
provenance already recorded in
`research/scoped_method/pilots/eia930_f8_development_20261107/source_manifest.json`. EIA values
are current historical revisions; label release at one hour after event is simulated using EIA's
nominal availability schedule. The three BAs are correlated subclusters under one data provider.
Use the 2021 training and 2022–2023 development windows and the same imputation, UTC continuity,
and threshold rules from the earlier protocol.

## Frozen model pair

For each BA independently, set `cutoff` to its 2021 90th-percentile actual demand. The incumbent
predicts high-load label 1 iff `D[t-24h] >= cutoff`. The challenger is a single
`HistGradientBoostingClassifier` fit only on eligible 2021 examples to predict `D[t] >= cutoff`.
Frozen hyperparameters: `max_iter=150`, `learning_rate=0.05`, `max_leaf_nodes=15`,
`l2_regularization=1.0`, `random_state=1729`. Train with inverse-frequency class weights computed
from the 2021 training labels; classify positive iff predicted probability is at least 0.5.

Frozen numeric features at time `t`: `DF[t]`; actual demand lags at 1, 24, 168 and 336 hours;
mean and maximum actual demand over the prior 24 hours (ending at `t-1`); and sine/cosine pairs
for UTC hour, weekday, and day-of-year. All features use only the EIA values with timestamps at or
before `t`; the model weights and cutoff use only 2021. Rows with a missing feature, missing target,
nonpositive D/DF, or populated EIA imputed-demand field are excluded. No feature/threshold
preprocessing is estimated from 2022–2023 labels.

## F8 profile gate

On 2022–2023, compute only: eligible event count, disagreement frequency between incumbent and
challenger, challenger correctness among disagreements, and contiguous 2,000-hour episode count.
The F8 target matches only if disagreement frequency is in `[0.01, 0.05]` and challenger
correctness on disagreements is at least `0.85` in at least two of the three registered BAs. No
policy outcomes, net costs, or tuning based on 2022–2023 results are produced in this step. If the
profile fails, stop this candidate pair; do not move the threshold or classifier cutoff after
seeing the profile.

If the profile passes, freeze a separate method comparison protocol before running policies. A
positive method result will still require a separately untouched future window and another
independent provider/domain. No F8 novelty or e-process guarantee follows from this profile screen.
