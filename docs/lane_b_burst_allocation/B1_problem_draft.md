# B1 draft: two-instance separation between oblivious and evidence-responsive label allocation

**Status: lead draft (2026-10-28, tick 2). The argument is sketched; no step is verified.** This is a
target for the numerical check and for a Codex methodology review. It is not a result.

## Setting

- **Stream:** events `t = 1, …, T`, each with a free disagreement indicator `D_t ∈ {0, 1}`.
- **Labels:** on a disagreement, a label reveals `Z_t ∈ [−C, C]`. Agreements have `Z_t = 0`.
- **Budget:** a hard pathwise budget of `B` labels at unit price. Labels arrive with fixed delay
  `d`; take `d = 0` first.
- **Monitor:** any anytime-valid e-process for the charter null `E[Z_t − ε | F_{t−1}] ≤ 0` at
  level `α`, with HT increments under predictable propensities. This is valid for any
  predictable `q` (DISCERN Thm 5; Lemma L context).

## Rule classes

- **Oblivious rule.** `q_t` is a predictable function of `(D_1..D_t, t, remaining budget)` only.
  It never uses the values of labelled `Z`. Fixed, paced, horizon-capped and uniform rules are
  oblivious, and so is DISCERN-style routing on disagreement.
- **Evidence-responsive rule.** `q_t` may also depend on labelled `Z` values from the past.

## Two instances with identical disagreement law

Both instances share the same `D` process: a burst of `L` consecutive disagreements on `[s, s+L)`,
then sparse disagreements at rate `ρ` on `[s+L, T]`. They differ only in the law of `Z` on
disagreements.

- **H (harmful burst).** The onset is at `s`. `Z` has mean `μ > ε` in the burst and afterwards.
- **N (harmless burst).** The burst has `Z` mean `μ_0 < ε` (the null holds there). The onset is at
  `s+L`, and `Z` has mean `μ > ε` afterwards.

Let `K_α ≈ log(1/α) / KL(μ ‖ ε)` be the order of the number of harmful labels any level-`α`
anytime test needs before it can alarm. The precise constant depends on the e-process.

**Budget regime:** `K_α ≤ B < 2K_α` (a "tight" budget), with the sparse phase long enough to supply
`K_α` disagreements: `ρ(T − s − L) ≥ K_α`.

## Claim 1 (oblivious lower bound, sketch)

The `D` law is identical in H and N, so under an oblivious rule the number of labels `b` spent in
the burst has the same distribution in both. If the rule detects in H within the burst with
probability `p`, then `b ≥ ≈K_α` with probability about `p`. In N, those `b` labels are wasted on
harmless data, and only `B − b < K_α` remain for the harmful sparse phase. In N, detection then
fails with probability about `p`.

Hence for every oblivious rule, roughly:

    P_H(detect within burst) + P_N(detect by T) ≤ 1 + o(1).

So in one of the two instances, the rule either misses or incurs delay of order
`K_α / (ρ q)` instead of `K_α / q_burst`.

## Claim 2 (responsive upper bound, sketch)

Consider a rule that samples the burst at full rate and stops spending on the burst once a
constant-confidence sequential test says "mean ≤ ε". Its error `δ` is fixed and does not shrink
with `α`.

- **In N:** it spends `m_δ ≈ log(1/δ) / KL(μ_0 ‖ ε)` labels on the burst, leaving `B − m_δ`. That is at
  least `K_α` when `B ≥ K_α + m_δ`, so it detects in the sparse phase.
- **In H:** it keeps spending with probability at least `1 − δ` and detects within the burst. A wrong
  stop only delays detection; it does not break validity.

**Separation as α → 0.** The responsive rule needs `B ≥ K_α + O(1)` to succeed in both instances.
Every oblivious rule fails one instance whenever `B < 2K_α − o(K_α)`. The gap is of order
`log(1/α)/KL`.

## Honest assessment (before any check)

- **Combination risk for the mechanism is HIGH.** "Sample while the statistic is high, skip while it
  is low" is exactly the DE-CuSum on-off principle (Banerjee–Veeravalli), and Geng–Bayraktar–Lai use
  posterior-driven sampling under a hard cap. A responsive rule that wins Claim 2 is likely an
  e-process / hard-cap adaptation of DE-CuSum, not a new mechanism.
- **What might still be new is the theorem.**
  - A lower bound showing every oblivious (data-value-independent) routing rule pays a
    `Θ(log(1/α)/KL)` budget gap under identical-disagreement-law burst instances. This class includes
    DISCERN-style disagreement gating and paced or horizon budgets.
  - The matching anytime-valid hard-budget upper bound.
  - Geng's Prop. 2 says uniform sampling is first-order optimal under iid pre-change data. The
    separation relies on the non-iid pre-change burst, which is the substantive model difference.
- **Checks needed:**
  - Zhang–Cheung's inventory-reserving lower bound may already imply Claim 1 (tick 2 reading).
  - Claim 1 needs care: `b` can be random and correlated with `D`, but not with `Z` values. With
    `d > 0`, a delay term enters.
- **B3 implication.** A DE-CuSum-style responsive baseline must be in the comparison. If it already
  attains Claim 2, the lane's contribution reduces to the separation theorem plus an analysis of
  that baseline. That would have to be judged as a theory note, not a new algorithm.

## Next steps

1. Numerical check on a Bernoulli instance (exact or Monte Carlo): best oblivious `b` against the
   responsive stop rule against DE-CuSum-style on-off, all with the same e-process and hard cap.
2. Formalise Claim 1 with a change-of-measure argument restricted to `D`-measurable allocation.
3. Codex methodology review of the claims and the combination risk.
