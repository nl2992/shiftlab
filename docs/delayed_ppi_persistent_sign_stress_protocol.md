# Delayed PPI persistent-sign and informative-delay stress screen

**Status: frozen before execution; descriptive assumption stress, not a new validity claim.**

## Question

The existing delayed-PPI evidence is calibrated under IID outcomes and under a persistent-scale Markov null with fresh fair signs. This screen separates two questions: (1) whether a marginally zero but serially predictable sign process violates the conditional-mean premise used by the e-process, and (2) how outcome-dependent response times change alarm availability when event-order evidence is committed only through the resolved prefix.

## Frozen design

- Run 2,000 independent streams per cell, horizon 2,400, seed block 20400000–20401999, and exact 480-request hard cap. Use CUDA for vectorized stream generation and monitor calculations when available; preserve CPU execution.
- Sign process: initialize a fair sign and flip it each event with probability `(1-rho)/2`, for `rho ∈ {0, 0.50, 0.90, 0.98}`. Set paired cost `Z_t ∈ {-1,+1}` to that sign and the source-trained proxy `H_t=0`. Every cell has marginal `E[Z_t]=0`; only `rho=0` has the stated IID conditional-mean null. For `rho>0`, `E[Z_t | Z_(t-1)] = rho Z_(t-1)`, so these cells intentionally violate the monitor's conditional-mean null.
- Query with independent Bernoulli probability 0.20 until 480 requests have been used; no further requests are made after the cap. Use the same query uniforms and outcomes across delay profiles and monitor variants within each seed/rho.
- Delay profiles for queried positive/negative outcomes: `fixed12=(12,12)`, `positive_fast=(0,12)`, and `positive_slow=(12,0)`. Unqueried events have a known zero PPI increment and resolve immediately. Neither the query policy nor monitor may inspect the current outcome or its delay before query selection. Process evidence only through the contiguous resolved event prefix; drain all finite delays before final integrity checks.
- PPI increment: `X_t=Q_t Z_t/q_t`, with zero proxy `H_t=0`, `q_t=0.20` while querying remains active and `X_t=0` after the hard cap is exhausted. This zero-proxy special case of PPI isolates the conditional-mean assumption without source-proxy estimation. Use the existing predictable-bound e-process with the conservative bound `B_t=2/q_t-1=9` while active (and 1 after exhaustion), alpha 0.05, default registered stakes. Compare `full_stream` with an equal-weight fixed-start mixture at events 0, 300, ..., 2,100. These are established monitors, not candidate new algorithms.

## Outcomes and interpretation

Save every stream-monitor row, cell summaries, a Parquet metrics file, protocol/source hashes, environment manifest, and checksums. Report alarm probability and exact one-sided binomial intervals, mean first-alarm event and wall time among alarms, labels, query-path integrity, and empirical lag-one sign correlation. Check the cap, complete delayed-prefix drain, monitor equality at the event-time endpoint across delay profiles for matched seeds, and query-path equality. For each `rho`, the IID implementation/calibration control uses a Bonferroni one-sided 97.5% upper limit across its two monitors; delay profiles reuse identical streams. Elevated alarm rates at `rho>0` demonstrate the conditional-mean assumption's relevance; they are not a defect in the e-process under its stated null. Delay profiles may alter wall-time alarms while leaving the fully drained event-time path unchanged. The screen does not test arbitrary dependence, selective non-arrival, using latency as evidence, or a dependence-aware alternative.

No visual is planned. Any future research visual must use PaperBanana.

## Reproduction

```powershell
uv run shiftlab-dive-delayed-ppi-assumption-stress --device cuda --output-dir outputs/delayed_ppi_assumption_stress_2000_registered
```
