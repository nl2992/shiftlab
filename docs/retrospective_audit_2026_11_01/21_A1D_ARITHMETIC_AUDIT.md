# A1d bound arithmetic audit — 2026-11-01

Command: `python -B scripts/retrospective_audit/recompute_a1d.py` — exit 0.

All 279 stored rational calendar curves have unique risk-grid points, nonincreasing costs, and nondecreasing secant slopes. Existing mixture_bounds.py reproduces all 24 stored C_mix upper values exactly. For prior 1/10, alpha 1/4, the lower and upper relative gaps both equal 0.050655732256628005. For prior 1/5, alpha 1/2, the interval is [0.04681696274945033, 0.0472549764249934]. The historical rounded lower claims 5.07% and 4.68% agree.

These are reproductions of stored-grid arithmetic using the existing bounding implementation. They are not independent LP reruns, a proof that every continuous curve is convex, or an independent audit of the lower-bound derivation. The grid tests alone cannot prove convexity between sampled risk points. J values were taken from the historical summary rather than solved anew. All these limitations remain required W08 work; G08 is unsigned. Exact rational intermediate values are in A1D_BOUND_RECOMPUTATION.json. No historic protocol, bound, verdict or output was edited.
