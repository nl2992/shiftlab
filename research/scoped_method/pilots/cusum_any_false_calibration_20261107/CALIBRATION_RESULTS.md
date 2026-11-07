# E-CUSUM null calibration results

**Stage 1 completed:** 2026-11-07. This reports only the preregistered null grid; independent
alternative evaluation outcomes were unopened at report time. Protocol: [`PROTOCOL.md`](PROTOCOL.md).
The independent alternative evaluation was frozen in [`EVALUATION_FREEZE.md`](EVALUATION_FREEZE.md)
before its first run.

## Selection

The largest qualifying grid value is **alpha = 0.005**. At that value 22 of 1,000 `F0_null`
streams promoted; the Bonferroni-adjusted one-sided 99% Wilson upper bound across the seven tested
alpha values is 0.04062, below the frozen 0.05 limit. The next larger grid value, alpha = 0.01, had
40/1,000 promotions and an adjusted upper bound of 0.06290, so it fails. This is empirical
finite-horizon calibration under the specified simulator null, not an anytime guarantee and not a
replacement for the e-CUSUM published ARL interpretation.

## Full frozen grid

| Alpha | False promotions / 1,000 | Bonferroni one-sided 99% Wilson upper | Rule |
|---:|---:|---:|---|
| 0.05 | 215 | 0.25617 | Fail |
| 0.02 | 81 | 0.11058 | Fail |
| 0.01 | 40 | 0.06290 | Fail |
| 0.005 | 22 | 0.04062 | Pass; selected |
| 0.002 | 12 | 0.02740 | Pass |
| 0.001 | 8 | 0.02176 | Pass |
| 0.0005 | 5 | 0.01730 | Pass |

The most stringent observed value is not selected: the frozen rule chooses the **largest** alpha
passing the adjusted null bound. No threshold was added or changed after inspecting outcomes.

## Reproduction and provenance

Calibration used seed base `7110701101`, 1,000 streams at each of seven alphas, one policy per
run, with four workers. All 7,000 jobs completed successfully in 408.9 seconds total. Each
`null_<alpha>/manifest.json` records the source hashes, code revision (`b090461148d7f6c3ff52f7f1e2fc4c0beda97b42`),
contract, and runtime. Raw `records.jsonl` files are retained beside the manifests. Their SHA-256
hashes:

| Alpha | Raw record SHA-256 |
|---:|---|
| 0.05 | `455029585084c16e285c3a8c3eb4c1904181f7468fea773c93ae074a24fe64fb5` |
| 0.02 | `0293e4fad4750ca2a8d3c8aeb06b9608b8a73f86fb5ec516b635ef2dcb8e04ad` |
| 0.01 | `9343d90a743f3546c26c1c38b18201f7468fea773c93ae074a24fe64fbfdbd51` |
| 0.005 | `5490c327b32ccc5e1cb177df7bfb182df339d128eac7a8dd17f646ed0209cbce` |
| 0.002 | `8ea159d71aa2373949a06d5142d72e34d48e33374d41a463117c5aa561714ee5` |
| 0.001 | `50b1bfb4839d029fb5dd556b5488063fc712d0f3c51228126bcaa82763d599a5` |
| 0.0005 | `8e9607766373951000a8ad14601e6de3bcef9b7dbbdb50d5b77529372daa5bb2` |

## Interpretation

This answers the baseline-fidelity gap left by the e-SR-only calibration: the existing e-CUSUM
implementation has a usable empirically calibrated alpha grid point in this null and contract.
Whether that operating point preserves net-cost advantage in the worthwhile reversal cell remains
unknown until the independent evaluation in `EVALUATION_FREEZE.md` is executed. No real data has been
opened, and no method novelty or independent transfer is established by this calibration.
