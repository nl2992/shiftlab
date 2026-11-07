# Development comparison: E_rb / RMM vs the matched two-sided e-SR (protocol, locked before run)

**Locked:** 2026-11-06, before any run under the seed bases below. **Status of evidence:**
development (post-development for E_rb/RMM, whose parameters were set on earlier development
data). This is not confirmatory evidence, and the regimes are the already-exposed synthetic
families. Its purpose is to decide whether the track-A rollback contribution survives the simple,
previously unrun competitor identified in `LEDGER.md` (Shin et al. entry).

## Question

Does E_rb (and RMM) reduce all-in deployment cost relative to a two-sided e-SR on the label clock
that starts a component at every label and restarts at each switch, under the same contract?

## Contract and seeds

- `bench.CONTRACT`: T=2000, B=200, c_q=.05, c_s=5, alpha=.05; common simulator, paired streams.
- Main panel: seed base `2026120601`, 100 seeds per regime.
- Null panel: seed base `2026120602`, 1000 seeds per regime.
- Neither base appears anywhere else in the repository (checked before the run).

## Regimes

- Reversal (primary): `F3_reversal_800`, `W_reversal_700`, `S_reversal_400`, `V_reversal_1000`.
- Late improvement (secondary): `V_late_600`, `W_late_1000`, `F1_late_800`.
- Stationary better (secondary): `F0_better`.
- Null / adverse (safety): `F0_null`, `V_null`, `V_worse` (null panel).

## Policies (fixed)

- Track-A methods: `E_rb:{h}` and `rmm:{h}+RMM` for hosts
  h in {`gated_deployment`, `discern_style`, `SMCS+retain-incumbent`, `gated_adaptive_range`}
  (the four hosts of the earlier WP1 post-development estimand), and `rmm:LRMD_k1`.
- Matched competitor (primary comparator, fixed now, not selected on outcomes):
  `two_sided_esr_label_clock` with defaults (`calibration="rmm_matched"`, Algorithm 3 bets,
  alpha/2 per side).
- e-SR sensitivity variants (descriptive): `esr_rmmbets_fullalpha` (RMM's bet grid, full alpha per
  side), `esr_arl` (ARL calibration).
- Other fidelity comparators (descriptive): `shekhar_ramdas_rcs_t3_anyexcl`,
  `river_page_hinkley_t3`.
- Context: the four hosts alone, `CONTROL_never_switch`.

## Estimands and analysis

- **Primary.** Per seed, the equal-weight mean over the 4 reversal regimes x 4 hosts of
  `J(E_rb:h) - J(two_sided_esr_label_clock)`; mean and 95% paired t interval over 100 seed blocks.
  E_rb is "favourable vs e-SR" iff the upper 95% limit < 0.
- **Secondary (each reported with paired 95% t intervals, Holm-adjusted across the listed
  secondary contrasts):** (S1) same as primary with `rmm:h+RMM` in place of E_rb;
  (S2) late regimes: `rmm:h+RMM - e-SR`; (S3) late regimes: `E_rb:h - e-SR`; (S4) `F0_better`:
  `E_rb:h - e-SR`.
- **Safety.** First-promotion rate on each null-panel regime with a Wilson 95% upper limit;
  registered bound `bench.NULL_PROMOTION_BOUND = 0.0936`.
- Per-regime and per-host contrasts are exploratory and unadjusted.
- Guardrails reported alongside cost: labels used, switches, rollbacks, harmful-switch rate.

## Decision rule (stated now)

- If the primary upper limit < 0 and E_rb passes the safety bound: the E_rb rollback mechanism
  survives the matched e-SR competitor on development data. Next step is a mechanism ablation
  (alpha split, host restart, post-verdict acquisition, gate), then a frozen confirmatory claim on
  fresh seeds and untouched real streams.
- If the upper limit >= 0: the track-A statistic is not shown to beat a two-sided e-SR. Record it
  as a negative result; any track-A claim must then rest on a component that the e-SR lacks, tested
  directly.
- No regime, host or comparator is added or dropped after the run.

## Reproduce

```bash
uv run --extra drift python scripts/sota_fidelity/esr_vs_erb_dev.py run --panel main --out outputs/sota_fidelity/esr_vs_erb_dev
uv run --extra drift python scripts/sota_fidelity/esr_vs_erb_dev.py run --panel null --out outputs/sota_fidelity/esr_vs_erb_dev
uv run python scripts/sota_fidelity/esr_vs_erb_dev.py analyze --out outputs/sota_fidelity/esr_vs_erb_dev
```
