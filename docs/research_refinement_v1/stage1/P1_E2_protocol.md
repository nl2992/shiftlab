# P1: E2 acquisition and pacing protocol (H-B1a, H-B1b, H-B2)

**Status: revised after the Codex Stage 1 review (`CODEX_PROTOCOL_REVIEW_1.md`); ready for freeze
review. Not frozen. No confirmation seed has been used.** The design in section 3 was selected on
development blocks only and is locked in `P1_E2_locked_design.json` (cells, order, n, multiplicity).
Hypotheses are those of `FINAL_RESEARCH_PROPOSAL.md` section 4. The mechanism (disagreement gating)
is DISCERN's; H-B1 is a replication under the repository's decision-cost contract and H-B2 is a
pacing test.

## 1. Scientific scope

- Quantity monitored: incumbent decision harm, `E[Z_t | F_{t-1}] <= epsilon` with
  `Z_t = c(pi_t(X_t), Y_t) - c(pi_ref(X_t), Y_t)`, `epsilon = 0.1`, `|Z_t| <= C = 5`, `Z_t = 0`
  whenever the deployed and reference actions agree (`D_t = 0`).
- Filtration: `F_{t-1}` holds past features, disagreement indicators, tariffs, coins and queried
  costs. Feedback is immediate for queried events and absent otherwise. Propensities `q_t` are
  `F_{t-1}`-predictable (constant; frozen from validation; a 200-event past-only tariff window; or
  a function of elapsed time and past spend); coins are independent of `Z_t`.
- Validity of each arm follows `stage0/VALIDITY_TABLE.md` (CA-1 to CA-3). The reserve stop is a
  stopping time of past spend. The stop rule in section 8 checks validity empirically.
- Synthetic oracle truth (regime weights, expected costs, burst masks, onsets) lives in `Oracle` and
  is used only for summary endpoints. Replays receive `MonitorInputs` only; a test scrambles every
  oracle field and checks that alarms, labels and dollars do not change.
- Credit: gating is DISCERN's. Lemma L covers zero-anchor HT at `epsilon = 0` only; at the registered
  `epsilon = 0.1` fixed and paced HT are genuinely different monitors.

## 2. Arms and engines

All arms use the identical engine `PredictableBoundMeanEProcess` (the default fixed-stake mixture,
stakes `(0.05, 0.1, 0.2, 0.4, 0.8)`, equal weights, `alpha = 0.05`, labelled `fixed08`), the same
increment conventions and the same hard dollar reserve `target * horizon`, with
`target = r * mean(validation tariffs)`. A reserve stop occurs before an event whose maximum tariff
(2.5) the remaining reserve cannot cover (past spend only). Tariffs lie in `[0.5, 2.5]`.

| Arm | Query rule | Increment | Bound `B_t` |
|---|---|---|---|
| `gated_ht_fixed` | disagreements only, `q` frozen from validation: `min(1, target / mean(validation D*tariff))` | `Z/q - eps` if queried, else `-eps` | `5/q + eps` |
| `gated_ht_paced` | disagreements only, `q_t = clip(target / mean(last 200 D*tariff), 0.10, 1)` | same | `5/q_t + eps` |
| `gated_ht_horizon` (new baseline) | disagreements only, `q_t = clip(min(q_fixed, (reserve - spent) / ((T - t) * rate)), 0.10, 1)` with `rate = mean(validation D*tariff)` | same | `5/q_t + eps` |
| `uniform_ht` | **every event** (agreements included), constant `q = r`, coin `U_t < q` | `Z/q - eps` if queried, else `-eps` | `5/q + eps` |
| `uniform_ppi` | every event, constant `q = r`; ridge proxy `h` fitted before monitoring, updated on queries | `h + (Z - eps - h)/q` if queried, else `h` | `(5+eps)(2/q - 1)` |

**Horizon-aware reserve baseline.** `gated_ht_horizon` caps spend per remaining-horizon fraction. It
reacts to spend, not to the disagreement rate, and uses only validation data, elapsed time and past
spend (predictable). It is the simple reserve-protection alternative that the 200-event pacer must
beat for a pacing claim to mean more than "anything that conserves the reserve works". It is
reported (detection, expenditure, reserve survival) in every burst cell, and is not in a Holm family.

