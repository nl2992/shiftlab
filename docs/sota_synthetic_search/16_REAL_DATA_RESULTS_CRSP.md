# 16. CRSP replay results (single run of the frozen protocol in doc 15; exploratory, imposed clock)

10 cohorts, 20 query seeds, date-batched, 95% cohort-bootstrap intervals. Source: `outputs/sota_search/crsp_replay/{runs.csv,summary.json}`.

| direction | labels | parent log-wealth | DK log-wealth | DK − parent [95% CI] | crossing parent / DK |
|---|---|---|---|---|---|
| harm | 5% | −0.71 | −1.25 | −0.54 [−0.62, −0.46] | 0.000 / 0.000 |
| harm | 20% | −1.41 | −1.90 | −0.49 [−0.63, −0.35] | 0.015 / 0.015 |
| benefit | 5% | +0.79 | +0.29 | −0.50 [−0.64, −0.38] | 0.290 / 0.295 |
| benefit | 20% | +4.09 | +1.68 | −2.41 [−2.79, −2.09] | 0.795 / 0.740 |

**Verdict against the pre-set rule:** DK is **not supported on real data, and the effect is reversed**: its log-wealth is significantly *lower* than the plain pooled parent in all four cells, and its crossing rate is no higher. Neither arm detects harm (the candidate is not worse than the reference in this stream); both detect the benefit direction at 20% labels, the parent more strongly.

**Interpretation.** The discounted bet reacts to the recent past; on a stream with a stable mean excess (no change-point) pooling all history is more efficient, so discounting only adds variance. This is consistent with the synthetic design: DK targets *adaptation after a change*, and this replay contains no known change. So the replay neither contradicts the synthetic change-point results nor supports a real-data win. HG and BD could not be tested here (doc 15). No benchmark was beaten on real data.

**Consequence for the exit condition.** Synthetic: partial (doc 11). Real: not met, DK worse than its parent. The honest summary is that the synthetic gains do not transfer to this stationary-ish replay; a real test of the change-point claim needs a dataset with a known or verifiable regime change and a null segment, which this stream does not provide. No re-tuning or re-run was done.
