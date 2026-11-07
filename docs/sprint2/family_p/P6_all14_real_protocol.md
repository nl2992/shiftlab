# P6 all-14-source real-stream cost replay

Registered 2026-11-05 before execution. This is a post-development descriptive replay of saved paired loss streams. The source datasets and streams were already used in development or prior sprint analyses; new policy seeds measure Monte Carlo variation only and do not create independent dataset confirmation.

## Question and frozen comparison

How do P6_LRMD_U and its parent M_LRMD_SUI compare in realized all-in cost on all 14 registered real-stream sources, against A5b, D2, the RMM host and the adaptive-range certificate? The primary contrast is paired episode mean `J(P6_LRMD_U)-J(M_LRMD_SUI)`, where `J = prediction loss + .05 * requested labels + 5 * switches`. Secondary contrasts use A5b, D2, `rmm:gated_deployment+RMM`, `gated_adaptive_range+front`, and never-switch. Promotion and resource use are descriptive secondary outcomes.

No episode is classified as a late improvement, reversal, or null from its realized outcome. In particular, the nine cached Atlas sources have no verified event-time, causal-change, or feature-publication metadata. The five UCI sources have chronological rows, but their fixed challenger/incumbent fits do not provide causal change labels. This replay cannot satisfy or imply genuine late-improvement transfer.

## Sources and execution

Use the nine previously used Atlas loss caches and five Sprint-fresh UCI loss caches, exactly as found in the repository. Each source contributes its stored chronological 2,000-event episodes (230 total across 14 sources). The registered per-source feedback delays are `screen.py`'s `REAL_DELAYS` and `FRESH_DELAYS`; budget and cost remain `B=200`, `c_q=.05`, `c_s=5`.

- Policies: `P6_LRMD_U`, `M_LRMD_SUI`, `A5b`, `D2`, `rmm:gated_deployment+RMM`, `gated_adaptive_range+front`, `CONTROL_never_switch`.
- 20 policy-randomness seeds per episode; seed base `2026110902`, distinct from the prior P-family real run and the R5 follow-up.
- Nominal alpha `.05`, matching the prior P-family real screen.
- Preserve output under `outputs/sprint2/round5/p6_all14_real20/` with the runner manifest and raw records.

## Analysis and limits

Average the 20 policy-seed outcomes within each episode, then compute paired candidate-minus-comparator cost differences per source. Report every source separately, the number of episodes, the mean paired difference, a 95% t interval across episodes, and the fraction of episodes favoring P6. Also report per-source mean cost, labels, switches, and promotion rate. Because windows from one dataset are serially adjacent, episode-level t intervals may be optimistic; the five fresh UCI streams have small episode counts. Provide an equal-source average as a descriptive summary, not a population estimate. Do not pool all episodes as independent sources or interpret evaluator-side `gain_is_proxy` fields as ground-truth harm.

The outcome is retrospective empirical cost on cached paired losses. It is not a prospective promotion guarantee, a causal application utility estimate, or independent generalization evidence. Report negative and mixed results without changing the frozen protocol.