**Uniform HT definition.** `uniform_ht` does not use the free disagreement indicator `D_t`. It
queries every event with constant `q = r`, pays the tariff for every query (agreements included,
where `Z_t = 0`), uses increment `Z_t/q - eps` if queried and `-eps` otherwise, and bound `C/q + eps`.
Because `E[tariff * 1{queried}] = q E[tariff]`, `q = r` matches its **expected** spend per event to
the gated target `r * E[tariff]`, and the reserve is the same. Realised spend is not matched and is
reported per arm. Tests: it buys labels on a stream made only of agreements while the gated arm buys
none; flipping the disagreement flags changes nothing.

**H-B1a is a gating ablation.** It compares the same engine with and without the free zero-cost
knowledge of agreements. It replicates DISCERN's label economics under this contract; it does not
establish a new allocation method.

**Engines.** Primary engine `fixed08`. Secondary engine `timans_grapa` (Timans et al. GRAPA through
`replay_engine`, 100-event burn-in) is run on the core cells only and is not in any Holm family. Grid
and burst cells use `fixed08` only.

## 3. Cells and generators

Stream length 3,200 events (`d = 16`); events 0-399 proxy training, 400-799 validation (pacer seed,
proxy validation); monitoring starts at event 800 and the horizon is 2,400 monitored events. All
indices below are in monitored coordinates. Pre-monitor events are always stationary.

New generators call the existing generator (`_generate`, scenario `boundary_local_harm`, severity
0) for `X` and the standardised noise `z` (identical for every severity), then re-apply the
unmodified mechanism `mean = X0 - 0.9 X1 + severity * w_t * exp(-5 |X0 - 0.9 X1|)`,
`Y = 1{mean + 0.3 z > 0}` with a stream-specific weight `w_t`, and the existing policies (deployed
threshold 0.5 on `ndtr(score/0.3)`; reference `_source_action`, FN 5, FP 1). The disagreement band
is score in `(-0.290, 0)`. A **burst** replaces a random fraction `pi` of the events in a window by
in-band events (`X0 := 0.9 X1 + s`); `X1`, the tariff coordinate and `z` are untouched. Existing code
is not modified.

**Core cells (locked, n in section 7).**

| Cell | Generator | `r` | Severity |
|---|---|---|---|
| `b1_r0.02`, `b1_r0.05`, `b1_r0.20` | `boundary_local_harm`, `w_t = 1[t >= onset]`, onset ~ DU{300..1500} | 0.02, 0.05, 0.20 | 1.5 |
| six `mech_*` cells | same generator, gated fixed only; training cells `(severity, r)` in `{0.8, 1.5} x {0.02, 0.10}`, held-out `(1.0, 0.05)`, `(2.0, 0.05)` | | |

**Burst-class generators** (parameters: severity `s`, budget `r`, length `L`, burst fraction `pi`):

- **(i) disagreement burst after onset.** Harm from `onset ~ DU{300..1200}`; burst window
  `[onset + g, onset + g + L)`, `g ~ DU{100..300}`, `pi = 0.5`, scores `U(-0.290, 0)` (harmful).
- **(ii) harmless burst, then late harm.** Burst window `[b0, b0 + L)`, `b0 ~ DU{100..400}`,
  `pi = 0.8`, scores `U(-0.290, -0.275)` with `w = 0` (in-band events with `p <= 0.18`, per-event
  expected paired cost below `epsilon`, so the null holds); onset `= b0 + L + DU{100..500}`, harm to
  the end, no burst after onset. Burst expenditure relative to the reserve is varied through `L` and
  `r` so that cells span reserve exhaustion and non-exhaustion.
- **(iii) recurrent harmful regimes.** Harm windows `[o + 2Lk, o + 2Lk + L)`, `k = 0, 1, ...`,
  `o ~ DU{200..600}`, each with a burst (`pi = 0.5`, full band); null in between.

