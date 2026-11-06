# Pre-opening protocol amendment — MN-DS publisher strata

**Written:** 2026-11-06, before test prediction/loss/policy outcomes were computed.  
**Amends:** `protocol.md`, before any Q4 test opening.  
**Reason:** record exact context economics and make the frozen gate/acquisition rules executable.

## Frozen validation-only context summary

The source list is the three outlets in the already-preserved validation eligibility artifact,
which requires at least 100 July–September records; all other outlets map to `other`. The exact
validation records are:

| Context | Q3 rows | Frozen frequency | Challenger gain | Equal-count Q3 block gains | Static baseline |
|---|---:|---:|---:|---|---|
| `eveningstandard` | 127 | 0.060736 | +0.015748 | +0.023256, −0.071429, +0.095238 | incumbent |
| `sputnik` | 102 | 0.048780 | +0.078431 | +0.117647, +0.058824, +0.058824 | challenger |
| `tass` | 102 | 0.048780 | −0.107843 | −0.088235, −0.058824, −0.176471 | incumbent |
| `other` | 1,760 | 0.841703 | −0.018182 | −0.044293, −0.027257, +0.017065 | incumbent |

The `validation_selected_source_static` rule in the protocol (gain at least 0.03, at least 100
rows, positive gain in at least two of three blocks) therefore deploys the challenger only on
`sputnik`. No Q4 outcomes informed these values or rules.

## Executable query and evidence rules

- Split each context's 50-label allowance into a maximum of 25 promotion-stage labels and 25
  rollback-stage labels. Unused stage quota is not reallocated to another context or stage. If the
  gate never promotes, the rollback-stage allowance remains unused. The global pathwise cap remains
  200 labels.
- Query each disagreement with propensity 1 until the current stage quota is consumed. For
  agreement events the two binary predictions are identical, so paired gain is exactly zero and
  is entered as zero without querying. For a queried disagreement, compute `g_t` only after the
  target's simulated release. If the current-stage quota is spent, stop requesting and stop
  starting further evidence updates for that stage after its already-requested labels are
  processed.
- For each context, freeze `p_s` to the Q3 frequency in the table and `T` to the total number of
  valid Q4 rows established in the opening manifest. At event index `t`, use
  `h_(s,t)=(T-t)*p_s`. Set `kappa=5/h` if `h>5`; otherwise disable the corresponding action. These
  are pre-event quantities and use no future publisher sequence or target. The economic cost-to-go
  threshold is a decision heuristic; it does not prove future gain or cost optimality.
- For promotion, the tested increment is `x_t=g_t-kappa`; for rollback it is
  `x_t=-g_t-kappa`. Given the predictable bound `b_t=1+kappa`, update each fixed stake
  `lambda` by `E_t(lambda)=E_(t-1)(lambda)*(1+lambda*x_t/b_t)` and take the equal-weight mixture.
  The stage crosses at `E_t >= 1/0.00625`. Membership, threshold, and bound are fixed before the
  outcome. Pending feedback is buffered and applied in source-context event order. A promotion or
  rollback becomes effective only for events after the release that caused its crossing.
- Queries and labels already issued remain counted after a stage changes. No repeated promotion,
  alpha recycling, or post-hoc threshold changes are allowed.

The update is a standard predictable bounded-mean betting process. Its crossing interpretation
requires the conditional mean null for the particular context/stage and the stated release-time
filtration. Serial MN-DS outcomes may violate that condition; real-data crossing rates and replay
costs are descriptive and do not certify statistical validity.

## Review and opening gate

This amendment and `protocol.md` must both be hashed into the runner's exclusive opening manifest.
The script must refuse to run if either hash, model hash, raw-source hash, fixed context registry,
or existing no-overwrite marker differs. The pre-test parser may inspect the target column only to
apply the frozen valid-class inclusion rule and to compute a row-ID hash; it must write and fsync
the opening marker before any predictions, losses, net costs, or policy outcomes are computed.
