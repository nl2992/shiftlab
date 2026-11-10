# C_FIDELITY_AUDIT: DISCERN-style PrPl-EB `psi_E` / variance penalty

Status: exploratory fidelity audit, 2026-11-09. Branch `research/paper3-safe-budgeted-intervention-2026-11-09`
(base `8af33afe`). Ledger rows: `ledger/atlas.jsonl` kind `fidelity` (see end).

## 1. Where the issue is
`scripts/promising_directions/sota/competitors/certificate_stops.py::PrPlEBCS.update`. The pre-fix port
(commit `89cf1bd2`) used `psi_E(l) = -log(1-l) - l` together with `v_i = 4 (W_i - mu_{i-1})^2`. The fix
(commit `64ee5a46`, "Failure Atlas v2", already in `8af33afe`) uses `psi_E(l) = (-log(1-l) - l)/4`. The
pre-fix product inflated the variance penalty `sum v_i psi_E(l_i)` by exactly 4x.
The RMM/LRMD v2 report (`docs/failure_atlas_v2_report.md`, correction note) says every DISCERN-style number
there predates the fix.

## 2. Source check
* Waudby-Smith and Ramdas, arXiv:2010.09686 (PrPl-EB, Theorem 2). **VERIFIED by me** on 2026-11-09: the PDF
  was fetched and text-extracted (`pdftotext`); eq. (13) `M_t(m) = exp{ sum lambda_i (X_i - m) - v_i psi_E(lambda_i) }`,
  `v_i := 4 (X_i - mu_hat_{i-1})^2`, eq. (14) `psi_E(l) := (-log(1-l) - l)/4`, and eq. (15) the plug-ins
  `lambda_t = sqrt(2 log(2/alpha) / (sigma2_{t-1} t log(1+t))) ^ c`, `sigma2_t = (1/4 + sum (X_i - mu_i)^2)/(t+1)`,
  `mu_t = (1/2 + sum X_i)/(t+1)`. The corrected code matches these exactly.
* DISCERN, arXiv:2609.17560, Appendix A. **UNVERIFIED**: I did not retrieve it. The repository docstring
  states DISCERN prints `psi_E = -log(1-l) - l` and `v_i = (W_i - mu)^2` (no factor 4); that is consistent
  with the pre-fix port having mixed the two conventions (kept WSR's 4 in `v_i`, dropped the 1/4 in psi_E).
  The two conventions are algebraically equal (`4 (.)^2 * psi/4 = (.)^2 * psi`), so the CS the paper intends is the
  corrected one either way.

## 3. Fix and test
Implementation: `src/shiftlab/paper3/atlas/certificate_stops.py` (port, header cites `8af33afe`); `legacy_psi=True`
reproduces the pre-fix behaviour **for this audit only**. Tests (`tests/paper3/atlas/test_atlas.py`):
independent brute-force grid reference of eqs. 13-15 matches the fixed CS endpoints within 1e-3 over 300 steps;
legacy CS is >1.5x wider; fixed CS covers p=.3 in >=92% of 300 sequences (observed <=8% miscoverage).
On a Bernoulli(.6) [0,1] stream the legacy CS at t=2000 is [0.455, 0.713] vs fixed [0.537, 0.627]
(width 0.258 vs 0.089, 2.9x).

## 4. Pre/post reproduction (identical seeds, unmodified v2 harness)
`scripts/paper3/atlas/run_fidelity.py`: v2 validation regimes V_late_1000_p72, V_better_p62, V_better_p70, V_null,
V_dep_null_r8, V_late_1000_d50; seeds 5000-5019, seed base 20261104, T=2000, B=200, c_q=.05, c_s=5, alpha=.05;
policies Gated, DISCERN-style, and each with +RMM; pre-fix patched in-process, 480 runs per variant.
Archive: `outputs/paper3/atlas/fidelity/records.json`, `side_by_side.csv`.

**Result: no change.** 480/480 paired runs have identical net cost (max abs diff 0.0), identical labels and identical
promotion flags. Side by side (mean net cost, pre = post): V_better_p70 DISCERN 448.28 / DISCERN+RMM 346.95;
V_better_p62 421.56 / 383.80; V_late_1000_p72 391.78 / 368.20; V_null 370.56 / 370.60; V_dep_null_r8 371.96 / 377.30;
V_late_1000_d50 398.24 / 372.70. A single-episode probe (V_better_p70) shows the CS did change (gain bounds
[-0.0678, 0.2729] legacy vs [-0.0561, 0.2611] fixed at event 1901) but never crossed 0 in either variant.

Interpretation (stated limits): at the v2 contract the HT scale `c = 1/p_min = 20` dominates the interval, so the
/4 correction (7% narrower here) never changes a verdict; DISCERN-style behaves as a never-certify rule, practically
identical to Gated (gaps in the table are RMM and noise). Hence (i) the "DISCERN+RMM - DISCERN" gains in the v2
report are **not** overstated by this bug *in this contract* (numbers unchanged), so the correction note's
direction of concern is not supported by this 6-regime x 20-seed subset (full 13-regime / real-stream rerun not done);
(ii) a different and larger fidelity gap remains: this adapter (HT weights with floor 0.05, no learned judge
routing, no Tier-0) is a weak stand-in for DISCERN, so "beats DISCERN" claims carry little weight. Pre-fix numbers
must not be reused as calibrated comparisons; none are used in this workstream (`discern_fixed` only; `discern_legacy`
appears solely as a fidelity row).

Atlas-grid check (`discern_legacy` vs `discern_fixed`, 32 cells x 30 seeds, alt streams): J difference
-0.04 [-0.19, +0.05]; 76% of paired episodes identical.
