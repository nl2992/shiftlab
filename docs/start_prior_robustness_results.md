# Fixed-prior robustness results

This exploratory CUDA screen compared five fixed Beta start-time priors and full-stream betting
under expected-horizon misspecification and four independent delay laws. The frozen design is in
[start_prior_robustness_protocol.md](start_prior_robustness_protocol.md); all stream metrics,
null summaries, paired tests, hashes, and the exact executed source snapshot are in
[outputs/start_prior_robustness/](../outputs/start_prior_robustness/).

The alternative grid contains 216 cells and 200 paired streams per cell (43,200 generated
streams, reused as common random numbers across prior and delay conditions). The null screen
contains 72 scenario/query/horizon/delay cells with 500 streams each. Generation resolved to the
NVIDIA RTX 4060 Laptop GPU.

Across all alternative cells, mean detection was:

| Fixed prior or comparator | Mean detection | Difference from uniform |
| --- | ---: | ---: |
| Uniform Beta(1,1) | 60.9% | reference |
| Center Beta(2,2) | 61.2% | +0.26 percentage points |
| Late Beta(2,1) | 61.9% | +0.99 percentage points |
| Early Beta(1,2) | 58.7% | −2.19 percentage points |
| Edge Beta(0.5,0.5) | 60.2% | −0.73 percentage points |
| Full-stream betting | 40.7% | −20.20 percentage points |

The outcome depends on the assumed horizon. At 0.5× / 1.0× / 1.5×, center-prior detection was
50.17% / 67.33% / 66.06%, versus 50.92% / 67.42% / 64.44% for uniform. Center therefore lost
0.75 points under the short prior horizon, was essentially tied at nominal, and gained 1.61 points
under the long prior horizon. The late prior led uniform by 1.81 and 2.14 points at the first two
scales, then trailed by 0.97 points at 1.5×. In 1,080 paired cellwise tests with Holm adjustment,
center had no significant wins; late had four significant wins, all in its favor; early had 24
significant losses, and full-stream betting had 108 significant losses. These are exploratory
screening findings, not evidence for changing the default.

Event-order detection was identical across the four delay laws for every paired stream/method
combination (64,800 paired keys, zero discordances). That is expected: the monitor waits for a
complete event-order prefix before evaluating evidence, so independent delays affect when an alarm
becomes available, not which event-time prefix crosses the threshold. Among detections, average
wall-clock delay for center was 608.4 events with immediate feedback, 611.8 with uniform 0–6,
615.8 with uniform 0–12, and 620.4 with fixed 12. Delay laws therefore change operational latency
without changing event-order power in this simulator.

Across 432 method/null cells, empirical false-escalation rates were at most 1.6%. The largest
one-sided exact Clopper–Pearson upper bound was 4.80% with simultaneous 95% Bonferroni coverage.
With only 500 streams per cell, this is a calibration screen, not final certification.

## Method implication

The prior evidence suggests sensitivity to the expected-horizon specification. A mathematically
valid next candidate is a fixed multihorizon start mixture. Let E_(h,k) be a valid component
e-process starting at the kth of eight positions under horizon scale h ∈ {0.5, 1.0, 1.5}. Freeze
weights ρ_h ≥ 0 and w_k ≥ 0 before a stream, with both weight vectors summing to one, and define

    E_t = sum_h ρ_h sum_k w_k E_(h,k),t.

This remains an e-process by convexity and does not update weights from observed outcomes. The
candidate is a standard fixed mixture, not a novelty claim. Its purpose is to hedge uncertainty in
the planned monitoring horizon. Compare it with the uniform and late priors on a fresh development
block, then use separate null and alternative blocks for confirmation if it improves robustness.

The current run used the exact source snapshot recorded in its manifest. The working runner has
since received a small CLI reporting correction; the executed snapshot is retained so the metric
hashes and code provenance remain verifiable.

No figure was made. If a visual is added, use PaperBanana as requested by the project owner.
