# Fixed-graph two-component switching LP (v1)

## Result

On the registered six-event delayed-reversal cell, a fixed two-mode finite-state
controller with a single root lottery exactly matches the cost, causal-null risk,
and component metrics of the previously recovered unrestricted sequence-form LP
policy. The lottery activates the intervention controller with probability `2/5`.
This is exact post-hoc distillation of that oracle policy, not independent efficacy
evidence, and the oracle has no exact dual certificate.

## Contract

- Horizon `T=6`, hard query budget `B=3`, label delay `d=1`.
- False-promotion risk bound `alpha=1/10` under the full-history causal null, where
  each conditional label-success probability is at most `1/2`.
- Query cost `1/100`; switching cost `1/10`.
- Alternative: recurrent hidden regime with transition probabilities `1/4` in
  either direction, emissions `1/20` and `19/20`, and prior `1/2`.

## Controller and LP

The incumbent mode never queries or switches. The active mode queries at event 1,
queries event 2 only if the first visible label is positive, and promotes at event 3
only after two positive labels. While deployed it queries at event 4, rolls back at
event 5 when that label is negative, and otherwise holds its action.

Exact enumeration gives active-mode cost `173083/64000` and null risk `1/4`.
The incumbent cost is `3` with zero risk. For root activation mass `x`, the exact
one-variable LP is

```text
minimize  x * C_active + (1-x) * C_incumbent
subject to x * R_active + (1-x) * R_incumbent <= 1/10
           0 <= x <= 1.
```

Because the active mode improves alternative cost and has risk `1/4`, the optimum is
`x=2/5`. Its total cost is `461083/160000`, with decision cost `1141923/400000`,
query cost `1481/200000`, switch cost `3129/160000`, expected queries `1481/2000`,
and expected switches `3129/16000`. The saved unrestricted numerical LP reports the
same rationalized point and metrics, giving zero recovered-policy gap.

## Scope and interpretation

This verifies a compact policy representation on one registered cell; it does not
prove that the unrestricted numerical LP is globally optimal, because no exact dual
certificate is available. The controller was distilled after inspecting that LP,
so the match is not an independent comparison. Root randomization under a single
linear risk constraint is elementary LP structure. The result therefore does not
establish a novel acquisition rule, a new guarantee, or a methodological advance.

The likelihood-ratio/promotion gate only controls false promotion under the causal
null. Promotion evidence accumulated before a regime reversal does not certify
continued benefit afterward. In this controller those are separate decisions:
economic reversal evidence triggers rollback, while the null-risk calculation applies
to promotion.

## Reproduction

Run `PYTHONPATH=src python scripts/solve_switching_two_component_fsc_lp.py` from the
repository root. Exact component values, the mixture result, the saved reference
hash, and the script hash are recorded in
`outputs/switching_two_component_fsc_lp_v1/results.json`.
