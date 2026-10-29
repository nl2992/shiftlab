# Gafni et al. change-count regret: full theorem audit

**Checked:** 2026-10-29 against the official ICML 2026 proceedings PDF. This is a source-scope
audit, not an independent reproof or a claim that ATC solves delayed budgeted model switching.

## Model and results verified

Gafni, Iyengar and Zeevi, [*The Cost of Learning Under Multiple Change Points*](https://proceedings.mlr.press/v306/gafni26a.html), ICML 2026, PMLR 306, pp. 32542–32580. The complete official PDF was downloaded and extracted; provenance and SHA256 are in `switching_source_manifest_v34.json`.

The model is scalar, independent observations that are IID within each of at most `S+1` segments, with unknown piecewise-constant means, known sub-Gaussian proxy `sigma^2`, and mean diameter at most `M`. The learner observes each `X_t` immediately and predicts the current mean using the past. Regret is expected cumulative squared tracking error from `t=2` through `T`. No labels are selectively purchased; the learner does not choose a deployment action.

ATC uses an anytime GLR/CUSUM-style split statistic and restarts its running-mean estimator when the statistic crosses a time-varying threshold. Theorem 4.1 states

`R_ATC <= C_V sigma^2 (S+1+alpha)(1+log T) + C_B sigma^2 S log(T/alpha) + C_M M^2(alpha+S)`.

Theorem 4.2, under `M >= c_0 sigma`, gives

`R*_T >= c sigma^2 (S+1) [1 + log(floor(T/(S+1))+1)]`.

Thus ATC is near-minimax for this *fully observed squared-mean-tracking* problem. Both theorem statements and assumptions were checked in the official proceedings version, rather than relying on the earlier arXiv proof sketch.

## Proof route checked in the appendix

- Appendix A.3 decomposes tracking error into a variance term and a post-change bias term (Lemma A.1). For each deterministic restart index, Lemma A.2 gives a uniform deviation event over split points and times. The proof handles random restart times by upper-bounding their indicators with a sum over deterministic restart indices; it does not condition the confidence bound on the selected restart.
- The bias bound in Lemma A.3 charges rare deviation events by `O(M^2 alpha)` and each change's undetected interval by `O(M^2 + sigma^2 log(T/alpha))`. A missed change is not simply assumed away: Proposition 3.1 bounds the loss in effective SNR for detecting a later change by the population evidence of the earlier missed change. Appendix A.6 proves the algebraic Claim A.12 by completing the square, then invokes the fixed-restart confidence event.
- Lemma A.4 bounds expected false alarms by `sum_r alpha_r <= alpha`, giving `E[K] <= S+1+alpha`. Lemma A.5 sums within-block running-mean variances as a harmonic series. Combining Lemmas A.3 and A.5 yields Theorem 4.1.
- Appendix A.5 proves the lower bound by two relaxations. Lemma A.9 gives a detection-delay lower bound even when segment means are revealed; Lemma A.10 gives an estimation-variance lower bound even when change points are revealed. The proof takes the larger of these bounds. Remark A.11 explicitly says this establishes at least the larger mechanism; although an additive construction is possible, it has the same asymptotic rate and is omitted. Do not paraphrase this as an additive lower-bound decomposition on one common hard instance.

This review follows the published proof structure and checks the key inequalities/relaxations at source level. It is not a line-by-line independent verification of every constant or auxiliary lemma.

## Boundary for budgeted delayed switching

The result closes novelty based on generic multiple-change mean tracking, selective restart, or an `S log T` dynamic tracking rate under full observations. Its anytime false-alarm allocation is for ATC restarts, not for a model-promotion event under ShiftLab's separate history-adaptive conditional null. The theorem has no query budget, pending queue, label delay, query fees, model action, deployment switch cost, promotion/rollback decision, or paired-loss regret comparator.

Running ATC on labels from a fixed query calendar is a plausible **baseline adapter**, not an automatic theorem transfer. Sparse samples change segment geometry in query-index time; fixed delay adds calendar-time staleness; predictions are charged every calendar event; and a tracking estimate does not itself provide a causal-null promotion certificate. A valid adapter bound must quantify all of these effects and then be paired with a separate valid switch-risk rule. This is a derivation/comparator task, not a candidate novelty claim.

G1 remains open only for a result about the interaction of selective delayed observations, the conditional-null any-promotion constraint, and reversible economic switching that is not supplied by combining ATC with standard safe testing or constrained planning. G2–G5 remain held.
