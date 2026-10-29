# Promotion-dominance diagnostic protocol v1

Registered 2026-10-29 before running the diagnostic, at starting commit
`169d17e`. This is a small deterministic structural screen, not efficacy or
confirmation. No seeds, real data, prior outputs, or historical files are used.

Use the registered first-promotion HMM and costs: B=3, d=1, alpha=1/10,
c=1/100, k=1/10, transitions 1/4, emissions 1/20 and 19/20, prior 1/2.
Evaluate T in {5,6,7}, horizons fixed before execution. Build the unmodified
first-promotion reference at its existing 200,000-node limit. At each reachable
pre-promotion learner information set, let p_s be the conditional alternative
probability of a positive outcome at future event s. Compare:

- no-query/no-promotion continuation cost S = sum_s p_s;
- a relaxed promotion lower bound L = k + (1-p_t) + sum_{s>t} E[min(e_0,1-e_0), min(e_1,1-e_1) conditional on the latent state at s].

The lower bound grants the policy exact knowledge of future latent states,
free information and zero future switching cost, while still requiring first
promotion now. It does not grant knowledge of future outcome noise. Check L
against the exact promotion continuation for both allowed current query choices.
Record counts where S-L >= 0 versus L>=S (with ties), as well as L>=S-1/100.
The lower-bound check is mandatory for every information set and choice; any
failure invalidates the diagnostic. Count state sets and cache sizes; do not infer
end-to-end runtime gains or risk superiority from counts. Save code/config hashes
and result JSON under `docs/risk_preserving_approx/` or a unique output path.
No synthetic Monte Carlo or real-data replay is authorized by this diagnostic.
