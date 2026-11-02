# B3+ case-study screening protocol

Registered 2026-11-02, **before any new dataset was downloaded or screened**. The method is
frozen first (commit `e846107`); no method parameter may change during screening.

## 1. Frozen method under test

**P7s**: P3b's disagreement-gated paired IPW e-process and promotion threshold, unchanged, plus
settled-decision acquisition. `acq_shape="settled"`, `r_max=1.0`, hopeless floor `0.25`, settled
floor `0.0` (q still clipped at `p_min=0.05`). Defined in
`scripts/promising_directions/b3_plus_policy.py`; specified in `B3_PLUS_METHOD.md` section 8 of
`B3_PLUS_RESULTS.md`. **Frozen. Not tuned per dataset.**

## 2. Evaluation configuration, identical for every dataset

`T = 2000` events per episode, budget `B = 200`, `c_q = 0.05`, `c_s = 5`, 100 shared
query-randomisation seeds, seed base `20261101`. Episodes are non-overlapping within the locked
window, `K = min(50, floor(L/2000))`. Comparators: P0, P3b, P6, and P2 where available. P1 is a
hindsight reference, never a deployable baseline.

Delay is declared **per dataset before evaluation**, from the dataset's own documented feedback
latency where one exists, otherwise the audit rule capped at 100 events. The declared delay is
recorded in the registry before the locked window is read.

## 3. Pre-registered SUCCESS rule

A dataset becomes a case study only if **all** of the following hold.

1. **B3+ improves on P3b.** The 95% CI of the paired `P7s - P3b` net-cost difference lies
   entirely below 0. Bootstrap over episodes when `K >= 5`; over seeds when `K < 5`, and the case
   is then marked LOW-POWER in every table it appears in.
2. **Switching is actually worth doing on this stream.** `mean(P7s) < mean(P0)`. Without this,
   "B3+ beats P3b" only means it wastes less on a stream where no one should deploy certified
   switching at all. This condition is why airlines, bank, elec2 and criteo are **not** case
   studies despite P7s beating P3b on all four.
3. **No leakage.** The model pair is selected on train/dev windows only; realised locked-window
   losses are never used to pick a pair, a delay or a parameter. Labels are released only after
   the declared delay. The hard budget holds pathwise.
4. **Mechanism is explicable.** The benefit is attributable from saved records (promotion time,
   labels before and after promotion, switch and rollback counts).
5. **Distinct dataset.** Not another episode set, another model pair, or a relabelling of a
   dataset already selected.

`USELESS` statuses: `USELESS_INELIGIBLE`, `USELESS_NO_HEADROOM`, `USELESS_NO_IMPROVEMENT`,
`USELESS_UNSTABLE`, `USELESS_DATA_QUALITY`, `USELESS_DUPLICATE`.

## 4. Headroom pre-check, computed on dev data only

A pair is eligible for locked-window evaluation only if, **on the dev window**:
disagreement rate `>= 0.02`; the challenger's dev loss is below the incumbent's; and
`(dev advantage per event) * T > c_s`, i.e. switching could repay its cost within an episode.
Failing this is `USELESS_NO_HEADROOM`, decided without touching the locked window.

## 5. Mandatory disclosure of the screening denominator

The five selected cases are a **selected set**, because selection in section 3 condition 1 uses
the locked-window outcome. Therefore:

- Every candidate ever entered into the queue is recorded in `discarded_cases.json` /
  `successful_cases.json` with its status, before-the-fact declared delay, and source.
- `B3_PLUS_FIVE_CASE_STUDIES.md` and the manuscript **must** state the total number screened,
  the number eligible, and the number selected, in the caption or body of the main table.
- The five may be presented as five positive case studies. They may **not** be described as an
  unbiased success rate, nor may the paper imply the method was evaluated only on these five.
- The seven-stream table (where P7s beats P3b on 7/7 but clears condition 2 on only 3) stays in
  the paper as the unselected comparison.

Violating this disclosure would make the empirical claim misleading even though every individual
number is real.

## 6. Current standing under this rule

| Stream | P7s vs P3b | P7s < P0 | Status |
|---|---|---|---|
| spam | -6.66, CI below 0 | 247.43 < 849.00 | **SUCCESS** (LOW-POWER, K=1) |
| rialto | -5.31, CI below 0, episode boot | 98.42 < 202.06 | **SUCCESS** (K=16) |
| weather | -3.20, CI below 0 | 472.57 < 504.00 | **SUCCESS** (LOW-POWER, K=3) |
| airlines | -0.56, CI below 0 | 780.84 > 776.80 | `USELESS_NO_HEADROOM` (cond. 2) |
| bank | -0.57, CI below 0 | 427.61 > 419.38 | `USELESS_NO_HEADROOM` (cond. 2) |
| elec2 | -0.06, CI below 0 | 397.52 > 389.50 | `USELESS_NO_HEADROOM` (cond. 2) |
| criteo | -0.04, CI below 0 | 699.16 > 693.92 | `USELESS_NO_HEADROOM` (cond. 2) |

**3 of 5 cases in hand. 2 more independent datasets required.** Screened so far: 7.