Onsets and burst masks are drawn from `default_rng([seed, 0xE2A1])` and `[seed, 0xE2B2]`, independent
of the stage boundaries (monitor start 800, original change 1,600, end 3,200); query coins are
`default_rng(seed + 9173)` as in `comparison_seed`.

**Onset (evaluator-side).** The onset is the start of the first *planned* harm regime whose expected
paired cost over the regime exceeds `epsilon` (population-level by construction). The repository's
sample-path rule is stored as `sample_path_onset` and not used: it labelled null gaps as onsets in an
earlier development run.

### 3.1 Development grid and selection rule (block `e2_dev_grid`)

Grid, 100 streams per cell (63 cells, `fixed`/`paced`/`horizon` arms, `fixed08`):
- classes (i), (iii): severity `{0.15, 0.25, 0.4, 0.7}` x `r {0.02, 0.05, 0.10}` x `L` in
  `{200, 500}` (i) or `{150, 300}` (iii);
- class (ii): severity 1.5, `r {0.05, 0.10, 0.20}` x `L {60, 120, 200, 300, 450}`.

Pre-specified rules, applied by `scripts/analyze_e2.py select-grid` to the development grid only:
- **(i), (iii):** a cell is eligible when paced detection is in `[0.20, 0.80]` and the planned harm is
  material in at least 95% of streams. Select at most 2 per class, closest to 0.5 (ties by name). If
  none is eligible the class is registered as **UNINFORMATIVE** (not support) and is excluded from
  the Holm family.
- **(ii):** bands by the fixed arm's share of streams whose reserve is exhausted before onset: `A`
  `[0, 0.2)`, `B` `[0.2, 0.8)`, `C` `[0.8, 1]`; select, per band, the cell closest to the band centre
  (0.1, 0.5, 0.9).

**Locked selection (from the development grid; see `P1_E2_locked_design.json` for all 63 cells).**
Development detection (100 streams, selection-biased):

| Cell | Class | Role | Paced | Fixed | Horizon | Fixed reserve exhausted pre-onset | Reserve used pre-onset (fixed / paced) |
|---|---|---|---:|---:|---:|---:|---|
| `g_i_s0.4_r0.02_L500` | i | NI | 0.59 | 0.57 | 0.64 | 0.00 | 0.33 / 0.34 |
| `g_i_s0.25_r0.05_L500` | i | NI | 0.40 | 0.72 | 0.72 | 0.00 | 0.33 / 0.34 |
| `g_iii_s0.25_r0.02_L150` | iii | NI | 0.51 | 0.53 | 0.50 | 0.00 | 0.17 / 0.18 |
| `g_iii_s0.25_r0.02_L300` | iii | NI | 0.53 | 0.66 | 0.67 | 0.00 | 0.17 / 0.17 |
| `g_ii_s1.5_r0.05_L120` | ii | paced > fixed (band A) | 1.00 | 0.59 | 0.94 | 0.06 | 0.72 / 0.35 |
| `g_ii_s1.5_r0.05_L200` | ii | paced > fixed (band B) | 1.00 | 0.08 | 0.70 | 0.62 | 0.94 / 0.40 |
| `g_ii_s1.5_r0.1_L300` | ii | paced > fixed (band C) | 1.00 | 0.00 | 0.58 | 0.97 | 0.99 / 0.39 |

Classes (i) and (iii) were at the ceiling in the first draft (severity 1.5, `r = 0.10`: all arms
about 100%), which Codex judged uninformative. In the grid, paced detection leaves the ceiling at
lower severity and budget. In several class-(i) cells paced is clearly **worse** than fixed
(for example 0.12 against 0.38 at severity 0.15, `r = 0.05`, `L = 200`): the pacer throttles queries
during an after-onset burst. This is why fixed-vs-paced non-inferiority is a real test here.

## 4. Endpoints and censoring

- **Detection by the horizon** (primary): `detected = 1` iff the *first* alarm (`log E >= log(1/alpha)`)
  occurs at index `>= onset`. A pre-onset alarm counts as a false alarm (`false_alarm_pre_onset = 1`),
  not a detection; both are reported. No-alarm and reserve-exhausted streams count as not detected;
  all streams are analysed.
