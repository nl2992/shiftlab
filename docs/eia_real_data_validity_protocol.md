# WP4 minimum: EIA real-data validity and injected-harm protocol

**Status:** specification, 2026-10-27. Written before any monitor was run on an EIA path. The
paired stream builder had not yet produced the development windows when this text was drafted.
The specification hash and UTC time are recorded in Section 9 before the first registered run.

This protocol is the WP4 minimum level of
[the phase goal](agent_goal_stratified_monitor_phase.md) (Section 4 WP4 and Section 4A). It is a
**validity and positive-control study**, not a method comparison and not a confirmation. Both
algorithm branches of this phase (WP2 stratified, WP3 data-efficient) stopped at their
pre-screens, so the stratified arm is not alive and is not run here.

## 1. Questions

1. **Validity (primary).** On real EIA demand paths, does every monitor in the WP1 panel keep its
   per-path false-alarm probability at or below `alpha = 0.05` under the random-orientation null?
2. **Positive control (descriptive).** When harm with a known onset is injected into the same real
   paths, how often, how fast, and at what label cost does each monitor detect it?
3. **Unmodified streams (descriptive).** On the real frozen-versus-weekly policy pair, what do the
   monitors conclude, and how often do they agree with the deterministic full-feedback verdict?

Question 3 is not ground truth for harm. Costs are imposed research costs.

## 2. Data and decision task

- **Source.** `data/raw/eia/EBA.zip`, retrieved 2026-10-20T01:32:49Z, SHA-256
  `3a6143c4bd853c3d6a9d9d3bb3ca7f1603a641835e9c7a050e5c8a927101936f` (receipt in
  `data/reports/eia_2026_holdout_readiness.json`). Respondents CISO and ERCO.
- **Event.** An hour with all four contemporaneous EBA series (D, DF, NG, TI) present and an
  observed next-hour demand. Features are those four values; the outcome is next-hour demand.
- **Threshold.** `tau` per respondent = 90th percentile of next-hour demand over
  2019-01-01 – 2024-12-30.
- **Action.** Procure reserve if the policy's forecast exceeds `tau`.
- **Imposed costs.** Shortfall (no reserve, demand > `tau`) 5; idle reserve (reserve, demand ≤
  `tau`) 1; otherwise 0. Implemented in `src/shiftlab/dive/reserve_costs.py`.
- **Policies.** Deployed: frozen Ridge fitted on 2019–2024. Reference: weekly-refit Ridge (the
  existing EIA retraining protocol), with an assumed label delay of 24 hours for its refits.
- **Full-information pairing (assumption).** Reserve procurement does not change demand, so one
  realised outcome scores both policies. Paired cost `Z = c(deployed) − c(reference)` lies in
  `[−5, 5]` and is exactly zero when the actions agree.
- **Paths.** One continuous development stream 2025-01-01 → 2026-10-19T17Z per respondent, split by
  calendar into four registered paths, indexed in this order: `p0` CISO-2025, `p1` CISO-2026,
  `p2` ERCO-2025, `p3` ERCO-2026. All four windows were examined in earlier forecasting replays;
  they are development data.
- **Pre-window rehearsal.** The same procedure shifted one year back (fit 2019–2023, run 2024)
  provides the validation disagreement path for pacing and the injected-harm band. Nothing from
  the four registered paths is used to set any parameter.
- **Label scarcity** is imposed by our own known query randomisation, so propensities are exact.
  Label tariffs are constant at 1 per queried event (the pacer and reserve rules are the WP1 rules
  with constant tariffs).
- **Evaluator side.** Demand and `Z` are evaluator-side. A monitor reads `Z` only at queried
  events (and at no event for agreements, where it is known to be zero).

Implementation: `src/shiftlab/dive/eia_paired_reserve.py`, `scripts/build_eia_paired_reserve.py`.

**Outcome-free stream facts, seen before freeze.** Disagreement depends only on the two policies'
actions, not on the outcomes. The builder reported the following before any monitor ran.

