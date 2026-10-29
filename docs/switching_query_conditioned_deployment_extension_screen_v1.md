# G1 screen: query-conditioned deployment after action-dependent acquisition

**Date:** 2026-10-29. **Status:** local separation established; algorithmic novelty not established.

## Scope correction to the earlier transport screen

The no-go in `switching_transport_acquisition_candidate_v1.md` compares channels under the restriction that the next deployment probability is a single `p` in every query stratum. Its averaging argument does not establish domination when the deployed action may depend on the selected query. The note itself flags this as an unresolved case; the derivation below makes the difference explicit.

## Local separation

At a decision state, let the currently installed action be `O ~ Bernoulli(1/2)`. The learner must request one of two eligible paired labels `J in {0,1}`; query fee and feedback timing are identical in all choices. Before seeing the queried label, the learner chooses its next deployed action `A`. Suppose the predictable continuation reward is `v(J,A)=1{J=A}`, and the switch fee is `k in (0,1)`.

An action-conditioned joint rule sets `J=O` and `A=J`. It obtains reward one and incurs no switch, hence net value `1`. Any rule that requires `J` to be independent of `O` has `P(J != O)=1/2`. If it sets `A=J` with probability `x` and otherwise retains `O`, its expected reward is `1/2+x/2`, expected switch fee is `kx/2`, and net value is `1/2+x(1-k)/2`. For `k in (0,1)`, the best such choice is `x=1`, with value `1-k/2`. Thus the strict local gap is `k/2`.

This is an exact one-step witness that the fixed-stratum target `p` restriction can discard action/query coupling value. It does **not** show a gain from acquired labels: the label is ignored, and the continuation score is supplied. It proves no cumulative regret, delayed-feedback, risk-control or reversal-monitoring guarantee. It is a diagnostic to prevent overextending the previous no-go, not a candidate paper result.

The general one-step decision can be written as a finite linear program over joint masses `x[o,j,a] >= 0`, with `sum_{j,a} x[o,j,a]=P(O=o)`. Expected switch cost and any predictable continuation value linear in `(o,j,a)` are linear objectives; per-action/query floors are linear constraints. This is simply randomized controlled sensing/action selection with the previous action included in state.

## Primary-source boundary

Atan and van der Schaar, *Data-Driven Online Decision Making with Costly Information Acquisition* ([primary arXiv source](https://arxiv.org/abs/1602.03600)), already formulate simultaneous/sequential costly information acquisition followed by action selection and prove sublinear regret. Reyzin, Saha and Wu, *Expert Advice with Costly Observations* ([UAI 2026 primary source](https://proceedings.mlr.press/v337/reyzin26a.html)), already study adaptive observation subsets and observation costs in online expert learning. The source audits in `switching_cams_comparator_contract_v1.md` and `switching_two_law_game_duality_v1.md` add delayed request reservation, economic switching charges, and the full-history causal-null any-promotion constraint to the comparison contract, while also showing that the finite combined problem is an extensive-form game.

Atan and van der Schaar's primary formulation is particularly relevant: the learner chooses an observation set and then selects an action as a function of the observed state, optimizing their joint expected reward minus observation cost; their online policy operates on the resulting two-stage MDP (Sections 3.1–3.2). Add the incumbent action to the state and include its transition charge, and the local joint choice above is a standard state-augmented control decision. The strict gap is only against the artificially factorized comparator that forbids this joint control; it is not a gap against the relevant prior class or the repository's unrestricted finite extensive-form oracle.

These sources do not, in the inspected formulations, give the exact local action/query coupling witness above together with ShiftLab's delayed, pathwise-budgeted, repeated-switching and causal-null contract. However, state augmentation and joint-kernel optimization are standard, and this one-step separation supplies no efficient sequential algorithm or guarantee beyond the full-history game. Therefore this does **not** pass G1 and should be closed as a contribution candidate. Reopen only if a sequential method exploits some additional structure and proves a growing-horizon advantage over joint observation/action control, delayed CAMS/Online LLM Picker adaptations, and the exact game on small horizons.

No efficacy experiment follows until a precise sequential rule and a theorem-level gap from these source-matched methods are derived. The theorem must separately account for query-result likelihood, delayed release, the pathwise request cap, switching charge, and worst-case any-promotion risk. A promotion-risk guarantee remains distinct from current challenger value after a regime reversal.
