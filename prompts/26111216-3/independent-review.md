# Independent adversarial audit: B=5 proof

**Verdict: ACCEPT** for the stated B=5 model scope after incorporating the requested self-contained details. No counterexample or mathematical flaw was found.

The accepted result is `rho_Gamma(T)>=40/303>0.13` for all `T>=16`, with `B=5`, `d=1`, `c=k=0`, `alpha=1/10`,
`r in (1/200,1/100)`, and `g in (2/5,1/2)`. It covers adaptive deterministic plans and randomized mixtures,
conditional on the established one-query Bellman lemma and the project's release-before-action convention.

The reviewer verified that `D_5` includes all five four-spin terms, and the posterior includes all ten triple terms
and one five-emission/six-spin term. Four-subset minimum exponents for `1234,1235,1245,1345,2345` are
`2,3,2,3,2`; triple-tail minima for `123,124,125,134,135,145,234,235,245,345` are
`4,3,2,4,3,4,3,2,3,2`; the six-spin term has minimum exponent 3. The subset bounds, null-mixture masses, endpoint
constants, monotonicity, and witness prior ratios were accepted.

Exact maxima are causal `60400/23331=2.5888303116<2.59` and IID `30200/9999=3.0203020302<3.03`. The witness
has conditional gain/risk at least `gr[3-(r^4+3r^3)/2]>2.99gr`; retained rewards occur by T=15. Mixing with
never-promote at weight `2 alpha` yields the claimed margin and ratio.

The proof note now states the Bellman induction, first-promotion leaf summation, same-step pending-query accounting,
and witness definition. The review is a fresh adversarial pass by a separate model-family agent; it is not external
or cross-family review. No general-budget, other-delay, positive-cost, novelty, or empirical conclusion follows.
