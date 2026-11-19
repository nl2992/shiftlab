# Focused novelty review: Paper 4 uniform premium result

**Date:** 2026-11-12. **Scope:** M6–M10, including the B=3–6 proofs and bounded-budget corollary. **Verdict:** PROCEED, score 6/10. This is an early novelty gate, not an ICML acceptance prediction or a complete correctness audit.

## Proposed contribution

For a symmetric stationary anti-persistent two-state HMM, the reviewed theorem notes establish a positive lower bound on the difference between constrained decision values under the IID-fair null and the full causal-null family. On the explicit open rectangle `r in (1/200,1/100)`, `g in (2/5,1/2)`, with `d=1`, `c=k=0`, and `alpha=1/10`, M10 gives `rho_Gamma >= 0.10` for every `1<=B<=6` and `T>=20`. Query timing may be adaptive.

**Verifiable delta:** replacing IID-fair-null promotion control by control against admissible causal nulls removes at least 10% of the IID-constrained value of information, uniformly over the stated horizon, budget range, and parameter rectangle.

## Closest literature and delta

| Work | Overlap | Difference from M10 |
|---|---|---|
| Fauß, Zoubir & Poor (2020), [Minimax Optimal Sequential Hypothesis Tests for Markov Processes](https://arxiv.org/html/1811.04286v2) | Rectangular conditional-law uncertainty, history-dependent least-favourable laws, Bellman equations, constrained minimax testing. | Does not establish the nominal-versus-causal constrained decision-value gap, its VOI normalization, or uniformity under a hard label budget and adaptive query timing. |
| Koolen & Grünwald (2022), [Log-optimal anytime-valid E-values](https://ir.cwi.nl/pub/33120/33120.pdf) | Dual optimization using mixtures of stopped null laws; closest proof-method ancestor. | The mixture-duality tool is established. The query-position mixture combined with HMM continuation bounds yields a different linear decision-value separation. |
| Clerico et al. (2026), [Time-sensitive anytime-valid testing](https://arxiv.org/html/2605.06521v1); Taga, Oymak & Shekhar (ICML 2026), [Learning to Bet for Horizon-Aware Anytime-Valid Testing](https://proceedings.mlr.press/v306/taga26a.html) | Finite-horizon Bellman control for time-sensitive or horizon-aware testing. | These works optimize rejection behavior under deadlines; they do not compare two constrained policy optima for dependent latent-state decision value under a label budget. |
| Modak et al. (2025), [Sequential Adversarial Hypothesis Testing](https://arxiv.org/html/2511.10181v1) | Adaptive adversaries choosing single-letter laws from convex sets; asymptotic error-exponent regions. | Both hypotheses are worst-case classes there. Here the alternative is a fixed HMM and the target is a finite-budget cumulative decision-value gap. |
| Sethi et al. (ICML 2026), [Asymptotically Optimal Sequential Testing with Markovian Data](https://proceedings.mlr.press/v306/sethi26a.html) | Sequential testing with Markov dependence and non-asymptotic expected-stopping-time lower bounds. | Observed Markov-chain transition testing, not latent-state decision control or an IID-versus-causal calibration premium. |
| Corenflos (2026-11-09), [An iterated-logarithm price of anytime validity for log-optimal e-processes](https://arxiv.org/html/2611.11874v1) | Explicit validity premium, dual null mixtures, and a bounded/unbounded regime. | Simultaneous-horizon log-e-power regret for Gaussian location models; neither contains nor implies the HMM decision-value result. |
| Koning & van Meer (2025), [Anytime Validity is Free: Inducing Sequential Tests](https://arxiv.org/html/2501.03982v4) | Shows planned-horizon tests can be sequentialized without losing terminal-horizon power. | A different comparison: sequentialization versus the original fixed-horizon test, not changing the null family. |

The review also checked Safe Testing (Grünwald et al.), fork-convexity, composite-null optimality, and test/e-process optimality equivalence. No exact prior statement was identified. Search absence is not proof of absence.

## Limitations that must shape the claim

- The proof's null mixture uses query position and forces one queried label to zero; it need not react to observed labels. The theorem supports a cost of requiring causal-null validity. It does not isolate a premium caused specifically by outcome-adaptive adversary reactions. An intermediate null-class comparison would be needed for that stronger mechanism claim.
- The parameter region is narrow and fixes `alpha=0.1`, `d=1`, and zero query and switching costs. The 10% is a fraction of VOI, not total loss or per-round cost.
- B=3–6 are instances of a common certificate, not four independent methodological contributions. A general fixed-B lemma would improve the paper.
- The broader “mixing causes persistence / deterministic chains alone vanish” story is not established by these bounded-budget results.

## Reviewer record

Fresh-context native Codex reviewer, requested model `gpt-6-astra`, effort `xhigh`; the returned model identity was not exposed, so independence is not promoted beyond fresh-context review and remains provisional. The substantive verdict is PROCEED, 6/10. This clears the novelty screen only; main-track sufficiency remains open.

## Next theory target (conjectural, not a result)

Generalize the position-mixture certificate to arbitrary fixed `B`, prove all remainder bounds uniformly over histories, query gaps, and horizons, extend the IID witness, and choose an explicit `r_0(B)` that leaves a positive margin. The reviewer’s algebra suggests a normalized separation of order `1/(B+2)` as `r` tends to zero, but this is an unverified extension and would not establish a common bound on a fixed rectangle for growing `B`.

## Search trail

Queries covered (i) adaptive/null-mixture sequential testing, (ii) horizon-aware anytime-valid testing, (iii) Markov and hidden-Markov testing with observation budgets, and (iv) relative premium/value-of-information formulations. Primary sources were opened for Modak et al. (2025), Clerico et al. (2026), Taga et al. (ICML 2026), Sethi et al. (ICML 2026), Corenflos (2026), and Koning & van Meer (2025). Full exact queries and reviewer transcript are retained in `.aris/traces/novelty-check/2026-11-12_run01/`.
