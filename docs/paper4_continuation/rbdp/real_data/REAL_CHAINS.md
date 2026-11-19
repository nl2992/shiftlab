# Real binary streams: does the causal-safety premium appear? (2026-11-16/17)

Protocol and addenda: `PROTOCOL.md` (written before each phase was fitted). Builder: Sonnet subagent; every headline
number below was re-derived by the lead from stored fits unless marked. All streams are public series fetched into the
git-ignored `data/raw/real_chains/`; no repo holdouts were opened. A positive result means the **fitted two-state
model** has a premium and that the IID-optimal policy would break the causal budget under that model. It is not a field
test of the policy, and the null in the game is adversarial, not claimed to be present in any dataset.

## Headline (updated 2026-11-17 after Phase 4b)

**Target met: 10 real datasets support the premium** (Phase 4b, `PROTOCOL.md` Addendum D, run stopped at 10). Each is a
Project Gutenberg text read as a vowel/consonant stream; each has a positive premium, the IID-optimal policy breaks the
causal budget α = 0.1, and 0 of 5 time-shuffles is positive. Raw: `results/attempts_phase4b.jsonl`, `phase4b_run.log`.

| Text (book id) | r1 | best ρΓ (cell) | causal risk of IID-optimal policy | positive shuffles |
|---|---|---|---|---|
| English (1342) | −0.383 | 0.200 (T16 B4) | 0.325 | 0/5 |
| French (78027) | −0.366 | 0.346 (T16 B4) | 0.325 | 0/5 |
| German (78079) | −0.347 | 0.150 (T16 B3) | 0.2 | 0/5 |
| Spanish (61851) | −0.534 | 0.415 (T32 B4) | 0.325–0.4 | 0/5 |
| Italian (61885) | −0.488 | 0.414 (T32 B4) | 0.325–0.4 | 0/5 |
| Portuguese | −0.432 | 0.200 (T16 B4) | 0.4 | 0/5 |
| Dutch | −0.346 | 0.201 (T16 B4) | 0.325 | 0/5 |
| Swedish | −0.489 | 0.111 (T16 B3) | 0.2 | 0/5 |
| Danish | −0.398 | 0.139 (T16 B3) | 0.2 | 0/5 |
| Finnish | −0.423 | 0.340 (T32 B4) | 0.325–0.4 | 0/5 |

**Target met: 20 real datasets (Phase 5, Addendum E, run stopped at 20).** Ten more, from three source types: a geyser,
structural proteins and further languages. Same evaluator and shuffle control; best cell T16 B4 for all. Raw:
`results/attempts_phase5.jsonl`, `phase5_run.log`; script `run_phase5.py`.

| Dataset | Source type | n | r1 | best ρΓ | causal risk of IID-optimal policy | positive shuffles |
|---|---|---|---|---|---|---|
| `faithful` (waiting > 70) | geyser | 272 | −0.498 | 0.310 | 0.325 | 0/5 |
| `geyser` (waiting > 70) | geyser | 299 | −0.562 | 0.440 | 0.8 | 0/5 |
| Elastin, human (P15502) | protein, hydrophobic/polar | 786 | −0.130 | 0.092 | 0.3 | 0/5 |
| Elastin, bovine (P04985) | protein, hydrophobic/polar | 747 | −0.218 | 0.234 | 0.325 | 0/5 |
| Hungarian | text | 3000 | −0.554 | 0.348 | 0.325 | 0/5 |
| Polish | text | 3000 | −0.398 | 0.203 | 0.325 | 0/5 |
| Czech | text | 3000 | −0.384 | 0.162 | 0.325 | 0/5 |
| Latin | text | 3000 | −0.503 | 0.425 | 0.325 | 0/5 |
| Romanian | text | 3000 | −0.383 | 0.159 | 0.325 | 0/5 |
| Catalan | text | 3000 | −0.485 | 0.417 | 0.325 | 0/5 |

**Target met: 25 real datasets (Phase 6, Addendum F, run stopped at 25).** Raw: `results/attempts_phase6.jsonl`,
`phase6_run.log`; script `run_phase6.py`.

| Dataset | Source type | n | r1 | best ρΓ (cell) | causal risk of IID-optimal policy | positive shuffles |
|---|---|---|---|---|---|---|
| Spidroin-2, *T. clavipes* (P46804) | silk protein | 627 | +0.530 | 0.176 (T32 B4) | 0.5 | 0/5 |
| Elastin, chicken (P07916) | protein | 750 | −0.227 | 0.170 (T16 B4) | 0.325 | 0/5 |
| Elastin, sheep (P11547) | protein | 100 | −0.224 | 0.143 (T16 B4) | 0.325 | 0/5 |
| Esperanto (78054) | text | 3000 | −0.544 | 0.427 (T16 B4) | 0.325 | 0/5 |
| Welsh, *Y Gododin* (9842) | text | 3000 | −0.335 | 0.240 (T16 B4) | 0.325 | 0/5 |

