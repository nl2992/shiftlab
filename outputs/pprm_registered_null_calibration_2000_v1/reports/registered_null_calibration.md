# Registered scenario population-null calibration

This experiment evaluated 2000 independent 6,400-event streams per registered population-null scenario, using a batched implementation of the PPRM block estimator and e-process recursion, block size 20, four queried labels per block, a 20% hard label-dollar budget, reliance cap 0.1, and a fixed 10% CM-EB / 90% positive-betting e-process mixture. The monitor recursion is checked against the scalar production class; the batched Ridge normal equations match the prediction component of DecisionLossProxy. CUDA was requested and resolved to cuda.

| Scenario | Monitor | False escalations / streams | Rate | Wilson 95% interval |
|---|---|---:|---:|---:|
| stationary | fixed_mixture_w0p1 | 0 / 2000 | 0.0000 | [0.0000, 0.0019] |
| stationary | block_cm_eb | 0 / 2000 | 0.0000 | [0.0000, 0.0019] |
| benign_nuisance | fixed_mixture_w0p1 | 0 / 2000 | 0.0000 | [0.0000, 0.0019] |
| benign_nuisance | block_cm_eb | 0 / 2000 | 0.0000 | [0.0000, 0.0019] |

These Monte Carlo rates test implementation behavior for the named synthetic generators. They do not prove the e-process assumptions, establish validity for arbitrary serial dependence or delayed feedback, or generalize to other distributions. Residual-variance shift is excluded: the evaluator marks it as harmful rather than a population null.
