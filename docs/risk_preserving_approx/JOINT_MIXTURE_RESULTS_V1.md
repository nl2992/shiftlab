# Joint causal-null mixture of incumbent policies: T=7 result

2026-10-29. **Result:** no improvement in the registered candidate set.
The protocol `JOINT_MIXTURE_PROTOCOL_V1.md` was committed before execution.
The numerical mixture LP used 66 candidates: the never-promote policy and the
65 recovered master policies from the registered 64-cut sequence. It used the
original causal-null sequence form for the *combined* realization plan, rather
than summing component-wise worst-case risks. This maintains private root
randomization and lets the null respond only to the observed history.

The LP returned a two-component mixture: never-promote weight 31/35 and the
iteration-0 candidate weight 4/35. After exact fraction reconstruction, its
alternative cost is `59747/17500 = 3.414114285714...`; exact full causal-null
risk is `1/10`; no extra root repair was needed. This matches the earlier
conservative mixture, and the previously verified rational lower bound yields
an absolute gap below `0.072566086303`. The numerical mixture-LP objective was
3.4141142857142857, inequality violation 1.39e-17, and equality residual zero.
This does not certify optimality within the mixture class: no exact mixture-LP
dual certificate was produced.

The signed certificate is `joint_mixture_t7_v1.json` and its optimizer-free
verifier is `scripts/research_risk_approx/verify_joint_mixture.py`. The verifier
rebuilds the existing lower-bound certificate, each selected component's cost,
the combined exact realization flow, and the full adversarial risk. It shares
model and reconstruction helpers with the generator, and therefore is not an
independently implemented switching model. The auxiliary source-sequence run is
kept at `outputs/risk_preserving_approx/joint_mixture_source_run_v1.json`, whose
hash is recorded in the signed-result metadata; it is not a historical output.

This falsifies a hoped-for improvement from jointly optimizing mixtures on this
single finite candidate set. It does not rule out richer components, a different
constraint-generation path, or structural approximation. Full learner/null
trees and all candidate evaluations were still required; no runtime gain or
novelty follows. The desired candidate and the synthetic and real-data baseline
wins remain unestablished. Continue the original objective by addressing the
pre-promotion bottleneck rather than rerunning the same mixture search.
