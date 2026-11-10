# Paper 4 publication decision

**Date:** 2026-11-10. **Branch:** `research/paper4-antitone-frontier-2026-11-09`.

## Primary status: **NO-GO — Prior art** (main-track novelty)

The scheme is prior art (sequence-form oracle / constraint generation). The double-oracle source was read only
for its abstract and introduction (pp. 829–831), so the label is provisional pending a full read. The
conclusion is not expected to flip.

Secondary status: **engineering result retained, attribution open.** Candidate B, re-engineered as FCG-fast,
was 1.3–1.85× faster than the exact reference at T=10, in single runs. The gain is confounded: the reference lacks
FCG-fast's belief cache, and the reference timing varies by 20–38% between runs. It is not established as the
fastest solver.

## Answers to directive §22

1. **New theorem?** None that survives. The risk identity is algebra on Krale et al.'s (NeurIPS 2025) nature-MDP
   best response. FCG correctness (theory/01 §4) is PROVED, but it is a standard cutting-set argument.
2. **Proof status:** the identity is PROVED and numerically verified (276 events, three routes). FCG
   correctness is PROVED.
3. **Closest published results:** Krale et al. 2025, Theorem 3 and Definition 3 (verifier). Sequence-form double
   oracle (Bošanský et al. 2014) and cutting-set robust optimisation (Mutapcic & Boyd 2009) for the cut loop. The
   last two are cited from memory and were not re-read.
4. **Why not equivalent?** No mathematical non-equivalence was found. The only problem-specific element is the
   choice of separation oracle.
5. **Algorithmic mechanism:** IID-first lazy generation of exact causal-null cuts, with a product-state
   best-response oracle and an exact final certificate.
6. **Standard:** all components.
7. **What cannot be removed?** Nothing measured. The cut loop never fired at T=10. Where it fired (T ≤ 8) it was
   slower than the reference.
8. **Original causal-null guarantee?** Yes. Risk is exactly 1/10 on every cell, as rational arithmetic.
9. **Against the unrestricted oracle?** Yes. `U` equals the reference `V_ref` exactly, and `V*` lies in
   `[L, U]` with gap ≤ 4e-14. The reference shares the decomposed-game code, so this equality is partly a
   self-consistency check. The independent evidence is the exact dual `L` and the T ≤ 3 brute force.
10. **Non-vacuous?** Yes, on every cell.
11. **End-to-end compute?** Reduced at T=10 by 1.3–1.85×, but the reduction comes from skipping the null tree
    (the Candidate B route), not from cuts.
12. **Beats strongest source-faithful methods?** Only the in-repo exact reference has been compared. External
    comparators were not run.
13. **Outside development instances?** Not tested. There are no confirmation instances and no holdouts.
14. **Practical meaning:** it gives exact certified switching policies; the regime is synthetic HMMs.
15. **Strongest reviewer objections:**
    1. It is double-oracle / cutting planes with a known evaluator.
    2. The speed-up is engineering of an existing relaxation pipeline.
    3. The cuts are never exercised at scale, and are slower where they are.

## What was discovered

- In every T=10, d=2, B=4 cell tested (3/3), and in every persistent smaller cell, the IID-relaxed optimum is
  already exactly causal-safe. The repo's earlier Candidate B runs show the same (activation 1).
  Cuts were needed only at T ≤ 8 with d=1 under anti-persistent regimes, and there they recover a 0.3–0.5% cost
  improvement over IID-plus-repair.
- Exact certification is cheap. The verifier needs 56–72 states. The cost is the learner tree build with exact
  beliefs. Both methods do this work, but FCG-fast caches beliefs and the reference does not.

## What was disproved / closed

- Value-sensitive pruning: no pruning at the registered tolerances (`../../risk_preserving_approx/PAPER4_VALUE_SHIELD_DECISION_V1.md`).
- The antitone/inversion-frontier verifier as a contribution: it reduces to prior art and has no leverage.
- The repo helper `mix_with_never_promote` is unsafe on stochastic policies. This is a latent hazard. No saved
  result is invalid, because callers re-verify.

## IID-tightness check (done, 2026-11-10): explained, so the lead is closed

`experiments/results/iid_tightness_v1.json`: in all 6 IID-safe cells (C1, C4, C5, S1, S2, S3), the IID LP optimum
is a root mixture of two pure plans with **monotone** promotion events. The existing theorem
`docs/switching_monotone_promotion_reduction_v1.md` therefore explains `R_causal = R_IID`. In the IID-unsafe cells,
one plan (weight 0.4) is non-monotone, as predicted. No new phenomenon remains. The paragraph below is kept for the
record; its question is now answered "explained".

## Precise next research action (superseded by the check above)

The only regularity with possible theoretical content is **IID-tightness**: the IID-relaxed optimum is
causal-safe across these cells. The repo already proves that monotone promotion events have causal risk equal
to IID risk (`docs/switching_monotone_promotion_reduction_v1.md`). The cheap next check is whether the T=10
IID optima are monotone. If they are, tightness is explained by an existing theorem and nothing new remains.
If they are not, characterising when the IID optimum is causal-safe would be a new, falsifiable theorem
target. Do not start that without the user's go-ahead. It is a different research question from the
optimiser.
