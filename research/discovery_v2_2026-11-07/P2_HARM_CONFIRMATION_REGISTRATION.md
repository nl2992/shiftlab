# P2 harm-attribution confirmation — registration

Registered 2026-11-07 **before any twin stream was built or any policy was run** on these datasets. The only contact with the data
so far: downloading the raw zips (SHA-256 below), listing their members, reading CSV headers and first rows to write loaders, and
`p2_confirm.py check` (shapes, columns, chronological order, episode counts). No losses, realised advantages or promotions have
been computed.

## Motivation
`DISCOVERY_DECISION.md` §1 reported an **exploratory** finding from the P2 attribution controls on five exposed UCI streams:
certified-port breaks under PERM (split fixed effect only) were almost never harmful (mean harmful-promotion rate .0001, max .0017),
while breaks under BSWAP (serial dependence only) were (mean .0084, max .069). This registration freezes that hypothesis and tests it
on datasets that **no P2 analysis has used**.

## Confirmation data (new to P2 and to this programme)
| dataset | UCI id | raw zip SHA-256 | target | dropped as leakage / redundant | delay (events) | episodes |
|---|---|---|---|---|---|---|
| tetouan_power | 849 | 3c4bf684…ddbbfe | Zone 1 power | other zones' power | 144 (10-min) | 18 × 20 splits |
| steel_energy | 851 | d82d28b3…aeadef | Usage_kWh | CO2, both power factors, Load_Type, WeekStatus, Day_of_week | 96 (15-min) | 12 × 20 |
| seoul_bike | 560 | 139e9908…e33c4 | Rented Bike Count | non-functioning days removed | 24 (hourly) | 2 × 20 |

Full hashes are asserted in `scripts/p2_confirm.py` (`RAW_SHA`). Raw data stays in `data/raw/p2_confirm/` (gitignored).
Downloaded but **excluded before any analysis**: Beijing multi-site air quality (UCI 501), because its city and period overlap the
exposed `beijing_pm25` stream; and Air Quality (UCI 360), because it has only 3 episodes and uses −200 missing-value codes. No outcome was
computed for either.

## Construction and run (unchanged components)
* Twin streams: `scripts/sota_sprint/twin_null.build` unchanged: same HGB model, 20 splits, 30% chronological training window,
  T=2000, ≤20 episodes, median-threshold binarisation on the training window. Only the loaders, delays and output directory are
  swapped in.
* Conditions: `p2_controls.transform` unchanged (PERM / 100-event BSWAP / ESWAP, plus ORIG). Condition seeds are
  [20261108, dataset index, condition index].
* Runner: `scripts/sota_sprint/screen.py` unchanged, with the same contract and the same 14 policies as `P2_CONTROLS_REGISTRATION.md`.
  It uses 3 policy seeds and seed base 2026110820.
* Code caveat as before: the codex/sprint2-leaderboards MOPE fixes (c66185c0, 81dc4d34) are not included.

## Frozen hypotheses
"Harmful promotion" means a promotion in an episode whose realised challenger advantage (mean of l0−l1 over the episode) is ≤ 0.
H_c is the harmful-promotion rate pooled over the 10 certified ports (`xu_acquisition_only` excluded), the 3 seeds and all episodes
of all three datasets, episode-weighted. P_c is the corresponding promotion rate.

* **HC1 (primary).** Δ = H_BSWAP − H_PERM > 0, with the 95% lower bound > 0. The bound comes from a split-cluster bootstrap that
  resamples splits within each dataset, with 4000 draws, paired across conditions.
* **HC2 (primary).** The fixed-effect-only breaks are near-harmless: the bootstrap 95% upper bound of H_PERM is ≤ 0.005.
* **Power guard.** If P_BSWAP < 0.02, the result is classed **inconclusive (underpowered)**, not as falsified.
* **CONFIRMED** iff HC1 and HC2 both pass and the power guard is not triggered. If HC1 or HC2 fails while powered, the hypothesis is
  **FALSIFIED** on this data and reported as such.
* **Secondary, reported regardless:**
  * HC3: Δ > 0 point estimate on ≥ 2 of 3 datasets.
  * S1: ESWAP validity (every certified port's upper CI ≤ .0936 on every dataset).
  * S2: under BSWAP, ≥ 3 of 10 certified ports break on ≥ 1 dataset.
  * PERM break count.

Analysis: `scripts/p2_confirm_analyze.py`, run once on the complete outputs. No threshold, dataset, block length, pooling or policy
set will be changed after the build.

## Interpretation note (stated in advance)
PERM preserves each episode's realised advantage and makes the stream exchangeable. A valid gate should therefore rarely promote when
the advantage is ≤ 0, so HC2 partly tests i.i.d.-null validity. HC1 is the substantive claim: on real streams with the per-split effect
removed, serial dependence alone produces promotions that are wrong for the episode.
Evidence class if confirmed: **CONFIRMED on three new UCI streams under this twin construction**. It is not a claim about other
constructions, block lengths or native implementations.
