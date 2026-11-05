# Sprint 2 Family T: evidence-mechanism transfer to published hosts

Implementation: [scripts/sota_sprint/fam_t.py](../../../scripts/sota_sprint/fam_t.py);
tests: [tests/sprint2/test_fam_t.py](../../../tests/sprint2/test_fam_t.py); raw runs: `outputs/sprint2/T/`
(gitignored). Ledger: [ledger.json](ledger.json). Results: [results.md](results.md).

## Pre-declared before any screen result was read (2026-11-04)

* **Evidence interface.** fam_d's `cert(side)` (`update(z, event_t, last) -> e-value`). Modules:
  `qsg` (V1), `a5b` (V2, any rho), `env8` (Markov with declared rho <= .8), `cmean`
  (Family T's own conditional-mean EB e-process, V1-avg; fam_r.py did not exist at build time,
  `fam_t.fam_r_evidence()` picks up `fam_r.EVIDENCE` if it appears), `cmean_s` (started, V1).
* **Hosts.** Model Picker / CAMS / Model Selector through `TGate` (= fam_d.DeployGate + optional
  A5b adaptive-density gap rule on the gate's own front-loaded queries); gated_adaptive_range and
  discern_design_floor through `_DepMixin` (mode `replace`: the module's verdict; mode `AND`: host CS
  and module must both promote, either discards).
* **Selection rule (T4 -> T5 parameter set, and "best evidence" for T6).** Among the candidates of
  a configuration, the *safe-best* is the lowest mean J over `bench2.RISK_ALTS` subject to a
  development promotion rate <= .0936 (bench.NULL_PROMOTION_BOUND) on every one of
  `bench2.RISK_NULLS` (F0_null, F0_worse, F5_dep_null_r8, F5_dep_null_r95). The *economic-best*
  (Track E) ignores the null constraint. T5's single parameter set is chosen on the CAMS rows only
  (T4), so the MP and MS rows are a transfer test of a fixed setting.
* **T6 2x2** on the gated host: evidence {host MOPE CS, safe-best module} x acquisition {front,
  C2 / C6 (fam_c, unchanged)}. Interaction = (best,best) - (best,base) - (base,best) + (base,base),
  paired per seed over RISK_ALTS.
* **Environments (20 dev seeds, base 2026110701).** Nulls F0_null, F0_worse, F5_dep_null_r8,
  F5_dep_null_r95; targeted alternatives F5_dep_better_r8, S_dep_better_r95 (dependence) and F0_better,
  F7_near_better, F9_bursty_better, F1_late_800; outside the intended region F3_reversal_800 and
  F6_delay400_better. Real: the 5 fresh streams (3 seeds) and the 5 twin known-null streams (1 seed per
  split).
* **Track R.** The two best transferred mechanisms and their hosts at every alpha of
  `bench2.ALPHA_GRID`, dev base 2026110701 and eval base 2026110711 on RISK_NULLS + RISK_ALTS.
  T3's missing held-out panel is registered separately in
  [T3_trackR_followup_protocol.md](T3_trackR_followup_protocol.md).

Common-contract ADAPTATIONS: (1) the certificate hosts are one-shot, so a module replacing their
verdict runs a single promotion test at alpha (no rollback cycle); (2) in `TGate` gate-acquired labels
are shared with the host with the combined frozen propensity (fam_d's rule); (3) fam_c's controllers
still read the host MOPE bounds for their value projection when the verdict evidence is replaced.
