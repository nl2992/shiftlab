# B1 implementation notes (protocol B1-certified-switching, sha256 98f85250...)

Development run, not confirmatory. Code: scripts/promising_directions/b1_certified_switching.py.

## Reuse decision
Self-contained numpy simulator. `gated_increment` returns `-epsilon` on agreement (this breaks the
structural zero D_t = 0 required here) and `DisagreementPacer` is a tariff-window pacer for a
different budget rule; `promotion.py` targets the registered PPI promotion study. Reuse would bend
semantics, so none was used. The delayed-prefix argument of docs/delayed_event_prefix_validity.md
is cited, not re-proved.

## Joint law
Per regime (e0, e1): P(both wrong) b = (e0 + e1 - 0.25)/2, P(only f0 wrong) = e0 - b, P(only f1 wrong)
= e1 - b. Disagreement is 0.25 in every regime. b: pre-change 0.025; W1/W3 phase 2 (0.30, 0.12): 0.085;
W2 post (0.30, 0.35): 0.20; W3 after reversal (0.10, 0.30): 0.075. D_t = loss(f0) - loss(f1), so
E[D] > 0 means the challenger is better. Post-change means: W1 +0.18, W2 -0.05, W3 +0.18 then -0.20.
Change point: steps t > 600 (1-indexed). W3: phase 2 lasts R ~ Geometric(1/150) steps.
Streams (losses, regimes, R, query uniforms) depend only on (seed-base, world), shared across
policies, budgets and switch costs.

## Timing and validity
At step t the policy (i) deploys, (ii) issues query + bet using only labels of events <= t-d-1,
(iii) releases the label of event t-d into wealth with the bet frozen at issue, (iv) may switch,
effective at t+1. A query costs 0.05 at issue; the budget is debited at issue and a query is
impossible at 0 remaining. IPW increment X_t = Q_t D_t / q_t (zero on agreement, no query on
agreement); q_t is predictable (function of remaining budget and past free agreement indicators),
|X_t| <= 1/p_min, bet in [0, p_min/2] so factors stay >= 0.5. Under E[D_t | G_t] <= 0 each factor has
conditional mean <= 1 (also when q_t = 0, where X_t = 0), so wealth over the released prefix is a
nonnegative supermartingale (delayed event-prefix note). After a switch the test restarts; events
issued before the switch are discarded from the new segment. Promotion tests are only "first
promotion" valid (reported false-promotion = any promotion in W2/W4).

## Choices left open by the protocol
- Bet: aGRAPA-style lambda = clip(mu/(s2+mu^2), 0, p_min/2) from exponentially discounted (0.99)
  released increments (10 pseudo-observations, prior second moment 1). The discount affects only
  the bet (predictable), not the cumulative wealth.
- Pacing: q = remaining/(rate_hat * steps left) clipped to [0.05, 1]; rate_hat = (free past
  disagreements + 5)/(t + 20). After exhaustion no queries; wealth freezes; policies hold.
- P1 pays one switch at t = 1. P2: query w.p. B/T uniformly until budget out or alarm (querying
  stops after the alarm), IPW increment X = Q l0/q - 0.15 (0 when no budget), nominal 0.15 =
  0.10 + 0.05, discounted-Kelly bet mu/s2 capped at 3, switches once to f1, never rolls back.
- P3: promotion test on cumulative wealth since start/last rollback; rollback mirrored test
  (-X) since promotion; threshold 20; decision on current wealth.
- P4 LB_t: shifted e-processes prod(1 + lambda_s (X_s - m)) on grid m = 0, 0.01..0.30 (same
  frozen bets lambda_s, monotone in m), LB = largest m with wealth >= 20 at the current time
  (0 if none), cumulative since last promotion/rollback. Validity: for the smallest grid m >= the
  maximal conditional mean in the segment, the m-process is a supermartingale, so LB <= max_s
  E[D_s | G_s] over the segment for all t w.p. >= 0.95. This is NOT a bound on the recent mean; it
  lags change points because the segment includes the pre-change period. No sliding or
  discounted window is used. m_hat = min(150, T-1-t).
- P4w (unregistered, exploratory, excluded from all decisions): LB as max over 10 predeclared
  starts (segment start + 150 j) at level 0.05/10 (union bound). Same validity statement.
- P5: deploys the better model per true regime from the first step of the regime (W1/W3: f0, f1,
  [f0]; W2/W4: f0), pays switches, no queries.

## Inference choices
BEST is chosen per (B, c_s) among P0-P2 by world-averaged mean cost. World-averaged per-seed cost
= mean over the four worlds at the same seed index; paired percentile bootstrap, 2000 resamples,
resampling seeds jointly. Q2 conditions are evaluated in each (B, c_s) and SUPPORTED requires all
four (the protocol does not say; analogous to Q1 POSITIVE). Validity violation = one-sided 95%
Clopper-Pearson LOWER bound on P3 false-promotion rate > alpha (upper bound also reported).
Limiting-factor attribution is by cost decomposition plus post-hoc counterfactual reruns (delay 1,
c_q = 0, p_min = 0.5) that were not saved.
