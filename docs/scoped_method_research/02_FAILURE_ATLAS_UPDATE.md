# Failure Atlas update (2026-11-06)

This scoped update integrates the corrected Sprint 2 adaptive-range replay and the bounded
rollback/acquisition audit. It preserves earlier Failure Atlas and experiment records. Full details,
source hashes and limitations remain in
[`CORRECTED_REPLAY_AUDIT.md`](../scoped_method_research_2026-11-06/CORRECTED_REPLAY_AUDIT.md),
[`MECHANISM_ABLATION.md`](../scoped_method_research_2026-11-06/MECHANISM_ABLATION.md), and
[`BASELINE_FIDELITY.md`](../scoped_method_research_2026-11-06/BASELINE_FIDELITY.md).

## Confirmed failure patterns (within tested simulators)

1. **Late-improvement blindness under scarce or delayed labels.** Gated promotion can spend the
   horizon gathering evidence after an improvement occurs late. Front-loaded acquisition improves
   the exposed average synthetic and retrospective real replay relative to ordinary Gated, while
   C2/C6 reduce query spending on selected late cells but do not improve timely promotion. Thus the
   observed net-cost gain is principally label thrift, not evidence that late improvement is
   recognized sooner. Exposed five- and nine-source real replay intervals are clustered and must
   not be represented as independent confirmation.
2. **Rollback sensitivity after reversals.** E_rb can respond to reversals in selected synthetic
   regimes, but observed gains depend on restart grid and alpha. Existing audits show the horizon
   gate did not bind in inspected reversal cells; alpha .10 versus .05 changed cost by roughly
   4–6 units. Similar E_rb and `-nogate` behavior leaves no demonstrated gate mechanism. A matched
   two-sided SR/CUSUM comparison is required before attributing any advantage to the wrapper.
3. **Null misspecification risk.** Under the registered iid `V_null`, corrected 1,000-seed false
   promotions were 0/1000 for Gated, 1/1000 for Gated+front and 1/1000 for pace-tuned. Under
   dependent null stresses, acquisition variants promoted substantially more often (e.g. 106/1000
   vs 9/1000 for `V_null_dep_r8`). Those dependent cases are outside the stated conditional-null
   class and are robustness results, not theorem violations.

## What is not established

No distinct repair has survived matched development falsification yet. Corrected replay is not
fresh confirmation; “fresh” in the prior run means a new policy RNG cohort on previously exposed
streams. Real streams have imposed delays and constructed paired losses, not authentic model
training/prediction/label-release chronology. Out-of-class false promotions do not establish
failure under the advertised null. The attached bounded joint rollback/acquisition pilot is
development-only and cannot be used as confirmation.

See the prior Failure Atlas and `CORRECTED_REPLAY_AUDIT.md` for full regime tables, source-cluster
intervals, run manifests, checksums and reproducibility limits.
