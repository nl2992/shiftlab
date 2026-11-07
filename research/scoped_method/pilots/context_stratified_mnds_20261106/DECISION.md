# Context-stratified MN-DS screen decision — 2026-11-06

**Status: `BENCHMARK_ONLY`; no repair or confirmation claim.** This records the one-time Q4
replay under the frozen implementation and analysis. It does not establish a new method, a
multi-dataset transfer result, or a positive real-world validation.

## Protocol and opening

The validation-selected static source rule and the context-wise promotion/rollback composition
were frozen using Q3. The implementation and pre-opening analysis amendment were committed in
`b777e9e8` before the replay. The exact source, protocol, model, and data hashes are in
`run/code_freeze.json`; the one-opening manifest is `run/TEST_OPENED.json`. The exclusive marker
was written before predictions, losses, or policy outcomes were computed. The archive SHA-256 is
`ce71a92bc8d8d896e8eeacbbe1e73819f42e09b535a04a47d5b67d968c9ddd5f`; the frozen model SHA-256 is
`091e42ed4bfd76a2302cd177b96be72b7e7309bba1b136d44d9af7b9448ade34`.

Q4 contains 3,052 eligible chronological records from October–December 2019. The context counts
are 2,585 other, 184 Evening Standard, 152 Sputnik, and 131 TASS. The test source registry,
ordered-ID hash, and Q3-selected policy decision are preserved in the opening manifest. The
feedback release delay is simulated as 24 hours. This is a retrospective real-data replay, not an
authentic label-release experiment.

## Primary result

The candidate is the standard context-wise composition documented in the protocol, not a novel
statistical method. It requested 100 labels (5.00 cost units), made no switch, and left the
incumbent deployed in all contexts. Its predictive loss was 1,033 and net cost was 1,038, or
340.10 per 1,000 events. Never-switch had the same predictive loss, no label expenditure, and net
cost 338.47 per 1,000. The candidate therefore costs 1.64 more per 1,000 than never-switch.

Against the Q3 validation-selected static source policy, the candidate's point saving was only
2.29 per 1,000, below the preregistered 5-unit practical threshold; the simultaneous 99%
7-day moving-block interval for candidate minus static was `[-5.75, +3.62]`. It fails the frozen
primary gate. The candidate's contrasts against PFA-SR, RMM, E_rb, and E_swcert were each only
about 1.6 per 1,000, below the 5-unit threshold despite 99% intervals below zero. No candidate
context promoted, so these are label-cost reductions relative to global methods that spent the
budget, not evidence of better predictive decisions.

The static rule selected the challenger only for Sputnik based on Q3. On Q4, that policy made one
promotion and incurred 1,040 errors plus 5 switch-cost units. The candidate's 1,033 errors and zero
switches show that the validation-selected source decision did not transfer uniformly. The
candidate's source-level point differences versus static were +6.79 per 1,000 in Evening Standard,
−70.72 in Sputnik, and +9.54 in TASS; intervals are wide and each named publisher is a single
cluster. These results do not support a general source-specific intervention claim.

All 17 policy costs and paired intervals are in `run/RESULTS.md` and `run/summary.json`. Daily
sufficient statistics are in `run/daily_cost_sufficient_statistics.csv`. Private row-level paired
records remain under the ignored raw-data directory; their path and checksum are embedded in
`run/summary.json`. This result has no independent source-level replication.

## Gate compliance and interpretation

The run was opened before this checkpoint rechecked that the prior economic-headroom and novelty
gates had passed. They had not: the earlier headroom matrix found no safety-qualified method, and
the calibrated SR screen missed its null-error gate. Therefore retain this Q4 replay as a
**descriptive, exposed screen only**, not as the independent confirmation requested by the broader
research plan. Do not retune on Q4, call it confirmation, or reuse it as untouched evidence. The
remaining frozen confirmation sources must stay closed unless a distinct candidate first passes
the synthetic economic and novelty gates.

The result does not identify a distinct repair. It is consistent with the existing observation
that distributional/source heterogeneity can make a global challenger misleading, but the
context-wise gate did not deploy and its small cost differences do not meet the registered
practical threshold. The strongest current decision remains `BENCHMARK_ONLY`, not a paper-ready
method claim.

## Reproduction and hashes

```sh
uv run python scripts/sota_sprint/run_mnds_contextual_transfer.py smoke
uv run python scripts/sota_sprint/run_mnds_contextual_transfer.py freeze
uv run python scripts/sota_sprint/run_mnds_contextual_transfer.py run
```

The one-time runner refuses to overwrite `TEST_OPENED.json` or result files. Do not rerun the
opening command. The committed runner is `scripts/sota_sprint/run_mnds_contextual_transfer.py` at
`b777e9e8`. Result hashes:

| Artifact | SHA-256 |
|---|---|
| `run/summary.json` | `685ea331625bb4f09bb9f1c05b645fc2cce1f8a7c63a2f89b33fae172f65b323` |
| `run/RESULTS.md` | `d9a4f738f68367e4d05590137e15105a38095a7544f0bc8c56c8d6b2aa5d46ba` |
| `run/daily_cost_sufficient_statistics.csv` | `240d7ae7ab679301c7aa4df71507cc6e27b59066c6db486c448bc7b4f098fa2d` |

## Smallest next step

Close this candidate lane as `BENCHMARK_ONLY`; do not open another real-data holdout or search
another context partition. The bounded two-sided SR calibration has already selected alpha 0.0005
from 1,000 null streams (16 promotions; adjusted 99% Wilson upper bound 2.82%), but the late-gain
screen at that setting did not clear its frozen comparator and independent-null precision gates.
That existing-method result is documented in
`../srr_any_false_calibration_20261106/CALIBRATION_RESULTS.md` and
`../srr_late_improvement_20261106/EVALUATION_RESULTS.md`. The smallest useful next work is a
claim-bounded benchmark/case-study outline; no new candidate or confirmation run is justified by
this lane.