Spidroin-2 fits a persistent hidden chain (t01 0.062, t10 0.123, e1 0.765) and still has a premium at T32 B4: the first
real persistent stream with a positive premium.

The earlier phases below are kept as the record of what was screened.

## Earlier phases (before Phase 4b)

- Before Phase 4b, the count of 10 was not reached by any rule that survived the controls.
- **Phase 1** (30 fixed candidates, primary cell T = 32, B = 3): 0 positive. 8 passed the structure gates; 7 of those are
  persistent chains with no premium, as the theory predicts.
- **Phase 2** (30 anti-persistence-screened candidates): 3 evaluated (P6, P23, P24), 3 positive under the broader any-cell
  rule. P6 is degenerate (value gap 0.03–0.07, emissions at both bounds). P23 and P24 are the **Old Faithful geyser**
  again, the same source as Phase 1 c01/c02. 19 of 22 exchange tick streams have positive autocorrelation (+0.2 to +0.72),
  contrary to the bid-ask-bounce guess.
- **Phase 3** (systematic Rdatasets mining, 97 items, 640 streams): 153 passed the screen, 150 evaluated, 13 passed the
  non-degeneracy condition and the shuffle control, giving 6 distinct items resting on 3 independent series. **The lead's
  white-noise control shows these are not evidence** (below).
- **What survives:** one genuine real anti-persistent process with a fitted premium: the Old Faithful geyser (alternating
  long/short eruptions and long/short waits).

## The one that survives: Old Faithful

| Stream (source) | n | r1 | fit t01, t10, e0, e1 | rho at T=32,B=3 | best cell | IID-policy causal risk |
|---|---|---|---|---|---|---|
| eruptions > 3 min (`faithful`, c01) | 272 | −0.461 | 0.930, 0.631, 0.115, 1.000 | 0 | 0.130 at T=16,B=4 | 0.2 |
| waiting > 70 min (`faithful`, P23) | 272 | −0.498 | 0.906, 0.601, 0.011, 1.000 | 0.144 | 0.310 at T=16,B=4 | 0.2 / 0.325 |
| waiting > 70 min (`geyser`, P24) | 299 | −0.562 | 0.988, 0.847, 0.211, 1.000 | 0 | 0.070 at T=16,B=4 | 0.325 |

Delay 2 for P23 at T = 16: rho 0 at B = 2, 0.226 at B = 3. The gap C0 − V*_IID at the best cells is 0.8 to 1.3, so these are
not ratios of small numbers. The lead recomputed c01, P23 and P24 from their stored fits and got the same values. These
three rows are one source (one geyser), not three datasets. Caveats: n is 272–299; G1 passes for P24 by BIC only; fits are
at the emission bound e1 = 1.

## Why Phase 3 does not count (lead control, `wn_control.py`)

Every qualifying Phase 3 stream is a "rises" stream (sign of the first difference). The sign of the increment of an
**i.i.d.** series is anti-persistent by construction (lag-1 autocorrelation ≈ −1/3), so such streams pass the r1 screen
without any hidden regime. The Phase 3 shuffle control shuffled the 0/1 stream, which does not remove that construction.
The correct control is a series with no regime at all. Drawing 24 i.i.d. Gaussian series (n = 108–425, seed 20261117),
forming their "rises" streams and running the identical screen and `eval_stream`:

| | white-noise control (24 series) | Phase 3 (150 evaluated streams) |
|---|---|---|
| pass r1 screen | 24 of 24 (r1 −0.22 to −0.59) | 153 of 640 |
| pass G1 | 6 (25%) | 46 (31%) |
| positive, any-cell rule | 6 (25%) | 35 (23%) |
| positive and non-degenerate | 2 (8%) | 13 (8.7%) |

The rates match. Pure noise with no regime produces "qualifying" streams at the same rate as the real data, so the 13 Phase 3
streams (6 items, 3 underlying series) are what the pipeline returns for noise; they are **not** counted as support. G1
(a held-out likelihood gate) passes noise 25% of the time here and its BIC margin was negative for every Phase 3
qualifier. Lesson for the protocol: any binary stream built from a difference needs the matching noise control before it
can count.

## What this does and does not say

- It does **not** show that 10 real datasets support the premium; that count cannot be produced honestly from the sources
  tried. The premium needs strongly anti-persistent hidden regimes with informative labels; real streams with that structure
  are rare in what was screened. The robust, independent-of-method observation is that the persistent ones (7 of 8
  gate-passers in Phase 1) have no premium, as the synthetic theory says.
