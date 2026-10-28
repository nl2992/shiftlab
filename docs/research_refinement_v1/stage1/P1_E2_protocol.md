# P1: E2 acquisition and pacing protocol (H-B1a, H-B1b, H-B2)

**Status: draft for freeze review. Not frozen. No confirmation seed has been used.**
Development smoke run on the development block only (section 9). Hypotheses are those of
`FINAL_RESEARCH_PROPOSAL.md` section 4, unchanged. The mechanism (disagreement gating) is DISCERN's;
this study is a replication under the repository's decision-cost contract, and a pacing test.

## 1. Scientific scope

- Quantity monitored: incumbent decision harm, `E[Z_t | F_{t-1}] <= epsilon` with
  `Z_t = c(pi_t(X_t), Y_t) - c(pi_ref(X_t), Y_t)`, `epsilon = 0.1`, `|Z_t| <= C = 5`, `Z_t = 0`
  whenever the deployed and reference actions agree (`D_t = 0`).
- Filtration: `F_{t-1}` holds past features, past disagreement indicators, past tariffs, past
  coins and past *queried* costs. Feedback is immediate for queried events and absent otherwise.
  Propensities `q_t` are `F_{t-1}`-predictable (constant, frozen from validation, or a 200-event
  past-only tariff window); coins are independent of `Z_t`.
- Validity of each arm is as in `stage0/VALIDITY_TABLE.md` (CA-1..CA-3). The reserve stop is a
  stopping time of past spend. Nothing here establishes validity of an arm beyond that table; the
  stop rule in section 8 checks it empirically.
- Synthetic oracle truth (regime weights, expected costs, burst masks, onsets) lives in
  `Oracle` and is used only for summary endpoints. Replays receive `MonitorInputs` only; a test
  scrambles every oracle field and checks that alarms, labels and dollars are unchanged.
- Credit: gating is DISCERN's. Lemma L explains label-time propensity invariance of zero-anchor HT
  at `epsilon = 0`; it does **not** hold at the registered `epsilon = 0.1`, so fixed and paced HT
  are genuinely different monitors here.

## 2. Arms and engines

All arms use the identical engine `PredictableBoundMeanEProcess` (the default fixed-stake mixture,
stakes `(0.05, 0.1, 0.2, 0.4, 0.8)`, equal weights, `alpha = 0.05`, labelled `fixed08`), the same
increments convention and the same hard dollar reserve `target * horizon`, where
`target = r * mean(validation tariffs)`. A reserve stop occurs before an event whose maximum tariff
(2.5) the remaining reserve cannot cover. Tariffs are in `[0.5, 2.5]`.

| Arm | Query rule | Increment | Bound `B_t` |
|---|---|---|---|
| `gated_ht_fixed` | disagreements only, `q` frozen from validation: `min(1, target / mean(validation D*tariff))` | `Z/q - eps` if queried, else `-eps` | `5/q + eps` |
| `gated_ht_paced` | disagreements only, `q_t = clip(target / mean(last 200 D*tariff), 0.10, 1)` | same | `5/q_t + eps` |
| `uniform_ht` | **every event** (agreements included), constant `q = r`, coin `U_t < q` | `Z/q - eps` if queried, else `-eps` | `5/q + eps` |
| `uniform_ppi` | every event, constant `q = r`; ridge proxy `h` fitted on pre-monitor events and updated on queried events | `h + (Z - eps - h)/q` if queried, else `h` | `(5+eps)(2/q - 1)` |

**Uniform HT definition (lead requirement).** `uniform_ht` does not use the free disagreement
indicator `D_t`. It queries every event with constant `q = r`, pays the label tariff for every
query (including queries on agreement events, where `Z_t = 0`), uses increment `Z_t/q - eps` if
queried and `-eps` otherwise, and bound `C/q + eps`. Because `E[tariff * 1{queried}] = q E[tariff]`,
`q = r` makes its expected spend per event equal the gated target `r * E[tariff]`, i.e. the same
reserve. A test (`test_uniform_ht_spends_on_agreements`) shows it buys labels on a stream where
every event is an agreement while the gated arm buys none, and another that flipping the
disagreement flags leaves it unchanged. Without this the arm would collapse to fixed gated HT and
H-B1a would be vacuous.

