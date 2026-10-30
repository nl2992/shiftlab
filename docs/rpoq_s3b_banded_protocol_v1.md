# RPOQ S3b: lattice-artifact and banded-structure test, protocol (pre-registered, exploratory)

**Branch:** `research/rpoq-s1-fatal-flaw-audit`. **Date:** 2026-10-29. **Follows:** [`rpoq_s3_structure_results_v1.md`](rpoq_s3_structure_results_v1.md).

| Label | Value |
|---|---|
| Work type | Exact dynamic programme, synthetic, fresh instance |
| Status | **Exploratory.** The hypothesis was suggested by S3's descriptive follow-up, so it is not independent of S3. It does not overturn S3's registered verdict |
| Claim level | None |
| Frozen before | Any S3b solver output (a calibration run may change `T` once, as in S3) |

## Hypotheses

- **H-lattice:** S3's non-monotone sawtooth in the informative context comes from the binary contrast and fixed-fraction bet producing a coarse wealth lattice. A four-level contrast should raise the monotone fraction.
- **H-band:** failing that, the optimum is still compact, with at most 2 breakpoints in wealth within each decision group.

## Instance (frozen)

Same protocol as S3 (event order, prefix updates, delay `d=2`, hard budget with frozen wealth when exhausted, absorbing alarm at `1/alpha`, `alpha=0.2`, bet fraction 0.5, grid {0.25, 0.5, 0.75, 1}, `P(A)=1/2`) except:

- Contrast levels `Z ∈ {−1, −0.5, +0.5, +1}`.
- Context A: proxy `H=0.5`; alternative pmf (0.05, 0.15, 0.30, 0.50), mean 0.525.
- Context B: proxy `H=0`; alternative pmf (0.10, 0.20, 0.30, 0.40), mean 0.35.
- Null, both contexts: uniform pmf (0.25 each), mean 0.
- `T=8`, budgets `B ∈ {3, 4, 5}`.
- The bet is `c / |X_min|` with `X_min` taken over all contrast levels.

## Criteria

- **C0 (validity, must hold):** exact null alarm probability of the optimal policy and of all 16 constant tables ≤ 0.2.
- **C1c (monotone):** fraction of groups (≥3 wealth values) with a weakly monotone optimal selection ≥ 0.90, at every budget.
- **C1b (banded):** fraction of groups admitting a selection with at most 2 changes ≥ 0.90, at every budget.
- **C2:** gap to the best constant table ≥ 0.02 at some budget (same as S3).

## Decision rule

| C0 | C1c | C1b | Outcome |
|---|---|---|---|
| fail | any | any | Bug. Fix and rerun. |
| pass | pass | any | H-lattice supported. The monotone structure holds on this instance. S3's verdict on its own instance stands. Nominate to S4 only with C2. |
| pass | fail | pass | H-band supported (exploratory). Compact but not a single threshold. A banded policy class could be nominated, with the caveat above. |
| pass | fail | fail | No compact structure on either instance. Close the adaptive-policy branch. |

## Calibration

A scratch run may report optimal power at `B=4`. If it falls outside (0.05, 0.95), `T` alone may change once (to 6 or 10), recorded here. No other parameter changes.

## Reproduction

`uv run python -m shiftlab.dive.rpoq_exact levels` writes `outputs/rpoq_s3b_levels_v1/results.json`.
