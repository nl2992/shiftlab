# In-repo comparator ports (WP1e)

Branch `research/drift2act-rar-autoresearch-2026-11-07`, base `main@7354480a`, 2026-11-07. No other branch was modified.
Code: `src/shiftlab/sota/inrepo/` (ported modules + `atlas_methods.py` registry), adapters
`src/shiftlab/bench/contract/adapters_inrepo.py` (tier `COMMON_CONTRACT_PORT`), tests `tests/d2a_rar/test_inrepo_ports.py`.
Nothing here is evidence about method quality; it documents provenance, outputs, nulls and port fidelity.

Search: `git grep` over `git for-each-ref` (all local and `origin/*` refs) for each name before declaring anything missing.

## Sources and port status

| Component | Source (ref@commit : path) | In branch as | Status |
|---|---|---|---|
| Gap-Mix (`exact0.8_s4`, `env0.8_s4`, `thin4/10_s4`, `iid_*`, `mlr_*`) | `origin/research/gave-r-2026-11-06@03289d1d` : `src/shiftlab/gaver/gapmix.py` (last changed d636765e) | `sota/inrepo/gapmix.py` | ported unchanged |
| PAVE (full / tuned) | same ref : `gaver/pave.py` (a7116a16) | `inrepo/pave.py` | ported unchanged |
| Delay-gated PAVE, Gap-Mix x PAVE factorial (`gaver:<ev>:<acq>`) | same ref : `gaver/integrated.py` (8fe567a7) | `inrepo/integrated.py` | ported unchanged |
| FreshCheck, paced/CUSUM/cost-threshold comparators, Page-CUSUM default | same ref : `gaver/freshcheck.py` (5521a269) | `inrepo/freshcheck.py` | ported unchanged |
| E_rb detector logic + two-phase (online adaptation) | same ref : `gaver/erb_port.py` (5521a269); E_rb origin `origin/codex/sprint2-leaderboards@a2dd04a1 scripts/sota_sprint/fam_e.py` (`_rb`) / `fam_b.py` | `inrepo/erb_port.py` | PARTIAL (see below) |
| RMM detector + pacers | `origin/codex/sprint2-leaderboards@a2dd04a1` : `scripts/failure_atlas_v2/restart_monitor.py` (3fa468f7), `scripts/promising_directions/sota/competitors/controls.py` (5a714add) | `inrepo/rmm.py` (3 classes verbatim) | PARTIAL |
| DSS / straddle, episode_front, Markov-LR, gap-10 thinning (`thinned_hedged_gate`), Page-CUSUM rollback shell | `main@7354480a` `src/shiftlab/dive/{atlas_components,atlas_dependence_baselines,switching_explore}.py` | importable in place; factories in `inrepo/atlas_methods.py` | no copy needed |
| Two-phase persistence (offline) | `main@7354480a` `dive/persistence_promotion.py::_two_phase_decisions` | importable; offline matrix function, not an online method | online adaptation = `erb_port.TwoPhaseMethod` |
| H2c, HG, PPRM | `main@7354480a` `hgxh2c/baselines.py`, `dive/pprm_risk_monitor.py` | importable | **no common-contract adapter** (below) |

Only edit to ported files: `shiftlab.gaver` -> `shiftlab.sota.inrepo` in import lines, plus a 4-line provenance header.
`test_port_source_identical` re-extracts each file with `git show` and checks that equality.

## What each method outputs, and the null it targets

Nulls use the WP0 registry keys (`registry/null_assumptions.yaml`). d_t = incumbent loss minus candidate loss.

| Method (adapter name) | Output | Target null (registry id) | Caveat |
|---|---|---|---|
| `gapmix:exact0.8_s4`, `gapmix:env0.8_s4` | promotion (+ window-mean rollback) | marg: declared stationary 2-state Markov class, `rho_bar` 0.8 declared (`gap_mix`) | closed-loop/informative delay/rho>rho_bar not proven |
| `markov_lr_gate`, `gapmix:mlr_default8` | promotion (+ rollback) | marg: homogeneous Markov skeleton, pi <= (1+h)/2 (`markov_lr`) | gaps approximated as equal; D binarised by sign |
| `thinned_hedged_gate`, `gapmix:thin10_s4/thin4_s4` | promotion (+ rollback) | cond on retained labels (`thinned_hedged_gate`) | lag-10 independence assumed, not proved |
| `episode_front`, `gapmix:iid_s4/iid_repo32` | promotion + rollback | cond: E[-D_t-h \| F_{t-1}] <= 0 (`episode_front`) | econ check and rollback outside the argument |
| `dss`, `straddle` | label allocation + promotion + rollback | cond (`dss_straddle`) | no proof for delayed-release selection |
| `pave_full`, `pave_tuned`, `gaver:*:pave` | label allocation (+ unchanged DSS promotion/rollback) | none of its own; inherits evidence null (`pave`) | `gaver:*:*` are in the `pave` registry row, null=none by acquisition |
| `freshcheck:fresh_*` | promotion + certified rollback | cond: keep-null E[-D\|F] >= h (`freshcheck`) | empirical level control only |
| `freshcheck:reuse_*`, `paced_*`, `page_cusum_default` | promotion + heuristic rollback | none (`page_cusum` for the CUSUM) | not an e-process; score on economics only |
| `erb`, `erb_a05` | promotion + rollback | cond, keep-null (`e_rb`) | detector logic only |
| `two_phase` | promotion only | cond (`two_phase_persistence`) | adaptive phase boundary is a GAVE-R adaptation of the offline design |
| `rmm_detector` | promotion + rollback + randomised label allocation | cond, first promotion <= alpha_det under iid conditional null (`rmm`) | base policy and restart not ported |

