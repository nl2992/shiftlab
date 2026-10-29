# RPOQ S6 and S6b: CRSP label-allocation replay, results

**Branch:** `research/rpoq-s1-fatal-flaw-audit`. **Date:** 2026-10-29. **Protocols:** [S6](rpoq_s6_crsp_allocation_headroom_protocol_v1.md), [S6b](rpoq_s6b_validation_selected_variance_protocol_v1.md).

| Label | Value |
|---|---|
| Data | CRSP CIZ next-day panel `crsp_ciz_next_day` v`5211412140dcb86f08f9` (WRDS), test split 2020–2025. The user confirmed the licence covers this use and instructed its use. Raw panel kept outside Git; only aggregate result files are committed |
| Design | 10 disjoint cohorts of 300 PERMNOs from the train-split universe (seed 20261029), 94k to 126k test events each; 20 query seeds per cohort; budgets 5% and 20% of events |
| Evidence level | Exploratory external-sequence replay. Release clock (next date), 5 bps costs and the conditional-mean null are **imposed**. Crossings are descriptive, with no error control |
| Claim level | **None.** No candidate beat the benchmarks |
| Artifacts | `outputs/rpoq_s6_crsp_headroom_v1/`, `outputs/rpoq_s6b_crsp_asivs_v1/` (results, per-run CSV, checksums); code `src/shiftlab/dive/rpoq_crsp_replay.py`, `rpoq_crsp_replay_b.py` |
| Figures | Not generated. `AGENTS.md` requires PaperBanana, which needs an image-model API key not available in this session. Dependency not met; no substitute generator used |

On these cohorts the candidate policy has a lower cost than the reference (mean paired excess cost −4.9 to −7.1 bps per event), so the meaningful direction is **benefit certification** (can the monitor show the candidate is better under a label budget). The harm direction is reported as descriptive.

## S6 (registered): mean final log-wealth, benefit direction

Cohort-cluster bootstrap 95% intervals over 10 cohorts (each cohort averaged over 20 query seeds).

| Budget | Uniform | Neyman/ASI (linear) | Neyman − uniform | Oracle (evaluator-only) | Oracle − uniform | Crossing rate (uniform / Neyman / oracle) |
|---|---|---|---|---|---|---|
| 5% | 1.41 [1.02, 1.78] | 1.09 [0.76, 1.41] | **−0.33 [−0.51, −0.17]** | 3.87 [2.40, 5.32] | +2.46 [1.16, 3.66] | 0.31 / 0.19 / 0.79 |
| 20% | 6.54 [5.01, 7.87] | 4.80 [3.78, 5.67] | **−1.74 [−2.42, −1.03]** | 10.71 [6.10, 15.20] | +4.17 [1.07, 7.51] | 0.84 / 0.77 / 0.96 |

Full feedback (every label): 20.34 [13.80, 26.69].

- The linear Neyman/ASI allocation is **worse** than uniform at both budgets, with intervals excluding zero.
- The oracle reference (reads outcomes, not implementable) shows large allocation headroom, so the protocol's "headroom is small, stop" rule did not trigger.

## S6b (registered): ASI-VS, benefit direction

The residual-variance model is chosen per cohort on validation data only (selected `log` in 8 of 10 cohorts, `log_abs` in 2, `lin` in none, at both budgets).

| Budget | ASI-VS | ASI-VS − uniform | ASI-VS − linear Neyman | ASI-VS − oracle |
|---|---|---|---|---|
| 5% | 1.36 [0.97, 1.75] | −0.05 [−0.22, +0.15] | **+0.28 [+0.05, +0.50]** | −2.51 [−3.65, −1.26] |
| 20% | 6.06 [4.93, 7.23] | −0.49 [−1.27, +0.34] | **+1.26 [+0.53, +2.07]** | −4.66 [−8.48, −0.75] |

**Registered verdict: not supported.** The criterion required ≥ +0.5 log-wealth over both uniform and linear Neyman with a lower bound above 0 at both budgets. ASI-VS clearly improves on the linear Neyman rule, but it is statistically indistinguishable from uniform at both budgets (intervals include 0), and it recovers only a small part of the oracle gap.

## Harm direction (descriptive)

Log-wealth is negative for every implementable rule (for example uniform −0.46 at 5% and −0.99 at 20%) because the candidate is better on average. Under full feedback the harm e-process nonetheless crossed `1/α` at some date in 50% of cohort-level runs; the oracle crossed in 16% at 20%. Positive-excess periods exist in the data, and with imposed dependence and non-stationarity these crossings cannot be separated from a validity failure of the imposed null. They are reported as observations only.

## What this does and does not establish

- On real CRSP data at matched budgets, **no allocation rule tested beat uniform querying.** One baseline from the Active Statistical Inference family (linear residual-variance model) is significantly worse than uniform; a validation-selected variant repairs it back to parity.
- It does **not** show that no allocation rule can help: the oracle gap is large. It shows that residual-variance allocation with the models tried does not capture it on this stream.
- Baselines not run: the repo's evidence-directed rule, Robust ASI, PPRM, Podkopaev–Ramdas, `comparecast`. A win or loss here says nothing about those.
- The same cohorts were used to observe the S6 results before S6b ran; S6b's design used validation data only, and its protocol was committed before the S6 results were read. A one-cohort, two-seed smoke run on the test split was seen earlier and is disclosed in the S6b protocol.

## Consequence for the goal

"Verified win on synthetic and real data over the known benchmarks" is **not met**: S3 and S3b closed the adaptive-policy branch, and the best implementable real-data candidate ties uniform. The real-data result is a clean negative with a measured headroom (oracle − uniform of +2.5 and +4.2 log units) that a better implementable rule would have to approach.
