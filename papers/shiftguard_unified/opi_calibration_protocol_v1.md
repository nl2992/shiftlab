# Molitor OPI stationary-bandit calibration protocol v1

**Status:** frozen and executed 2026-10-26.  
**Question:** Does an independent implementation of the paper's bounded DR pseudo-outcomes, LIL confidence sequences, and finite-class elimination rule retain all optimal policies under a stationary logged-bandit null, and how often does it identify a unique best policy by a fixed horizon?  
**Comparator provenance:** Molitor (2026), arXiv:2606.17515v1; LIL confidence sequence from Waudby-Smith et al. (2024), arXiv:2210.10768v3.  
**Implementation:** `src/shiftlab/dive/anytime_policy_identification.py`.  
**Runner:** `scripts/reproduce_molitor_opi_calibration.py`.

## Frozen design

- Two actions, one stationary context-free reward law, known fixed logger `h=(0.5, 0.5)`, three fixed target policies with action-1 probabilities `(0, 0.5, 1)`, Bernoulli rewards, horizon `T=2,000`, and `1,000` independent stream replications per scenario.
- **Null:** both action means are `0.55`, so all three candidates are optimal. Primary error metric is whether any optimal policy is ever removed from the candidate set at any time through `T`; a unique-policy stopping event is also counted as erroneous under this tie scenario.
- **Alternative:** action means `(0.40, 0.70)`, so the policy values are `(0.40, 0.55, 0.70)` and action 1 is the unique best candidate. Record the anytime unique-separation rate, correct singleton rate at `T`, and censored stopping time.
- The learner uses a fixed predictable reward model `rhat=0.5`, shared action propensities, and only its current logged action/reward and known candidate class. True action means and best-policy identity are evaluator-only.
- Use bounded doubly robust lower and mirrored upper pseudo-outcomes with truncation `k=1`. The action-specific propensity ratio is used when integrating the reward-model term. Unsupported candidate actions raise an error.
- **Primary error allocation:** `alpha/(2m)` per one-sided endpoint, where `alpha=0.05` and `m=3`, to control the simultaneous lower and upper bounds by a direct union bound. A paired `alpha/m` per-tail sensitivity is included only to quantify the effect of the allocation used in the inspected author simulation code; it is not a full reproduction of that code or a guarantee-valid comparator configuration under the component one-sided bounds.
- Generate all stream tensors on CUDA when available; run the sequential confidence-sequence calculations in NumPy. Save per-stream and cell summary tables, exact Clopper-Pearson 95% intervals, environment/device metadata, and hashes.

## Interpretation limits

This is a stationary two-action special case, not a contextual, drifting, delayed-feedback, slate, real-data, or downstream-cost study. Monte Carlo calibration does not prove the theorem. It does not repair source-code fidelity or theorem-bookkeeping issues in the pinned reference implementation. The stationarity/overlap assumptions are satisfied by construction. A separate independent verifier must confirm all rows, seeds/replication IDs, confidence intervals, and hashes before reporting results.

