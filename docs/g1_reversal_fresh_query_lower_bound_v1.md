# G1 two-world lower bound: fresh queries after reversal

**Date:** 2026-10-30. **Status:** proved elementary information bound; novelty is not established
and this is not a method contribution.

## Contract

Consider two environments and an already deployed challenger. Before a known time `tau`, both
environments generate the same observable history and the same queried-label law. In world `P0`
there is no reversal. In world `P1`, at `tau` the label law changes. Each queried post-`tau` label is
conditionally independent with law

```text
P0: Bernoulli(1/2 + eps)
P1: Bernoulli(1/2 - eps),   0 < eps < 1/2.
```

The challenger is beneficial in `P0` and harmful in `P1`; the learner may make predictable,
history-dependent query decisions and must obey a pathwise total request cap. Interpret a label
`Y` as a binary reward comparison with challenger-minus-reference increment `2Y-1`, so the mean
increment is `+2 eps` in `P0` and `-2 eps` after reversal in `P1`. Each requested label is released
exactly `d >= 1` rounds after request. A rollback decision is measurable with respect to the
learner's released-label transcript. Let `R_m` be the event that rollback has occurred by
`tau+m`. Suppose the procedure is required to satisfy both

```text
P0(R_m) <= gamma        (false rollback control in a persistent good world)
P1(R_m^c) <= beta       (rollback by the deadline after reversal).
```

Assume `beta + gamma < 1`.

## Proposition

Let `K_m` be the maximum number of post-reversal queried labels that can be released by
`tau+m`. For any such procedure,

```text
K_m * kl(1/2 + eps || 1/2 - eps) >= 2(1 - beta - gamma)^2,
```

where `kl` is Bernoulli Kullback–Leibler divergence. Since at most one request can be made per
round and labels have fixed delay `d`,

```text
K_m <= max(0, m - d + 1).
```

Consequently, a necessary latency condition is

```text
m >= d - 1 + 2(1 - beta - gamma)^2 / kl(1/2 + eps || 1/2 - eps).
```

For a pathwise budget with `B_rem` unreserved requests remaining at `tau` (after subtracting pending
reservations), a necessary feasibility condition
for the requested rollback error levels at any time is

```text
B_rem * kl(1/2 + eps || 1/2 - eps) >= 2(1 - beta - gamma)^2.
```

As `eps -> 0`, `kl(1/2+eps || 1/2-eps) = 8 eps^2 + O(eps^4)`, so the required fresh-label count
scales at least as `(1-beta-gamma)^2/(4 eps^2)`.

## Proof

Let `H_m` be the full learner-observable transcript through `tau+m`, including predictable query
choices, released labels, and any internal randomized decisions. Before `tau`, the two laws agree,
so the pre-reversal transcript contributes zero relative entropy. Conditional query randomization
is the same algorithmic kernel under both environments and contributes no relative entropy. By the
chain rule for relative entropy, each post-reversal queried label contributes at most
`kl(1/2+eps || 1/2-eps)`, while unqueried or not-yet-released labels contribute zero to the
observable transcript. Therefore

```text
KL(P0(H_m) || P1(H_m)) <= K_m * kl(1/2+eps || 1/2-eps).
```

The event `R_m` is a test between the transcript laws. Its assumed error bounds imply
`P1(R_m)-P0(R_m) >= 1-beta-gamma`, hence their total variation distance is at least
`1-beta-gamma`. Pinsker's inequality gives
`KL(P0(H_m)||P1(H_m)) >= 2(1-beta-gamma)^2`. Combining the inequalities proves the first claim.
At time `tau+m`, at most the requests from rounds `tau` through `tau+m-d` have been released, so
the number is at most `max(0,m-d+1)`; the hard budget also bounds it by `B_rem`. This proves the
latency and budget corollaries.

The result formalizes one important separation: labels and promotion evidence collected before
`tau` cannot distinguish `P0` from `P1`; post-reversal current-value safety needs fresh released
information or an explicitly stated non-statistical fallback. It does not say a likelihood-ratio
confidence set under a correctly specified recurrent HMM is invalid: if the model includes the
latent reversal and new observations update its filter, that is a different, model-conditional
guarantee.

## Novelty audit and decision

This is an elementary adaptive two-point testing lower bound (KL chain rule plus Pinsker), not yet
a new theorem for the paper. Active quickest change detection already jointly studies sampling
control, false-alarm constraints, and detection delay; some work also includes observation
switching costs. Gafni, Iyengar, and Zeevi give an information-theoretic lower bound and a
near-minimax algorithm for multiple-change-point regret. The present proposition specializes
standard testing tools to finite fresh-label budgets and fixed release delay; it does not establish
a strict separation from those methods or solve repeated switching with a valid economic objective.
See [active quickest detection with sampling control](https://doi.org/10.1080/07474946.2023.2187417),
[quickest detection with observation-switching cost](https://doi.org/10.1109/TSP.2021.3057258), and
[Gafni et al., ICML 2026](https://proceedings.mlr.press/v306/gafni26a.html).

**Decision:** retain this as a lower-bound sanity check and as a guard against treating stale
pre-reversal evidence as current evidence. Do not claim novelty or implement a detector from this
proposition alone. A live method would need to attain a sharp repeated-reversal budget/regret frontier
under the controlled-HMM information contract and outperform/source-separate from the named
change-detection methods plus the repository's exact small game. This proposition is a testing
latency/budget constraint; it does not itself lower-bound net economic regret or incorporate the
size of the switching fee.