**Engines.** Primary engine `fixed08` (default mixture; Lemma L applies at `eps = 0` only).
Secondary engine `timans_grapa` (Timans et al. GRAPA, replayed through `replay_engine` on the same
increments and bounds, 100-event source burn-in). GRAPA rows are reported for every arm but are
**not in any Holm family**.

## 3. Cells and generators

Stream length 3,200 events (`d = 16`); events 0-399 proxy training, 400-799 validation (pacer seed,
proxy validation); monitoring starts at event 800 and the monitored horizon is 2,400 events. All
indices below are in monitored coordinates. Pre-monitor events are always stationary.

All new generators call the existing synthetic generator (`_generate`, scenario
`boundary_local_harm`, severity set to 0) to obtain `X` and the standardised noise `z`, which are
identical for every severity. They then re-apply the unmodified mechanism
`mean = X0 - 0.9 X1 + severity * w_t * exp(-5 |X0 - 0.9 X1|)`, `Y = 1{mean + 0.3 z > 0}`, with a
stream-specific weight `w_t`, and the existing policies (deployed: threshold 0.5 on
`ndtr(score/0.3)`; reference: `_source_action`, FN 5, FP 1). The disagreement band is score in
`(0.3 Phi^-1(1/6), 0) = (-0.290, 0)`. Existing code is not modified (`src/shiftlab/dive/e2_acquisition_pacing.py`).

A **burst** replaces a random fraction `pi` of the events in a window by in-band events:
`X0 := 0.9 X1 + s` with `s` drawn from a band. `X1`, the tariff coordinate, and `z` are untouched.

| Cell | Generator | Budget `r` | Severity |
|---|---|---|---|
| `b1_r0.02`, `b1_r0.05`, `b1_r0.20` | `boundary_local_harm`, `w_t = 1[t >= onset]`; onset ~ DiscreteUniform{300..1500} | 0.02, 0.05, 0.20 | 1.5 |
| `b2_i` (class i) | harm from `onset ~ DU{300..1200}`; **disagreement burst after onset**: window `[onset+g, onset+g+500)`, `g ~ DU{100..300}`, `pi = 0.5`, `s ~ U(-0.290, 0)` (full band, harmful) | 0.10 | 1.5 |
| `b2_ii` (class ii) | **harmless burst, then late harm**: burst window `[b0, b0+400)`, `b0 ~ DU{100..400}`, `pi = 0.8`, `s ~ U(-0.290, -0.275)` with `w = 0` (narrow subband at `p` in `[1/6, 0.18]`); onset `= b0 + 400 + DU{100..500}`, harm to the end, no burst | 0.10 | 1.5 |
| `b2_iii` (class iii) | **recurrent harmful regimes**: harm windows `[o + 600k, o + 600k + 300)` for `k = 0, 1, ...` inside the horizon, `o ~ DU{200..600}`; each harm window carries a burst (`pi = 0.5`, full band); null in between | 0.10 | 1.5 |

Onsets are drawn per stream from the stated distributions with
`np.random.default_rng([seed, 0xE2A1])`, independently of the stage boundaries (monitor start 800,
original change 1,600, end 3,200); burst masks and in-band scores use `[seed, 0xE2B2]`; the common
query coins are `default_rng(seed + 9173).random(...)` (as in `comparison_seed`).

**Null property in class (ii).** In the burst window the per-event expected paired cost is
`E[D Z] = 6p - 1` on in-band events with `p = Phi(score/0.3) <= 0.18`, hence below `epsilon`. A test
checks the oracle expectation `<= epsilon` in every checked stream, and the sample mean within
Monte Carlo noise. The pre-burst baseline mean (about 0.07) is also below `epsilon`.

**Onset definition (evaluator-side).** The onset is the start of the first planned harm regime,
provided the evaluator's expected cost over that regime exceeds `epsilon`. The repository's
`_material_harm_onset` (first regime whose finite-stream average exceeds the margin) is stored as
`sample_path_onset` but **not used**: in development it labelled a null gap after the harmless burst
as the onset, because baseline averages can cross `epsilon` by chance. Fixing this was a pre-run
generator change; development was rerun (section 9).

**Held-out mechanism cells (descriptive, section 6).** Variants of the same generator as `b1`
(`gated_ht_fixed`, `fixed08` only): training cells `(severity, r)` in
`{0.8, 1.5} x {0.02, 0.10}`; held-out cells `(1.0, 0.05)` and `(2.0, 0.05)`.

