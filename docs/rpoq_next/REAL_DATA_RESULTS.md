# Real-data results

## R0 (protocol [`REAL_DATA_PROTOCOL.md`](REAL_DATA_PROTOCOL.md)): context heterogeneity and stability, development splits only

CRSP CIZ panel, 10 disjoint cohorts of 300 train-universe PERMNOs, benefit `Y = −Z` (candidate over reference, 5 bps), 8 train-quantile bins. Validation 2015–2017 versus calibration 2018–2019. **Test split not read.** Artifact: `outputs/rpoq_next/r0/results.json`; code `scripts/rpoq_next/crsp_heterogeneity.py`.

| Context | top-bin SNR / median (val) | top-bin val μ̂ 95% CI (cohort bootstrap) | Spearman(val SNR, cal SNR) | top-bin cal μ̂ | Heterogeneity | Stable |
|---|---|---|---|---|---|---|
| size (`log1p_dlycap`) | 5.09 | excludes 0 | **0.738** | +0.0013 (+13 bps) | **yes** | **yes** |
| abs_return (`|dlyret|`) | 1.85 | — | −0.762 | ≈ 0 | no | no |

Mean benefit by size bin (bps per event), validation: 16.0, 8.3, 4.9, 2.6, 4.5, 3.0, 2.7, 3.7; calibration: 12.7, 6.9, 4.6, 1.8, 1.5, −0.9, −0.1, −1.3 (bin 0 = smallest).

**Registered verdict:** the mechanism has purchase on CRSP through the size context (both criteria met for one definition); not through absolute return.

**Caveats that bound what this means.**
- Bin 0 is the smallest-cap stocks, where a flat 5 bps cost is not credible; the apparent benefit there is partly a consequence of the imposed cost assumption, and these stocks are where microstructure effects are largest. This is a retrospective property of the panel, not a deployable edge.
- Heterogeneity weakened between validation and calibration (large bins turned negative), i.e. the nonstationarity the synthetic `het_flip` setting warns about is partly present in the data, even though the top bin held.
- This establishes only that there is structure for an allocation rule to use. It says nothing yet about whether the rule beats uniform at a matched budget.
