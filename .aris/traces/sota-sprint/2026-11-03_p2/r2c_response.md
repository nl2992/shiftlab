Reviewer-Model: gpt-5

1. `claim_supported`: **partial**

2. `what_results_support`

- Synthetic results support the scoped statement: all 9 powered certified ports exceed the `.0936` bound at one of the tested persistent Markov nulls (`rho=.8/.9/.95`), while A5b remains below the bound, including its reported upper limits.
- The registered twin experiment supports the real-stream failure pattern. K1 passes **9/9**: each powered certified port has at least one dataset with point promotion above `.0936` and clustered-bootstrap lower bound above `.05`.
- Maximum powered-port promotion is about `.428`, consistent with “up to .43.”
- RMM promotion is high on several persistent datasets, reaching approximately `.14–.62`; the raw records and NPZ hashes agree with the reported artifacts.
- A5b’s real point estimates are indeed `.000–.058`. Most excess promotions are not harmful under the registered episode-realised-advantage definition: harmful-promotion rates for powered ports are generally ≤ `.07`, and average decision-cost differences are small relative to the promotion-rate failures.
- The protocol was registered before twin construction, and K0’s split-level advantage intervals contain zero for all five datasets.

3. `what_results_dont_support`

- A5b does **not** fully “remain below the bound” on real streams in the certified sense: K2 fails because its clustered-bootstrap upper bound reaches about `.100` on `bike_hour`, above `.0936`.
- “RMM reaches `.14–.62`” needs qualification: RMM is near zero on metro; `.14–.62` describes its elevated results on the other persistent datasets, not its full observed range.
- The real-power claim is too broad. The fresh real challenger is empirically better in most episodes overall (`56/62`), but A5b promotion is not uniformly weak: it promotes at rates around `1.0` on bike_hour and `.938` on metro, while being weak on appliances, Beijing, and household power. Thus the result shows substantial power loss on some streams, not generally across all real streams.
- The twin null is exchangeable over the split/role randomisation, not a conditional null for every fixed split. Per-split realised advantages are nonzero, so “known null” should remain explicitly marginal.
- These are common-contract ports, not necessarily faithful implementations of every published method, and the consecutive episodes provide limited independent real-stream replication. The results demonstrate empirical failure under these tested conditions, not universal invalidity of the methods.

4. `missing_evidence`

- A pre-specified, per-dataset power analysis with uncertainty intervals for A5b under genuinely better challengers.
- More independent real streams or independent resampling units beyond 20 split randomisations on five datasets.
- A formal analysis connecting the exchangeable-twin marginal null to the exact promotion estimand and clustered inference.
- Sensitivity analyses for episode length, delay, split construction, twin training imbalance, and persistence-estimation method.
- A direct RMM comparison under the same real known-null protocol with a clearly defined full-range summary.

5. `suggested_claim_revision`

> In the tested synthetic stationary Markov marginal-null family, all 9 powered certified ports exceeded the registered `.0936` false-promotion bound at one or more tested persistence levels between `.8` and `.95`, whereas A5b remained below it in those simulations. In five exchangeable-twin real-stream experiments, every powered certified port exceeded `.0936` on at least one persistent dataset, with rates up to `.43`; RMM variants also showed elevated promotion on several datasets, up to `.62. A5b had lower point estimates (`0–.058`), but its clustered-bootstrap upper bound exceeded `.0936` on the smallest dataset. Most promotions were toward the twin with lower realised episode loss, so the marginal-validity failures generally had small realised decision-cost impact. Separate fresh-real experiments show substantial A5b power/cost loss on some, but not all, streams with empirically better challengers. Together, these results provide scoped empirical evidence of a validity–power trade-off for certified deployment under serial dependence; they do not establish a theorem or universal method ranking.

6. `next_experiments_needed`

- Replicate the twin-null experiment on more independently sourced persistent datasets, with a larger number of independent split units.
- Pre-register a power study using exchangeable or randomized genuinely-better challengers, reporting promotion probability and confidence intervals per dataset.
- Re-run A5b and RMM across episode lengths and delays, including block/bootstrap sensitivity.
- Analyze whether a dependence-robust certificate can retain A5b-like null control without its observed power loss.
- Preserve the distinction between marginal validity, conditional validity, and decision harm in all follow-up claims.

7. `confidence`: **medium**

The registered protocol, raw records, NPZ content hashes, and analysis code are internally consistent. Confidence is limited by the small number of independent real datasets/splits, clustered consecutive windows, port implementations, K2’s narrow failure, and the over-broad wording of the power and RMM-range portions.

The required ChatGPT planning connection could not be completed because the local bridge remained unavailable with an `EPERM` log-access error; this review was therefore completed from the repository artifacts and read-only checks.