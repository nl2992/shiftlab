# Q1 evidence hook (label-outcome seam) - status, 2026-11-07

**Done (no Stage B experiment run; a registered amendment line is required first).**

Code: `src/shiftlab/bench/contract/{evidence_seam,evidence_q1,adapters_evidence}.py`; 12-line opt-in hook in `adapters_drift2act.py`.
Tests: `tests/d2a_rar/test_q1_evidence.py` (+ golden `tests/d2a_rar/golden/`). Registry: `docs/d2a_rar/registry/Q1_EVIDENCE_IMPLS.json`.
Preflight: `scripts/d2a_rar/q1_hook_preflight.py` -> `results/d2a_rar/q1_hook_preflight.json`. MC: `results/d2a_rar/q1_hook_validity_mc.json`.

## Counts
* Stage-B batch 001 Q1 evidence identities marked NOT_IMPLEMENTED: **42** (the brief said 39). All 42 are now implemented and preflight
  ELIGIBLE. Registry-wide: 134 of 142 drift2act Q1 identities (and 134 of 142 contract_native ones through the promoter shell).
* Not enabled: 8 = `full_sup_denominator` (FL-016) and `rho_robust_gapmix` (FL-022): BLOCKED_BY_LEDGER, closed constructions.

## Validity classes of the 42 (see the registry JSON for filtration / transition model / stopping / parameter uncertainty)
* PROVEN_DECLARED_CLASS 34, DOMINATED_BY_VALID 5, NOT_CLAIMED 3 (gap-ignorant `plugin_slack_inflation` marg, `dependence_test_router` marg).
* Exact-gap/bucketed/tempered/Dirichlet/restart (marg): numerator any predictable predictor, denominator the certified exact-gap null
  supremum (gapmix); envelope variants: gapmix `envelope_u`; cond: conditional bets against `q0`. Exact-gap and envelope mixtures are
  checked equal to the gapmix components (`test_exact_gap_and_envelope_match_gapmix_components`).
* All of them require predictable (G_{i-1}) or exogenous-with-propensity selection and non-informative delay. NOT assumed otherwise.

## Deviations from the grammar hypotheses (each is in the registry `deviations`)
* LFD / interval envelopes are centred on the DECLARED rho_bar (default 0.8), not on the plug-in kernel (a data-centred null set cannot be certified).
* Hazard / semi-Markov enter as restart (onset) weights only; hazard-aware belief transition T^g inside the Drift2Act filter is NOT implemented.
* `adaptive_restart_budget` prunes without re-allocating (valid, but cannot add power; hypothesis untestable as stated).
* `selector_alpha` is the certificate level for `min_of_both` and the screen level for the router; score min_of_both at its own alpha.
* Many-start exact-LR variants use rho cells of width 0.02 (certified, looser) to stay in the CPU budget.
* HIGH_OVERLAP identities stay baseline/ablation-only; nothing here is a novelty claim.

## Open
* Drift2Act host runs are out-of-contract for validity (monitor-adaptive selection, no propensity); a host with declared-propensity audits is needed for in-contract host claims.
* `contract_native` Q1 identities are buildable through the shell but the stage_b resolver (other agent) must be pointed at `evidence_q1.build_evidence`.