| Respondent | `tau` | Window | Events | Disagreement rate | Disagreements (approx.) |
|---|---:|---|---:|---:|---:|
| CISO | 31781.4 | 2025 | 8,640 | 0.0003 | 3 |
| CISO | 31781.4 | 2026 | 6,943 | 0.0216 | 150 |
| ERCO | 64002.0 | 2025 | 8,664 | 0.0001 | 1 |
| ERCO | 64002.0 | 2026 | 6,797 | 0.0010 | 7 |

The rehearsal disagreement rates are 0.0015 (CISO) and 0.0003 (ERCO), so the gated arms' fixed
propensity is 1 at every budget.

Consequences, stated before the run:
- On `p0`, `p2`, and `p3`, the random-orientation null is close to vacuous for every arm. With a
  handful of nonzero `Z`, no valid monitor can accumulate evidence, so a pass there carries little
  information.
- **`p1` (CISO-2026) is the informative real-data null path.**
- The injected-harm control (Section 6) creates many more disagreements after onset, and it is
  the informative real-data positive control.
- The audit's split boundaries drop the hours of 2024-12-31 and 2025-12-31. This is inherited and
  harmless.

## 3. Arms

All arms come from the WP1 panel, with WP1's code semantics, `alpha = 0.05`, and the fixed stake
mixture `(0.05, 0.1, 0.2, 0.4, 0.8)`. Within a replicate all arms share the same signs and query
uniforms.

| Arm | Construction | Labels |
|---|---|---|
| `full_feedback` | Mixture on `Z − epsilon`, bound `5 + epsilon` | Every event (unmatched upper reference) |
| `ungated_ht` | Uniform Horvitz–Thompson, `q = budget rate`, bound `5/q + epsilon` | Any event |
| `gated_ht_fixed` | WP1 gated HT, fixed disagreement propensity from the rehearsal rate | Disagreements only |
| `gated_ht_paced` | WP1 gated HT, 200-event past-only pacer | Disagreements only |
| `gated_eb_paced` | WP1 paced gating with the plug-in empirical-Bernstein engine | Disagreements only |

Budget rates `r ∈ {0.02, 0.05, 0.10, 0.20}`, each with the WP1 hard reserve stop.

**Not run, with reasons.**
- `gated_ppi_paced`: its proxy would need a delayed-feedback refit on real streams. That is outside
  the minimum level.
- Stratified arm: WP2 stopped.
- Timans, PPE, and Xu adaptations: WP1 S3 measures them on synthetic paths. Real-data validity of
  their constructions is not claimed here.

Implementation: `src/shiftlab/dive/orientation_replay.py`. It is vectorised over replicates, and
tests require it to equal the scalar WP1 replay (`replay_gated`) per replicate.

## 4. Analysis (a): random-orientation null (primary, registered pass/fail)

- **Construction.** Independent `S_t ∈ {−1, +1}` with probability 1/2 swap the roles of the two
  policies, so the monitor sees `S_t Z_t`. Conditional on the real path, `E[S_t Z_t | path, past
  coins] = 0` and the null holds exactly. This gives `P(alarm | path) ≤ alpha` for each path; the
  check is per path, under real covariates, outcomes, and dependence.
- **Replicates.** 1,000 per path. All arms and budgets share the coins.
- **Coins.** For path `p_k`, `rng = numpy.random.default_rng(59200000 + k)`. Draw
  `signs = 2 * rng.integers(0, 2, size=(1000, n)) − 1`, then `uniforms = rng.random((1000, n))`.
- **Cells.** 4 paths × (1 full-feedback cell + 4 arms × 4 budgets) = 68 cells, at the registered
  `epsilon = 0.1`.
- **Statistic.** Alarm before the reserve stop or the end of the path.
- **Pass rule.** For every cell, the exact one-sided 95% Clopper–Pearson upper bound on the alarm
  rate is at most 0.05.
- **One registered fix.** If any cell fails, that cell is re-run once with 4,000 fresh replicates
  from `default_rng(59230000 + 100 k + j)`, where `j` is the cell's index in the registered cell
  order. Its pass or fail is then judged by the same rule. A cell that fails both the original
  check and its single re-run is a **validity failure** (goal exit C), and the phase hands back.
