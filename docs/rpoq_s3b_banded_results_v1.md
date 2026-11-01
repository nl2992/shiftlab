# RPOQ S3b: lattice-artifact and banded-structure test, results

**Branch:** `research/rpoq-s1-fatal-flaw-audit`. **Date:** 2026-10-29. **Protocol:** [`rpoq_s3b_banded_protocol_v1.md`](rpoq_s3b_banded_protocol_v1.md). **Status:** exploratory, synthetic, no claim.

Instance as registered (four contrast levels, `T=8`, `d=2`, `alpha=0.2`). No parameter was changed after the first output (calibration at `B=4`: power 0.0604, inside the (0.05, 0.95) range). The multi-level extension of the solver reproduces S3's binary result exactly (B=3 power 0.0330) and its tests pass.

| B | Power: optimal | Best constant | Gap | Neyman/ASI | Always q=1 | Null alarm (opt / worst constant) | Monotone | Banded (≤2 changes) | Groups |
|---|---|---|---|---|---|---|---|---|---|
| 3 | 0.0029 | 0.0005 | +0.0023 | 0.0005 | 0.0000 | 0.0005 / 0.0001 | 0.759 | 0.772 | 228 |
| 4 | 0.0604 | 0.0461 | +0.0143 | 0.0225 | 0.0410 | 0.0052 / 0.0039 | 0.630 | 0.608 | 316 |
| 5 | 0.2056 | 0.1804 | +0.0252 | 0.1147 | 0.1722 | 0.0179 / 0.0176 | 0.637 | 0.661 | 386 |

## Registered verdict

- **C0 (validity): pass** at every budget (largest null alarm 0.0179 against `alpha = 0.2`).
- **C1c (monotone ≥ 0.90): fail** at every budget (0.63 to 0.76). **H-lattice is not supported:** a four-level contrast did not remove the non-monotone structure.
- **C1b (banded, ≤ 2 changes, ≥ 0.90): fail** at every budget (0.61 to 0.77). **H-band is not supported.**
- C2 (gap ≥ 0.02): met only at `B=5` (+0.0252).

Per the decision table, both structure tests failing means **no compact structure on either instance: close the adaptive-policy branch.** The adaptive optimum is a lookup over fine-grained wealth and buffer states with no short description in these instances.

## What survives (descriptive)

- The exact optimum beats the best fixed table by a small, consistent margin (+0.002 to +0.03 absolute power) and beats the Neyman/ASI table by more (for example 0.2056 against 0.1147 at B=5). That is an *oracle* comparison (alternative law known to the optimiser), so it is an upper reference and not an implementable gain.
- In both instances the Neyman/ASI allocation shape was worse than the best constant table. In these toy instances power is driven by wealth growth under a betting bound, not by estimator variance alone. Whether that carries to real data is addressed separately (S6).

## Consequence

Two registered structure tests have failed. Per the plan's kill criteria, the adaptive-policy (RPOQ) branch ends here. The real-data work (S6, S6b) therefore evaluates **allocation baselines and one validation-selected variant**, not an RPOQ policy.