- **Labels to alarm or horizon:** queried labels at indices `<= first_alarm`; for streams with no
  alarm, total labels up to the horizon or reserve stop (right censored, kept at the censoring
  value). Pre-onset labels are included for both arms.
- **Expenditure and reserve survival:** `dollars` (realised), `dollars_pre_onset`,
  `dollars_post_onset`, `reserve_used_frac_pre_onset`, `reserve_exhausted`,
  `reserve_exhausted_before_onset` (processed events `<= onset`). Reported for every arm and cell.
- Per-stream rows: cell, seed, arm, engine, onset, first_alarm, detected, false_alarm_pre_onset,
  labels_spent, labels_to_alarm_or_horizon, dollars, plus budget, processed events,
  `window_labels` (labels in `[onset, onset + 300)`) and the columns above.

## 5. Hypotheses and exact tests

One-sided family-wise level `alpha_F = 0.025` throughout. Pairing is by seed (same stream and coins
for all arms). The analysis **rejects** (raises) duplicate `(cell, seed, arm, engine)` rows, cells
whose seeds differ in their arm/engine rows, NaN statistics, unpaired streams, and seed sets that
differ from the registered ones; it never drops pairs or takes a first duplicate.

**H-B1a (gating ablation).** `gated_ht_paced` detects by the horizon more often than `uniform_ht`
(both `fixed08`) at `b1_r0.02` and `b1_r0.05`. Per budget, exact one-sided McNemar
`P(Bin(b + c, 1/2) >= b)`; Holm over 2 at `alpha_F`. Finding 1 is withdrawn if either fails.
Expected spend is matched, realised spend differs and is reported per arm (dollars, labels).
Secondary, outside the family: `gated_ht_fixed`, `gated_ht_horizon`, `uniform_ppi`, GRAPA.

**H-B1b (acquisition expenditure, not faster detection).** At `b1_r0.20`, ratio of means
`mean(L_gated) / mean(L_uniform)` of labels-to-alarm-or-horizon for `gated_ht_paced` and
`uniform_ht`: paired-bootstrap (10,000 stream resamples, seed 20261028) upper 97.5% percentile
`< 0.5`, **and** the joint detection condition: the Newcombe (method 10) one-sided 97.5% lower bound
of `P(gated detects) - P(uniform detects)` exceeds `-0.05`. Both must hold (an intersection-union
test, so no further adjustment), so cheap non-detection cannot count as efficiency. Pre-onset labels
count against the gated arm; the result does not show lower post-onset sample complexity.

**H-B2 (burst classes, locked cells only).** At the locked cells of section 3.1, with
`d = P(fixed detects) - P(paced detects)` (paired, `fixed08`):
- classes (i), (iii): non-inferiority of fixed, `d > -0.05`: Newcombe (1998, method 10) one-sided 97.5%
  lower bound with the continuity-corrected `phi` adjustment; the Holm p-value is the smallest
  one-sided level at which the bound exceeds -0.05 (bisection);
- class (ii): paced detects more than fixed, exact one-sided McNemar;
- **multiplicity: one Holm family over all `K = 7` locked H-B2 tests, equal weights, `alpha_F`**.
  Class (ii) bands A and C are expected to show weaker or null contrasts by design (A: reserve
  mostly survives; C: both fail only if exhausted); they are tests, not forced successes.
- If a class has no eligible grid cell it is **UNINFORMATIVE** (no class lacked a cell in this
  selection). A cell flagged `underpowered` in the locked design, when not rejected, means
  inadequate power, not disconfirmation.

**Reported, not tested:** per-cell detection with Wilson intervals, expenditure and reserve survival
for all arms including `gated_ht_horizon`, censored delay, GRAPA rows.

## 6. Mechanism check (descriptive; a retrospective association)

On the mechanism cells fit least squares on the training cells and evaluate on the held-out cells,
per stream: outcome `log(1 + delay)` (delay `= first_alarm - onset`, zero if the alarm preceded onset,
`horizon - onset` when none).
- Mechanism predictor: `log(1 + window_labels)`, the fixed 300-event count of labels queried after
  onset. This is a **post-onset** count: a retrospective association, not an online delay predictor
  or a demonstrated mechanism.
