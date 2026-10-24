# Evidence-directed query allocation: development results

**Run:** `outputs/evidence_directed_allocation_30/`  
**Protocol:** [`evidence_directed_allocation_protocol.md`](evidence_directed_allocation_protocol.md)  
**Status:** Exploratory only. No independent calibration or confirmation has been run.

## Design and integrity checks

The CUDA run used 30 seeds in each of stationary, benign-nuisance, and boundary-local-harm
scenarios (180 method-stream rows total), with 3,200 generated events, a 10% target dollar rate,
`q_min=0.05`, `q_max=0.50`, `alpha=0.05`, a common fixed e-process bound, and shared per-seed
query uniforms. The comparison methods were fixed uniform querying and the frozen evidence-directed
rule. Every method respected its pathwise cap. All 30 boundary-harm onsets were reached by each
method. No chart was generated because PaperBanana was unavailable.

## Findings

| Scenario | Method | False escalations | Detection / reached | Mean spend / cap | Mean labels | Mean horizon | Stream-mean RMSE |
|---|---|---:|---:|---:|---:|---:|---:|
| Stationary | Uniform | 0/30 | n/a | 346.13 / 359.09 | 229.6 | 0.974 | 0.0687 |
| Stationary | Evidence-directed | 0/30 | n/a | 195.43 / 359.09 | 129.5 | 1.000 | 0.0843 |
| Benign nuisance | Uniform | 0/30 | n/a | 357.74 / 359.09 | 179.9 | 0.758 | 0.0687 |
| Benign nuisance | Evidence-directed | 0/30 | n/a | 266.06 / 359.09 | 127.9 | 0.998 | 0.0785 |
| Boundary-local harm | Uniform | 0/30 | 0/30 | 346.13 / 359.09 | 229.6 | 0.974 | 0.0734 |
| Boundary-local harm | Evidence-directed | 0/30 | 0/30 | 230.20 / 359.09 | 152.3 | 1.000 | 0.0899 |

On boundary harm, the paired stream-mean RMSE difference (evidence-directed minus uniform) was
`+0.0165` (95% seed-bootstrap interval `[-0.0011, +0.0323]`). The paired spend difference was
`-115.94` (95% t interval `[-131.65, -100.22]`), and the label difference was `-77.3`
(`[-87.8, -66.8]`). The mean processed-horizon difference was `+0.026` (`[+0.011, +0.041]`).

The allocation therefore used less of the available cap and processed more events in the harmful
scenario, but did not detect harm or improve estimation accuracy in this block. Fixed uniform also
detected no harms, so this comparison is underpowered for a power ranking. Zero alarms across 30
streams per control are descriptive and do not establish a low false-alarm rate. The candidate's
mean propensity was only 0.055–0.065 across scenarios and its maximum observed propensity was at
most 0.140, showing that the e-value urgency signal rarely activated. The simple linear urgency
map is not ready for promotion.

## Interpretation and next step

The result is consistent with a conservative feedback loop: the monitor starts at `q_min`; weak
early evidence keeps the query rate near its floor; the limited feedback then leaves too little
evidence to raise the rate. The budget taper adds further conservatism as labels are spent. This is
a development diagnosis, not evidence that evidence-directed querying is generally inferior.

Do not confirm this exact candidate. A new development block may compare a small prespecified grid
of urgency curves that amplify modest positive log-evidence while retaining the positive query
floor, hard-cap stopping rule, and common monitor bound. Select on reached-harm detection under the
fixed cap, while reporting spend, horizon, and estimation error; then calibrate the selected rule on
fresh nondegenerate null streams before testing it on disjoint reversal profiles. Any changed
propensity mapping still uses the standard predictable-factor argument and is not a novelty claim.

Reproduce with the command in the protocol. The Parquet metrics, CSV summaries, paired contrasts,
report, environment, and SHA-256 manifest are in [`outputs/evidence_directed_allocation_30/`](../outputs/evidence_directed_allocation_30/).
