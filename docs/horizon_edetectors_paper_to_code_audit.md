# Horizon-calibrated SR and CUSUM e-detectors: paper-to-code audit

**Scope.** This note documents the bounded-score Shiryaev–Roberts (SR) and CUSUM e-detectors
implemented in `src/shiftlab/dive/horizon_edetectors.py`. They are simple monitoring baselines for
the charter's conditional excess-cost score; they do not establish the null for any supplied data.

## Primary source and mapping

The primary source is Shin, Ramdas, and Rinaldo, [*E-detectors: a nonparametric framework for
sequential change detection*](https://arxiv.org/abs/2203.03532), arXiv:2203.03532v4 (2023). Its
Section 2.2 defines an e-detector by the stopped-process inequality
`E[M_tau] <= E[tau]` under every pre-change law. Section 2.3 constructs SR as a sum over all
consecutive start times and CUSUM as the maximum over those starts; Section 2.4 gives the recursive
baseline-increment forms

```text
SR_t    = f_t * (1 + SR_(t-1))
CUSUM_t = f_t * max(1, CUSUM_(t-1))
```

with both statistics initialized at zero. A fixed convex mixture of valid e-detectors is also a
valid e-detector (Proposition 2.3). The module maps these recursions to bounded-mean betting factors
`f_t(s) = 1 + s * x_t / B` for a fixed, constructor-supplied stake vector and fixed weights. Each
stake component has conditional expected factor at most one when `E[x_t | F_(t-1)] <= 0`,
`|x_t| <= B`, and the stake is fixed in advance. The code carries the recursions in log space and
does not tune stakes or weights online.

For `kind="cusum"` with multiple stakes, the implementation takes the fixed weighted mixture of
the stake-specific CUSUM statistics. This is a mixture of CUSUM e-detectors; it is not the maximum
over start times of a mixture of stake-specific factors. Each stake-specific CUSUM is bounded above
by its SR counterpart, so the fixed weighted CUSUM mixture is bounded above by the corresponding
SR mixture and inherits the same finite-horizon crossing guarantee.

The paper's standard e-SR/e-CUSUM threshold controls average run length, not a finite-horizon
probability of any alarm. This implementation uses the explicit finite-horizon calibration below;
it does not use the paper's standard `1 / alpha` threshold.

## Finite-horizon calibration used here

Fix horizon `H` and suppose each calendar-time factor is nonnegative and satisfies
`E[f_t | F_(t-1)] <= 1`. For a predictable skip, set `f_t = 1`. The SR and CUSUM statistics are
e-detectors: for every bounded stopping time `tau`, `E[M_tau] <= E[tau]`. Let `T` be their first
crossing time of `H / alpha` and stop at `tau = min(T, H)`. Then `E[M_tau] <= E[tau] <= H`, while
`M_tau >= H / alpha` on `{T <= H}`. Markov's inequality gives

```text
P(max_(t <= H) M_t >= H / alpha) = P(T <= H) <= alpha.
```

This applies to either detector and to any fixed convex mixture of its stake components. The
guarantee is finite-horizon and requires the registered horizon; it is not an anytime-valid
`1 / alpha` crossing guarantee. It relies on the conditional-mean null, boundedness, predictable
stakes/skip decisions, and valid event and feedback semantics. The class validates numeric bounds
and configuration only; it cannot verify those scientific assumptions.

## Skip and start-time convention

The implementation counts every calendar position toward `H`. A skipped position contributes
factor one and still advances the recurrence. Thus it opens a new calendar-time start: an SR sum
contains the unit contribution from that start, and CUSUM considers its unit suffix. This is the
canonical all-calendar-start construction. It does not omit skipped positions from the horizon,
reset the process after a skip, or choose starts based on outcomes. A skip decision must itself be
predictable under the null filtration. This convention keeps the new-start recursion explicit and
avoids an optional-start selection rule.

## Implementation and validation boundary

`HorizonCalibratedEDetector(kind="sr" | "cusum")` exposes a single bounded-score update API,
fixed stake mixtures, log statistics, the `H / alpha` threshold, alarm time, and strict horizon
enforcement. Its `alarm_time` uses one-based calendar positions, while WP1's `first_alarm` field is
zero-based. A stake-one observation at `x = -B` has factor zero and log factor negative infinity;
the next calendar time still admits a new start, so the SR statistic recovers from that zero factor.
`tests/test_horizon_edetectors.py` checks the log-space recursions against brute-force
products over every possible start, including skips; verifies CUSUM is no larger than SR for the
same factors; checks zero-factor recovery; and covers calibration, alarm timing, invalid inputs, and
horizon overrun.

This is an implementation-level formula and API audit, not a new theorem, empirical calibration,
power claim, or validation of the Paper 1 harm null. Real-data or synthetic false-alarm conclusions
still require a protocol that fixes the filtration, score, bound, horizon, query/feedback regime,
and evaluation design before looking at outcomes.