- Baseline: design parameters only (`log r`, severity).
- Report held-out RMSE and Spearman against the baseline and the training-mean constant. No claim
  follows from this check.
- **Development result, stated plainly:** the window-count predictor *lost* to the design-parameter
  baseline (held-out RMSE 0.478 against 0.458; training-mean constant 0.534; Spearman 0.37 for both).

## 7. Power and sample size

Exact McNemar power: `M ~ Bin(n, delta)` discordant pairs, wins `| M ~ Bin(M, psi)`, reject when
the wins reach `k(M) = min{k : P(Bin(M, 1/2) >= k) <= alpha'}`:

    power(n) = sum_m Bin(m; n, delta) * P(Bin(m, psi) >= k(m)),

`alpha' = alpha_F / m` for the Holm family of size `m` (Bonferroni, sufficient for Holm). The smallest
`n` with power >= 0.9 uses Wilson 80% lower limits for `delta` and `psi` (pessimistic). The
non-inferiority cells are powered by simulation (300 replications, seed 1, Jeffreys-smoothed cells)
under a **true difference of zero** with discordance at the Wilson 80% upper limit of the
100-stream development discordance, at `alpha_F / 7`. `n` is rounded up to 100, floored at 1,000 and
capped at 3,000 per cell; a cell that needs more is flagged `underpowered`.

| Contrast | Dev table (both, first only, second only, neither) | Pessimistic n (power >= 0.9) | Registered n |
|---|---|---:|---:|
| H-B1a `b1_r0.02` | 0, 179, 0, 71 | 13 | 1,000 (floor) |
| H-B1a `b1_r0.05` | 14, 226, 0, 10 | 9 | 1,000 (floor) |
| H-B1b (`b1_r0.20`) | ratio 0.299, detection +0.19 lower bound (250 dev streams) | n/a | 1,000 |
| (i) `g_i_s0.4_r0.02_L500` NI | 48, 9, 11, 32 | 2,000 | 2,000 |
| (i) `g_i_s0.25_r0.05_L500` NI | 38, 34, 2, 26 | 3,000 | 3,000 |
| (iii) `g_iii_s0.25_r0.02_L150` NI | 37, 16, 14, 33 | 3,000 | 3,000 |
| (iii) `g_iii_s0.25_r0.02_L300` NI | 44, 22, 9, 25 | 3,000 | 3,000 |
| (ii) `g_ii_s1.5_r0.05_L120` | 59, 0, 41, 0 (paced only 41) | 36 | 1,000 (floor) |
| (ii) `g_ii_s1.5_r0.05_L200` | paced only 92, fixed only 0 | 12 | 1,000 (floor) |
| (ii) `g_ii_s1.5_r0.1_L300` | paced only 100, fixed only 0 | 10 | 1,000 (floor) |
| mechanism cells (6) | descriptive | n/a | 500 each |

**Total: 20,000 confirmation streams** (3 x 1,000 + 6 x 500 + 2,000 + 3 x 3,000 + 3 x 1,000), inside the 50,000
ceiling and the 48,000 seeds of 16 sub-blocks. Runtime at about 0.15 s per stream with 8 workers:
roughly 45 minutes. The three 3,000 cells sit at the simulation's 0.9 boundary (the ceiling): their
power is about 0.86-0.9, so a failed non-inferiority result there is reported as possibly
underpowered. The Newcombe interval and the Holm level (`alpha_F / 7`) are what keep these n high.

## 8. Seed blocks, registry mapping, freeze and stop rule

Registry (`configs/seed_registry.yaml`): `e2_dev_smoke_and_power` 100000000-100001999 (used, development),
`e2_dev_grid` 100500000-100509999 (used, development), `e2_confirmation` 100100000-100149999
(reserved). A stream's seed **is** the generator seed (derived streams are seed-indexed). Each cell
owns a disjoint sub-block.

- `e2_dev_smoke_and_power`: primary cells 250 wide in order `b1_r0.02, b1_r0.05, b1_r0.20, b2_i,
  b2_ii, b2_iii`, then the six mechanism cells 80 wide (ends 100001979).