## 4. Endpoints and censoring

- **Detection by the horizon** (primary): `detected = 1` iff the *first* alarm of the e-process
  (`log E >= log(1/alpha)`) occurs at index `>= onset`. An alarm before onset counts as a false
  alarm (`false_alarm_pre_onset = 1`) and **not** as a detection; both are reported. An alarm at or
  after onset counts. No-alarm and reserve-exhausted streams count as not detected; all streams are
  analysed.
- **Labels to alarm or horizon:** the number of queried labels at indices `<= first_alarm`; for
  streams with no alarm, the total labels bought up to the horizon or reserve stop (right
  censored, kept at the censoring value). Pre-onset labels are included for both arms.
- Per-stream rows: cell, seed, arm, engine, onset, first_alarm, detected, false_alarm_pre_onset,
  labels_spent, labels_to_alarm_or_horizon, dollars, plus budget, processed events and
  `window_labels` (labels queried in `[onset, onset + 300)`, for section 6).

## 5. Hypotheses and exact tests

One-sided family-wise level `alpha_F = 0.025` throughout ("97.5%"). Pairing is by seed (same
stream and coins for all arms).

**H-B1a.** `gated_ht_paced` (the S3-registered gated arm) detects by the horizon more often than
`uniform_ht` (both `fixed08`) in `b1_r0.02` and `b1_r0.05`. Per budget, with `b` = streams where
gated detects and uniform does not and `c` the reverse, the exact one-sided McNemar p-value is
`P(Bin(b + c, 1/2) >= b)` (`p = 1` when `b + c = 0`). Holm over 2 at `alpha_F`.
Finding 1 is withdrawn if either budget fails. Secondary, not in the family: the same test for
`gated_ht_fixed`, and against `uniform_ppi`.

**H-B1b.** At `b1_r0.20`, with `L_g, L_u` the labels-to-alarm-or-horizon of `gated_ht_paced` and
`uniform_ht`, the ratio of means `mean(L_g) / mean(L_u)` has a paired-bootstrap upper 97.5% bound
`< 0.5`: 10,000 resamples of streams (seed 20261028), percentile 97.5. Single test at `alpha_F`.
Censoring is as in section 4; the pre-onset labels count against the gated arm.

**H-B2.** At `r = 0.10`, `d = P(fixed detects) - P(paced detects)` (paired, `fixed08`).
- Classes (i) `b2_i` and (iii) `b2_iii`: non-inferiority of fixed, `d > -0.05`, i.e. the one-sided
  97.5% lower bound of `d` exceeds -0.05. CI method: **Newcombe (1998) method 10**: Wilson limits
  for the two marginals with the continuity-corrected `phi` correlation adjustment for paired
  proportions (`scripts/analyze_e2.py:newcombe_lower`). The p-value for Holm is the smallest
  one-sided level at which the lower bound exceeds -0.05 (monotone, found by bisection).
- Class (ii) `b2_ii`: paced beats fixed, exact one-sided McNemar p-value as above.
- Holm over the 3 p-values at `alpha_F`. Fixed failing in (i) or (iii), or paced not winning in
  (ii), are admissible outcomes and are reported.

**Not tested, reported:** GRAPA rows, `uniform_ppi`, `gated_ht_fixed` in `b1`, per-cell detection
proportions with Wilson intervals, censored delay, labels and dollars.

## 6. Mechanism check (registered as descriptive)

On the mechanism cells, fit by least squares on the training cells and evaluate on the held-out
cells, per stream, the outcome `y = log(1 + delay)` where delay is `first_alarm - onset` (zero if
the alarm preceded onset) and `horizon - onset` when there is no alarm.
- Mechanism predictor: `log(1 + window_labels)` (fixed 300-event informative-label count after
  onset; every query in a gated arm is on a disagreement) plus intercept.
- Baseline predictor: design parameters only, `log r` and severity plus intercept.
- Report held-out RMSE and Spearman against the baseline and the training-mean constant. No
  threshold decides a claim; this is not a hypothesis test.

## 7. Power and sample size

