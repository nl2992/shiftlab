# Prior-art equivalence audit: initial source-level boundary

2026-10-29. This is a focused initial audit, not a complete novelty determination.
Original repo source audits remain unchanged. Read primary passages listed below;
absence of an identical statement does not prove a result novel.

| Source and inspected scope | Shared structure | Difference / remaining reduction | Status |
| --- | --- | --- | --- |
| [Kara and Yüksel, JMLR 2022](https://jmlr.org/papers/volume23/20-1152/20-1152.pdf), Theorems 16–17 and surrounding assumptions | Finite-memory approximation and explicit near-optimality bounds for known-model POMDPs | Discounted single-model objective and filter stability do not directly bound a separate causal-null worst-case event. Need prove whether an augmented hidden-root game plus constraint recovery transfers the claimed joint error/rate. | UNRESOLVED — EXACT REDUCTION REQUIRED |
| [Cubuktepe et al., AAAI 2021](https://cdn.aaai.org/ojs/17401/17401-13-20895-1-2-20210518.pdf), model and Algorithm 1 verification discussion | Uncertain partially observed model, finite-state controller and robust verification; paper explicitly uses exact verification to check the synthesized specification | An exact history-augmented safety model exists; the two-law objective can be encoded with mode/cost augmentation, but a uniform bound against the unrestricted oracle and improved compact scaling are not established by this comparison. Need model-match and complexity reduction. | UNRESOLVED — EXACT REDUCTION REQUIRED |
| [Horák et al., one-sided POSGs](https://arxiv.org/abs/2010.11243), as mapped in `switching_lagrangian_posg_reduction_v1.md` | Hidden-root scalarization maps the finite game to established strategy composition and value recursion | Shared policy, asymmetric information and two-law objective alone do not establish a new method; recovery of a constrained optimizer and scalable compression require additional work. The current checkpoint checked the source identity and existing reduction, not the full proof independently. | Generic scalarized representation: established equivalence in repository; compact approximation: unresolved |
| Khonji, Jasour and Williams, IJCAI 2019, as audited in `switching_ccpomdp_approximation_audit_v1.md` | Finite-horizon chance constraint and approximation | Existing source audit describes a fixed-law, constant-horizon result. A causal-null family can be expanded into multiple fixed null constraints but may be exponential; a one-constraint FPTAS cannot simply be invoked. Recheck the primary proof before claiming a separation. | UNRESOLVED — EXACT REDUCTION REQUIRED |

The safety-repair lemma in `PROBLEM_AND_THEOREM_TARGET.md` is elementary mixture
algebra, not a methodological novelty claim. It is useful only if a separate
construction supplies a uniformly valid small risk excess, a value bound against
V*, and favorable end-to-end complexity. The posterior-alias counterexample
rejects the posterior-only representation, not all compact controllers.

A candidate-specific audit must fill in shared/different assumptions, necessity
of each difference, proof adaptation and the missing lemma; only then decide
proved equivalent, proved distinct, unresolved or falsified. Candidate A has not
yet provided that theorem or representation.