- `e2_dev_grid`: the 63 grid cells in `GRID_CELLS` order, 100 seeds each (ends 100506299).
- `e2_confirmation`: 16 sub-blocks of 3,000 seeds (100100000 + 3,000 k), in the locked order:
  `b1_r0.02, b1_r0.05, b1_r0.20`, the six mechanism cells, then the seven locked burst cells
  (`P1_E2_locked_design.json: order`). The first `n` seeds of each sub-block are used.
  Sub-blocks end at 100147999.

Tests check that sub-blocks are disjoint and inside the registered blocks, that the three blocks are
disjoint and that registry entries match.

**Freeze gate.** `scripts/run_e2_acquisition_pacing.py --block confirmation` calls
`shiftlab.freeze.require_freeze(docs/research_refinement_v1/stage1/P1_E2_freeze.json)` before any
confirmation seed is generated and reads cells, order and n only from the locked design (CLI sample
sizes are rejected). A test shows no seed or stream is produced when the freeze check fails.

**Stop rule on validity failure.** For every (arm, engine), pool all streams in all cells and count
`false_alarm_pre_onset`. The arm-engine is **withdrawn** (results reported as invalid; any dependent
hypothesis withdrawn) if the exact one-sided binomial p-value of `k` pre-onset alarms in `n` streams
against rate 0.05 is `< 0.05 / (number of arm-engine pairs)`.

## 9. Implementation and smoke record

**Files (all new in P1; edited in place after Codex review):**
`src/shiftlab/dive/e2_acquisition_pacing.py`, `scripts/run_e2_acquisition_pacing.py`,
`scripts/analyze_e2.py`, `tests/test_e2_acquisition_pacing.py`,
`docs/research_refinement_v1/stage1/P1_E2_locked_design.json`; `configs/seed_registry.yaml` edited
only to mark `e2_dev_grid` as used (development).

**Code state.** Git HEAD `8faeea1` plus uncommitted edits to the files above; config SHA-256
(`e2.config_digest()`) `5b75903fbc22ee6b4b06e37208733afa9d3a7cdf776f3f3fab6635c93d622b30`.

**Commands (Git Bash, repository root):**

    uv run --no-sync pytest tests/test_e2_acquisition_pacing.py tests/test_seed_registry.py -q
    uv run --no-sync ruff check <files>; uv run --no-sync ruff format <files>
    uv run --no-sync python scripts/run_e2_acquisition_pacing.py --block dev --n-per-cell 250 \
        --n-mech 80 --out outputs/e2_dev --workers 8
    uv run --no-sync python scripts/run_e2_acquisition_pacing.py --block grid --n-per-cell 100 \
        --out outputs/e2_grid --workers 8
    uv run --no-sync python scripts/analyze_e2.py select-grid --rows outputs/e2_grid/rows.parquet \
        --dev-rows outputs/e2_dev/rows.parquet \
        --out docs/research_refinement_v1/stage1/P1_E2_locked_design.json
    # confirmation (NOT YET RUN; requires the freeze record):
    #   run_e2_acquisition_pacing.py --block confirmation --out outputs/e2_confirmation --workers 8
    #   analyze_e2.py confirm --rows outputs/e2_confirmation/rows.parquet --locked <locked design> \
    #       --out outputs/e2_confirmation/confirm.json

**Runtime.** Dev block: 1,980 streams, 15,960 rows (five arms in the core cells), 335 s on 8
workers. Grid block: 6,300 streams, 18,900 rows, 710 s on 8 workers. About 0.1-0.15 s per stream
effective (0.85 s per stream on one worker for the core cells including GRAPA). `outputs/` is
gitignored; nothing under it is for commit.

**Tests:** 20 pass (this file plus the seed registry). They cover: class-(ii) null property
(oracle expectation below `epsilon`), harm above `epsilon`, burst disagreement rate, seed
disjointness for dev/grid/confirmation and registry match, uniform HT unbiasedness and its
independence of `D_t`, uniform HT spending on agreements, horizon baseline (bounds, reserve,
predictable), expenditure columns, rejection of duplicate/ragged/NaN/wrong-seed rows and unpaired
streams, grid-selection rules including the UNINFORMATIVE path, an end-to-end tiny run with oracle
scrambling, and the freeze gate running before any seed.

