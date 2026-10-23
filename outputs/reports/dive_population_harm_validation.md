# DIVE population decision-harm validation

Generated: `2026-10-23T09:40:33.769639+00:00`

This is deterministic one-dimensional adaptive quadrature of the benchmark's 
population paired cost difference. It is independent of the finite stream seeds used 
for monitor evaluation. The score is `S=X0-0.9*X1 ~ Normal(0, 1.81)`. The incumbent 
uses the source posterior 0.5 threshold; the reference uses the asymmetric-cost 
threshold `C_FP/(C_FN+C_FP)`. Nuisance features do not enter either policy.

Configured material-harm margin: **0.100000 cost units**.

| Scenario | Severity | Population excess cost | Excess minus margin | Interpretation |
|---|---:|---:|---:|---|
| `stationary` | 0.00 | 0.07929513 | -0.02070487 | Population null: no shift |
| `benign_nuisance` | 0.00 | 0.07929513 | -0.02070487 | Population null: nuisance coordinates shift; signal law is unchanged |
| `boundary_local_harm` | 1.50 | 0.37827449 | +0.27827449 | Harmful alternative: positive outcomes increase near the boundary |
| `residual_variance` | 1.50 | 0.13188153 | +0.03188153 | Harmful alternative: residual scale increases |

The stationary and benign-nuisance scenarios satisfy the population conditional-mean 
null for the fixed 0.10 margin. A finite stream can still have an oracle average above 
the margin because its realized covariates vary; that pathwise flag is not itself the 
null parameter or a false-alarm event. False escalation is a monitor crossing under the 
population null. The boundary-local and residual-variance cases are alternatives only 
when their population excess cost exceeds the configured margin.

The report validates these four Gaussian-score cases only. It does not prove the 
monitor's guarantee, estimate real-world utility, or cover delayed/selective feedback.

Oracle integration source SHA-256: `14118dc2912b8236fb4215dd64ebe2108870c51a1963816eaa004f583e9dda8c`.