For McNemar contrasts the number of discordant pairs is `M ~ Bin(n, delta)` and, given `M`, the
wins are `Bin(M, psi)` with `psi = b/(b+c)` from development. The exact one-sided test rejects when
the wins reach `k(M) = min{k : P(Bin(M, 1/2) >= k) <= alpha'}`, so

    power(n) = sum_m Bin(m; n, delta) * P(Bin(m, psi) >= k(m)),

with `alpha' = alpha_F / 2` for H-B1a and `alpha_F / 3` for H-B2(ii) (Bonferroni levels, sufficient
for Holm to reject all). The smallest `n` with power >= 0.9 is computed twice: at the development
plug-in `(delta, psi)`, and pessimistically at the Wilson 80% lower limits of both. The
non-inferiority contrast is powered by simulating the paired multinomial (Jeffreys-smoothed
development cells, 400 replications per `n`, `alpha' = alpha_F / 3`). The H-B1b bound is powered by
resampling development streams.

Development-set values (section 9, 250 streams per cell):

| Contrast | dev cells (both, first only, second only, neither) | `delta` | `psi` | n (plug-in) | n (pessimistic) |
|---|---|---:|---:|---:|---:|
| H-B1a, `b1_r0.02` | 0, 179, 0, 71 | 0.716 | 1.00 | 12 | 13 |
| H-B1a, `b1_r0.05` | 14, 226, 0, 10 | 0.904 | 1.00 | 9 | 9 |
| H-B2 (ii) | 0, 249, 0, 1 | 0.996 | 1.00 | 7 | 7 |
| H-B2 (i) non-inferiority | 249, 0, 0, 1 | 0 | n/a | grid n = 400 reaches power 1.00 (n = 200: 0.71) | n/a |
| H-B2 (iii) non-inferiority | 250, 0, 0, 0 | 0 | n/a | same | n/a |
| H-B1b | ratio 0.299 (dev) | | | power 1.00 already at n = 50 | |

**Registered n.** The power-driven requirement is at most 400 streams per cell (non-inferiority
cells). The development effects are near-deterministic (zero reversed pairs), so the McNemar
requirements are tiny. A **precision floor of 1,000 streams per primary cell** is registered so
that detection proportions have Wilson half-widths <= 0.031, the bootstrap is stable, and the
non-inferiority tests keep power >= 0.9 under a true fixed-minus-paced difference of -2 points
(simulated 0.93 and 0.97 at n = 1,000 for two discordance patterns). Mechanism cells: 500 streams
each.

- `n = 1,000` for each of the 6 primary cells (6,000 streams) and 500 for each of 6 mechanism cells
  (3,000): **9,000 streams in total**, well inside the 50,000-stream ceiling. At about 0.15 s per
  stream with 8 workers (section 9) this is about 25 minutes on CPU.
- Low-information caveat: because the development effects are close to deterministic, the power
  calculation is not informative about smaller effects. H-B1a and H-B2(ii) will almost surely be
  rejected if development behaviour carries over; the contrasts that can still fail are the
  non-inferiority tests and H-B1b.

## 8. Seed blocks, registry mapping, and stop rule

Registry (`configs/seed_registry.yaml`): `e2_dev_smoke_and_power` 100000000-100001999 and
`e2_confirmation` 100100000-100149999. A stream's seed **is** the generator seed (no offset; the
derived streams in section 3 are seed-indexed). Cells own disjoint consecutive sub-blocks; the first
`n` seeds of a sub-block are used and the rest stay reserved.

| Cell | Development sub-block (n used) | Confirmation sub-block (n registered) |
|---|---|---|
| `b1_r0.02` | 100000000-100000249 (250) | 100100000-100105999 (1,000) |
| `b1_r0.05` | 100000250-100000499 (250) | 100106000-100111999 (1,000) |
| `b1_r0.20` | 100000500-100000749 (250) | 100112000-100117999 (1,000) |
| `b2_i` | 100000750-100000999 (250) | 100118000-100123999 (1,000) |
| `b2_ii` | 100001000-100001249 (250) | 100124000-100129999 (1,000) |
| `b2_iii` | 100001250-100001499 (250) | 100130000-100135999 (1,000) |
| `mech_s0.8_r0.02` | 100001500-100001579 (80) | 100136000-100137999 (500) |
| `mech_s0.8_r0.10` | 100001580-100001659 (80) | 100138000-100139999 (500) |
| `mech_s1.5_r0.02` | 100001660-100001739 (80) | 100140000-100141999 (500) |
| `mech_s1.5_r0.10` | 100001740-100001819 (80) | 100142000-100143999 (500) |
| `mech_s1.0_r0.05` (held out) | 100001820-100001899 (80) | 100144000-100145999 (500) |
| `mech_s2.0_r0.05` (held out) | 100001900-100001979 (80) | 100146000-100147999 (500) |