**Development results (DEVELOPMENT, descriptive; not confirmatory evidence).** Core cells, 250
streams each, `fixed08`: detection / mean labels to alarm or horizon / realised dollars.

| Cell | gated fixed | gated paced | gated horizon | uniform HT | uniform PPI |
|---|---|---|---|---|---|
| `b1_r0.02` | 0.68 / 34 / 64 | 0.72 / 36 / 68 | 0.72 / 34 / 64 | 0.00 / 44 / 66 | 0.00 / 44 / 66 |
| `b1_r0.05` | 0.95 / 72 / 169 | 0.96 / 73 / 178 | 0.96 / 70 / 168 | 0.06 / 114 / 173 | 0.00 / 115 / 173 |
| `b1_r0.20` | 0.99 / 111 / 307 | 0.99 / 111 / 307 | 0.99 / 111 / 307 | 0.74 / 371 / 707 | 0.58 / 410 / 707 |

Realised spend differs between gated and uniform arms (307 against 707 dollars at `r = 0.20`),
because gated arms stop paying at an early alarm and only query disagreements; expected spend and
the reserve are matched. Registered tests on the development rows (labelled development): H-B1a
179:0 and 226:0; H-B1b ratio 0.299, upper bound 0.308, detection lower bound +0.199, so the joint
condition holds in development. Burst cells (selection-biased, 100 streams, from the grid) are in the
table of section 3.1; the pipeline run on the locked cells gave Holm rejections in five of seven H-B2
tests (not for `g_i_s0.4_r0.02_L500` and `g_iii_s0.25_r0.02_L150`, where fixed and paced are equal
within noise). In the class-(ii) cells the horizon baseline sits between fixed and paced
(detection 0.94/0.70/0.58 against fixed 0.59/0.08/0.00 and paced 1.00 in bands A/B/C), so the
200-event pacer's advantage is not just reserve conservation. Pre-onset false alarms are at most 2
per 1,450-1,930 streams for the fixed08 gated arms and 0 for uniform arms; no arm-engine would be
withdrawn. The older ceiling cells `b2_i`, `b2_ii`, `b2_iii` remain in the development block only.

## 10. Design problems and risks

1. **Selection on 100 streams per grid cell is noisy.** Detection in band `[0.20, 0.80]` in
   development need not hold in confirmation; a cell may leave the band. The tests are still
   valid (the design is locked), but information may be lower than selected for. Confirmation
   reports the confirmation detection of each cell.
2. **Three non-inferiority cells are near their power ceiling** (about 0.86-0.9 at n = 3,000 under
   a true difference of zero). In development fixed was *better* than paced in two of them, so real
   power is likely higher, but this is not assumed.
3. **Class (ii) mechanism is reserve exhaustion** and its band-A/C contrasts follow from construction.
   Band B and the comparison with `gated_ht_horizon` are the informative parts.
4. **H-B1b counts pre-onset labels** and is an acquisition-expenditure result; the joint detection
   condition prevents cheap non-detection from qualifying.
5. **Mechanism check lost to the design-parameter baseline** in development and is an association.
6. **Engine and scope.** `fixed08` only for burst cells; GRAPA on core cells. Synthetic, one generator
   family, `d = 16`, one tariff rule; no real-data transfer claim.
7. **Composition** across monitor, certify and promote is not controlled and not claimed.

## 11. Freeze checklist

- [ ] Commit code, locked design and this protocol.
- [ ] `shiftlab.freeze.write_freeze`: experiment `E2`, protocol `P1_E2_protocol.md`, files listed in
      the hand-off message (every repository module and script the run imports, the registry and the
      locked design), seed block `e2_confirmation`; record at
      `docs/research_refinement_v1/stage1/P1_E2_freeze.json`.
- [ ] Codex protocol re-review of this revision.
- [ ] Run the confirmation exactly as in section 9.
