# Spec: Page (1954) CUSUM / Hinkley (1971) Page-Hinkley as implemented in river / scikit-multiflow

Status: retrieval spec (step 1), short. Not yet independently checked. Written 2026-11-06. Nothing
executed. The primary papers (Page 1954 Biometrika 41:100-115; Hinkley 1971 Biometrika 58:509-523)
were NOT read (paywalled); only implementations and the Shin et al. reference list were. Classical
statements below are marked UNVERIFIED.

## 1. Citation, versions, code

- Page, E. S. (1954). Continuous inspection schemes. Biometrika 41(1/2):100-115 (cited by both
  docstrings below). Hinkley, D. V. (1971). Inference about the change-point from cumulative sum
  tests. Biometrika 58(3):509-523 (UNVERIFIED, not cited by either implementation read).
  Sebastiao & Fernandes (2017), cited by river for the PH test (docstring only).
- river `river/drift/page_hinkley.py`: repo online-ml/river, file blob sha
  `c14c82121e19afc9d251fdb5339a00a89f3f48f8`, last file commit
  `d7085cde5bf90898b338d1ad522c71b9b9aa26f8` (2026-09-21); repo HEAD read at `4768de0579f977315e65cd23ee658534c1d62c26` (2026-11-02);
  latest release tag 0.26.1 (release-to-commit mapping not checked).
- scikit-multiflow `src/skmultiflow/drift_detection/page_hinkley.py`: repo scikit-multiflow/
  scikit-multiflow (not archived flag, last push 2023-11-02), master `d073a706b5006cba2584761286b7fa17e74e87be`
  (2020-11-18), file blob `540768647359664217ad8951a580d8cce0713711`.
- Both read in full via the GitHub contents API; copies in `.../scratchpad/edet/ph_river`,
  `ph_skmf`.

## 2. Native problem and estimand

Detect an increase (river also a decrease, `mode`) in the mean of a real stream without a model of
the pre- or post-change law; no null hypothesis, no false-alarm calibration; the threshold lambda is
a user constant. Feedback: every value observed immediately. Classical Page CUSUM (known
pre/post laws): S_n = max(0, S_{n-1} + log LR_n), alarm when S_n >= h, optimal in Lorden's sense
(Shin et al. cite Lorden/Moustakides for the optimality, v4 p2; Page's own derivation UNVERIFIED).

## 3. Exact algorithm

river (read):
```
update(x):  if drift_detected: _reset()
  x_mean.update(x)                     # running arithmetic mean over ALL points since reset
  dev = x - x_mean
  sum_inc = alpha*sum_inc + dev - delta
  sum_dec = alpha*sum_dec + dev + delta
  min_inc = min(min_inc, sum_inc); max_dec = max(max_dec, sum_dec)
  if x_mean.n >= min_instances:
     test_inc = sum_inc - min_inc ; test_dec = max_dec - sum_dec
     drift = test_inc > threshold  (mode up) | test_dec > threshold (down) | either (both)
```
Initial min_inc = +inf, max_dec = -inf, sums 0. Detection strictly `>`.

scikit-multiflow (read): `x_mean += (x - x_mean)/sample_count` (sample_count starts at 1);
`sum = max(0, alpha*sum + (x - x_mean - delta))` (a reflected, CUSUM-form recursion, increase only);
`sample_count += 1`; return without testing while `sample_count < min_instances`; alarm if
`sum > threshold`; reset on next call.

## 4. Defaults

Both: min_instances = 30, delta = 0.005, threshold (lambda) = 50, alpha = 1 - 0.0001. river adds
mode = "both" (two-sided). The scikit-multiflow docstring example uses a 0/1 stream shifted to
4..7. river example (seeded) reports a change at index 1006 (doctest in the file).

## 5. Guarantee

None. No ARL/PFA guarantee, no assumption set. Thresholds are not calibrated to alpha; with alpha < 1 the
sum is an exponentially discounted drift statistic. The running mean includes post-change data, so
power degrades after long pre-change runs. Not a statement of the papers (UNVERIFIED).

## 6. Mapping to ShiftLab; achievable tier

Contract has labelled, delayed, budgeted losses; PH runs on whichever labelled values arrive
(label-clock or masked). Tier: T1 only for the plain full-information stream by running river on the
same input (never ported by the authors' code; "author" here is the library). Contract version: T3
(masked, delayed, source-moment standardised, simulation-calibrated threshold).

## 7. Existing ShiftLab code

- `src/shiftlab/sota_search/detectors.py:193-203` `page_hinkley`: statistic
  m_t = sum of ((obs - mu)/sd - delta) with delta = 0.1 (default), statistic m_t - min_s m_s, one-sided
  (increase), updated only when a label has arrived (delay via `shift_time`, mask `label_mask`).
  DISCREPANCIES vs river/skmf: (a) centering uses the nominal source mean mu and sd from a
  separate source stream (`source_moments`, l.91-103), not a running mean; (b) no forgetting
  (alpha = 1) and no `min_instances`; (c) delta = 0.1 in standardised units vs 0.005 raw; (d) river's
  min-subtraction form is kept (equals skmf's reflected form only when alpha = 1); (e) no reset
  after alarm; threshold chosen elsewhere (file l.25-45 labels it SOURCE_INSPIRED_BASELINE);
  (f) increase only, river default mode is both. With known pre-change mean it is Page's CUSUM on
  the standardised loss with reference value delta, i.e. the same family as `cusum` (l.182-190,
  slack 0.5) and `paired_cusum.py`; the two differ only by reflected vs min form and slack.
- Honest tier: inspired-by / T3; must not be called "river PageHinkley" in tables. River defaults
  (30, 0.005, 50, 0.9999) are not used anywhere in the repo (grep of the files read).

## 8. Reproduction tests

- Running river on a seeded stream: doctest "Change detected at index 1006, input value: 5" for
  `random.Random(12345)`, `rng.choices([0,1], k=1000) + rng.choices(range(4,8), k=1000)` and
  default `PageHinkley()` (file docstring, river @ d7085cd). Reproducible only with river's own
  mean implementation; a Python port should match the index.
- Identity: with alpha = 1, river's `sum_inc - min_inc` equals skmf's reflected `sum` only if the
  skmf recursion is the same cumulative sum with a running floor; in general the two reset-free
  statistics coincide (Lindley identity: max(0, sum_{k<=n} y_k - min_{j<=n} sum_{k<=j} y_k))
  (UNVERIFIED against Page, standard).

## 9. Open questions / UNVERIFIED

Page 1954 and Hinkley 1971 content; the exact installed river version for 0.26.1; behaviour when
alpha < 1 (differs between the two libraries since river keeps the min of the discounted sum while
skmf reflects at zero).
