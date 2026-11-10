# Reviewer objections (directive §18; Opus reviewer agent, read-only; verified by the lead on Opus)

Reviewer approval or rejection is not formal verification. Every factual point below was re-checked against
the result JSON or the code.

## Strongest objections (all accepted)

1. **No method novelty.** FCG is constraint generation (sequence-form oracle methods) with Krale et al.'s
   nature-MDP best response as the separation oracle. The proofs are weak duality plus relaxation.
2. **The mechanism is never shown to pay off.** Cuts never fire at T=10. Where they fire (T ≤ 8), FCG is
   slower than the exact reference. The T=10 gain comes from single runs with 20–38% noise, and the baseline
   lacks FCG's belief cache.
3. **Narrow synthetic scope and threat model.** The cells are two-state synthetic HMMs only. There are no holdouts
   and no external comparators. The no-coin-visibility null differs from Krale's coin-seeing nature, and that
   difference must be stated (now done in theory/01, Lemma 2).

## Correctness review

No error. Points checked:
- the dual sign conventions and the residual correction (`x <= 1` follows from flow constraints);
- realization-space repair, which the null may even infer harmlessly, because never-promote has zero risk;
- risk rows keyed by full outcomes;
- tolerance handling.

Minor issues:
- `F(int(v))` truncation in the exact dual assumes integer flow coefficients (true for ±1 flows; undocumented).
- The protocol's alternative stop condition is not implemented.

## Missed framings the reviewer proposed (status)

| Proposal | Status |
|---|---|
| Characterise **IID-tightness** (when the IID optimum is causal-safe) | Done. Fully **explained** by the existing monotone theorem in all 6 safe cells (`results/iid_tightness_v1.json`); lead closed |
| A T=10, d=1 anti-persistent cell, as the decisive test of whether cuts ever matter at scale | Not run. It would need a new registered protocol and user approval to continue |
| Warm-started LPs, to make small adversary support pay off | Not run |
| Use FCG + exact dual as tooling for Papers 1–3 | Recorded in `contribution_statement.md` |
