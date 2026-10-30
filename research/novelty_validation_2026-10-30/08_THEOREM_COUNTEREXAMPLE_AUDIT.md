# 08. Theorem and counterexample audit

## Statements and their status

**S1 (validity under any predictable bet) — PROVED here, standard.** Let `X_t` be adapted with `E[X_t | G_{t-1}] ≤ 0` under the
null and `X_t ≥ −B_t` with `B_t` known given `G_{t-1}`, `λ_t` G_{t−1}-measurable in `[0, c/B_t]`, `c<1`. Then `1+λ_tX_t ≥ 1−c > 0`,
`E[1+λ_tX_t | G_{t−1}] ≤ 1`, so `W_t = ∏(1+λ_sX_s)` is a nonnegative supermartingale and Ville gives `P(∃t: W_t ≥ 1/α) ≤ α`.
Consequences: (a) H2c's guided bet is covered — **validity does not depend on how λ is chosen**, so the guide cannot create or destroy validity (confirmed empirically: every X1 world and sweep cell has H2c false-alarm < .03, D2 stream A 0 alarms);
(b) this makes H2c's validity a known argument, not a contribution. Independent check: the numerical sweep in X1 shows no world with false-alarm > α.
*Required assumptions:* conditional null, known `q` and context-free cap `B_t`, label-release filtration (fixed or outcome-independent delay); bet uses only released labels.

**S2 (no growth-rate theorem) — UNPROVED / not claimable.** For fixed bet λ the expected log-growth is `E log(1+λX) ≈ λμ − λ²E[X²]/2`
(second-order, bounded X), maximised at `λ* = μ/E[X²]`. H2c sets `λ = hic · clip(m_b/(hib·s_b), 0,1)` with `m_b/s_b` the Brier moment ratio,
so it is near-optimal iff `λ ≈ λ*_cost`; this is a *calibration of the Brier-to-cost scaling*, i.e. a Kelly restatement, which the task
says is insufficient. A separation theorem would need a class where the optimal predictable bet is a function of a proxy statistic's
history that no cost-only predictable bet approaches (a regret lower bound). **Not attempted to a proof; no candidate class identified beyond X1's heuristics.**

**S3 (joint ≥ separate) — trivial.** Any pair (acquisition class, best-response switching) is a feasible policy for the joint problem,
so `J ≤` separate; checked on 192 exact instances (0 violations). A strict gap on a toy is DP-implied (07 §2).

## Counterexamples retained as regression tests (`tests/test_novelty_validation.py`, 4 passed)
| id | statement | test |
|---|---|---|
| CE1 | guiding with the tested statistic reproduces cost-only Kelly exactly (exact reduction) | `test_h2c_reduces_to_cost_only_kelly_when_guided_by_itself` |
| CE2 | misleading Brier shift under a flat cost null keeps H2c false-alarm < α | `test_guidance_does_not_change_validity_in_null_worlds` |
| CE3 | cost up / Brier down ⇒ H2c power collapses vs cost-only Kelly | `test_guidance_is_harmful_when_brier_opposes_cost` |
| CE4 | joint DP never worse than separate; B = 0 ⇒ delay irrelevant | `test_joint_dp_never_worse_than_separate_and_b0_equals_no_query` |
Previously retained by the repository: HG covariate-dependent cap counterexample (`docs/hg_validation/02_VALIDITY_COUNTEREXAMPLES.md`), G5 estimand mismatch (`icml_sprint/02`), evaluator null-harm bug (exhaustive ledger).

## Adversarial checklist (task Phase E) — what I tested and what I did not
| item | status |
|---|---|
| conditional vs stationary-average null | defined (04); no new test |
| predictable bets / leakage | S1; the guide uses only labels released by `s`; X1 mask is independent of increments |
| probability-dependent increment bounds | uniform context-free caps used (repository fix); **not** re-attacked |
| known vs estimated nominal risk | D2 uses estimated `U_0` with `δ_S`; stream A is vacuous (no power) ⇒ **calibration validity not stress-tested** |
| covariate-dependent querying | not tested here (repo: invalid for marginal null with covariate caps) |
| delayed / out-of-order labels, outcome-dependent release | fixed delay only; **not tested** |
| hard budget exhaustion | **not tested** here (repo G6 partial) |
| temporal dependence | **not tested** here (dependence NO_GO preserved) |
| incorrect proxy | X1 "opposed/masked" worlds = harmful-guide counterexamples; validity unaffected |
| multiple candidates / sequential selection | **not tested** |
Empirical false-alarm rates below α are **not** claimed as evidence of anytime validity; validity rests on S1.
