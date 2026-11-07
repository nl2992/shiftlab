Reviewer-Model: gpt-5

Overall, the evidence supports a conservative `SOTA_NOT_MET` verdict and makes P1/P2 reasonable development candidates, but does not support the intended claims at their full breadth.

## C1 — RMM transfer

1. `claim_supported`: **partial**

2. `what_results_support`:

- On fresh synthetic seeds, RMM reduces cost relative to the attached host by:

  - gated deployment: `−44.2`
  - corrected DISCERN: `−47.3`
  - SMCS: `−13.3`

- Against Xu on the two late-improvement regimes, all three evaluated certificate hosts improve by roughly `15–27` cost units per episode.
- IID-null first-promotion safety holds for these three hosts.
- Ablations are consistent with contributions from both the restart mixture (`−2.4` to `−5.5`) and continued acquisition (`−8` to `−11`).

Sources: [transfer results](</Users/nigelli/Desktop/ICML/Shift-lab/.claude/worktrees/dazzling-wilbur-a3e951/docs/sota_sprint/validation/transfer_results.md>), [RMM host results](</Users/nigelli/Desktop/ICML/Shift-lab/.claude/worktrees/dazzling-wilbur-a3e951/docs/sota_sprint/validation/rmm_certified_hosts.txt>).

3. `what_results_dont_support`:

- The registered five-host transfer test failed: only `3/5` hosts passed. The claim’s restriction to the three certificate hosts was made post hoc.
- RMM fails under persistent Markov nulls: promotion is about `.15` at `rho=.8` and `.66–.70` at `rho=.95`.
- It loses substantially on reversal and recurrent regimes.
- Fresh real streams contain no genuine late-improvement episodes, so real-world late-improvement transfer is untested.
- Ablations support attribution descriptively, not a definitive causal decomposition.

4. `missing_evidence`:

- A preregistered transfer test restricted to certificate hosts, ideally with an additional certificate family.
- Real streams containing genuine within-stream improvements.
- A certified treatment of rollback/reversal cost.
- A formal joint-error analysis for promotion followed by RMM rollback.

5. `suggested_claim_revision`:

> On fresh synthetic seeds, RMM substantially lowers cost when attached to three tested certified deployment hosts and improves late-improvement cost relative to Xu, while preserving IID-null first-promotion control. These gains are specific to the tested certificate hosts and late-improvement regimes; transfer to arbitrary hosts, robustness to persistent dependence, reversal performance, and real-data late-improvement behavior remain unestablished.

6. `next_experiments_needed`:

- Register the narrower three-host claim before rerunning it.
- Add a fourth certified host.
- Include reversal, recurrence, and persistent-null safety as primary endpoints.
- Construct or identify real streams with known late challenger improvement.

7. `confidence`: **high**

## C2 — Persistence validity/power trade-off

1. `claim_supported`: **partial**

2. `what_results_support`:

- Powered certified ports generally exceed the `.0936` bound on at least one persistent-null condition in the tested `rho=.8–.95` range. Examples include Xu (`.117`, `.239`), SMCS (`.097`, `.350`), and several strengthened ports with much larger rates.
- A5b stays below the registered bound across the tested in-class null grid through `rho=.95`; its Wilson upper bounds are also below the threshold. It passes the two descriptive out-of-class nulls (`.048`, `.018`).
- Its stationary cost is close to the unsafe certified frontier; the largest reported disadvantage is `+7.4`.
- On fresh real streams, A5b is substantially worse than the best certified comparator, by approximately `+61` to `+257`. Improvement counts are mostly zero, although not literally zero on every dataset.
- Estimated real persistence ranges from roughly `.4` to `.98`.

Source: [validation results](</Users/nigelli/Desktop/ICML/Shift-lab/.claude/worktrees/dazzling-wilbur-a3e951/docs/sota_sprint/validation/validation_results.md>), [real results](</Users/nigelli/Desktop/ICML/Shift-lab/.claude/worktrees/dazzling-wilbur-a3e951/docs/sota_sprint/validation/real_results.md>), [persistence estimates](</Users/nigelli/Desktop/ICML/Shift-lab/.claude/worktrees/dazzling-wilbur-a3e951/docs/sota_sprint/validation/real_persistence.json>).