Primary sub-blocks are 250 (development) and 6,000 (confirmation) seeds wide; mechanism sub-blocks
are 80 and 2,000. Development ends at 100001979 (1,999 is spare). Confirmation ends at 100147999
(100149999 is spare). The three `b1` budgets are separate streams, not reused paths. A test checks
that sub-blocks are disjoint and inside the registered blocks and that the registry entries match.

**Stop rule on validity failure.** For every (arm, engine), pool all streams in all cells and count
`false_alarm_pre_onset`. The arm-engine is **withdrawn** (all its results reported as invalid, and any
hypothesis that depends on it is withdrawn) if the exact one-sided binomial p-value of
`k` pre-onset alarms in `n` streams against rate 0.05 is `< 0.05/8` (8 arm-engine pairs). In the
class-(ii) cells the harmless burst lies before onset, so a validity failure there is also a failure
of the null property.

## 9. Implementation and smoke record

**Files (new only):** `src/shiftlab/dive/e2_acquisition_pacing.py`,
`scripts/run_e2_acquisition_pacing.py`, `scripts/analyze_e2.py`,
`tests/test_e2_acquisition_pacing.py`. No existing file edited.

**Code state.** Git HEAD at the time of the run `da38c6fb22c4688f563071beae1ac1a954af2385`
(branch `research/phase-progress-2026-10-27`) plus the four uncommitted new files above; config
SHA-256 (`e2.config_digest()`) `36c5b05ec4090dc6b2e2fd08020f8ef1442d5c2ed5f7f1e3995ecc96a0827bab`.
The manifest in `outputs/e2_dev/manifest.json` records `git_dirty = true`.

**Commands (Git Bash, repository root):**

    uv run --no-sync pytest tests/test_e2_acquisition_pacing.py -q
    uv run --no-sync ruff check <the four files>; uv run --no-sync ruff format <the four files>
    uv run --no-sync python scripts/run_e2_acquisition_pacing.py --block dev --n-per-cell 250 \
        --n-mech 80 --out outputs/e2_dev --workers 8
    uv run --no-sync python scripts/analyze_e2.py confirm --rows outputs/e2_dev/rows.parquet \
        --out outputs/e2_dev/confirm_on_dev.json
    uv run --no-sync python scripts/analyze_e2.py power --rows outputs/e2_dev/rows.parquet \
        --out outputs/e2_dev/power_plan.json
    # confirmation (NOT YET RUN):
    # ... run_e2_acquisition_pacing.py --block confirmation --n-per-cell 1000 --n-mech 500 \
    #       --out outputs/e2_confirmation --workers 8

Tests: 8 pass (about 17 s). Ruff check and format clean.

**Runtime.** 5 streams per cell on one worker: 60 streams in 51 s (0.85 s per stream, all arms and
both engines). Development block: 1,980 streams, 12,960 rows, 307 s with 8 workers.
`outputs/` is gitignored; nothing under `outputs/e2_dev/` is for commit.

**Development issues recorded.**
1. A first development run used the repository's sample-path onset rule; it mislabelled a null gap as
   the onset in class (ii) (for example onset at the burst end). Replaced by the design onset
   (section 3) and the development block was rerun in full. Class-wise results were unchanged because
   the dominant cases had matching onsets, but the bug was real.
