# A5b + C6 deadline-value acquisition: development screen

**Registered:** 2026-11-04. **Status:** small development pilot only. This does not amend the
SOTA sprint validation, consume its validation/confirmation block, or establish a novelty or SOTA
claim.

## Question

Can the existing C6 deadline-value acquisition controller reduce net decision cost when paired
with A5b's gap-indexed Markov sequential-universal-inference (SUI) evidence, while retaining the
same class-scoped promotion guarantee?

The only treatment change is predictable acquisition before the first verdict. The SUI evidence,
Markov parameter grid, start mixture, stopping thresholds, rollback rule, and post-verdict A5b
monitoring remain unchanged. For inference, queried signs must remain a stationary first-order
Markov chain independent of disagreement indicators; queries use only released history and the
current event's disagreement indicator. Under those assumptions the A5b likelihood already uses
the actual issue-time gaps, and predictable query stopping changes those gaps but not its
conditional likelihood argument. This is a source-level argument to check against the runner; the
simulation is not a proof.

## Novelty boundary and prior-art positioning

This is not a new deadline rule. `scripts/sota_sprint/fam_c.py::Controller` already implements C6:
front acquisition, a staged budget, an estimated benefit-per-label screen, a shadow price, and a
check that the evidence could arrive before its last useful decision time. `scripts/sota_sprint/fam_a.py`
already implements A5b's gap-aware Markov certificate and persistence-adaptive query spacing.
Existing published observation control and finite-horizon active testing cover the general
ingredients; deadline awareness alone is not the claim. The narrow question is whether this
combination supplies a useful **dependence-valid** acquisition improvement over A5b under the same
hard delayed-label contract. C6's earlier results with IID-style evidence do not establish that.

Primary comparators include A5b, A1b (density-off attribution control), X_A5C (post-discard
acquisition control), and C6 alone. Their registered definitions and outcomes are retained in
`fam_a.py`, `fam_x.py`, `fam_c.py`, `combos/README.md`, and `validation/validation_results.md`.
No generic scheduler novelty is asserted.

## Frozen configuration

- Contract: sprint values `T=2000`, `B=200`, `c_q=0.05`, `c_s=5`, `alpha=0.05`.
- C6 values: `gamma=3.0`, `zeta=0.25`, `two_stage=0.75`, `deadline=true`, `shadow=true`,
  `base=front`, and `skip_action=floor`, copied from the current checked-in C6 implementation and
  `docs/sota_sprint/family_c/tuned.json`.
- A5b values: exact current registry factory (SUI, adaptive spacing, `rho_sig=2.0`, and `_B`
  evidence settings). No retuning or per-regime choices.
- Paired development seeds: `[7701000, 7701030)`, with one common generated stream per regime and
  seed. Check the block against all local source and output manifests before running.
- Regimes: `F6_delay400_better`, `S_delay800_better`, `F1_late_800`, `V_late_600`, `F0_null`,
  `F5_dep_null_r8`, `F5_dep_null_r95`, and `F9_bursty_better`.
- Policies: `A5b`, `A1b`, `X_A5C`, `C6`, and `A5b_C6_deadline`. Keep all outcomes, including
  adverse and misspecified cells.

## Outcomes and stop rule

Primary development outcome is paired net cost versus A5b on the four delayed/late alternatives.
Also report episode-level cost differences, promotion and detection rates, request counts, labels
issued after the decision-value screen closes, and null false promotions separately for each null
regime. A1b and X_A5C diagnose whether the effect is merely acquisition pacing or the already-tested
post-discard saving. C6 alone is an explicitly misspecified-evidence reference under the dependent
nulls, not a safety comparator.

Advance only to a separate frozen validation proposal if the treatment has lower equal-cell mean
cost than A5b with a paired interval below zero on the four targeted cells, has no targeted cell
with an upper paired cost increase above `+0.01` per event, and does not show an implementation
failure or a null-frequency pattern inconsistent with the inherited Markov-class guarantee. With
30 seeds, null frequencies are diagnostics only; validity comes from the unchanged A5b proof and
must be reviewed independently. If the cost rule fails, close this composition and do not tune C6
on these seeds.

## Source and artifact discipline

The source manifest must be frozen after the runner is written and before execution. Include this
protocol, the runner, A5b/C6 implementations, simulator, regime definitions, and existing result
specification hashes, plus the seed block and run command. Write raw paired rows and a compact
summary below `outputs/sota_sprint/a5b_c6_deadline_dev_2026-11-04/`; do not add raw data to Git.
Do not run the separate frozen validation or confirmation blocks.