3. `what_results_dont_support`:

- The evidence does not establish validity for unknown persistence in general; it covers a finite Markov family and selected rho values.
- “Every powered port exceeds the bound” is only supportable as “each tested powered port fails somewhere in the persistent-null grid,” not “each exceeds it at every rho.”
- A5b’s out-of-class result is descriptive, not part of the registered guarantee.
- The real-data results measure cost/power, not real-data false-promotion validity, because no known-null real streams were available.
- The registered non-inferiority condition failed: only `1/5` iid stationary alternatives passed, and the broader H0/H2 superiority tests failed.

4. `missing_evidence`:

- A formal lower-bound or impossibility argument for unknown persistence.
- More persistence models, including non-Markov and heterogeneous dependence.
- Real streams with known null truth, such as equally accurate retrained models.
- Author-code implementations or independently validated comparator implementations.
- A pre-registered real-data power comparison with non-optimistic episode dependence handling.

5. `suggested_claim_revision`:

> In the tested stationary Markov marginal-null family, most powered certified ports violate the registered false-promotion bound somewhere between `rho=.8` and `.95`, whereas A5b remains below the bound on the tested grid and two descriptive out-of-class nulls. This robustness is purchased with a substantial loss of power/cost performance on the tested real streams. The results demonstrate an empirical validity–power trade-off, not a general theorem about unknown persistence.

6. `next_experiments_needed`:

- Prove or formally characterize the claimed trade-off.
- Add broader dependence classes and persistence mixtures.
- Run known-null real-stream experiments.
- Recompute real-data uncertainty using non-overlapping or block-aware episodes.
- Compare against author implementations where available.

7. `confidence`: **high**

## C3 — Verdicts and publication positioning

1. `claim_supported`: **partial**

2. `what_results_support`:

- `SOTA_NOT_MET` is well supported: H0, H2, HR, and HD failed, and no candidate met the full success gate.
- P1 and P2 have credible, distinct empirical stories and are reasonably described as candidates for further paper development, with P2 appropriately prioritized.
- The register explicitly records the principal evidence gaps.

Source: [execution report](</Users/nigelli/Desktop/ICML/Shift-lab/.claude/worktrees/dazzling-wilbur-a3e951/docs/sota_sprint/REPORT.md>) and [publication register](</Users/nigelli/Desktop/ICML/Shift-lab/.claude/worktrees/dazzling-wilbur-a3e951/docs/sota_sprint/publication_register.md>).

3. `what_results_dont_support`:

- “P3–P6 are not supported” is too categorical. P5 is explicitly not supported, but P3, P4, and P6 are classified as needing evidence rather than definitively rejected.
- “Main-track candidates” is a publication judgment, not an experimentally established result.
- P2 still lacks the formal lower-bound argument needed for its strongest interpretation.
- P1’s strongest transfer claim remains post-hoc scoped and synthetic-only.

4. `missing_evidence`:

- The formal and real-data evidence gaps listed for P1/P2.
- Clearer separation between “not supported,” “needs evidence,” and “negative result.”
- Independent author-code comparator validation.
- A formal review of the amended/post-hoc claims.

5. `suggested_claim_revision`:

> The sprint verdict is `SOTA_NOT_MET`. P2 is the strongest empirical paper candidate, and P1 is a promising but currently synthetic, narrowly scoped method candidate. P3 and P4/P6 should be described as unsupported as standalone contributions pending additional evidence; P5 is not supported as a standalone contribution.

6. `next_experiments_needed`:

- Prioritize P2’s formal persistence argument and known-null real validation.
- Then rerun P1 with preregistered host scope, genuine late improvements, and reversal safety.
- Keep P3–P6 as benchmark findings, limitations, or negative results unless their specific evidence gaps are resolved.

7. `confidence`: **high**

The 12 cited numerical prechecks are present and consistent with the result files, but that verifies transcription, not the broader scientific claims.