2. A severity exploration at 0.3 and 0.5 (100 streams per burst class, development seeds, gated and
   uniform HT only) tried to avoid the ceiling in classes (i) and (iii); detection stayed 0.96-1.00
   for gated arms. Severity 1.5 (the existing generator's value) was kept. Not part of any claim.
3. One parallel launch failed with a Windows DLL-load error from too many simultaneous worker starts;
   rerun with 8 workers.

**Development results (DEVELOPMENT, descriptive only; not confirmatory evidence).**
Engine `fixed08`; 250 streams per cell; detection, pre-onset false-alarm rate, mean labels to alarm
or horizon.

| Cell | gated fixed | gated paced | uniform HT | uniform PPI |
|---|---|---|---|---|
| `b1_r0.02` | 0.676 / 0.004 / 34 | 0.716 / 0.004 / 36 | 0.000 / 0.000 / 44 | 0.000 / 0.000 / 44 |
| `b1_r0.05` | 0.948 / 0.000 / 72 | 0.960 / 0.000 / 73 | 0.056 / 0.000 / 114 | 0.000 / 0.000 / 115 |
| `b1_r0.20` | 0.992 / 0.000 / 111 | 0.992 / 0.000 / 111 | 0.740 / 0.000 / 371 | 0.580 / 0.000 / 410 |
| `b2_i` | 0.996 / 0.004 / 94 | 0.996 / 0.004 / 93 | 1.000 / 0.000 / 114 | 1.000 / 0.000 / 124 |
| `b2_ii` | 0.000 / 0.000 / 239 | 0.996 / 0.004 / 141 | 0.160 / 0.000 / 227 | 0.056 / 0.000 / 232 |
| `b2_iii` | 1.000 / 0.000 / 53 | 1.000 / 0.000 / 52 | 1.000 / 0.000 / 62 | 1.000 / 0.000 / 84 |

GRAPA (secondary) detection: gated paced 0.748 / 0.984 / 0.996 in `b1`; uniform HT 0.000 / 0.200 /
0.772; gated fixed in `b2_ii` 0.000, paced 0.996. The registered tests applied to the development
rows (labelled development): H-B1a McNemar 179:0 and 226:0 (p about 1e-54 and 1e-69); H-B1b ratio
0.299, upper 97.5% bound 0.308; H-B2 non-inferiority lower bounds -0.017 (i) and -0.015 (iii), and
paced wins 249:0 in (ii). Validity: pre-onset alarms among 1,980 gated-fixed streams: 2; gated-paced
and uniform arms among 1,500 streams: at most 3 per arm-engine; no arm-engine would be withdrawn.
Mechanism (descriptive): held-out RMSE of `log(1 + delay)` 0.478 for the fixed-window label count,
0.458 for the design-parameter baseline, 0.534 for the training mean; Spearman 0.37 for both. The
label-count predictor did **not** beat the simpler baseline in development.

## 10. Design problems and risks stated plainly

1. **Near-deterministic McNemar contrasts.** H-B1a and H-B2(ii) have zero reversed pairs in
   development. They test a large, structural effect, not a close call. For `uniform_ht` at
   `r = 0.02` the bound `C/q + eps = 250.1` makes every bet tiny, so zero detection is expected.
2. **Class (ii) mechanism is reserve exhaustion.** Fixed gating spends its reserve inside the
   harmless burst (processed events about 520 of 2,400) and cannot detect the late harm. The
   prediction is therefore confirmed by construction, as a *design-sensitive* property. A longer
   gap or a smaller burst would weaken it. This is why the result is "informative either way".
3. **Ceiling in classes (i) and (iii).** All four arms detect about 100%; the non-inferiority tests
   pass because nothing separates the arms, and say little about milder regimes. The earlier S3
   finding (fixed no worse than paced under `harmful_adaptation`) is not contradicted.
4. **H-B1b counts pre-onset labels.** The gated arm's ratio is partly the 0.086/0.20 disagreement
   rate against the uniform rate, not only faster detection. The registered ratio is kept.
5. **Mechanism check unsupported in development.** Reported as descriptive; a negative result will
   be recorded.
6. **Engine caveat.** `fixed08` is the only primary engine; GRAPA's burn-in and adaptive bets are
   outside Lemma L. Dev GRAPA false alarms are within bounds.
7. **Composition and generator scope.** Synthetic, single-generator family, `d = 16`, one tariff
   rule; no real-data transfer claim.

## 11. Freeze checklist (open)

- [ ] SHA-256 freeze record of this file and of the four code files.
- [ ] Codex protocol review.
- [ ] Update `configs/seed_registry.yaml` status of `e2_dev_smoke_and_power` to used (dev run done)
      before confirmation; `e2_confirmation` stays reserved until the freeze.
- [ ] Commit the code, then run the confirmation exactly as in section 9.
