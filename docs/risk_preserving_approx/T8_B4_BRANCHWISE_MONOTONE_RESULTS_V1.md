# T=8, B=4 branchwise monotonicity result

The registered verification passed on the saved largest-gap B=4 policy. The
recovered behavior has exactly one randomized pre-promotion information state;
forcing its wait or fourth-query choice yields deterministic pre-promotion
branches. Each branch was checked over all 256 potential-label tapes, with zero
coordinatewise monotonicity violations and at most four requests on every tape.

| Branch | IID tape risk | Independent causal-null risk | Alternative cost |
|---|---:|---:|---:|
| Wait after the first two released positives (3-sample promotion test) | `1/8` | `1/8` | `161848068857/48828125000` |
| Query a fourth label, then test four positives | `1/16` | `1/16` | `695091486731/195312500000` |

For a deterministic monotone promotion event, coupling each adaptive null success
probability `p_t <= 1/2` to a fair Bernoulli label proves that robust risk is at
most the IID fair-tape risk; the IID fair law belongs to the null family, so the
two risks agree. The implementation checked this with both an independently
written history recursion and the existing causal-game evaluator. Both branch
risk equalities hold.

The saved behavior is the `3/5`–`2/5` mixture of these branches at the released
label boundary. Its weighted branch risk and exact full-history causal-null risk
are both `1/10`. The weighted branch cost
`1666179899873/488281250000` exactly matches the saved full-decomposition policy's
cost. On this synthetic cell it matches the decomposed reference and beats the
best fixed calendar (and the tested finite calendar portfolio) by
`11126044659/976562500000`.

This is a stronger verified baseline and a useful certificate construction, not
yet an algorithmic win: the exact optimizer supplied the split and the branch
policies. Monotone-event coupling, randomized sample-size allocation and delayed
group-sequential/futility testing are established ideas. The result supplies no
value bound for a policy class generated without the oracle and does not pass G1.
No new seeds, real data or holdouts were accessed.

The registered protocol, source, exact per-tape results and hashes are in
`T8_B4_BRANCHWISE_MONOTONE_PROTOCOL_V1.md`,
`t8_b4_branchwise_monotone_v1.json` and
`scripts/research_risk_approx/verify_t8_b4_branchwise_monotone.py`.
The JSON records exact branch metrics, risk recursions, tape counts and zero
violations (not a 256-row tape dump). The executed runner snapshot SHA-256 is
`1b6432cb88bce49ca2a14d3853b7fa5096d45ee0274b5cd901c10c28476c7d7d`; the result
JSON SHA-256 is `aa6f42806ea717bca2b73c00cb57e1af201b9011d9378763f91eda6bcc93465a`.
