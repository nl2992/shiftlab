# B1 registered protocol: does paired-benefit certification improve net switching cost?

Registered 2026-10-30 before execution. Status: development (synthetic). It is not a confirmatory
study and makes no novelty claim. Every component is established: paired e-processes,
structural zeros on agreement, disagreement querying in the CAMS style, and predictable betting.

## Questions

- Q1 (Gate B, central failure pattern 1). Under a matched label budget and delay, does
  switching on a valid paired certificate of candidate advantage reduce total net cost relative
  to the strongest simple policy? The comparison policies are never-switch, always-challenger,
  and switching on an incumbent-harm alarm.
- Q2 (residual novelty question 2). Does a persistence-aware promotion rule improve on the plain
  certificate rule when advantages reverse, without loss when advantages persist? The
  persistence-aware rule promotes only when the certified lower bound on advantage, times the
  expected remaining persistence under a declared hazard, exceeds the switch cost.

## Stream (evaluator-side truth hidden from policies)

- Horizon and labels: T = 2000, 0/1 classification loss, with labels released after a fixed delay
  d = 5.
- Query cost and budget: each query costs c_q = 0.05. The pathwise hard budget is
  B in {200, 400}, which is 10% or 20% of T.
- Switch cost: c_s in {5, 20} per promotion or rollback.
- Two frozen models: the incumbent f0 and the challenger f1.
- Disagreement and labels: at each t the model agreement indicator is observed for free, since
  both predictions are visible. On agreement, both models have the same loss, so the paired loss
  difference D_t = 0 exactly.
- Change point: tau = 600.

Worlds (pre-change errors: f0 0.10, f1 0.20; disagreement rate 0.25):

| World | Post-change errors | Notes |
|---|---|---|
| W1 useful-persistent | f0 0.30, f1 0.12 | |
| W2 useless | f0 0.30, f1 0.35 | The incumbent is harmed, but the challenger is worse. |
| W3 reversing | as W1 until t = 600 + R, then f0 0.10, f1 0.30 | R ~ Geometric(mean 150). |
| W4 benign | no change | |

The runner implements the error and disagreement joint law and documents it. It sets per-world
disagreement probabilities that are consistent with the marginal error rates.

## Policies (identical budget, delay, query costs and switch costs)

| Policy | Rule |
|---|---|
| P0 | Never switch. |
| P1 | Deploy the challenger from t = 1, paying one switch. |
| P2 | Incumbent alarm then switch. Uniform querying at rate B/T, and a cost-null discounted-Kelly e-process on the incumbent loss against a nominal of 0.10 + epsilon (epsilon = 0.05) at level alpha. The policy switches to f1 on alarm. It never rolls back. |
| P3 | Certified switch. Query disagreements only, at a predictable rate. The rate is paced so that the budget lasts to T; the paced rate is (remaining budget) / (expected remaining disagreements), capped to [p_min, 1] with p_min = 0.05. The policy uses an IPW paired e-process for H0: E[D_t \| past] <= 0 with predictable bets lambda_t in [0, p_min/2]. It promotes when wealth >= 1/alpha. After promotion, a mirrored e-process for H0': E[-D_t \| past] <= 0 triggers rollback at 1/alpha. |
| P4 | Persistence-aware certified switch. Same evidence as P3, but promotion additionally requires LB_t * m_hat > c_s. LB_t is an anytime-valid lower confidence bound on recent mean advantage, from the same e-process family inverted on a grid. m_hat = min(1/h, T - t), with declared hazard h = 1/150 for all worlds; this is a known-persistence assumption and is reported as such. Rollback is as in P3. |
| P5 | Oracle (evaluator truth). It deploys the better model in every regime and pays switch costs. It is reported for headroom only and is not a comparator. |

Settings: alpha = 0.05. Delayed increments are applied at release time with the bet frozen at
issue time. The runner documents why the product is a nonnegative supermartingale under the
stated null and fixed delay, or reuses the repository's delayed event-prefix construction
(`docs/delayed_event_prefix_validity.md`) and cites it.

## Metrics and inference

- Net cost per path: deployment loss + c_q × queries + c_s × switches.
- Also recorded: false promotion (promotion in W2 or W4), time to promotion, number of rollbacks,
  labels used, and budget violations, which must be 0.
- Seeds: 500 per (world, B, c_s), paired across policies by shared streams. The CI is a paired
  percentile bootstrap over seeds, 2000 resamples.

## Decision rules (fixed before execution)

**Q1.** Let BEST be the single simple policy among P0, P1 and P2 with the lowest mean net cost
averaged equally over W1–W4, computed separately for each (B, c_s).

- POSITIVE: P3 reduces the world-averaged mean net cost versus BEST by at least 10%, the paired
  CI excludes 0 in every (B, c_s), and no single world is more than 10% worse than BEST in that
  world.
- NEGATIVE: P3 is no better than BEST in at least half of the (B, c_s) settings.
- Otherwise: MIXED. Report which factor limits P3: candidate headroom, delayed evidence, query
  cost, switch cost, or irreversibility.

**Q2.**

- SUPPORTED: P4 beats P3 in W3 by at least 10% with the CI excluding 0, and is not worse than P3
  by more than 2% in W1.
- NOT SUPPORTED: otherwise.

Even if Q2 is supported, P4 uses a known hazard, so it is a decision-theoretic plug-in result
rather than a statistical novelty claim.

**Validity check.** The P3 false-promotion frequency in W2 and W4 must be at most alpha, up to
Monte Carlo error, with a one-sided 95% Clopper-Pearson upper bound reported. A violation halts
the efficacy interpretation.
