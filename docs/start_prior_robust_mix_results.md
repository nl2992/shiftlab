# Robust fixed-mixture start-prior development results

This registered development screen tested five fixed convex blends between the nominal-horizon
Beta(2,1) prior and the uniform eight-start prior. The 18 alternative cells used 500 paired CUDA
streams each. The independent null block used 1,000 streams per scenario, with a 30-cell
simultaneous false-escalation bound. See the frozen [protocol](start_prior_robust_mix_protocol.md)
and machine-readable [outputs](../outputs/start_prior_robust_mix_development/).

## Selection and calibration

The prespecified maximin objective averages detection across the three query rates within each
onset/severity group, then takes the minimum over six such groups. **Pure Beta(2,1), `rho=1`, ranked
first**: its maximin rate was 20.87% and macro group rate 69.74%. The next best fixed blend,
`rho=0.75`, reached 19.47% maximin and 69.21% macro; uniform reached 15.33% and 67.62%. Detection
decreased monotonically along the tested shrinkage path as `rho` moved toward uniform.

The largest observed null false-escalation rate was 1.80%; its simultaneous one-sided 95% exact
upper bound was 3.41%, below the 5% screen criterion. All 30 cells passed. The generator resolved to
CUDA. Output row counts, seed ranges, source hashes, environment, and Parquet checksums are recorded
in `outputs/start_prior_robust_mix_development/manifest.json`.

## Decision

The protocol required an interior blend to improve the maximin rate over both endpoints before
freezing it for confirmation. None did, so **stop this shrinkage branch**. This negative screen
supports the already independently confirmed Beta(2,1) option over these five blends; it does not
show that it is optimal over all start-time priors. The mixture construction and offline prior
selection are standard consequences of convex e-process mixtures and independent development /
evaluation, not a novelty claim. No confirmation run is warranted for this branch.

No figure was required. PaperBanana was unavailable in this session; future visuals must use it when
available.
