# Findings

## B=3 horizon extension (2026-11-11)

- **Result-to-claim verdict: partial.** The completed B=3 extension has certified positive Gamma at T=13–15 for two fixed parameter points, t=2/3 and t=3/4. Corrected rho intervals remain positive and above half the corresponding T=12 baselines.
- The t=2/3 series changes little; the t=3/4 series declines by 15.65% from T=12 to T=15. Finite horizons do not determine whether either series tends to zero or stays positive.
- No uniform-in-T B=3 lower bound or counterexample was established by the bounded proof attempt. Keep the theorem conjectural and the publication decision open.
- The initial rho reporting formula used the lower VOI endpoint for both interval ends. The corrected postprocessor accounts for that uncertainty; impact is below 1e-12 on displayed T=15 lower endpoints.
- **Next:** finish the corrected B=4 T=13 retry; then inspect B=3 primal/dual certificates at T=12 and T=15 and test a bounded multi-position-null relaxation if the certificates expose a tractable structure.
- Review assurance: secondary Codex verdict `partial`, confidence high, same-family/provisional; reviewer model was requested but not reported by the host.
