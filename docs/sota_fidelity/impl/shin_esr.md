# Implementation: Shin-Ramdas-Rinaldo e-SR / e-CUSUM and river Page-Hinkley

Status: implemented 2026-11-06. Not yet reviewed by the lead session. Registered opt-in only
(`bench.FIDELITY_ADAPTERS_20261106`, `fidelity_extras.EXTRA`); not in `ALL_COMPARATORS` or any pool.

## Files

- `scripts/promising_directions/sota/competitors/shin_esr.py` (T2 core + T3 adapter; every line mapped to
  an equation in the module docstring, NEJSDS numbering with arXiv v4 in parentheses)
- `scripts/promising_directions/sota/competitors/river_page_hinkley.py` (T1 detector via river, T3 adapter)
- `scripts/failure_atlas_v2_flq/fidelity_extras.py`, `scripts/sota_sprint/bench.py` (registration)
- `tests/sota_fidelity/test_shin_esr.py`, `test_river_page_hinkley.py`; `test_fidelity_registration.py`
  edited only to skip entries whose optional package (river) is not installed
- `scripts/sota_fidelity/smoke_shin_esr.py` (smoke comparison below)
- Decision records: `LEDGER.md` (Shin and Page-Hinkley entries), `specs|checks/shin_edetectors.md`,
  `specs|checks/page_hinkley.md`

## What was built

| Piece | Tier | Source |
|---|---|---|
| `algorithm3_grid` (sub-E psi, v_min 0) | T2 | Algorithm 3 / eqs (94)-(96) = (B.10)-(B.12), Algorithm 4 bisection |
| `BoundedMeanEDetector` (e-SR, e-CUSUM, mixture over bets, Remark 2.7 start weights) | T2 | eq (70) increment, (13),(14), (24)-(28), Remark 2.7 |
| `two_sided_bounded_grid` | T2 of the stcpR6 construction (not in the paper) | stcpR6 `convertDeltaToExpParams` |
| `TwoSidedESRDeploymentAdapter` (`two_sided_esr_label_clock`) | T3 | label clock; never "Shin et al.'s algorithm" |
| `RiverPageHinkleyDeploymentAdapter` (`river_page_hinkley_t3`) | detector T1 (river 0.26.1 called, not re-implemented); wrapper T3 | river `PageHinkley` |

Choices that follow the check file rather than the printed text: increment is eq (70) (the code and the
checker's NBA reproduction), the grid is built from the eq (72) surrogate; `M_0 = 0` (not the typo
`M_0 = 1`); weak `>=` alarm (paper (7)), the R code uses `>`; `v_min = 0` (stcp), not stcpR6's 1.

## Adapter design

- Label clock = delivery order. `z = loss(deployed) - loss(other)`, `X = (z+1)/2`, `m = 1/2`, so eq (70)
  is `1 + lambda z`. Pacer: shared `PacedDisagreementAcquisition`, no IPW (disagreement-conditional mean).
- Two alternating one-sided detectors, promote (incumbent deployed) and rollback (challenger
  deployed), each at `alpha/2` (stcpR6 split). The simultaneous stcpR6 50/50 mixture is implemented in
  the core (`two_sided_bounded_grid`) and tested but is not what acts in deployment.
- A new e-SR start at EVERY label (RMM: every 10). After any switch both detectors restart and labels
  requested at or before the switch event are dropped (RMM clears `order`/`queue` the same way).
- `calibration="rmm_matched"` (default): RMM's finite-horizon form. Start weights `1/B` over the first
  `B` labels, threshold `1/alpha_side` on the weighted sum (Remark 2.7 with total mass 1), Algorithm 3
  grid at the equivalent unit-mass level `alpha_side/B`. `calibration="arl"`: Def 2.6 unit mass,
  threshold `1/alpha_side` (Theorem 2.4; ARL only).
- `bets="algorithm3"` (default, Delta range `[2 delta_min, 1]` with `delta_min = 0.05`; for +-1
  outcomes `v = 1` so `Delta_op = E s <= 1`) or `bets="rmm"` (0.15/0.3/0.5, uniform).