- **Sensitivity (descriptive, no pass rule).** The same coins at `epsilon = 0` sit on the null
  boundary, so they are the sharpest per-path check. Report them next to the primary rates.

## 5. Analysis (b): unmodified streams (descriptive)

- **Coins.** 200 query replicates per path from `default_rng(59220000 + k)` (uniforms only; no
  signs).
- **Deterministic reference.** `full_feedback` is deterministic on each path. Its alarm and alarm
  time are the full-feedback verdict.
- **Reported per arm and budget:** alarm probability; agreement with the full-feedback verdict;
  labels and events processed at alarm or stop.
- **Interpretation limit.** An alarm says that the frozen policy's imposed-cost excess over weekly
  refitting exceeded `epsilon` at some time on a previously examined window. It is not evidence of
  real operational harm.

## 6. Analysis (c): injected harm with known onset (descriptive positive control)

- **Onsets.** At fractions 0.25, 0.50 and 0.75 of each path (`floor(f n)`).
- **Injection.** After onset, every deployed procure event whose frozen margin (forecast − `tau`)
  lies in `(0, m]` is switched to no reserve (under-procurement). `m` is the median positive
  margin among deployed procure events in the respondent's 2024 rehearsal; it is set without
  looking at any registered path. Implementation: `src/shiftlab/dive/eia_injected_harm.py`.
- **Coins.** 200 query replicates per path and onset from `default_rng(59210000 + 10 k + o)`,
  where `o ∈ {0, 1, 2}` indexes the onset.
- **Reported per arm, budget and onset:**
  - post-onset detection probability, with pre-onset alarms counted separately and **never** as
    detections;
  - median and mean censored delay, in events and in hours from onset;
  - labels and dollars;
  - the injected post-onset mean excess (evaluator-side), stated next to each row.
- **Delay accounting.** Monitor labels are assumed to arrive at once. With an assumed label delay
  `d`, every HT-type alarm time shifts by `d` hours and is otherwise unchanged, because pacing and
  queries use only decision-time information. Report the `d = 0` delay and state the shift.
- **Interpretation limit.** Pre-onset alarms on these paths can reflect real frozen-versus-weekly
  differences, so this positive control is not a clean power study.

## 7. What this protocol cannot show

- That the real policy pair is harmful or harmless.
- Application utility (the costs are imposed).
- Real-time availability (EIA publication times are unknown and the data are revised).
- Any claim about prospective data. The windows are development data; see Section 8.

## 8. Prospective clock

The arms' code and the policy construction are frozen by the hashes in Section 9 at its UTC time.
Under goal Section 4A, only EIA hours whose **pull time** is after that timestamp can count as
prospective. Pull order is the guarantee; real-time availability is not. No such pull is made
in this protocol. The earliest useful prospective check is after about six weeks
(about 1,000 hours per respondent). It needs the user's go-ahead for an API key or a fresh bulk
snapshot (about 700 MB).

## 9. Freeze record

The freeze record lives in [`eia_real_data_validity_freeze.json`](eia_real_data_validity_freeze.json),
written before the first registered run. It holds:
- the SHA-256 of this file;
- the SHA-256 of `reserve_costs.py`, `eia_paired_reserve.py`, `orientation_replay.py`,
  `eia_injected_harm.py`, `eia_validity_analysis.py`, and the runner
  `scripts/run_eia_real_data_validity.py`;
- the SHA-256 of the paired-stream artifact `outputs/eia_paired_reserve/streams.parquet`;
- the freeze UTC time.

The runner refuses to start unless every recorded hash matches the files on disk. That freeze
time also starts the prospective clock in Section 8.

Seed blocks `59200000–59200003`, `59210000–59210032`, `59220000–59220003` and
`59230000–59230399` were checked as unused in `docs/`, `papers/`, `scripts/`, `src/`, and
`configs/` on 2026-10-27.

## 10. Continue / stop

- **Pass:** WP4's validity minimum is met for every arm still alive. The real-data validity table
  goes into the benchmark manuscript, and injected-harm results are reported as descriptive only.
- **Validity failure** (Section 4 rule): hard stop (goal exit C). Report it before anything else.