None of these target absolute risk or the economic objective as a test; the economic quantity is measured by J.

## Fidelity of the common-contract adapters (all simplifications)

F1 `obs_mode="shadow"` required. F2 the Atlas harness needs a constant delay `d`; `declared_delay` (default 10) is an adapter argument,
not read from the stream. F3 Atlas `s`:=`c_s`, `c`:=`c_q`, hurdle := `env.hurdle`, alpha 0.1; rollbacks cost `c_b`.
F4 queries carry `propensity=1.0` (deterministic rules; RMM uses its own q with `state.u[0]`). F5 Atlas pending-event bookkeeping assumes in-order,
lossless release; with missing labels DSS's pending cap of 2 can stall. F6 queries blocked by the label/pending cap are revoked (counted in
`n_revoked`; PAVE/FreshCheck credit counters are not restored); a refused model change is re-issued next round. F7 models 0/1 only.
Adapter metadata (`claimed_null`, `registry_id`) is checked against the registry by a test.

## Regression evidence (test_inrepo_ports.py, 22 passed in 189.6 s)

* A. Source identity (5 gaver files + RMM class blocks): exact.
* B. Bit-for-bit vs a temporary `git show` extraction (per-seed action path, cost, queries, promotions identical): Gap-Mix gates
  (`exact0.8_s4`, `env0.8_s4`, `thin10_s4`, `mlr_default8`, rho 0.5, B/T 0.1), FreshCheck/E_rb/two-phase/CUSUM (persistent and reversal cells),
  PAVE (kappa .1, q .03) and `gaver:gapmix:pave` on `on0.6_L1_strong_harmful_d50_b0.05_s0.1`.
* C. Documented-cell reruns with fewer seeds (same seeds as the source, a subset):
  * Gap-Mix null table (`docs/gaver/10_GAPMIX_RESULTS.md` 1.4), 40-60 of the 500 seeds, rho 0.8, B=250/100: count must not exceed the documented
    count and must lie within 4 binomial sd of n*k/500 (cells: iid_s4 202/500, thin10_s4 21, mlr_default8 4 at B=250; exact0.8_s4 29, env0.8_s4 24, iid_s4 36 at B=100). Passed.
  * PAVE (`docs/gaver/20_PAVE_RESULTS.md`, d=50 regression cell, seeds 101090000+i). Documented n=60: DSS 0.4014, PAVE 0.3818, episode_front 0.3876, PAVE-DSS -0.0196.
    Exploratory 30-seed run before writing the test: DSS 0.4060, PAVE 0.3796, episode_front 0.3889, PAVE-DSS -0.0264 (per-seed sd 0.066, se 0.012). The shipped test
    uses 8 seeds with 3-se tolerances (weak power, it mainly guards gross breakage; the bit-for-bit test carries the exactness claim).
  * FreshCheck family (`docs/gaver/30_FRESHCHECK_RESULTS.md` Table A, persistent kind). Documented vs exploratory 32-stream mean J/T:
    existing_cusum 0.507/0.504, fresh_reserve 0.467/0.445, fresh_noreserve 0.418/0.420, erb 0.418/0.420, two_phase 0.569/0.580 (se ~0.017); null false promotion 0/30 (documented 0/1000 for fresh/two_phase, 10/1000 erb).
    fresh_reserve is 1.3 se below the documented value, within the test's 0.06 tolerance.
* Contract checks: 11 adapters run through `run_paired(verify=True)` (audit verifier, leak guard, label cap, no retrain/alert use); an `episode_front` adapter run is replayed
  natively from the delivered labels and reproduces the identical query sequence and model path (clean constant-delay stream).

## Not ported / limits

* **E_rb original** (`fam_e._rb` -> `fam_b.RecoveryMonitor` on certificate hosts): needs the sprint event/disagreement simulator and four host modules; only the detector
  logic exists as the GAVE-R `erb_port` adaptation (adaptations listed in its docstring). `NOT_PORTED["e_rb_sprint"]`.
* **RMM wrapper** (`RestartMixtureMonitor`, `_View`): needs the sprint `Event/QueryRequest` types and base policies; detector + pacers are ported and `rmm_detector` runs detector-only (PARTIAL).
* **H2c / HG / PPRM**: importable in `shiftlab.hgxh2c`, `shiftlab.dive.pprm_risk_monitor`, but they bet on prediction-powered proxy increments and a source calibration
  that `ObservableState` does not expose (PPRM also monitors one model's absolute risk). `NOT_PORTED["h2c"|"pprm"]` raise with the reason. A labels-only variant would be a different method.
* **Standalone Page-CUSUM** (`sota_search/detectors.py::cusum`, on other branches, vectorised over simulated `sim` dicts with generator source moments): not ported; the Atlas Page-CUSUM rollback is used via `page_cusum_default`.
* `gapmix_rho.py` (rho-estimation variant) was not requested and is not ported.
* Atlas methods are single-incumbent/candidate switchers: no retrain, alert or abstain.
* Per-seed tolerances in class C tests are heuristic MC bounds, not preregistered.
