# Limitations

- **Self-review only.** Every agent was the same model, and no independent human or mathematical
  review took place.
- **Synthetic scope.**
  - Bernoulli losses with piecewise-constant means: one family with three structures, plus a single
    non-Bernoulli red-team probe.
  - Two actions only, and actions do not affect outcomes (prediction replay).
- **Matched α is a point-null match.** On boundary nulls, false-alarm rates at interior
  thresholds range from 0.04 to 0.39 (`07`).
- **Baselines.**
  - PH, batch and SR betting are textbook reimplementations. CUSUM and Kelly were cross-checked
    against repo code.
  - The Kelly detector is H2c-inspired, not H2c.
  - No PPRM, Shiryaev posterior rule, ADWIN or Cara/Regol baseline was run.
- **The simple references are fixed-sample monitors** with effective α of 0.5–1. The conclusions
  therefore concern controller form and threshold, not the presence or absence of monitoring.
- **Real data.**
  - One series per pair; release delays and costs are imposed, not measured.
  - OPSD dev years (2018–19) were exposed by the phase-1 headroom screen.
  - The OPSD snapshot may contain revised values.
  - The reserved 2020 window contains a public demand disturbance.
  - The primary monitor and controller were chosen on dev results (disclosed selection risk).
- **Confirmation scope.** Confirmation covered only the asymmetric S2 cells and one real window.
  Symmetric-regime conclusions are development-only.
- **Unverified prior art.** Classical QCD originals and the Xu et al. theorems were not read in
  full, so novelty verdicts are provisional.
- **No PaperBanana figures** were produced.
