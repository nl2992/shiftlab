# Track A economic gating: hindsight-gate headroom bound — results

Protocol: [econ_gate_bound_protocol.md](econ_gate_bound_protocol.md), locked in commit `8f7e8b1e`
before the run (manifest: same HEAD, clean worktree). Seed base 2026120801, 100 seeds × 5 regimes
× (3 base policies + never-switch). Machine-readable:
[econ_gate_bound_results.json](econ_gate_bound_results.json); raw records gitignored at
`outputs/sota_fidelity/econ_gate_bound/`. **Descriptive feasibility diagnostic on exposed
synthetic regimes; not confirmatory.** Sanity checks in the analysis passed: every base policy's
deployed path reproduces the simulator's prediction loss exactly, and never-switch's net cost equals
the realised incumbent loss.

## Verdict under the locked rule: STOP

For the primary base `esr_rmmbets_fullalpha`, the 95% interval for the headroom
H = J(never) − J(best hindsight veto gate) has upper limit below 10 in **4 of 4** primary regimes
(rule: >= 3 means stop). In fact H is negative everywhere: the best conceivable veto gate over a
valid detector is *more* expensive than never switching, by about the label spend.

| Regime | H, realised (95% CI) | H without label cost | H truth-informed | J base / gate / never | Gate saving over base |
|---|---|---|---|---|---|
| F3_reversal_800 | −9.98 [−9.99, −9.98] | 0.00 [0.00, 0.00] | −9.98 | 389.2 / 349.8 / 339.9 | 39.4 |
| W_reversal_700 | −9.99 [−10.00, −9.98] | 0.00 [0.00, 0.00] | −9.99 | 376.7 / 347.0 / 337.0 | 29.7 |
| S_reversal_400 | −9.99 [−9.99, −9.98] | 0.00 [0.00, 0.00] | −9.99 | 332.8 / 322.5 / 312.5 | 10.4 |
| V_reversal_1000 | −9.66 [−10.11, −9.21] | 0.32 [−0.13, 0.77] | −9.81 | 403.6 / 371.3 / 361.6 | 32.3 |
| F3_reversal_1200 (context) | −8.32 [−9.35, −7.29] | 1.66 [0.63, 2.69] | −8.93 | 408.7 / 386.7 / 378.4 | 22.0 |

The other two bases (`two_sided_esr_label_clock`, `rmm:LRMD_k1`) give the same picture: H between
−10.0 and −6.9 in every regime, and at most 3.04 [1.77, 4.31] without label cost (LRMD,
F3_reversal_1200). All values are in the JSON.

## Reading

1. **The hindsight gate vetoes every promotion.** On F3_reversal_800, W_reversal_700 and
   S_reversal_400 the label-free headroom is exactly 0 in all 100 seeds: with full knowledge of the
   realised losses, no promotion any of the three detectors proposed was worth accepting. A valid
   detector's promotion arrives too late in the beneficial window to repay the switch plus the
   post-reversal exposure.
2. **Gating does fix the base detectors' losses, but only down to never switching.** A gate could
   save 10–43 over the bare detector (the "gate saving" column), all of it by not promoting. Vetoed
   rollbacks contribute nothing (mean ≤ 0.02 per episode). That saving is the gap already visible in
   `esr_vs_erb_dev_results.md` reading 3; gating cannot turn it into a gain over never switching.
3. **The longer window helps only marginally.** Moving the reversal from 800 to 1200
   (F3_reversal_1200) lifts the label-free headroom to 1.7–3.0, still far below the margin.
4. **Why (consistent with the arithmetic in the lead review).** At p=.7 a disagreement label carries
   about 0.082 nats, so a level-.05 decision needs roughly 36 labels; at uniform pacing plus the
   100-round delay that is ~460 rounds per decision, about 37 cost units at G=0.08. The oracle gain
   of switching at round 0 and rolling back at the reversal is 22–70 on these regimes. A certified
   round trip cannot fit inside that.

## Assessment for track A

- **Stop** economic gating as a track-A method on these regimes. The locked rule fires, and the
  result is stronger than the rule: even the hindsight-optimal gate in the class does not beat never
  switching. This also matches the prior-art picture: horizon-pays promotion and cost-gated
  rollback are published (see [prior_art/econ_gate_external.md](prior_art/econ_gate_external.md)
  and the independent check), and the repo's own five earlier gates were closed.
- **What remains open is outside this class.** Beating never switching on reversal under this
  contract needs faster evidence (more labels earlier, larger effects, or a cheaper channel), not
  better switch filtering. Front-loaded pacing is the obvious lever, but it trades against late
  change (track B, M1) and its theory is Paper 3 territory.
- **Benchmark content to keep:** under the reference contract, no valid detector's promotion on the
  sprint reversal regimes is worth taking even in hindsight. Track-A reversal regimes therefore
  measure damage control (how close to never-switch a method stays), not gain.
- **Continue / pivot / stop:** stop track A economic gating. The remaining candidates need the
  user's choice: Paper 3 pacing theorem (theory-first, with its stop rule), or reframing the
  reversal results as a benchmark finding.

## Limits

The bound covers veto gates over these three detectors with their acquisition unchanged. It does
not bound policies with a different statistic, pacing or alpha, or uncertified policies (an
uncertified online selector beat never switching by 10.6 on F3_reversal_1200 in Atlas v2, but such
selectors are not certified: the economic switcher `gong_zhang_paid_obs` promotes on 99% of
V_null runs, and the online selectors cost 31–67 more than never switching on F0_null). The regimes are exposed development families.

## Reproduce

```bash
uv run --extra drift python scripts/sota_fidelity/econ_gate_bound.py run --out outputs/sota_fidelity/econ_gate_bound --workers 9
uv run python scripts/sota_fidelity/econ_gate_bound.py analyze --out outputs/sota_fidelity/econ_gate_bound
```
