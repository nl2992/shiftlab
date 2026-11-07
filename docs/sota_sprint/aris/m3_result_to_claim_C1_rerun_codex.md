Reviewer-Model: gpt-5

1. **claim_supported:** yes, narrowly scoped to the registered synthetic experiment.

2. **what_results_support**

- Amendment 5 HC passes on all four hosts.
- RMM lowers family mean cost versus every host, with 95% CIs entirely below zero:
  - gated deployment: −41.4 [−43.8, −39.0]
  - corrected DISCERN: −47.2 [−49.8, −44.6]
  - SMCS: −14.5 [−17.1, −11.9]
  - gated adaptive range: −32.1 [−34.5, −29.7]
- All 8 late-regime comparisons beat the strongest certified comparator, with Holm-adjusted p-values effectively zero.
- Iid-null first-promotion control passes for all four hosts.
- Persistent-Markov failure is accurately reported: rho=.8 rates are .124–.182; rho=.95 rates are .705–.723.
- Reversal point estimates are worse for three hosts; SMCS improves instead.

3. **what_results_don’t_support**

- No real-data late-improvement claim. The fresh real-data study contains no registered late-improvement episodes.
- No general guarantee of RMM validity beyond the tested iid conditional-null setting.
- No robustness claim beyond this synthetic Bernoulli/Markov generator and these seeds.
- “Loses on reversal” is strongest for gated deployment and DISCERN; gated adaptive range’s V-reversal loss is small and its CI includes zero.
- Comparator conclusions concern independently implemented ports, not author implementations.

4. **missing_evidence**

- Independent synthetic generators and broader shift/dependence structures.
- Real-data streams with identifiable late improvements and valid paired policy-loss comparisons.
- Formal validity analysis under the exact feedback, delay, dependence, and predictability assumptions.
- Reproduction using author code or independently audited comparator implementations.

5. **suggested_claim_revision**

“On 100 fresh seeds from the registered synthetic Bernoulli generator, attaching RMM to gated deployment, corrected DISCERN, SMCS, or gated adaptive range reduced net cost over the registered late-plus-stationary-improvement family, and each RMM host beat the strongest certified comparator on both late-improvement regimes after Holm correction over eight tests, while meeting the registered iid-null first-promotion bound. RMM had higher cost on reversal for three hosts by point estimate, including clear losses for gated deployment and DISCERN, and failed under persistent Markov nulls (rho=.8: .124–.182; rho=.95: .705–.723). Real-data late-improvement performance remains unestablished.”

6. **next_experiments_needed**

- Replicate across independently specified synthetic generators.
- Add genuinely late-improvement real-data or semi-synthetic evaluations with held-out outcomes.
- Audit or replace comparator ports with author implementations where possible.
- Test calibrated alternatives for persistent dependence, or explicitly restrict the method’s safety claim to iid feedback.

7. **confidence:** high

The evidence supports C1 as a registered, synthetic, conditional result—not as a general deployment or real-data claim.