- Null statement (derived, not in the paper; Ville on `V_n = S_n + sum_{j>n} pi_j`): if in the
  label-delivery filtration since the last restart the conditional mean of `X` is `<= m` (non-deployed
  not better), the active side fires within the budget with probability `<= alpha_side`. Not covered:
  serial dependence beyond the conditional-mean condition (no theorem claimed for rho > 0), out-of-order
  release, cumulative error over repeated promote/rollback cycles (levels add), switching cost.

## Deviations from the paper (T2 core and T3)

1. Alarm `>=` (paper) not `>` (R code). 2. Log-space recursions. 3. No Algorithm 2 (adaptive; defaults
for r, m, K_0 absent from the main text) and no Bernoulli `psi_B` grid (so the Bernoulli "69 baselines"
count is NOT reproduced). 4. Delta range for the adapter is a design constant, not eq (75) with
data-derived `m`, `delta`. 5. T3: everything in the previous section.

## Tests (`uv run pytest tests/sota_fidelity -q`: 79 passed, 2 skipped; the 2 skips are the existing UPF tests needing torch)

`test_shin_esr.py` (24): hand-computed SR / CUSUM / Remark 2.7 recursions on a 3-point sequence;
M_0 = 0; brute-force `sum over starts` and `max over starts` equal the recursions for a 3-bet signed
mixture; trivial e-process identities (`M^SR_n = n`, `M^CU_n = 1`); eq (75) numbers; Algorithm 3 on the
NBA inputs (190 components = K 189 + atom, `g_alpha = 13.1928`, weights sum 1, `psi*(Delta_k) = D_U
eta^-k`); NBA reproduction; two-sided mixture detects both directions and is invariant to `X -> 1-X`;
null false-alarm rate over the full budget horizon for the promote side AND the rollback side under
`rmm_matched` (`<= alpha_side + 3 s.e.`; observed about 0.008 against 0.025 with 600 runs) and under `arl`
(`<= n alpha_side + 3 s.e.` for a short horizon); large change detected on both sides and the
rollback follows the promotion; restart resets state and drops in-flight labels; budget / delay /
determinism / "decisions at t unchanged when the future is altered" in the simulator; state round trip.
The NBA test reads the Saha-Ramdas CSV (the checker's scratch copy or `$SHIFTLAB_NBA_CAV_CSV`) as data
only and skips if absent; the CSV is third party and is not vendored.

`test_river_page_hinkley.py` (3, needs `--extra drift`): river's docstring stream alarms at (1006, 5), the
same result as the checker's independent ports; adapter contract; PH is a change detector, not a sign
test.

## NBA Cavaliers reproduction (Plus-Minus, `m = 0.494`, alpha 1e-3, 640 games)

| Detector | This port | Paper |
|---|---|---|
| e-SR (eq (70), Algorithm 3 with Delta_L 0.024, Delta_U 1600) | game 378, 2015-03-10, value 1292.9 | game 378 |
| e-CUSUM | game 445, 2016-02-08 (value 963.9 at game 444, below 1000) | game 444, 2016-02-06 |

Same result with exact eq (75) ranges (378 / 445). The one-game e-CUSUM gap is unexplained (as in the
check file); it is recorded here, not tuned away. This is a numerical reproduction of the printed
example by a T2 port, not a line-by-line comparison against the R code.

## SMOKE comparison (5 seeds, NOT evidence)

Seed base 2026110699 (not `DEV_SEED_BASE`), contract T=2000, B=200, c_q=.05, c_s=5, alpha=.05.
Net cost J (lower is better), mean over 5 paired seeds; "promote" is the fraction of seeds that ever
deployed model 1. Command: `uv run --extra drift python scripts/sota_fidelity/smoke_shin_esr.py --out <dir>`
(built entirely from existing registry code; `rmm:LRMD_k1` from the RMM module's own
`FACTORIES`; `esr_rmmbets_fullalpha` = same adapter with RMM's bets and side alpha 0.05 to match LRMD;
`esr_arl` = ARL calibration).

| regime | policy | J | promote | rollbacks |
|---|---|---|---|---|
| F0_null | never switch | 351.4 | 0 | 0 |
| | two_sided_esr_label_clock | 361.4 | 0 | 0 |
| | esr_rmmbets_fullalpha | 361.4 | 0 | 0 |
| | esr_arl | 383.0 | 1.0 | 1.4 |
| | rmm:LRMD_k1 | 361.4 | 0 | 0 |
| | rmm:gated_deployment+RMM | 361.4 | 0 | 0 |
| | E_rb:gated_deployment | 361.4 | 0 | 0 |
| | river_page_hinkley_t3 | 361.4 | 0 | 0 |
| F0_better | never switch | 420.8 | 0 | 0 |
| | two_sided_esr_label_clock | 376.8 | 1.0 | 0 |
| | esr_rmmbets_fullalpha | 396.2 | 0.6 | 0 |
| | esr_arl | 345.6 | 1.0 | 0.4 |
| | rmm:LRMD_k1 | 392.2 | 1.0 | 0 |
| | rmm:gated_deployment+RMM | 383.8 | 0.8 | 0 |
| | E_rb:gated_deployment | 383.8 | 0.8 | 0 |
| | river_page_hinkley_t3 | 430.8 | 0 | 0 |
| F3_reversal_800 | never switch | 350.6 | 0 | 0 |
| | two_sided_esr_label_clock | 418.6 | 1.0 | 1.0 |
| | esr_rmmbets_fullalpha | 410.2 | 1.0 | 1.0 |
| | esr_arl | 341.0 | 1.0 | 1.0 |
| | rmm:LRMD_k1 | 421.4 | 1.0 | 0.8 |
| | rmm:gated_deployment+RMM | 421.0 | 1.0 | 1.0 |
| | E_rb:gated_deployment | 404.8 | 1.0 | 1.0 |
| | river_page_hinkley_t3 | 360.6 | 0 | 0 |
| S_reversal_400 | never switch | 319.6 | 0 | 0 |
| | two_sided_esr_label_clock | 329.6 | 0 | 0 |
| | esr_rmmbets_fullalpha | 344.0 | 0.2 | 0.2 |
| | esr_arl | 350.6 | 1.0 | 1.0 |
| | rmm:LRMD_k1 | 345.8 | 0.2 | 0.2 |
| | rmm:gated_deployment+RMM | 362.6 | 0.6 | 0.6 |
| | E_rb:gated_deployment | 356.0 | 0.6 | 0.6 |
| | river_page_hinkley_t3 | 329.6 | 0 | 0 |

What the smoke shows, and no more: with 5 seeds nothing is distinguishable (spreads of 10-60 J are within
what a handful of seeds produces). Qualitative: (i) the null rows confirm `rmm_matched` is conservative
and `arl` is not (it promotes in 5/5 null seeds, as expected from an ARL-only threshold); (ii) the variant that starts at every label (`esr_rmmbets_fullalpha`) promoted less often on F0_better (0.6) than `rmm:LRMD_k1`, which uses the same bets and side alpha but starts every 10 labels (1.0). A plausible mechanism, not tested here: with total start mass 1, spacing 10 gives 20 starts of mass 1/20 and every-label gives 200 starts of mass 1/200, so each start pays a ten-fold larger prior penalty; (iii) `esr_arl` has the lowest J on F0_better and F3_reversal_800 in these seeds, but it also promotes on every null seed; its J advantage is bought with an uncontrolled false-promotion rate, so the calibration must always be reported with the result; (iv) river PH never promotes where the challenger is better from
the start (a change detector, as documented). No claim about E_rb or RMM novelty follows. Seeds, a
pre-registered metric and the dev/confirmatory split are required before any such claim.

## Assessment

Continue. The matched simple competitor now exists and runs through the common harness; the
decision it informs (does RMM / E_rb beat a plain two-sided e-SR) needs a 20-seed development screen
on the registered environments, then a locked confirmation, before any statement. Open points: the
e-CUSUM one-game gap; Bernoulli `psi_B` grid and Algorithm 2 not ported; no numerical comparison against
the R implementation (T1 for the detector is not claimed for the e-detector).
