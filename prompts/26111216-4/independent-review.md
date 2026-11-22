# Independent adversarial audit: B=6 proof

**Verdict: ACCEPT**, conditional on the stated one-query-per-step, release-before-action-at-delay-one, stationary
symmetric HMM, and causal-null assumptions. No counterexample was found.

The accepted candidate proves `rho_Gamma(T)>=13/118>0.10` for `B=6`, `d=1`, `c=k=0`, `alpha=1/10`,
`r in (1/200,1/100)`, `g in (2/5,1/2)`, every `T>=20`.

The reviewer verified that the even-subset density expansion includes the unique six-spin term with exponent
`(u2-u1)+(u4-u3)+(u6-u5)`. The posterior numerator correctly uses odd subset sizes 1, 3, and 5. For each
subset, the paired-gap exponent plus `n-u_last` is bounded below by the code's `q(J)`, making the geometric tail
conservative for adaptive query gaps. The seven-component mixture has history mass
`2^-m(7-m+2z)/7`; each `nu_j` is causal because the queried-label index is public and other labels are fair.

The reviewer independently reran exact arithmetic and confirmed `D*=19492937149/20000000000`, causal maximum
`41125/13332`, IID maximum `11750/3333`, both at `m=1,y=0`. It accepted whole-rectangle monotonicity, the
Bellman continuation bound, the first-promotion leaf reduction, randomized-seed conditioning, and same-step pending
query accounting. The witness's retained first effects occur by time 18 and yield `zeta/(gr)>=3.49`, giving
`Gamma>=0.39 alpha gr` and the stated relative bound.

The reviewer requested explicit identification of `nu_j`, conditioning on private random seeds, and describing
`q(J)` as a lower bound on actual exponents. Those clarifications are included in the revised proof note.
Review is by a separate same-family agent; it is not formal or external validation. No B>=7, growing-budget,
other-delay, or positive-cost result is established.
