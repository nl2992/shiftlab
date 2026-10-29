# Conservative incumbent mixture: T=7 result

2026-10-29. **Result:** no improvement. The registered protocol is
`MIXTURE_INCUMBENT_PROTOCOL_V1.md`. The diagnostic regenerated 65 candidate
policies over 64 null cuts and optimized the conservative root-mixture risk bound
`sum_i w_i R_i` exactly over singleton and pairwise choices. This includes the
previous candidate-plus-never-promote repair, so it cannot be worse on the same
candidate set.

It selected the iteration-0 candidate with weight 4/35 and the never-promote
policy with weight 31/35: exactly the previous safe upper `59747/17500 =
3.414114285714...`. The actual worst-case causal-null risk, evaluated on the
mixed realization-flow policy without revealing the private root coin, is 1/10;
the conservative bound is also 1/10. The existing independently verified lower
bound yields a rigorous gap of approximately 0.072566086302. Both generation and
optimizer-free verification passed. The full signed artifact is
`mixture_incumbent_t7_v1.json`, and the verifier is
`scripts/research_risk_approx/verify_mixture_incumbent.py`. The verifier shares the
underlying economic model and certificate helpers with the generator.

This experiment does not show that all private mixtures are unhelpful: replacing
risk of a mixture by the mixture of component worst-case risks can be conservative,
because one null strategy need not maximize every component's risk. It gives no
speedup or novelty, does not beat the exact oracle, and does not address real data.
The next question is whether the exact combined-policy causal-null response,
rather than this separable upper bound, yields a better safe mixture from the same
candidate set. That must retain hidden root randomization and verify exact risk.
