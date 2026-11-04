# Version-indexed challenger: chronological real-data development screen

**Status:** one-pass exploratory screen; candidate is not retained as a SOTA improvement.

**Budget comparability warning:** v2 used a separately funded retraining channel with labels from
the entire preceding evaluation window. Those labels were not charged to the policy budget. This
screen is not an end-to-end budget comparison; the later “charged” run also had a provenance bug and
is invalidated. See the [corrected provenance screen](versioned_real_provenance_fixed_results.md).

## Construction

Runner: `scripts/sota_sprint/versioned_real_dev.py`. Output: ignored artifact
`outputs/sota_sprint/versioned_real_dev/records.json`. It reuses the UCI loaders in
`scripts/sota_sprint/fresh_real.py` and writes no registered fixed-loss cache. For each chronological
series, the incumbent logistic model is fit on the first 15%; challenger v1 is a frozen
HistGradientBoosting model fit on the first 30%; v1 is evaluated for 2,000 rows; v2 is retrained
at that boundary using labels through the v1 evaluation window and then evaluated for 2,000 rows.
The version gate tests each version only on its own post-activation events. Delay follows the
registered dataset delay; query/switch costs and B=200 follow the sprint contract. Two-model
baselines receive the available challenger in a replaceable slot; Model Picker sees all models
and masks labels issued before activation.

This was one development run per dataset, without seed variation or a new locked protocol. The
2,000 labels used to train v2 are available through a separate supervised-training channel and
are **not** included in the policy query budget or net cost. Therefore the screen measures gate
cost conditional on an externally funded retraining pipeline; it does not establish end-to-end
cost effectiveness. Results are descriptive and selection-biased toward these five datasets.

## Results

Net-cost differences are version gate minus comparator; negative favors the gate.

| Dataset | Gate net | Labels | Promoted | Δ RMM | Δ front gate | Δ Model Picker |
|---|---:|---:|:---:|---:|---:|---:|
| metro | 184.10 | 22 | yes | -67.90 | -11.05 | -1.10 |
| beijing_pm25 | 1427.00 | 200 | no | +340.00 | 0.00 | +486.90 |
| bike_hour | 534.50 | 130 | yes | -34.50 | +12.15 | +88.15 |
| appliances | 924.00 | 200 | yes | -103.00 | +35.60 | +227.30 |
| household_power | 1365.10 | 122 | yes | -90.90 | +4.75 | +73.35 |

The gate beats RMM on four datasets and loses badly on Beijing; its mean paired difference is
+8.54 cost units (worse). It beats the front-loaded certificate only on metro, ties Beijing, and
is worse on three; mean difference +8.29. It loses to the unprotected version-reset Model Picker
on four datasets and wins narrowly on metro; mean difference +174.92. Model Picker promotes in
all five, but this comparison does not measure false-promotion risk. On Beijing, v2's observed
error was lower than the incumbent's, yet the certificate did not promote within its 100-label
version reserve; this points to a possible power and allocation issue rather than a harmful update.
The gate's promotion count is 4/5, but this is not a calibrated false-promotion rate.

The candidate therefore **fails the current real-stream retention criterion**: it does not
improve over the strongest applicable baselines consistently, and its advantage over RMM is
small on average and driven by four selected datasets. Do not claim SOTA or proceed to confirmatory
validation for this exact construction. Retain the code and findings only as development evidence.
A plausible next direction is to reduce spending on weak early versions while preserving the
version-wise conditional test; any alpha/budget allocation change needs a fresh, predeclared screen,
including harmful-update and null streams. First charge retraining labels and costs in an
end-to-end comparison.

## Post-hoc allocation sensitivity

After inspecting the five streams, I added configurable fixed alpha/budget weights and ran a 1:3
v1:v2 allocation on the same data. This is explicitly post-hoc, not independent evidence. Alpha
and query allocations were (0.0125, 0.0375) and (50, 150) out of total alpha .05 and budget 200.
The weighted gate's net-cost differences versus the equal split were +0.00 metro, +0.00 Beijing,
+2.10 bike_hour, -3.45 appliances, and +1.05 household_power (mean -0.06; mean absolute change
1.32). Labels by version were metro 16/6, Beijing 50/150, bike 18/114, appliances 50/121, and
household_power 47/76. The reallocation does not materially improve the result or alter the
retention decision. The implementation is exposed through `version_weights` in
`scripts/sota_sprint/versioned_challenger.py`; the runner records this sensitivity as
`version_indexed_gate_v1v2_1to3`.
