# Check: Page-Hinkley as implemented in river / scikit-multiflow

Independent check of `specs/page_hinkley.md`, 2026-11-06. Nothing downloaded was executed; the
two algorithms were re-implemented from the source text in own scratch code
(`.../scratchpad/check_edet/ph_port.py`, `lindley.py`) and run on the docstring stream.

## Sources actually read

- river `river/drift/page_hinkley.py` at repo HEAD `4768de0579f977315e65cd23ee658534c1d62c26`
  (commit date 2026-11-02, resolves): blob `c14c82121e19afc9d251fdb5339a00a89f3f48f8`. The last
  commit touching the file is `d7085cde5bf90898b338d1ad522c71b9b9aa26f8` (2026-09-21); file
  identical at both. Read in full (127 lines).
- river tag **0.26.1** (latest release, published 2026-08-21): blob
  `7202710020d844441002f024dda5828c269f8cba`, a different blob from the spec's pin. This is the
  version `pyproject.toml` pins (`drift = ["river==0.26.1"]`, l.15). The diff vs HEAD is type hints
  plus one line: `self._max_decrease = -1` (0.26.1) versus `float("-inf")` (HEAD). I checked that
  this is behaviourally irrelevant for `delta > -1`: after the first update `sum_decrease = delta`
  (the deviation from the running mean is 0), which already exceeds -1. My port gives identical
  alarms for both initialisations on the docstring stream and two decrease streams.
- scikit-multiflow `src/skmultiflow/drift_detection/page_hinkley.py` at master
  `d073a706b5006cba2584761286b7fa17e74e87be` (resolves), blob
  `540768647359664217ad8951a580d8cce0713711`. Repo `archived: false`, last push 2023-11-02.
- Primary papers (Page 1954, Hinkley 1971) NOT read (paywalled; not fetched). Every classical
  statement is **UNVERIFIABLE** here, as in the spec.

## Claim table

| # | Claim | Verdict | Evidence |
|---|---|---|---|
| 1 | river update rule: running arithmetic mean since reset, `dev = x - mean`, `sum_inc = alpha*sum_inc + dev - delta`, `sum_dec = alpha*sum_dec + dev + delta`, min/max tracking, test only when `n >= min_instances`, strict `>`, reset on the call after an alarm | CONFIRMED | river l.108-127; `_reset` l.83-97; the mean is updated before `dev` is computed (l.112-113) |
| 2 | Initial `min_inc = +inf`, `max_dec = -inf`, sums 0 | CONFIRMED at HEAD; CORRECTED for the pinned release | l.89-90 at HEAD; 0.26.1 has `-1` for `_max_decrease` (harmless, see above) |
| 3 | Defaults 30, 0.005, 50, 1-0.0001; river adds `mode="both"` | CONFIRMED | river l.62-69; skmf `__init__` l.53 |
| 4 | skmf: `x_mean += (x - x_mean)/sample_count` (starts at 1), `sum = max(0, alpha*sum + (x - x_mean - delta))`, increase only, `sample_count += 1`, skip test while `sample_count < min_instances`, strict `>` | CONFIRMED | skmf l.71-72, 94-97, 105-109. Added: because `sample_count` is incremented before the check, the first test happens after 29 elements, river's after 30 (off by one) |
| 5 | Docstring example: river alarms at index 1006 with value 5 | CONFIRMED | Own port of both algorithms on `rng = random.Random(12345)`, `choices([0,1], k=1000) + choices(range(4,8), k=1000)`: river port alarm (1006, 5); skmf port alarm (1006, 5) |
| 6 | alpha < 1 is a discount on the cumulative sum, the mean is NOT discounted | CONFIRMED (docstrings are misleading) | Both docstrings call alpha a forgetting factor "to weight the observed value and the mean"; the code applies it only to the sum (river l.115-116; skmf l.95) |
| 7 | With alpha = 1 river's `sum_inc - min_inc` equals skmf's reflected `sum` (Lindley identity) | CONFIRMED for alpha = 1, delta >= 0 | 200 random streams x 300 points, 0 discrepancies beyond 1e-9 (`lindley.py`). River's `min_inc` omits S_0 = 0, but with a running mean the first increment is `-delta <= 0`, so the minimum is always attained at or below 0. For alpha < 1 the two differ, as the spec says |
| 8 | No guarantee; threshold is a user constant | CONFIRMED | no alpha/ARL/PFA anywhere in either file |
| 9 | Running mean includes post-change data so power degrades after long pre-change runs | CONFIRMED mathematically, not a source statement | follows from l.112-113; classical-literature statement UNVERIFIABLE |
| 10 | Classical Page CUSUM `S_n = max(0, S_{n-1} + log LR_n)` | UNVERIFIABLE (paper not read); consistent with Shin et al. p228-230 and the Lindley form in claim 7 | |
| 11 | river version used by the repo | CORRECTED | Spec says latest release maps to HEAD unchecked: it does not map exactly (16 commits ahead of tag 0.26.1). River is imported in the repo only for ADWIN (`scripts/evaluate_eia_drift_detectors.py:19-21,75`, `src/shiftlab/dive/gated_monitor_comparison.py:10,50`) |

## ShiftLab code: `src/shiftlab/sota_search/detectors.py`

- `page_hinkley` is at l.193-203: `m += (obs - mu)/sd - delta` on label arrival
  (l.200), `mmin = min(mmin, m)`, output `m - mmin` (l.201-202), both initialised at 0 (l.197).
  `delta = 0.1` default (l.193). One-sided (increase).
- Spec discrepancies (a) fixed source moments instead of a running mean: CONFIRMED
  (`source_moments` l.91-103, used at l.195); (b) no forgetting, no `min_instances`: CONFIRMED;
  (c) delta 0.1 in standardised units: CONFIRMED; (d) min-subtraction form: CONFIRMED; (e) no reset,
  threshold chosen elsewhere: CONFIRMED, `META` entry labels it SOURCE_INSPIRED_BASELINE (l.37-41);
  (f) increase only: CONFIRMED.
- Sharper statement the spec missed: with fixed centering `mmin` starts at 0, so
  `m - mmin` is exactly the reflected recursion `max(0, st + y - delta)`. Hence ShiftLab's
  `page_hinkley(delta)` is numerically identical to its own `cusum(slack=delta)` (l.182-190,
  slack 0.5 default): it is Page's CUSUM on the standardised loss with a known pre-change mean, not
  Page-Hinkley in the river/skmf sense (whose defining feature is the running mean). Only the
  default reference value differs (0.1 vs 0.5). This is the honest tier: inspired-by / T3.
- River defaults (30, 0.005, 50, 0.9999) appear nowhere in repo code (grep for PageHinkley/
  page_hinkley over `*.py` found only `detectors.py`, `scripts/sota_search/*`, `hgxh2c/stats.py:19`
  which lists it among non-anytime-valid alarms).

## Tier call and what to do

T1 only by calling river `PageHinkley` itself on the same input; contract version T3. The spec's
tier call stands. The reproduction test (docstring index 1006) passes in an independent port and
can be used verbatim. Recommend the ledger note that the repo's "page_hinkley" must not appear
under the river/skmf name in tables and is redundant with `cusum` at equal reference value.

**Verdict: ACCEPT WITH CORRECTIONS** (river pin vs release blob; skmf off-by-one;
page_hinkley == cusum(slack=delta); Page 1954 and Hinkley 1971 content remains UNVERIFIABLE).
