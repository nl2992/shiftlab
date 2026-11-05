# WP2 decision-flag audit

Audited 2026-11-04 against `protocol.md`, `BENCHMARK.md`, `wp2_run.py`,
`wp2_score.py`, `wp2_analyze.py`, the four WP2 raw run sets, and
`tests/sprint2/test_wp2.py`.

## Implemented decision flags

The runner derives each promotion from a 0-to-1 transition in the recorded deployed-model
trace. For every such transition at `tau`, it stores the realised paired advantage
`d_t = l0_t - l1_t` over the next 100, next 500, and remaining events, and the hold-to-end
economic-inappropriateness flag `EI = 1[sum_{t >= tau} d_t - c_s <= 0]`. `wp2_score.derive`
uses the **first** promotion for the primary V1/V3 flags, consistent with the protocol's
first-promotion primary analysis. `hp_path` is separately the any-promotion, whole-policy
path flag `promote and DB <= 0`; it is not a substitute for first-promotion EI because it
includes later rollbacks and all switches. Horizon windows are correctly truncated at episode
end and use the observed window length as the mean denominator.

The registered EI/V3 flag is narrower than the benchmark's all-in economic non-improvement
objective: EI subtracts switch cost from hold-to-end paired loss but excludes label cost and later
rollback. `hp_path` includes later switch/rollback outcomes but still excludes label cost. A new
existing-records supplement, `REALIZED_HARM.md` / `realized_harm.json`, reports the fraction of
whole policy episodes with `J(policy)-J(never-switch)>0`, including labels and actual policy paths.
This retrospective rate complements the registered per-promotion proxy; it is not a prospective
promotion error or expected-value guarantee.

Run 2 uses re-windowings of the same registered event streams; it is not independent data. A
follow-up audit now checks all eight Run-2 configurations (141,360 rows) using
`audit_wp2_run2.py`; it checks promotion fields, per-promotion EI arithmetic, net cost identity, and
paired harm against never-switch where available. Raw-record consistency was also checked for Run 1
(31,000 rows), Run 3 (23,750 rows), and Run 4 (4,650 rows): `ever_promote`, `n_promotions`, and `first_deploy`
matched the saved promotion list in every record; every stored EI flag matched its stored
rest sum and switch-cost threshold; every H-window length matched the truncated horizon; and
all saved `net` values matched `loss + .05 * labels + 5 * switches`. There were zero
mismatches in these checks. The boundary/multiple-promotion/truncated-horizon case is now
covered by `test_promo_stats_decision_flags_for_multiple_promotions_and_truncated_horizons`.

## Claim-label and analysis caveats

There is a material **method-label error** in the registered WP2 output: `xu_acquisition_only`
is listed as a certified V1 method in the protocol, in `wp2_analyze.py`'s `POWERED`/`CERT`/
`V1SET`, and consequently in generated table `claims` labels. The tested adapter reuses Xu's
acquisition component but uses ShiftLab's paired-loss certificate; it does not evaluate Xu's
published certificate. The amended analysis excludes Xu from published-method ranking and powered
sets, while retaining it in descriptive pooled V1 tables as “V1 composite (ShiftLab certificate;
Xu acquisition adapter).” This keeps the ShiftLab V1 result while avoiding attribution to Xu.
Raw rows and registered outputs remain unchanged; corrected output is under `amended_no_xu/`.
This classification amendment is not new independent evidence. WP2 H5 does not directly compare
Xu.

The H4 precision/recall table uses promotion-level rows without cluster-bootstrap intervals;
the protocol calls these descriptive. Its “V2 precision/recall” is the trivial rule that every
promotion is flagged as economically inappropriate (precision equals EI share, recall is 1
among promotions). It should be read as an all-promotions descriptive reference, not a
decision rule that predicts EI.

The comparator-pool audit found a broader class-label issue: excluding Xu still leaves the two
Choe–Ramdas ports and two ShiftLab QCE ports in the 11-member V1 adapter panel. They remain useful
common-contract test methods, but the 11-member set is not an 11-method published pool. A strict
reanalysis of the pooled V1/powered estimands using only the six shared `CERTIFIED_PUBLISHED` ports
is recorded in [`COMPARATOR_CLASS_AUDIT.md`](COMPARATOR_CLASS_AUDIT.md). It preserves the historical
and Xu-excluded outputs and remains post-development/descriptive.

## Verdict

The saved flags are internally consistent with the locked WP2 definitions in the audited raw
records. The main decision-flag implementation is supported by direct record checks and a
focused boundary test. The Xu classification issue has an amended analysis at `amended_no_xu/`,
alongside preserved historical outputs. That sensitivity retains the adapter in pooled V1 summaries
with an explicit composite label. For pooled H2/H4/H6 summaries that exclude the adapter, use the
separate `amended_no_xu_pool/` sensitivity. Any claims must identify the pool used and state that
same-sample pooled inference is not selection-adjusted. These checks establish implementation
consistency, not statistical validity of any method's claimed null.