- It **does** show the premium on one real physical alternator (the geyser), with a large value gap and IID-policy risk of
  0.2–0.325 against a budget of 0.1, under a fitted model.
- All values are fitted-model computations at float64; no confidence intervals on fitted parameters were computed.

## Files

`PROTOCOL.md` (with Addenda A, B); `results/attempts.jsonl`, `attempts_phase2.jsonl`, `attempts_phase3_screen.jsonl`,
`attempts_phase3.jsonl`, `phase3_candidates.json`, `wn_control.json`, one JSON per stream (`c*`, `p*`, `q*`);
scripts in `scripts/paper4_continuation/rbdp/real_data/` (`fetch*.py`, `fit.py`, `evaluate.py`, `run_all.py`,
`run_phase2.py`, `run_phase3.py`, `phase3_candidates.py`, `wn_control.py`).

## Target met: 35 real datasets (Phase 7, Addendum G, 2026-11-18)

Ten more, all **real model-promotion streams** (challenger-wins on disagreement rounds of cached incumbent/challenger
losses): the run stopped at 35 inside Family A. Raw: `results/attempts_phase7.jsonl` (merged in protocol order; lead checked
it is a prefix of the protocol order), shards `attempts_phase7_shard*.jsonl`; script `run_phase7.py`. n = 3,000 disagreement
rounds each; best cell T32 B4 for all; 0/5 shuffles positive for all.

| Dataset | r1 | best ρΓ | causal risk of IID-optimal policy |
|---|---|---|---|
| openml_ldpa (localisation, activity) | +0.598 | 0.114 | 0.25 |
| appliances (energy) | +0.706 | 0.039 | 0.3 |
| beijing_pm25 (air quality) | +0.662 | 0.013 | 0.3 |
| FOREX aud/sgd hourly | −0.055 | 0.025 | 0.3 |
| electricity meter MT_005 | +0.552 | 0.125 | 0.5 |
| electricity meter MT_010 | +0.755 | 0.094 | 0.25 |
| electricity meter MT_029 | +0.682 | 0.024 | 0.15 |
| PM2.5 Shanghai | +0.689 | 0.012 | 0.3 |
| PM2.5 Shenyang | +0.664 | 0.012 | 0.3 |
| Tetouan power, zone 1 | +0.802 | 0.001 | 0.15 |

Composition of the 35: 18 texts, 5 proteins, 2 geyser datasets, 10 model-promotion streams.

## Baseline panel on all 35 (`results/phase7_baselines/`, `iid_failure` panel, 12 settings per chain, 420 settings)

- **RB-DP (P7) is causal-safe on all 35** (risk/α = 1.00 in every setting), as are the safe baselines P1 fixed-sample, P2 count
  SPRT and P6 e-process gate.
- **IID-calibrated policies break the budget on 29 of 35**: HMM-filter threshold (P3) up to 4α, myopic VOI (P4) up to 4α,
  IID-optimal (P5) up to 8α (geyser). On the 6 others (openml_ldpa, appliances, beijing_pm25, PM2.5 Shanghai and Shenyang,
  Tetouan z1) they stay at α.
- **Cost: RB-DP is never more expensive than any safe baseline** (lead check over all 420 settings: cheaper than the best of
  P1, P2, P6 in 238, equal within 1e-9 in 182, more expensive in 0). Strictly cheaper in every setting on 11 chains (fr, es, it,
  pt, fi, geyser, bovine elastin, la, ca, eo, FOREX aud/sgd). P1 and P2 capture −0.54 to 0.91 of RB-DP's value of information
  (negative = worse than never promoting) and P6 0.83 to 1.00.

### Baseline panel at the positivity horizons T ∈ {16, 32} (2026-11-19; `results/phase7_baselines_T16_32/`)

Same panel and chains, horizons matched to the positivity cells (α ∈ {0.05, 0.1}, B ∈ {2, 3, 4}, T ∈ {16, 32}; 420 settings,
2,940 policy rows, no errors; `PANEL_TS=16,32 run_phase7_baselines.py`). Lead tally from `settings.jsonl`:

- **RB-DP is causal-safe on all 35** (0 violations); P1, P2, P6 also stay at α.
- **IID-calibrated policies (P3, P4, P5) break α on 31 of 35** (up from 29 at T ∈ {12, 20}); maxima P3 4α, P4 4α, P5 8α. They
  stay at α on beijing_pm25, PM2.5 Shanghai and Shenyang, and Tetouan z1.
- **RB-DP is never more expensive than the best safe baseline:** cheaper in 210 of 420 settings, equal within 1e-9 in 210,
  more expensive in 0. Strictly cheaper in every setting on 10 chains (fr, es, it, pt, fi, geyser, la, ca, eo, FOREX aud/sgd).
