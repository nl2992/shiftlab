# Track A economic gating: hindsight-gate headroom bound (protocol, locked before run)

**Locked:** 2026-11-07, before any run under the seed base below. **Status:** descriptive
feasibility diagnostic on already-exposed synthetic regimes. It nominates no method and is not
confirmatory.

## Why this comes before building a gate

Economic gating (promote or roll back only when the remaining horizon pays for the switch) has been
tried in this repo at least five times and closed each time: P4 persistence-aware switching, B3+
break-even promotion, EconomicStop, the sprint-2 R5 and H families (see
[prior_art/econ_gate_internal.md](prior_art/econ_gate_internal.md)). What has not been tested is a
gate wrapped around a *valid* detector on the four sprint reversal regimes, where every valid
method loses to never switching
([esr_vs_erb_dev_results.md](esr_vs_erb_dev_results.md), reading 3). Instead of building a fifth
gate, this diagnostic bounds what *any* gate of that kind could achieve.

## Gate class and the bound

A **veto gate** wraps a base policy P. P runs unchanged (its detector, restarts and label
acquisition are untouched) and proposes a desired model d_t. The gate sets the deployed model a_t;
it may change a_t only at a round where d_t changes, and only to d_t. Every horizon-, cost- or
hazard-based gate that filters a detector's switch decisions is in this class.

**Bound.** For each episode, the hindsight-optimal veto gate is found by dynamic programming over
P's proposal times using the *realised* losses (evaluator-side; sees every loss for free). Its net
cost J_gate* = realised prediction loss of the gated path + c_s × switches + c_q × P's labels is a
lower bound on the cost of every veto gate over P in that episode. A looser bound, J_gate*−label
cost, also covers gates that stop buying labels.

A secondary, less noise-optimistic version replaces realised losses with the evaluator-side expected
loss given the true advantage G_t (the "truth-informed gate"); reported descriptively.

## Contract, seeds, regimes, base policies

- `bench.CONTRACT`: T=2000, B=200, c_q=.05, c_s=5, alpha=.05; common simulator, paired streams.
- Seed base `2026120801`, 100 seeds per regime (not used anywhere in the repo; checked).
- Primary regimes: `F3_reversal_800`, `W_reversal_700`, `S_reversal_400`, `V_reversal_1000`.
  Context (not in the decision rule): `F3_reversal_1200`.
- Base policies (fixed now): `esr_rmmbets_fullalpha` (primary), `two_sided_esr_label_clock`,
  `rmm:LRMD_k1`. Control: `CONTROL_never_switch`.

## Estimands

For each regime and base policy, per seed: H = J(never) − J_gate*(P) (headroom of the best possible
gate over never switching), and G = J(P) − J_gate*(P) (the most a gate can save over P). Mean and
95% paired t interval over 100 seeds. Also: the share of G from vetoed promotions vs vetoed
rollbacks, and the truth-informed versions.

## Decision rule (stated now)

Using the primary base `esr_rmmbets_fullalpha` and the realised-loss bound:

- **Stop** economic gating for track A if, in at least 3 of the 4 primary regimes, the 95% interval
  for H has upper limit < 10 (the best conceivable veto gate is within 10 cost units of never
  switching, or worse). A real gate cannot reach the hindsight bound, so a method built on it
  cannot clear a practically useful margin over never switching on these regimes.
- **Continue** to a gate design (new protocol, its own prior-art check) only if H has lower limit
  > 10 in at least 2 of the 4 primary regimes, and the truth-informed H agrees in sign.
- Otherwise: inconclusive; report and ask the user before doing anything else.
- No regime, base policy or threshold is changed after the run. Results on the other base policies
  and on `F3_reversal_1200` are descriptive.

## Limits stated in advance

- The bound covers veto gates over these three detectors only. It does not bound gates that change
  the detector's own evidence, pacing or alpha, or policies built on a different statistic.
- The regimes are exposed development families with the challenger better from round 0; real
  streams in the repo have no verified reversals.

## Reproduce

```bash
uv run --extra drift python scripts/sota_fidelity/econ_gate_bound.py run --out outputs/sota_fidelity/econ_gate_bound --workers 9
uv run python scripts/sota_fidelity/econ_gate_bound.py analyze --out outputs/sota_fidelity/econ_gate_bound
```
