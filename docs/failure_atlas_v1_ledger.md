# Failure Atlas v1 ledger (EXPLORATORY; no confirmatory claim)

Protocol: `docs/failure_atlas_v1_protocol.md` including Amendment 1. All numbers below are copied from
`outputs/failure_atlas_v1/summary.md` (cycle 1), `outputs/failure_atlas_v1_cycle2/summary.md` (cycle 2) or
computed from the `state.json`/`archive.jsonl` next to them. Nothing here is confirmatory: discovery,
development and mechanism-validation seeds only.

## 1. Run record

- Cycle 1 invocation: not recorded in the repository. `outputs/failure_atlas_v1/run.log` header:
  `out=outputs/failure_atlas_v1 smoke=False workers=12`; other arguments were the script defaults.
- Cycle 2 command (repository root):
  `.venv/Scripts/python scripts/run_failure_atlas_loop.py --out outputs/failure_atlas_v1_cycle2 --workers 12 --val-offset 50000 --reuse-cells-from outputs/failure_atlas_v1/state.json --compare-to outputs/failure_atlas_v1`
  (started detached, logging to `outputs/failure_atlas_v1_cycle2/run.log`; `run.err` empty).
- Tests before the run: `.venv/Scripts/python -m pytest tests/test_failure_atlas.py tests/test_atlas_components.py tests/test_switching_explore.py -q` -> 94 passed. Smoke loop:
  `.venv/Scripts/python scripts/run_failure_atlas_loop.py --smoke --out outputs/failure_atlas_v1_cycle2_smoke --workers 8 --val-offset 50000` (completed, all stages).
- Cycle 1 header: 
  - git head `81707c0938a9ed293bf6d942d66808f15397f0ad`, dirty = True
  - source sha256:
  - `failure_atlas.py`: `4626be6e4d7f90520fdc860dc5b5db8f48ba49ad9a2bac9aa96415d6352b4e07`
  - `switching_explore.py`: `f7a330f595d2b2390c7a2b3bd4e08da7c3f71a2a8caf8463700f3ee71823dbee`
  - method-runs 175220; wall time 1828 s.
- Cycle 2 header: 
  - git head `81707c0938a9ed293bf6d942d66808f15397f0ad`, dirty = True
    (the new code was uncommitted when the run started; `switching_explore.py` and `eprocess.py` unchanged)
  - source sha256:
  - `failure_atlas.py`: `6d53c69695e76400431febf7c05e9ee2af82a6ee4a01fafb910e1f1a10576ae7`
  - `atlas_components.py`: `8b71867bf025d6d09274d1e66b52e7fb28da7ec0ccfd12861b7f90f3fa1c5aae`
  - `switching_explore.py`: `f7a330f595d2b2390c7a2b3bd4e08da7c3f71a2a8caf8463700f3ee71823dbee`
  - `eprocess.py`: `a9355d3883118ed32039feafe0db0b01fd8824dfbaed2e3d70e6710964565d41`
  - `run_failure_atlas_loop.py`: `4bc59e9b551067a107f5506b09499b5761e299cfdc8f34759b4e16d7003719ad`
  - method-runs 211460; wall time 3438 s; per stage:
  - stage1_discover: 1290 s
  - stage2_reproduce: 207 s
  - stage2b_diagnose: 181 s
  - stage4_isolate: 232 s
  - stage5_6_mechanism: 1528 s
- Cycle 2 reuses the cycle-1 sampled (240) and refinement (120) cells and the same discovery seeds, so classes
  are comparable. The refinement cells were therefore not re-chosen adaptively around cycle-2 failures.
  Stage-2b diagnostics use discovery seeds 3000-3099; mechanism validation uses seeds 250000-250019 (offset 50000).

## 2. Baseline registry

## Registry (stage 0)

| baseline | status | role | guarantee | notes |
|---|---|---|---|---|
| no_switch | implemented | floor | none needed (never promotes) | zero false promotion by construction |
| periodic_mean | implemented | ungated | none | periodic window-mean re-evaluation on a uniform calendar |
| episode_geo / episode_equal / episode_front | implemented | safety-gated | per-episode bounded-mean started-mixture e-process with alpha spending | validity under repeated episodes is a research target, not established here |
| allonset_edetector | implemented | safety-gated | all-onset mixture e-detector threshold 1/alpha; promotes once | no rollback |
| dal_restart | implemented | ungated | none (CUSUM-triggered query bursts) | detect-then-re-evaluate |
| pacing_bernoulli | implemented | ungated | none (EWMA threshold, Bernoulli query pacing) | budget respected only through the harness guard |
| c2_rho0.75 | implemented | safety-gated | rho*B to alpha-spent e-process gate; remainder to CUSUM rollback | exploratory C2 candidate used as a benchmark anchor, not a target |
| c1_hmm_cs | implemented | safety-gated | delayed-HMM likelihood-ratio confidence-set gate over a declared bank | exploratory C1 candidate; bank misspecification not covered |
| gong_zhang_delayed | missing | safety-gated (when added) | R6 baseline: delayed-feedback sequential testing wrapper | not in harness; every atlas entry carries this limitation |
| qiu_et_al_delayed | missing | safety-gated (when added) | R6 baseline: delayed-label monitoring wrapper | not in harness |
| ryabchenko_delayed_wrapper | wrapper-needed | safety-gated (when added) | R6 baseline: sequential testing under delayed feedback | requires a delayed-feedback wrapper around the base test; missing |
| online_fwer_comparator | missing | safety-gated (when added) | online FWER control across repeated promotion episodes | would replace ad hoc alpha spending in episode_* |
| hard_budget_pacing_comparator | missing | ungated (when added) | none (budget-feasible pacing comparator) | strong hard-budget pacing baseline absent |

The R6 baselines `gong_zhang_delayed`, `qiu_et_al_delayed`, `ryabchenko_delayed_wrapper` (wrapper-needed),
`online_fwer_comparator` and `hard_budget_pacing_comparator` are missing. Every failure below is a failure
against the implemented baselines only.

## 3. Cycle 1 results

## R_family kappa calibration (discovery null twins)

chosen kappa = 0.05 (calibrated=True, 80 distinct twins, seeds [0, 19])

| kappa | FP count | n | pooled any-FP rate |
|---|---|---|---|
| 0.5 | 1532 | 1600 | 0.958 |
| 0.3 | 1035 | 1600 | 0.647 |
| 0.2 | 653 | 1600 | 0.408 |
| 0.1 | 301 | 1600 | 0.188 |
| 0.05 | 117 | 1600 | 0.073 |
| 0.02 | 40 | 1600 | 0.025 |
| 0.01 | 19 | 1600 | 0.012 |

## Discovery counts by class (stage 1)

| class | cells |
|---|---|
| headroom_not_shared | 2 |
| info_limited | 57 |
| no_headroom | 189 |
| reference_unsafe | 20 |
| shared_failure | 92 |
| total | 360 |

### The R_law reference defect

R_law and R_family valued a promotion as the expected benefit of staying promoted until T. After a transient
window closes the posterior sees the harmful off state, so that tail made R_law never promote in the 57 cells
labelled `info_limited` below. Their "no_switch - R_law" CIs are all within [-0.0025, -0.0005] (negative:
R_law did not beat doing nothing). The information-limit test was therefore not informative in cycle 1.
Amendment 1 replaced the value by a promote-then-revert plan value.

In the stage-2 table below, 12 candidate cells were reproduced; 11 survived (label `shared_failure`). The twelfth,
`on0.3_L0.3_strong_harmful_d10_b0.05_s0.5`, is labelled `info_limited` only because of this defect.

## Reproduced failures (stage 2, fresh discovery seeds)

| cell | label | severity | H [95% CI] | best_safe | R_family null FP [Wilson] |
|---|---|---|---|---|---|
| on0.3_L0.6_strong_harmful_d10_b0.05_s0.1 | shared_failure | 0.1861 | +0.1861 [+0.1689, +0.2032] | episode_front | 0.130 [0.078,0.210] |
| on0.6_L1_strong_harmful_d10_b0.05_s0.1 | shared_failure | 0.1833 | +0.1833 [+0.1727, +0.1938] | allonset_edetector | 0.130 [0.078,0.210] |
| on0.8_L1_strong_harmful_d10_b0.05_s0.1 | shared_failure | 0.1056 | +0.1056 [+0.0998, +0.1113] | c1_hmm_cs | 0.130 [0.078,0.210] |
| on0.8_L1_strong_harmful_d10_b0.1_s0.1 | shared_failure | 0.1102 | +0.1102 [+0.1052, +0.1152] | episode_front | 0.090 [0.048,0.162] |
| on0.3_L0.6_strong_harmful_d10_b0.1_s0.1 | shared_failure | 0.1790 | +0.1790 [+0.1628, +0.1952] | episode_front | 0.090 [0.048,0.162] |
| on0.6_L1_strong_harmful_d10_b0.1_s0.1 | shared_failure | 0.1319 | +0.1319 [+0.1252, +0.1387] | allonset_edetector | 0.090 [0.048,0.162] |
| on0.8_L0.6_strong_harmful_d1_b0.05_s0.1 | shared_failure | 0.1115 | +0.1115 [+0.1049, +0.1181] | c1_hmm_cs | 0.070 [0.034,0.137] |
| on0.3_L0.6_strong_harmful_d10_b0.05_s0.5 | shared_failure | 0.2027 | +0.2027 [+0.1844, +0.2210] | episode_front | 0.090 [0.048,0.162] |
| on0.6_L1_strong_harmful_d50_b0.1_s0.1 | shared_failure | 0.1013 | +0.1013 [+0.0941, +0.1085] | allonset_edetector | 0.110 [0.063,0.186] |
| on0.3_L0.3_strong_harmful_d10_b0.05_s0.5 | info_limited | 0.1050 | +0.1050 [+0.0931, +0.1169] | no_switch | 0.090 [0.048,0.162] |
| on0.8_L0.6_strong_harmful_d1_b0.05_s0.5 | shared_failure | 0.1096 | +0.1096 [+0.1031, +0.1162] | no_switch | 0.100 [0.055,0.174] |
| on0.8_L0.6_strong_harmful_d1_b0.1_s0.5 | shared_failure | 0.1056 | +0.1056 [+0.0993, +0.1118] | c1_hmm_cs | 0.090 [0.048,0.162] |

### Per-baseline gap to R_family (mean, lower CI bound; cost per round)

| cell | episode_geo | episode_equal | episode_front | allonset_edetector | c2_rho0.75 | c1_hmm_cs | no_switch |
|---|---|---|---|---|---|---|---|
| on0.3_L0.6_strong_harmful_d10_b0.05_s0.1 | +0.217 (+0.198) | +0.303 (+0.282) | +0.186 (+0.169) | +0.207 (+0.190) | +0.255 (+0.232) | +0.315 (+0.294) | +0.315 (+0.294) |
| on0.6_L1_strong_harmful_d10_b0.05_s0.1 | +0.201 (+0.189) | +0.221 (+0.209) | +0.188 (+0.177) | +0.183 (+0.173) | +0.217 (+0.205) | +0.221 (+0.209) | +0.220 (+0.208) |
| on0.8_L1_strong_harmful_d10_b0.05_s0.1 | +0.108 (+0.102) | +0.108 (+0.102) | +0.108 (+0.102) | +0.108 (+0.102) | +0.108 (+0.102) | +0.106 (+0.100) | +0.107 (+0.102) |
| on0.8_L1_strong_harmful_d10_b0.1_s0.1 | +0.114 (+0.109) | +0.119 (+0.113) | +0.110 (+0.105) | +0.112 (+0.107) | +0.117 (+0.112) | +0.110 (+0.105) | +0.118 (+0.112) |
| on0.3_L0.6_strong_harmful_d10_b0.1_s0.1 | +0.194 (+0.179) | +0.290 (+0.275) | +0.179 (+0.163) | +0.186 (+0.177) | +0.234 (+0.217) | +0.331 (+0.321) | +0.401 (+0.394) |
| on0.6_L1_strong_harmful_d10_b0.1_s0.1 | +0.163 (+0.152) | +0.237 (+0.230) | +0.144 (+0.134) | +0.132 (+0.125) | +0.210 (+0.200) | +0.255 (+0.249) | +0.274 (+0.268) |
| on0.8_L0.6_strong_harmful_d1_b0.05_s0.1 | +0.112 (+0.106) | +0.112 (+0.106) | +0.112 (+0.106) | +0.112 (+0.106) | +0.112 (+0.106) | +0.112 (+0.105) | +0.112 (+0.105) |
| on0.3_L0.6_strong_harmful_d10_b0.05_s0.5 | +0.235 (+0.217) | +0.320 (+0.303) | +0.203 (+0.184) | +0.220 (+0.203) | +0.274 (+0.255) | +0.329 (+0.311) | +0.328 (+0.311) |
| on0.6_L1_strong_harmful_d50_b0.1_s0.1 | +0.125 (+0.116) | +0.199 (+0.193) | +0.107 (+0.099) | +0.101 (+0.094) | +0.176 (+0.167) | +0.229 (+0.223) | +0.228 (+0.223) |
| on0.3_L0.3_strong_harmful_d10_b0.05_s0.5 | +0.116 (+0.102) | +0.106 (+0.094) | +0.115 (+0.103) | +0.217 (+0.183) | +0.106 (+0.094) | +0.105 (+0.094) | +0.105 (+0.093) |
| on0.8_L0.6_strong_harmful_d1_b0.05_s0.5 | +0.110 (+0.104) | +0.110 (+0.104) | +0.110 (+0.104) | +0.110 (+0.104) | +0.110 (+0.103) | +0.110 (+0.103) | +0.110 (+0.103) |
| on0.8_L0.6_strong_harmful_d1_b0.1_s0.5 | +0.122 (+0.117) | +0.129 (+0.123) | +0.115 (+0.110) | +0.118 (+0.113) | +0.127 (+0.122) | +0.106 (+0.099) | +0.128 (+0.122) |

## Isolation (stage 4): does moving one axis to its easiest level remove the failure?

| failure cell | onset | duration | effect | d | budget_frac | s |
|---|---|---|---|---|---|---|
| on0.3_L0.6_strong_harmful_d10_b0.05_s0.1 | keeps (H lo +0.040, shared_failure) | keeps (H lo +0.113, shared_failure) | at easiest | keeps (H lo +0.135, shared_failure) | keeps (H lo +0.101, shared_failure) | keeps (H lo +0.184, shared_failure) |
| on0.6_L1_strong_harmful_d10_b0.05_s0.1 | REMOVES (H lo -0.125, no_headroom) | at easiest | at easiest | keeps (H lo +0.143, shared_failure) | keeps (H lo +0.052, shared_failure) | keeps (H lo +0.169, shared_failure) |
| on0.8_L1_strong_harmful_d10_b0.05_s0.1 | REMOVES (H lo -0.125, no_headroom) | at easiest | at easiest | keeps (H lo +0.092, shared_failure) | keeps (H lo +0.063, shared_failure) | keeps (H lo +0.089, shared_failure) |
| on0.8_L1_strong_harmful_d10_b0.1_s0.1 | REMOVES (H lo -0.027, no_headroom) | at easiest | at easiest | keeps (H lo +0.096, shared_failure) | keeps (H lo +0.063, shared_failure) | keeps (H lo +0.105, shared_failure) |
| on0.3_L0.6_strong_harmful_d10_b0.1_s0.1 | keeps (H lo +0.057, shared_failure) | keeps (H lo +0.098, shared_failure) | at easiest | keeps (H lo +0.143, shared_failure) | keeps (H lo +0.101, shared_failure) | keeps (H lo +0.131, shared_failure) |
| on0.6_L1_strong_harmful_d10_b0.1_s0.1 | REMOVES (H lo -0.027, no_headroom) | at easiest | at easiest | keeps (H lo +0.115, shared_failure) | keeps (H lo +0.052, shared_failure) | keeps (H lo +0.114, shared_failure) |
| on0.8_L0.6_strong_harmful_d1_b0.05_s0.1 | keeps (H lo +0.014, shared_failure) | keeps (H lo +0.092, shared_failure) | at easiest | at easiest | keeps (H lo +0.060, shared_failure) | keeps (H lo +0.105, shared_failure) |
| on0.3_L0.6_strong_harmful_d10_b0.05_s0.5 | keeps (H lo +0.031, shared_failure) | keeps (H lo +0.108, shared_failure) | at easiest | keeps (H lo +0.108, shared_failure) | keeps (H lo +0.087, shared_failure) | keeps (H lo +0.184, shared_failure) |
| on0.6_L1_strong_harmful_d50_b0.1_s0.1 | REMOVES (H lo -0.088, no_headroom) | at easiest | at easiest | keeps (H lo +0.115, shared_failure) | keeps (H lo +0.039, shared_failure) | keeps (H lo +0.085, shared_failure) |
| on0.8_L0.6_strong_harmful_d1_b0.05_s0.5 | keeps (H lo +0.019, shared_failure) | keeps (H lo +0.101, shared_failure) | at easiest | at easiest | keeps (H lo +0.058, shared_failure) | keeps (H lo +0.105, shared_failure) |
| on0.8_L0.6_strong_harmful_d1_b0.1_s0.5 | keeps (H lo +0.051, shared_failure) | keeps (H lo +0.095, shared_failure) | at easiest | at easiest | keeps (H lo +0.058, shared_failure) | keeps (H lo +0.097, shared_failure) |

### Stage 5/6 (cycle 1): no repair

## Mechanism stages 5-6

see per-failure rows below

- `on0.3_L0.6_strong_harmful_d10_b0.05_s0.1` (axes removing: []): no single axis removes the failure; no mechanism candidates

- `on0.6_L1_strong_harmful_d10_b0.05_s0.1` (axes removing: ['onset']): 14 proposed, 0 invalid, 14 run; best `991567bb7ec8` cost 0.3455, gap closure 0.14, null FP 0.00, gated=True; validation: candidate=991567bb7ec8, seeds=mechanism 200000+20, cost=0.337189, gap_closure=0.23652094993193132, null_fp=0.0, ablated_cost=0.337189, closes_50=False, null_ok=True, ablation_removes_gain=False, neighbours=[{'cell': 'on0.3_L1_strong_harmful_d10_b0.05_s0.1', 'best_safe': 'allonset_edetector', 'cand_minus_best_safe': [0.006908499999999977, -0.04016099482128983, 0.05397799482128979], 'cand_minus_R_family': [0.12177849999999997, 0.0667601292171513, 0.17679687078284864], 'null_fp': 0.0, 'no_worse_than_best_safe': False}, {'cell': 'on0.8_L1_strong_harmful_d10_b0.05_s0.1', 'best_safe': 'c1_hmm_cs', 'cand_minus_best_safe': [-0.004904500000000011, -0.015094325067887642, 0.00528532506788762], 'cand_minus_R_family': [0.1178215, 0.10472497444999605, 0.13091802555000392], 'null_fp': 0.0, 'no_worse_than_best_safe': True}], neighbours_ok=False, repair=False, validation_uses=1

- `on0.8_L1_strong_harmful_d10_b0.05_s0.1` (axes removing: ['onset']): 14 proposed, 0 invalid, 14 run; best `991567bb7ec8` cost 0.2505, gap closure 0.04, null FP 0.00, gated=True; validation: candidate=991567bb7ec8, seeds=mechanism 200000+20, cost=0.26069149999999996, gap_closure=0.039963007023776816, null_fp=0.0, ablated_cost=0.26069149999999996, closes_50=False, null_ok=True, ablation_removes_gain=False, neighbours=[{'cell': 'on0.6_L1_strong_harmful_d10_b0.05_s0.1', 'best_safe': 'allonset_edetector', 'cand_minus_best_safe': [-0.03909100000000002, -0.07565498703232579, -0.0025270129676742484], 'cand_minus_R_family': [0.126184, 0.07642902134706689, 0.1759389786529331], 'null_fp': 0.0, 'no_worse_than_best_safe': True}], neighbours_ok=True, repair=False, validation_uses=2, status=reclassified_development

- `on0.8_L1_strong_harmful_d10_b0.1_s0.1` (axes removing: ['onset']): 14 proposed, 0 invalid, 14 run; best `66051244cf2b` cost 0.2297, gap closure 0.15, null FP 0.00, gated=True; validation: candidate=66051244cf2b, seeds=mechanism 200000+20, cost=0.22924499999999998, gap_closure=0.15781363306743987, null_fp=0.0, ablated_cost=0.25458500000000006, closes_50=False, null_ok=True, ablation_removes_gain=True, neighbours=[{'cell': 'on0.6_L1_strong_harmful_d10_b0.1_s0.1', 'best_safe': 'allonset_edetector', 'cand_minus_best_safe': [0.027984999999999993, -0.008028951535427455, 0.06399895153542744], 'cand_minus_R_family': [0.1627, 0.1314869051685406, 0.1939130948314594], 'null_fp': 0.0, 'no_worse_than_best_safe': False}], neighbours_ok=False, repair=False, validation_uses=1

- `on0.3_L0.6_strong_harmful_d10_b0.1_s0.1` (axes removing: []): no single axis removes the failure; no mechanism candidates

- `on0.6_L1_strong_harmful_d10_b0.1_s0.1` (axes removing: ['onset']): 14 proposed, 0 invalid, 14 run; best `10862081b509` cost 0.2816, gap closure -0.06, null FP 0.00, gated=True; validation: candidate=10862081b509, seeds=mechanism 200000+20, cost=0.28298999999999996, gap_closure=-0.027428274505437444, null_fp=0.0, closes_50=False, null_ok=True, ablation_removes_gain=None, neighbours=[{'cell': 'on0.3_L1_strong_harmful_d10_b0.1_s0.1', 'best_safe': 'allonset_edetector', 'cand_minus_best_safe': [0.01635000000000001, 0.006102756775075564, 0.026597243224924457], 'cand_minus_R_family': [0.15226, 0.12312053613157539, 0.18139946386842462], 'null_fp': 0.0, 'no_worse_than_best_safe': False}, {'cell': 'on0.8_L1_strong_harmful_d10_b0.1_s0.1', 'best_safe': 'episode_front', 'cand_minus_best_safe': [-0.0017049999999999995, -0.0052736060127661685, 0.001863606012766169], 'cand_minus_R_family': [0.10861499999999999, 0.10045644029292117, 0.11677355970707881], 'null_fp': 0.0, 'no_worse_than_best_safe': True}], neighbours_ok=False, repair=None, validation_uses=1

- `on0.8_L0.6_strong_harmful_d1_b0.05_s0.1` (axes removing: []): no single axis removes the failure; no mechanism candidates

- `on0.3_L0.6_strong_harmful_d10_b0.05_s0.5` (axes removing: []): no single axis removes the failure; no mechanism candidates

- `on0.6_L1_strong_harmful_d50_b0.1_s0.1` (axes removing: ['onset']): 14 proposed, 0 invalid, 14 run; best `10862081b509` cost 0.2984, gap closure -0.02, null FP 0.00, gated=True; validation: candidate=10862081b509, seeds=mechanism 200000+20, cost=0.324785, gap_closure=-0.061810242159587026, null_fp=0.0, closes_50=False, null_ok=True, ablation_removes_gain=None, neighbours=[{'cell': 'on0.3_L1_strong_harmful_d50_b0.1_s0.1', 'best_safe': 'allonset_edetector', 'cand_minus_best_safe': [0.008799999999999975, -0.0046821672227988324, 0.02228216722279878], 'cand_minus_R_family': [0.11135999999999999, 0.08174463256807271, 0.14097536743192726], 'null_fp': 0.0, 'no_worse_than_best_safe': False}, {'cell': 'on0.8_L1_strong_harmful_d50_b0.1_s0.1', 'best_safe': 'episode_front', 'cand_minus_best_safe': [-1.5265566588595904e-17, -2.954214071730701e-17, -9.889924598848003e-19], 'cand_minus_R_family': [0.09444499999999999, 0.08102206172563782, 0.10786793827436215], 'null_fp': 0.0, 'no_worse_than_best_safe': True}], neighbours_ok=False, repair=None, validation_uses=1

- `on0.8_L0.6_strong_harmful_d1_b0.05_s0.5` (axes removing: []): no single axis removes the failure; no mechanism candidates

- `on0.8_L0.6_strong_harmful_d1_b0.1_s0.5` (axes removing: []): no single axis removes the failure; no mechanism candidates

Stage-6 outcomes in cycle 1: 5 survivors reached validation; repair flags [False, False, False, None, None] (False = criteria
not met, None = ablation unavailable so the repair criterion could not be evaluated). No candidate repaired a
failure. Cycle-1 reclassified_development pairs: ['on0.8_L1_strong_harmful_d10_b0.05_s0.1|991567bb7ec8']. Survivors with no single removing axis
(6 of 11) got no mechanism candidates in cycle 1.

## 4. Cycle 2 results (Amendment 1)

## R_family kappa calibration (discovery null twins)

chosen kappa = 0.05 (calibrated=True, 80 distinct twins, seeds [0, 19])

| kappa | FP count | n | pooled any-FP rate |
|---|---|---|---|
| 0.5 | 1524 | 1600 | 0.953 |
| 0.3 | 1033 | 1600 | 0.646 |
| 0.2 | 650 | 1600 | 0.406 |
| 0.1 | 298 | 1600 | 0.186 |
| 0.05 | 115 | 1600 | 0.072 |
| 0.02 | 37 | 1600 | 0.023 |
| 0.01 | 18 | 1600 | 0.011 |

Recalibrated kappa = 0.05 (same as cycle 1; calibrated = True).

## Discovery counts by class (stage 1)

| class | cells |
|---|---|
| headroom_not_shared | 1 |
| no_headroom | 215 |
| reference_unsafe | 21 |
| shared_failure | 123 |
| total | 360 |

## Class transitions: previous cycle (rows) -> this cycle (columns)

| prev \ now | headroom_not_shared | info_limited | no_headroom | reference_unsafe | shared_failure | total |
|---|---|---|---|---|---|---|
| headroom_not_shared | 1 | 0 | 0 | 0 | 1 | 2 |
| info_limited | 0 | 0 | 33 | 1 | 23 | 57 |
| no_headroom | 0 | 0 | 182 | 0 | 7 | 189 |
| reference_unsafe | 0 | 0 | 0 | 20 | 0 | 20 |
| shared_failure | 0 | 0 | 0 | 0 | 92 | 92 |

Previous-cycle class counts recomputed from its archive: headroom_not_shared=2, info_limited=57, no_headroom=189, reference_unsafe=20, shared_failure=92 (total 360)

### Cells entering or leaving shared_failure

| cell | previous | now | H (now) |
|---|---|---|---|
| on0.1_L0.15_strong_harmful_d1_b0.25_s0.5 | info_limited | shared_failure | +0.0644 |
| on0.1_L0.3_strong_harmful_d10_b0.05_s0.5 | info_limited | shared_failure | +0.0431 |
| on0.1_L0.3_strong_harmful_d1_b0.05_s0.1 | info_limited | shared_failure | +0.0489 |
| on0.1_L0.3_strong_harmful_d1_b0.05_s0.5 | info_limited | shared_failure | +0.0374 |
| on0.1_L0.3_strong_harmful_d1_b0.1_s0.1 | info_limited | shared_failure | +0.0784 |
| on0.1_L0.3_strong_harmful_d1_b0.1_s0.5 | info_limited | shared_failure | +0.1062 |
| on0.1_L0.6_strong_harmful_d10_b0.05_s0.5 | no_headroom | shared_failure | +0.0491 |
| on0.1_L0.6_strong_harmful_d10_b0.25_s0.1 | headroom_not_shared | shared_failure | +0.1050 |
| on0.1_L0.6_strong_harmful_d50_b0.1_s0.5 | no_headroom | shared_failure | +0.0898 |
| on0.1_L0.6_strong_harmful_d50_b0.25_s0.1 | no_headroom | shared_failure | +0.0780 |
| on0.1_L1_strong_harmful_d1_b0.25_s0.05 | no_headroom | shared_failure | +0.0522 |
| on0.3_L0.15_strong_harmful_d1_b0.1_s0.5 | info_limited | shared_failure | +0.0739 |
| on0.3_L0.15_strong_harmful_d1_b0.25_s0.5 | info_limited | shared_failure | +0.0845 |
| on0.3_L0.3_medium_harmful_d10_b0.25_s0.5 | info_limited | shared_failure | +0.0518 |
| on0.3_L0.3_medium_harmful_d1_b0.25_s0.05 | info_limited | shared_failure | +0.0641 |
| on0.3_L0.3_strong_harmful_d10_b0.05_s0.1 | info_limited | shared_failure | +0.1240 |
| on0.3_L0.3_strong_harmful_d10_b0.05_s0.5 | info_limited | shared_failure | +0.0920 |
| on0.3_L0.3_strong_harmful_d10_b0.1_s0.5 | info_limited | shared_failure | +0.1451 |
| on0.3_L0.3_strong_harmful_d1_b0.25_s0.5 | info_limited | shared_failure | +0.1128 |
| on0.3_L0.6_medium_harmful_d10_b0.1_s0.1 | no_headroom | shared_failure | +0.0569 |
| on0.6_L0.15_strong_harmful_d10_b0.05_s0.05 | info_limited | shared_failure | +0.0261 |
| on0.6_L0.15_strong_harmful_d10_b0.05_s0.1 | info_limited | shared_failure | +0.0346 |
| on0.6_L0.15_strong_harmful_d10_b0.1_s0.05 | info_limited | shared_failure | +0.0711 |
| on0.6_L0.15_strong_harmful_d10_b0.25_s0.1 | info_limited | shared_failure | +0.0808 |
| on0.6_L0.15_strong_harmful_d1_b0.05_s0.1 | info_limited | shared_failure | +0.0455 |
| on0.6_L0.15_strong_harmful_d1_b0.05_s0.5 | info_limited | shared_failure | +0.0436 |
| on0.6_L0.15_strong_harmful_d1_b0.1_s0.1 | info_limited | shared_failure | +0.0772 |
| on0.6_L0.15_strong_harmful_d1_b0.25_s0.5 | info_limited | shared_failure | +0.0810 |
| on0.6_L0.15_strong_harmful_d50_b0.25_s0.1 | info_limited | shared_failure | +0.0210 |
| on0.6_L0.6_medium_harmful_d50_b0.25_s0.1 | no_headroom | shared_failure | +0.0397 |
| on0.6_L1_medium_harmful_d50_b0.25_s0.5 | no_headroom | shared_failure | +0.0433 |

## Reproduced failures (stage 2, fresh discovery seeds)

| cell | label | severity | H [95% CI] | best_safe | R_family null FP [Wilson] |
|---|---|---|---|---|---|
| on0.3_L0.6_strong_harmful_d10_b0.05_s0.1 | shared_failure | 0.1965 | +0.1965 [+0.1781, +0.2150] | episode_front | 0.130 [0.078,0.210] |
| on0.6_L1_strong_harmful_d10_b0.05_s0.1 | shared_failure | 0.1937 | +0.1937 [+0.1831, +0.2044] | allonset_edetector | 0.130 [0.078,0.210] |
| on0.3_L0.6_strong_harmful_d10_b0.05_s0.5 | shared_failure | 0.2139 | +0.2139 [+0.1943, +0.2334] | episode_front | 0.090 [0.048,0.162] |
| on0.3_L0.6_strong_harmful_d10_b0.1_s0.1 | shared_failure | 0.1822 | +0.1822 [+0.1658, +0.1986] | episode_front | 0.090 [0.048,0.162] |
| on0.8_L1_strong_harmful_d10_b0.05_s0.1 | shared_failure | 0.1064 | +0.1064 [+0.1008, +0.1121] | c1_hmm_cs | 0.130 [0.078,0.210] |
| on0.8_L1_strong_harmful_d10_b0.1_s0.1 | shared_failure | 0.1104 | +0.1104 [+0.1054, +0.1154] | episode_front | 0.090 [0.048,0.162] |
| on0.6_L1_strong_harmful_d10_b0.1_s0.1 | shared_failure | 0.1334 | +0.1334 [+0.1264, +0.1404] | allonset_edetector | 0.090 [0.048,0.162] |
| on0.8_L0.6_strong_harmful_d1_b0.05_s0.1 | shared_failure | 0.1119 | +0.1119 [+0.1053, +0.1185] | c1_hmm_cs | 0.070 [0.034,0.137] |
| on0.6_L1_strong_harmful_d50_b0.1_s0.1 | shared_failure | 0.1146 | +0.1146 [+0.1083, +0.1208] | allonset_edetector | 0.110 [0.063,0.186] |
| on0.8_L0.6_strong_harmful_d1_b0.05_s0.5 | shared_failure | 0.1100 | +0.1100 [+0.1035, +0.1166] | no_switch | 0.090 [0.048,0.162] |
| on0.6_L0.6_strong_harmful_d1_b0.05_s0.1 | shared_failure | 0.1903 | +0.1903 [+0.1790, +0.2017] | allonset_edetector | 0.070 [0.034,0.137] |
| on0.6_L1_strong_harmful_d50_b0.05_s0.1 | shared_failure | 0.1582 | +0.1582 [+0.1444, +0.1719] | allonset_edetector | 0.110 [0.063,0.186] |

### Per-baseline gap to R_family (mean, lower CI bound; cost per round)

| cell | episode_geo | episode_equal | episode_front | allonset_edetector | c2_rho0.75 | c1_hmm_cs | no_switch |
|---|---|---|---|---|---|---|---|
| on0.3_L0.6_strong_harmful_d10_b0.05_s0.1 | +0.227 (+0.208) | +0.313 (+0.292) | +0.197 (+0.178) | +0.218 (+0.199) | +0.266 (+0.243) | +0.326 (+0.305) | +0.325 (+0.304) |
| on0.6_L1_strong_harmful_d10_b0.05_s0.1 | +0.211 (+0.200) | +0.231 (+0.220) | +0.198 (+0.187) | +0.194 (+0.183) | +0.228 (+0.216) | +0.231 (+0.220) | +0.231 (+0.220) |
| on0.3_L0.6_strong_harmful_d10_b0.05_s0.5 | +0.246 (+0.227) | +0.331 (+0.313) | +0.214 (+0.194) | +0.231 (+0.213) | +0.285 (+0.265) | +0.340 (+0.322) | +0.339 (+0.322) |
| on0.3_L0.6_strong_harmful_d10_b0.1_s0.1 | +0.197 (+0.182) | +0.293 (+0.278) | +0.182 (+0.166) | +0.190 (+0.180) | +0.237 (+0.220) | +0.334 (+0.324) | +0.405 (+0.398) |
| on0.8_L1_strong_harmful_d10_b0.05_s0.1 | +0.109 (+0.103) | +0.109 (+0.103) | +0.109 (+0.103) | +0.109 (+0.103) | +0.109 (+0.103) | +0.106 (+0.101) | +0.108 (+0.103) |
| on0.8_L1_strong_harmful_d10_b0.1_s0.1 | +0.114 (+0.109) | +0.119 (+0.113) | +0.110 (+0.105) | +0.112 (+0.107) | +0.118 (+0.112) | +0.111 (+0.105) | +0.118 (+0.112) |
| on0.6_L1_strong_harmful_d10_b0.1_s0.1 | +0.165 (+0.154) | +0.238 (+0.231) | +0.146 (+0.135) | +0.133 (+0.126) | +0.212 (+0.202) | +0.256 (+0.250) | +0.275 (+0.269) |
| on0.8_L0.6_strong_harmful_d1_b0.05_s0.1 | +0.113 (+0.106) | +0.113 (+0.106) | +0.113 (+0.106) | +0.113 (+0.106) | +0.113 (+0.106) | +0.112 (+0.105) | +0.112 (+0.106) |
| on0.6_L1_strong_harmful_d50_b0.1_s0.1 | +0.138 (+0.130) | +0.213 (+0.206) | +0.121 (+0.113) | +0.115 (+0.108) | +0.189 (+0.179) | +0.242 (+0.235) | +0.242 (+0.235) |
| on0.8_L0.6_strong_harmful_d1_b0.05_s0.5 | +0.111 (+0.104) | +0.111 (+0.104) | +0.111 (+0.104) | +0.111 (+0.104) | +0.110 (+0.104) | +0.110 (+0.104) | +0.110 (+0.103) |
| on0.6_L0.6_strong_harmful_d1_b0.05_s0.1 | +0.206 (+0.195) | +0.236 (+0.223) | +0.195 (+0.184) | +0.190 (+0.179) | +0.231 (+0.219) | +0.236 (+0.224) | +0.235 (+0.223) |
| on0.6_L1_strong_harmful_d50_b0.05_s0.1 | +0.171 (+0.158) | +0.186 (+0.171) | +0.160 (+0.146) | +0.158 (+0.144) | +0.184 (+0.169) | +0.186 (+0.171) | +0.185 (+0.171) |

## Diagnostic decomposition (stage 2b; evaluator-side, descriptive, 100 seeds)

Cost is per round. `front` = `episode_front`, the decision rule shared by the `diag_oracle_*` variants (oracle: onset and/or Kelly stake given by the evaluator; never methods). Parts: onset = front - known_onset; stake = front - known_stake; interaction = (front - known_both) - onset - stake; residual = known_both - R_family; gap = best_safe - R_family = (best_safe - front) + onset + stake + interaction + residual. Brackets are paired 95% CIs.

| cell | best_safe | Kelly stake | gap | best_safe-front | onset | stake | interaction | residual |
|---|---|---|---|---|---|---|---|---|
| on0.3_L0.6_strong_harmful_d10_b0.05_s0.1 | episode_front | 0.778 | +0.2012 [+0.1782, +0.2243] | +0.0000 [+0.0000, +0.0000] | +0.0992 [+0.0861, +0.1123] | +0.0562 [+0.0479, +0.0644] | -0.0023 [-0.0149, +0.0103] | +0.0482 [+0.0279, +0.0684] |
| on0.6_L1_strong_harmful_d10_b0.05_s0.1 | allonset_edetector | 0.778 | +0.1878 [+0.1775, +0.1981] | -0.0039 [-0.0066, -0.0013] | +0.0745 [+0.0646, +0.0845] | +0.0396 [+0.0327, +0.0465] | +0.0185 [+0.0063, +0.0307] | +0.0591 [+0.0429, +0.0753] |
| on0.3_L0.6_strong_harmful_d10_b0.05_s0.5 | episode_front | 0.778 | +0.2102 [+0.1914, +0.2291] | +0.0000 [+0.0000, +0.0000] | +0.0971 [+0.0841, +0.1102] | +0.0578 [+0.0488, +0.0668] | -0.0080 [-0.0232, +0.0071] | +0.0633 [+0.0427, +0.0840] |
| on0.3_L0.6_strong_harmful_d10_b0.1_s0.1 | allonset_edetector | 0.778 | +0.1843 [+0.1768, +0.1917] | -0.0049 [-0.0200, +0.0101] | +0.0754 [+0.0542, +0.0965] | +0.0387 [+0.0238, +0.0537] | +0.0027 [-0.0236, +0.0290] | +0.0724 [+0.0562, +0.0886] |
| on0.8_L1_strong_harmful_d10_b0.05_s0.1 | c1_hmm_cs | 0.778 | +0.1072 [+0.1015, +0.1128] | -0.0019 [-0.0030, -0.0008] | +0.0114 [+0.0074, +0.0155] | +0.0009 [+0.0001, +0.0017] | +0.0269 [+0.0222, +0.0315] | +0.0698 [+0.0629, +0.0767] |
| on0.8_L1_strong_harmful_d10_b0.1_s0.1 | episode_front | 0.778 | +0.1146 [+0.1105, +0.1187] | +0.0000 [+0.0000, +0.0000] | +0.0479 [+0.0417, +0.0540] | +0.0159 [+0.0122, +0.0196] | +0.0121 [+0.0057, +0.0185] | +0.0388 [+0.0324, +0.0452] |
| on0.6_L1_strong_harmful_d10_b0.1_s0.1 | allonset_edetector | 0.778 | +0.1252 [+0.1182, +0.1322] | -0.0193 [-0.0284, -0.0103] | +0.0769 [+0.0638, +0.0899] | +0.0390 [+0.0292, +0.0489] | -0.0053 [-0.0222, +0.0117] | +0.0339 [+0.0229, +0.0449] |
| on0.8_L0.6_strong_harmful_d1_b0.05_s0.1 | no_switch | 0.778 | +0.1149 [+0.1088, +0.1211] | -0.0005 [-0.0005, -0.0005] | +0.0183 [+0.0135, +0.0231] | +0.0021 [+0.0008, +0.0034] | +0.0342 [+0.0292, +0.0391] | +0.0608 [+0.0540, +0.0677] |
| on0.6_L1_strong_harmful_d50_b0.1_s0.1 | allonset_edetector | 0.778 | +0.1249 [+0.1179, +0.1318] | -0.0092 [-0.0140, -0.0045] | +0.0703 [+0.0614, +0.0791] | +0.0320 [+0.0254, +0.0386] | -0.0072 [-0.0201, +0.0058] | +0.0390 [+0.0296, +0.0485] |
| on0.8_L0.6_strong_harmful_d1_b0.05_s0.5 | c1_hmm_cs | 0.778 | +0.1065 [+0.0988, +0.1142] | -0.0006 [-0.0016, +0.0004] | +0.0182 [+0.0130, +0.0233] | +0.0024 [+0.0010, +0.0039] | +0.0257 [+0.0208, +0.0307] | +0.0608 [+0.0532, +0.0683] |
| on0.6_L0.6_strong_harmful_d1_b0.05_s0.1 | allonset_edetector | 0.778 | +0.1967 [+0.1860, +0.2074] | -0.0040 [-0.0071, -0.0008] | +0.0866 [+0.0746, +0.0986] | +0.0456 [+0.0375, +0.0536] | +0.0024 [-0.0083, +0.0131] | +0.0661 [+0.0508, +0.0814] |
| on0.6_L1_strong_harmful_d50_b0.05_s0.1 | episode_front | 0.778 | +0.1572 [+0.1443, +0.1702] | +0.0000 [+0.0000, +0.0000] | +0.0643 [+0.0565, +0.0720] | +0.0312 [+0.0257, +0.0367] | +0.0235 [+0.0132, +0.0338] | +0.0383 [+0.0240, +0.0526] |

### Per-baseline exposure (log(1/alpha) = 2.303)

| cell | method | cost | labels from favourable state | frac promoted | mean first-promotion round | final log e (episode 0) | analytic labels needed |
|---|---|---|---|---|---|---|---|
| on0.3_L0.6_strong_harmful_d10_b0.05_s0.1 | episode_geo | 0.4910 | 30.3 | 0.91 | 717 | +2.91 | 29.1 |
| on0.3_L0.6_strong_harmful_d10_b0.05_s0.1 | episode_equal | 0.5726 | 30.3 | 0.37 | 813 | +2.94 | 40.2 |
| on0.3_L0.6_strong_harmful_d10_b0.05_s0.1 | episode_front | 0.4618 | 30.3 | 0.95 | 683 | +2.40 | 26.8 |
| on0.3_L0.6_strong_harmful_d10_b0.05_s0.1 | allonset_edetector | 0.4786 | 30.3 | 0.98 | 664 | +2.19 | 26.0 |
| on0.3_L0.6_strong_harmful_d10_b0.05_s0.1 | c2_rho0.75 | 0.5193 | 24.0 | 0.77 | 757 | +2.43 | 28.1 |
| on0.3_L0.6_strong_harmful_d10_b0.05_s0.1 | c1_hmm_cs | 0.5820 | 31.1 | 0.00 | none | - | - |
| on0.3_L0.6_strong_harmful_d10_b0.05_s0.1 | no_switch | 0.5815 | 0.0 | 0.00 | none | - | - |
| on0.3_L0.6_strong_harmful_d10_b0.05_s0.1 | diag_oracle_known_onset | 0.3627 | 30.3 | 0.98 | 557 | +2.50 | - |
| on0.3_L0.6_strong_harmful_d10_b0.05_s0.1 | diag_oracle_known_stake | 0.4057 | 30.3 | 0.98 | 606 | +2.44 | - |
| on0.3_L0.6_strong_harmful_d10_b0.05_s0.1 | diag_oracle_known_both | 0.3088 | 30.3 | 0.98 | 470 | +2.40 | - |
| on0.6_L1_strong_harmful_d10_b0.05_s0.1 | episode_geo | 0.3922 | 19.9 | 0.46 | 931 | +2.24 | 29.1 |
| on0.6_L1_strong_harmful_d10_b0.05_s0.1 | episode_equal | 0.4166 | 19.9 | 0.04 | 995 | +2.73 | 40.2 |
| on0.6_L1_strong_harmful_d10_b0.05_s0.1 | episode_front | 0.3788 | 19.9 | 0.60 | 919 | +1.96 | 26.8 |
| on0.6_L1_strong_harmful_d10_b0.05_s0.1 | allonset_edetector | 0.3749 | 19.9 | 0.71 | 926 | +2.77 | 26.0 |
| on0.6_L1_strong_harmful_d10_b0.05_s0.1 | c2_rho0.75 | 0.4158 | 14.8 | 0.03 | 960 | +1.35 | 28.1 |
| on0.6_L1_strong_harmful_d10_b0.05_s0.1 | c1_hmm_cs | 0.4168 | 26.3 | 0.00 | none | - | - |
| on0.6_L1_strong_harmful_d10_b0.05_s0.1 | no_switch | 0.4163 | 0.0 | 0.00 | none | - | - |
| on0.6_L1_strong_harmful_d10_b0.05_s0.1 | diag_oracle_known_onset | 0.3043 | 19.9 | 0.91 | 838 | +2.48 | - |
| on0.6_L1_strong_harmful_d10_b0.05_s0.1 | diag_oracle_known_stake | 0.3392 | 19.9 | 0.80 | 872 | +2.20 | - |
| on0.6_L1_strong_harmful_d10_b0.05_s0.1 | diag_oracle_known_both | 0.2461 | 19.9 | 0.96 | 763 | +2.53 | - |
| on0.3_L0.6_strong_harmful_d10_b0.05_s0.5 | episode_geo | 0.4828 | 30.3 | 0.86 | 699 | +2.79 | 29.1 |
| on0.3_L0.6_strong_harmful_d10_b0.05_s0.5 | episode_equal | 0.5689 | 30.3 | 0.51 | 816 | +3.63 | 40.2 |
| on0.3_L0.6_strong_harmful_d10_b0.05_s0.5 | episode_front | 0.4540 | 30.3 | 0.93 | 672 | +2.36 | 26.8 |
| on0.3_L0.6_strong_harmful_d10_b0.05_s0.5 | allonset_edetector | 0.4732 | 30.3 | 0.98 | 663 | +2.28 | 26.0 |
| on0.3_L0.6_strong_harmful_d10_b0.05_s0.5 | c2_rho0.75 | 0.5106 | 23.8 | 0.74 | 738 | +2.37 | 28.1 |
| on0.3_L0.6_strong_harmful_d10_b0.05_s0.5 | c1_hmm_cs | 0.5815 | 30.4 | 0.00 | none | - | - |
| on0.3_L0.6_strong_harmful_d10_b0.05_s0.5 | no_switch | 0.5810 | 0.0 | 0.00 | none | - | - |
| on0.3_L0.6_strong_harmful_d10_b0.05_s0.5 | diag_oracle_known_onset | 0.3568 | 30.3 | 0.98 | 547 | +2.54 | - |
| on0.3_L0.6_strong_harmful_d10_b0.05_s0.5 | diag_oracle_known_stake | 0.3962 | 30.3 | 0.98 | 606 | +2.41 | - |
| on0.3_L0.6_strong_harmful_d10_b0.05_s0.5 | diag_oracle_known_both | 0.3071 | 30.3 | 0.98 | 470 | +2.47 | - |
| on0.3_L0.6_strong_harmful_d10_b0.1_s0.1 | episode_geo | 0.3837 | 60.6 | 0.99 | 570 | +3.17 | 27.8 |
| on0.3_L0.6_strong_harmful_d10_b0.1_s0.1 | episode_equal | 0.4822 | 60.6 | 0.91 | 699 | +6.63 | 41.2 |
| on0.3_L0.6_strong_harmful_d10_b0.1_s0.1 | episode_front | 0.3629 | 60.6 | 0.99 | 534 | +2.47 | 25.5 |
| on0.3_L0.6_strong_harmful_d10_b0.1_s0.1 | allonset_edetector | 0.3580 | 60.6 | 1.00 | 522 | +5.62 | 28.9 |
| on0.3_L0.6_strong_harmful_d10_b0.1_s0.1 | c2_rho0.75 | 0.4114 | 44.5 | 0.97 | 615 | +3.13 | 28.2 |
| on0.3_L0.6_strong_harmful_d10_b0.1_s0.1 | c1_hmm_cs | 0.5138 | 63.5 | 0.97 | 767 | - | - |
| on0.3_L0.6_strong_harmful_d10_b0.1_s0.1 | no_switch | 0.5801 | 0.0 | 0.00 | none | - | - |
| on0.3_L0.6_strong_harmful_d10_b0.1_s0.1 | diag_oracle_known_onset | 0.2876 | 60.6 | 1.00 | 431 | +2.56 | - |
| on0.3_L0.6_strong_harmful_d10_b0.1_s0.1 | diag_oracle_known_stake | 0.3242 | 60.6 | 1.00 | 492 | +2.57 | - |
| on0.3_L0.6_strong_harmful_d10_b0.1_s0.1 | diag_oracle_known_both | 0.2461 | 60.6 | 1.00 | 393 | +2.61 | - |
| on0.8_L1_strong_harmful_d10_b0.05_s0.1 | episode_geo | 0.2614 | 10.1 | 0.00 | none | +0.15 | 29.1 |
| on0.8_L1_strong_harmful_d10_b0.05_s0.1 | episode_equal | 0.2614 | 10.1 | 0.00 | none | +0.15 | 40.2 |
| on0.8_L1_strong_harmful_d10_b0.05_s0.1 | episode_front | 0.2614 | 10.1 | 0.00 | none | +0.15 | 26.8 |
| on0.8_L1_strong_harmful_d10_b0.05_s0.1 | allonset_edetector | 0.2614 | 10.1 | 0.00 | none | +0.24 | 26.0 |
| on0.8_L1_strong_harmful_d10_b0.05_s0.1 | c2_rho0.75 | 0.2612 | 7.2 | 0.00 | none | -0.24 | 28.1 |
| on0.8_L1_strong_harmful_d10_b0.05_s0.1 | c1_hmm_cs | 0.2595 | 20.5 | 0.14 | 983 | - | - |
| on0.8_L1_strong_harmful_d10_b0.05_s0.1 | no_switch | 0.2609 | 0.0 | 0.00 | none | - | - |
| on0.8_L1_strong_harmful_d10_b0.05_s0.1 | diag_oracle_known_onset | 0.2499 | 10.1 | 0.44 | 967 | +1.82 | - |
| on0.8_L1_strong_harmful_d10_b0.05_s0.1 | diag_oracle_known_stake | 0.2605 | 10.1 | 0.11 | 990 | +0.58 | - |
| on0.8_L1_strong_harmful_d10_b0.05_s0.1 | diag_oracle_known_both | 0.2221 | 10.1 | 0.71 | 931 | +1.98 | - |
| on0.8_L1_strong_harmful_d10_b0.1_s0.1 | episode_geo | 0.2534 | 19.8 | 0.30 | 972 | +1.61 | 27.8 |
| on0.8_L1_strong_harmful_d10_b0.1_s0.1 | episode_equal | 0.2604 | 19.8 | 0.00 | none | +1.82 | 41.2 |
| on0.8_L1_strong_harmful_d10_b0.1_s0.1 | episode_front | 0.2487 | 19.8 | 0.42 | 965 | +1.42 | 25.5 |
| on0.8_L1_strong_harmful_d10_b0.1_s0.1 | allonset_edetector | 0.2502 | 19.8 | 0.43 | 971 | +1.93 | 28.9 |
| on0.8_L1_strong_harmful_d10_b0.1_s0.1 | c2_rho0.75 | 0.2586 | 15.4 | 0.10 | 983 | +0.85 | 28.2 |
| on0.8_L1_strong_harmful_d10_b0.1_s0.1 | c1_hmm_cs | 0.2502 | 26.2 | 0.57 | 978 | - | - |
| on0.8_L1_strong_harmful_d10_b0.1_s0.1 | no_switch | 0.2594 | 0.0 | 0.00 | none | - | - |
| on0.8_L1_strong_harmful_d10_b0.1_s0.1 | diag_oracle_known_onset | 0.2008 | 19.8 | 0.86 | 910 | +2.44 | - |
| on0.8_L1_strong_harmful_d10_b0.1_s0.1 | diag_oracle_known_stake | 0.2328 | 19.8 | 0.69 | 950 | +1.94 | - |
| on0.8_L1_strong_harmful_d10_b0.1_s0.1 | diag_oracle_known_both | 0.1729 | 19.8 | 0.94 | 877 | +2.49 | - |
| on0.6_L1_strong_harmful_d10_b0.1_s0.1 | episode_geo | 0.3070 | 40.0 | 0.91 | 836 | +3.10 | 27.8 |
| on0.6_L1_strong_harmful_d10_b0.1_s0.1 | episode_equal | 0.3814 | 40.0 | 0.61 | 911 | +5.85 | 41.2 |
| on0.6_L1_strong_harmful_d10_b0.1_s0.1 | episode_front | 0.2927 | 40.0 | 0.96 | 820 | +2.44 | 25.5 |
| on0.6_L1_strong_harmful_d10_b0.1_s0.1 | allonset_edetector | 0.2734 | 40.0 | 1.00 | 816 | +6.81 | 28.9 |
| on0.6_L1_strong_harmful_d10_b0.1_s0.1 | c2_rho0.75 | 0.3619 | 41.5 | 0.80 | 879 | +2.86 | 28.2 |
| on0.6_L1_strong_harmful_d10_b0.1_s0.1 | c1_hmm_cs | 0.4019 | 49.0 | 0.98 | 974 | - | - |
| on0.6_L1_strong_harmful_d10_b0.1_s0.1 | no_switch | 0.4214 | 0.0 | 0.00 | none | - | - |
| on0.6_L1_strong_harmful_d10_b0.1_s0.1 | diag_oracle_known_onset | 0.2158 | 40.0 | 1.00 | 725 | +2.59 | - |
| on0.6_L1_strong_harmful_d10_b0.1_s0.1 | diag_oracle_known_stake | 0.2537 | 40.0 | 0.98 | 780 | +2.56 | - |
| on0.6_L1_strong_harmful_d10_b0.1_s0.1 | diag_oracle_known_both | 0.1821 | 40.0 | 1.00 | 686 | +2.60 | - |
| on0.8_L0.6_strong_harmful_d1_b0.05_s0.1 | episode_geo | 0.2648 | 10.7 | 0.00 | none | +0.41 | 29.1 |
| on0.8_L0.6_strong_harmful_d1_b0.05_s0.1 | episode_equal | 0.2648 | 10.7 | 0.00 | none | +0.41 | 40.2 |
| on0.8_L0.6_strong_harmful_d1_b0.05_s0.1 | episode_front | 0.2648 | 10.7 | 0.00 | none | +0.41 | 26.8 |
| on0.8_L0.6_strong_harmful_d1_b0.05_s0.1 | allonset_edetector | 0.2648 | 10.7 | 0.00 | none | +0.51 | 26.0 |
| on0.8_L0.6_strong_harmful_d1_b0.05_s0.1 | c2_rho0.75 | 0.2646 | 7.6 | 0.00 | none | -0.05 | 28.1 |
| on0.8_L0.6_strong_harmful_d1_b0.05_s0.1 | c1_hmm_cs | 0.2647 | 25.6 | 0.03 | 997 | - | - |
| on0.8_L0.6_strong_harmful_d1_b0.05_s0.1 | no_switch | 0.2643 | 0.0 | 0.00 | none | - | - |
| on0.8_L0.6_strong_harmful_d1_b0.05_s0.1 | diag_oracle_known_onset | 0.2465 | 10.7 | 0.55 | 959 | +2.03 | - |
| on0.8_L0.6_strong_harmful_d1_b0.05_s0.1 | diag_oracle_known_stake | 0.2626 | 10.7 | 0.20 | 988 | +0.96 | - |
| on0.8_L0.6_strong_harmful_d1_b0.05_s0.1 | diag_oracle_known_both | 0.2102 | 10.7 | 0.84 | 918 | +2.31 | - |
| on0.6_L1_strong_harmful_d50_b0.1_s0.1 | episode_geo | 0.3257 | 37.4 | 0.90 | 866 | +3.07 | 27.8 |
| on0.6_L1_strong_harmful_d50_b0.1_s0.1 | episode_equal | 0.3952 | 37.4 | 0.51 | 933 | +5.68 | 41.2 |
| on0.6_L1_strong_harmful_d50_b0.1_s0.1 | episode_front | 0.3099 | 37.4 | 0.97 | 852 | +2.45 | 25.5 |
| on0.6_L1_strong_harmful_d50_b0.1_s0.1 | allonset_edetector | 0.3007 | 37.4 | 1.00 | 850 | +6.21 | 28.9 |
| on0.6_L1_strong_harmful_d50_b0.1_s0.1 | c2_rho0.75 | 0.3661 | 39.3 | 0.77 | 894 | +2.86 | 28.2 |
| on0.6_L1_strong_harmful_d50_b0.1_s0.1 | c1_hmm_cs | 0.4217 | 12.0 | 0.00 | none | - | - |
| on0.6_L1_strong_harmful_d50_b0.1_s0.1 | no_switch | 0.4214 | 0.0 | 0.00 | none | - | - |
| on0.6_L1_strong_harmful_d50_b0.1_s0.1 | diag_oracle_known_onset | 0.2397 | 37.4 | 1.00 | 770 | +2.58 | - |
| on0.6_L1_strong_harmful_d50_b0.1_s0.1 | diag_oracle_known_stake | 0.2779 | 37.4 | 0.99 | 816 | +2.58 | - |
| on0.6_L1_strong_harmful_d50_b0.1_s0.1 | diag_oracle_known_both | 0.2148 | 37.4 | 1.00 | 734 | +2.59 | - |
| on0.8_L0.6_strong_harmful_d1_b0.05_s0.5 | episode_geo | 0.2613 | 10.5 | 0.00 | none | +0.29 | 29.1 |
| on0.8_L0.6_strong_harmful_d1_b0.05_s0.5 | episode_equal | 0.2613 | 10.5 | 0.00 | none | +0.29 | 40.2 |
| on0.8_L0.6_strong_harmful_d1_b0.05_s0.5 | episode_front | 0.2613 | 10.5 | 0.01 | 1000 | +0.29 | 26.8 |
| on0.8_L0.6_strong_harmful_d1_b0.05_s0.5 | allonset_edetector | 0.2613 | 10.5 | 0.01 | 1000 | +0.38 | 26.0 |
| on0.8_L0.6_strong_harmful_d1_b0.05_s0.5 | c2_rho0.75 | 0.2612 | 7.5 | 0.00 | none | -0.08 | 28.1 |
| on0.8_L0.6_strong_harmful_d1_b0.05_s0.5 | c1_hmm_cs | 0.2608 | 25.3 | 0.02 | 969 | - | - |
| on0.8_L0.6_strong_harmful_d1_b0.05_s0.5 | no_switch | 0.2608 | 0.0 | 0.00 | none | - | - |
| on0.8_L0.6_strong_harmful_d1_b0.05_s0.5 | diag_oracle_known_onset | 0.2432 | 10.5 | 0.51 | 954 | +1.92 | - |
| on0.8_L0.6_strong_harmful_d1_b0.05_s0.5 | diag_oracle_known_stake | 0.2589 | 10.5 | 0.17 | 980 | +0.78 | - |
| on0.8_L0.6_strong_harmful_d1_b0.05_s0.5 | diag_oracle_known_both | 0.2150 | 10.5 | 0.69 | 915 | +2.03 | - |
| on0.6_L0.6_strong_harmful_d1_b0.05_s0.1 | episode_geo | 0.3975 | 20.6 | 0.55 | 945 | +2.24 | 29.1 |
| on0.6_L0.6_strong_harmful_d1_b0.05_s0.1 | episode_equal | 0.4215 | 20.6 | 0.02 | 990 | +2.62 | 40.2 |
| on0.6_L0.6_strong_harmful_d1_b0.05_s0.1 | episode_front | 0.3820 | 20.6 | 0.65 | 923 | +1.91 | 26.8 |
| on0.6_L0.6_strong_harmful_d1_b0.05_s0.1 | allonset_edetector | 0.3780 | 20.6 | 0.69 | 922 | +2.71 | 26.0 |
| on0.6_L0.6_strong_harmful_d1_b0.05_s0.1 | c2_rho0.75 | 0.4162 | 17.1 | 0.19 | 961 | +1.69 | 28.1 |
| on0.6_L0.6_strong_harmful_d1_b0.05_s0.1 | c1_hmm_cs | 0.4217 | 29.4 | 0.01 | 999 | - | - |
| on0.6_L0.6_strong_harmful_d1_b0.05_s0.1 | no_switch | 0.4212 | 0.0 | 0.00 | none | - | - |
| on0.6_L0.6_strong_harmful_d1_b0.05_s0.1 | diag_oracle_known_onset | 0.2954 | 20.6 | 0.84 | 809 | +2.41 | - |
| on0.6_L0.6_strong_harmful_d1_b0.05_s0.1 | diag_oracle_known_stake | 0.3364 | 20.6 | 0.80 | 861 | +2.16 | - |
| on0.6_L0.6_strong_harmful_d1_b0.05_s0.1 | diag_oracle_known_both | 0.2474 | 20.6 | 0.94 | 754 | +2.45 | - |
| on0.6_L1_strong_harmful_d50_b0.05_s0.1 | episode_geo | 0.3982 | 18.7 | 0.44 | 944 | +2.07 | 29.1 |
| on0.6_L1_strong_harmful_d50_b0.05_s0.1 | episode_equal | 0.4181 | 18.7 | 0.01 | 1000 | +2.50 | 40.2 |
| on0.6_L1_strong_harmful_d50_b0.05_s0.1 | episode_front | 0.3855 | 18.7 | 0.53 | 924 | +1.81 | 26.8 |
| on0.6_L1_strong_harmful_d50_b0.05_s0.1 | allonset_edetector | 0.3859 | 18.7 | 0.58 | 932 | +2.50 | 26.0 |
| on0.6_L1_strong_harmful_d50_b0.05_s0.1 | c2_rho0.75 | 0.4165 | 13.7 | 0.07 | 976 | +1.41 | 28.1 |
| on0.6_L1_strong_harmful_d50_b0.05_s0.1 | c1_hmm_cs | 0.4179 | 11.3 | 0.00 | none | - | - |
| on0.6_L1_strong_harmful_d50_b0.05_s0.1 | no_switch | 0.4176 | 0.0 | 0.00 | none | - | - |
| on0.6_L1_strong_harmful_d50_b0.05_s0.1 | diag_oracle_known_onset | 0.3212 | 18.7 | 0.86 | 858 | +2.43 | - |
| on0.6_L1_strong_harmful_d50_b0.05_s0.1 | diag_oracle_known_stake | 0.3543 | 18.7 | 0.74 | 892 | +2.04 | - |
| on0.6_L1_strong_harmful_d50_b0.05_s0.1 | diag_oracle_known_both | 0.2665 | 18.7 | 0.93 | 791 | +2.42 | - |

## Isolation (stage 4): does moving one axis to its easiest level remove the failure?

| failure cell | onset | duration | effect | d | budget_frac | s |
|---|---|---|---|---|---|---|
| on0.3_L0.6_strong_harmful_d10_b0.05_s0.1 | keeps (H lo +0.045, shared_failure) | keeps (H lo +0.137, shared_failure) | at easiest | keeps (H lo +0.144, shared_failure) | keeps (H lo +0.102, shared_failure) | keeps (H lo +0.188, shared_failure) |
| on0.6_L1_strong_harmful_d10_b0.05_s0.1 | REMOVES (H lo -0.094, no_headroom) | at easiest | at easiest | keeps (H lo +0.147, shared_failure) | keeps (H lo +0.054, shared_failure) | keeps (H lo +0.173, shared_failure) |
| on0.3_L0.6_strong_harmful_d10_b0.05_s0.5 | keeps (H lo +0.032, shared_failure) | keeps (H lo +0.112, shared_failure) | at easiest | keeps (H lo +0.113, shared_failure) | keeps (H lo +0.089, shared_failure) | keeps (H lo +0.188, shared_failure) |
| on0.3_L0.6_strong_harmful_d10_b0.1_s0.1 | keeps (H lo +0.089, shared_failure) | keeps (H lo +0.099, shared_failure) | at easiest | keeps (H lo +0.145, shared_failure) | keeps (H lo +0.102, shared_failure) | keeps (H lo +0.137, shared_failure) |
| on0.8_L1_strong_harmful_d10_b0.05_s0.1 | REMOVES (H lo -0.094, no_headroom) | at easiest | at easiest | keeps (H lo +0.093, shared_failure) | keeps (H lo +0.063, shared_failure) | keeps (H lo +0.090, shared_failure) |
| on0.8_L1_strong_harmful_d10_b0.1_s0.1 | REMOVES (H lo +0.006, no_headroom) | at easiest | at easiest | keeps (H lo +0.097, shared_failure) | keeps (H lo +0.063, shared_failure) | keeps (H lo +0.108, shared_failure) |
| on0.6_L1_strong_harmful_d10_b0.1_s0.1 | REMOVES (H lo +0.006, no_headroom) | at easiest | at easiest | keeps (H lo +0.118, shared_failure) | keeps (H lo +0.054, shared_failure) | keeps (H lo +0.115, shared_failure) |
| on0.8_L0.6_strong_harmful_d1_b0.05_s0.1 | keeps (H lo +0.015, shared_failure) | keeps (H lo +0.093, shared_failure) | at easiest | at easiest | keeps (H lo +0.061, shared_failure) | keeps (H lo +0.106, shared_failure) |
| on0.6_L1_strong_harmful_d50_b0.1_s0.1 | REMOVES (H lo -0.032, no_headroom) | at easiest | at easiest | keeps (H lo +0.118, shared_failure) | keeps (H lo +0.053, shared_failure) | keeps (H lo +0.111, shared_failure) |
| on0.8_L0.6_strong_harmful_d1_b0.05_s0.5 | keeps (H lo +0.022, shared_failure) | keeps (H lo +0.101, shared_failure) | at easiest | at easiest | keeps (H lo +0.058, shared_failure) | keeps (H lo +0.106, shared_failure) |
| on0.6_L0.6_strong_harmful_d1_b0.05_s0.1 | keeps (H lo +0.015, shared_failure) | keeps (H lo +0.147, shared_failure) | at easiest | at easiest | keeps (H lo +0.046, shared_failure) | keeps (H lo +0.156, shared_failure) |
| on0.6_L1_strong_harmful_d50_b0.05_s0.1 | REMOVES (H lo -0.101, no_headroom) | at easiest | at easiest | keeps (H lo +0.147, shared_failure) | keeps (H lo +0.053, shared_failure) | keeps (H lo +0.129, shared_failure) |

## Candidate and repair table (stages 5-6)

| failure cell | axes removing | proposed/invalid | stage-6 candidate | val cost | gap closure | null FP | closes >=50% | ablation removes gain | neighbours ok | neighbour detail | repair | status | best dev candidate |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| on0.3_L0.6_strong_harmful_d10_b0.05_s0.1 | none | 23/0 | 891a240116da | 0.4055 | 0.29 | 0.00 | False | False | False | on0.1_L0.6_strong_harmful_d10_b0.05_s0.1: vs best_safe -0.009 [-0.067,+0.048], ok=False; on0.6_L0.6_strong_harmful_d10_b0.05_s0.1: vs best_safe -0.040 [-0.077,-0.002], ok=True | False |  | 891a240116da |
| on0.6_L1_strong_harmful_d10_b0.05_s0.1 | ['onset'] | 31/0 | bc27f3692d70 | 0.3463 | 0.15 | 0.00 | False | None | False | on0.3_L1_strong_harmful_d10_b0.05_s0.1: vs best_safe -0.015 [-0.048,+0.017], ok=False; on0.8_L1_strong_harmful_d10_b0.05_s0.1: vs best_safe -0.004 [-0.011,+0.003], ok=True | None |  | bc27f3692d70 |
| on0.3_L0.6_strong_harmful_d10_b0.05_s0.5 | none | 23/0 | b1a17927d9ad | 0.4435 | 0.28 | 0.00 | False | True | False | on0.1_L0.6_strong_harmful_d10_b0.05_s0.5: vs best_safe +0.041 [-0.016,+0.098], ok=False; on0.6_L0.6_strong_harmful_d10_b0.05_s0.5: vs best_safe -0.032 [-0.063,-0.001], ok=True | False |  | b1a17927d9ad |
| on0.3_L0.6_strong_harmful_d10_b0.1_s0.1 | none | 23/0 | 612b8e1a975e | 0.3699 | -0.09 | 0.00 | False | False | False | on0.1_L0.6_strong_harmful_d10_b0.1_s0.1: vs best_safe +0.058 [+0.013,+0.102], ok=False; on0.6_L0.6_strong_harmful_d10_b0.1_s0.1: vs best_safe +0.030 [-0.002,+0.063], ok=False | False |  | 612b8e1a975e |
| on0.8_L1_strong_harmful_d10_b0.05_s0.1 | ['onset'] | 31/0 | bc27f3692d70 | 0.2544 | 0.03 | 0.00 | False | None | True | on0.6_L1_strong_harmful_d10_b0.05_s0.1: vs best_safe -0.027 [-0.060,+0.006], ok=True | None | reclassified_development | bc27f3692d70 |
| on0.8_L1_strong_harmful_d10_b0.1_s0.1 | ['onset'] | 31/0 | 612b8e1a975e | 0.2369 | 0.12 | 0.00 | False | True | False | on0.6_L1_strong_harmful_d10_b0.1_s0.1: vs best_safe +0.008 [-0.027,+0.043], ok=False | False |  | 612b8e1a975e |
| on0.6_L1_strong_harmful_d10_b0.1_s0.1 | ['onset'] | 31/0 | 487ae8a2643f | 0.2799 | -0.01 | 0.00 | False | False | False | on0.3_L1_strong_harmful_d10_b0.1_s0.1: vs best_safe -0.001 [-0.013,+0.011], ok=False; on0.8_L1_strong_harmful_d10_b0.1_s0.1: vs best_safe -0.001 [-0.015,+0.012], ok=False | False |  | 487ae8a2643f |
| on0.8_L0.6_strong_harmful_d1_b0.05_s0.1 | none | 23/0 | b1a17927d9ad | 0.2454 | 0.21 | 0.00 | False | True | True | on0.6_L0.6_strong_harmful_d1_b0.05_s0.1: vs best_safe -0.088 [-0.130,-0.045], ok=True; on0.8_L0.3_strong_harmful_d1_b0.05_s0.1: vs best_safe -0.019 [-0.034,-0.005], ok=True | False |  | b1a17927d9ad |
| on0.6_L1_strong_harmful_d50_b0.1_s0.1 | ['onset'] | 31/0 | 487ae8a2643f | 0.2819 | 0.01 | 0.00 | False | True | True | on0.3_L1_strong_harmful_d50_b0.1_s0.1: vs best_safe -0.001 [-0.010,+0.008], ok=True; on0.8_L1_strong_harmful_d50_b0.1_s0.1: vs best_safe -0.002 [-0.003,-0.000], ok=True | False |  | 487ae8a2643f |
| on0.8_L0.6_strong_harmful_d1_b0.05_s0.5 | none | 23/0 | b1a17927d9ad | 0.2460 | 0.23 | 0.00 | False | True | True | on0.6_L0.6_strong_harmful_d1_b0.05_s0.5: vs best_safe -0.091 [-0.117,-0.064], ok=True; on0.8_L0.3_strong_harmful_d1_b0.05_s0.5: vs best_safe -0.014 [-0.027,-0.001], ok=True | False |  | b1a17927d9ad |
| on0.6_L0.6_strong_harmful_d1_b0.05_s0.1 | none | 23/0 | b1a17927d9ad | 0.2663 | 0.48 | 0.00 | False | True | True | on0.3_L0.6_strong_harmful_d1_b0.05_s0.1: vs best_safe -0.098 [-0.138,-0.057], ok=True; on0.8_L0.6_strong_harmful_d1_b0.05_s0.1: vs best_safe -0.023 [-0.043,-0.002], ok=True | False | reclassified_development | b1a17927d9ad |
| on0.6_L1_strong_harmful_d50_b0.05_s0.1 | ['onset'] | 31/0 | 612b8e1a975e | 0.3578 | 0.16 | 0.00 | False | True | False | on0.3_L1_strong_harmful_d50_b0.05_s0.1: vs best_safe +0.042 [-0.033,+0.118], ok=False; on0.8_L1_strong_harmful_d50_b0.05_s0.1: vs best_safe +0.000 [+0.000,+0.000], ok=True | False |  | 612b8e1a975e |

Stage-6 candidate legend (ids from the table above):

| id | acquisition / evidence / memory / decision | hypothesised slot | hypothesis |
|---|---|---|---|
| `487ae8a2643f` | uniform / weighted_starts / none / certificate_econ | evidence | Onset-informed starts promote as soon as evidence rejects when the economic margin is halved and there is no rollback. |
| `612b8e1a975e` | reserve_pacing / wide_stakes / none / rollback_monitor | evidence | Wide stakes with a decaying reserve: near-Kelly growth on the labels that arrive after a late onset. |
| `891a240116da` | straddle / weighted_starts / none / rollback_monitor | evidence | Onset-informed start weights with undecided-only straddle queries. |
| `b1a17927d9ad` | straddle / started_mixture_eprocess / none / rollback_monitor | acquisition | Querying while undecided adapts spend to the evidence. |
| `bc27f3692d70` | straddle / started_mixture_eprocess / none / rollback_monitor | evidence | Ablation of evidence (weighted_starts -> started_mixture_eprocess): Onset-informed start weights with undecided-only straddle queries. |

Repair verdicts: 12 survivors reached validation. Repair flags [False, None, False, False, None, False, False, False, False, False, False, False]
(True: 0, False: 10, None: 2).
Locked criteria: gap to R_family closed by >= 50%, null-twin FP <= alpha + 0.05, ablation removes most of the gain, and the
candidate is no worse than best_safe in two neighbouring cells. The per-cell ablation and neighbour results are in the
table above (columns `ablation removes gain`, `neighbours ok`, `neighbour detail`). `ablation removes gain = None` means the
hypothesised slot already held its default component (no ablation partner), so those rows are unverified, not repaired.

### reclassified_development pairs (validation seeds used more than once)

- `on0.8_L1_strong_harmful_d10_b0.05_s0.1|bc27f3692d70`
- `on0.6_L0.6_strong_harmful_d1_b0.05_s0.1|b1a17927d9ad`

These arose because a neighbour-cell check evaluated the same (cell, spec) pair that was also the main
validation target of another survivor. Their results count as development, not validation.

## Validation-seed use log (pairs used more than once are reclassified_development)

| cell|spec | uses | status |
|---|---|---|
| on0.1_L0.6_strong_harmful_d10_b0.05_s0.1|891a240116da | 1 | first use |
| on0.1_L0.6_strong_harmful_d10_b0.05_s0.5|b1a17927d9ad | 1 | first use |
| on0.1_L0.6_strong_harmful_d10_b0.1_s0.1|612b8e1a975e | 1 | first use |
| on0.3_L0.6_strong_harmful_d10_b0.05_s0.1|891a240116da | 1 | first use |
| on0.3_L0.6_strong_harmful_d10_b0.05_s0.5|b1a17927d9ad | 1 | first use |
| on0.3_L0.6_strong_harmful_d10_b0.1_s0.1|612b8e1a975e | 1 | first use |
| on0.3_L0.6_strong_harmful_d1_b0.05_s0.1|b1a17927d9ad | 1 | first use |
| on0.3_L1_strong_harmful_d10_b0.05_s0.1|bc27f3692d70 | 1 | first use |
| on0.3_L1_strong_harmful_d10_b0.1_s0.1|487ae8a2643f | 1 | first use |
| on0.3_L1_strong_harmful_d50_b0.05_s0.1|612b8e1a975e | 1 | first use |
| on0.3_L1_strong_harmful_d50_b0.1_s0.1|487ae8a2643f | 1 | first use |
| on0.6_L0.6_strong_harmful_d10_b0.05_s0.1|891a240116da | 1 | first use |
| on0.6_L0.6_strong_harmful_d10_b0.05_s0.5|b1a17927d9ad | 1 | first use |
| on0.6_L0.6_strong_harmful_d10_b0.1_s0.1|612b8e1a975e | 1 | first use |
| on0.6_L0.6_strong_harmful_d1_b0.05_s0.1|b1a17927d9ad | 2 | reclassified_development |
| on0.6_L0.6_strong_harmful_d1_b0.05_s0.5|b1a17927d9ad | 1 | first use |
| on0.6_L1_strong_harmful_d10_b0.05_s0.1|bc27f3692d70 | 1 | first use |
| on0.6_L1_strong_harmful_d10_b0.1_s0.1|487ae8a2643f | 1 | first use |
| on0.6_L1_strong_harmful_d10_b0.1_s0.1|612b8e1a975e | 1 | first use |
| on0.6_L1_strong_harmful_d50_b0.05_s0.1|612b8e1a975e | 1 | first use |
| on0.6_L1_strong_harmful_d50_b0.1_s0.1|487ae8a2643f | 1 | first use |
| on0.8_L0.3_strong_harmful_d1_b0.05_s0.1|b1a17927d9ad | 1 | first use |
| on0.8_L0.3_strong_harmful_d1_b0.05_s0.5|b1a17927d9ad | 1 | first use |
| on0.8_L0.6_strong_harmful_d1_b0.05_s0.1|b1a17927d9ad | 1 | first use |
| on0.8_L0.6_strong_harmful_d1_b0.05_s0.5|b1a17927d9ad | 1 | first use |
| on0.8_L1_strong_harmful_d10_b0.05_s0.1|bc27f3692d70 | 2 | reclassified_development |
| on0.8_L1_strong_harmful_d10_b0.1_s0.1|487ae8a2643f | 1 | first use |
| on0.8_L1_strong_harmful_d10_b0.1_s0.1|612b8e1a975e | 1 | first use |
| on0.8_L1_strong_harmful_d50_b0.05_s0.1|612b8e1a975e | 1 | first use |
| on0.8_L1_strong_harmful_d50_b0.1_s0.1|487ae8a2643f | 1 | first use |

## 5. Explanation ledger (cycle 2, one entry per reproduced failure)

Avoidable: H = cost(best_safe) - cost(R_family) with paired 95% CI (R_family's null-twin FP is within the locked
allowance in the table of reproduced failures); the R_law figure is the same difference against the law-aware
filter on the reproduction seeds. Decomposition: gap parts from stage 2b (per-round cost; onset/stake/interaction/residual
as defined there; "largest" is the largest of onset, stake and residual by mean). Repaired: yes / no / unverified.

| failure cell | avoidable? | isolated axis | decomposition attribution | repaired? |
|---|---|---|---|---|
| on0.3_L0.6_strong_harmful_d10_b0.05_s0.1 | yes: H +0.1965 [+0.1781, +0.2150] vs R_family; best_safe (episode_front) - R_law +0.3249 | none (no single axis) | onset +0.0992, stake +0.0562, interaction -0.0023, residual +0.0482; largest: onset-uncertainty | no |
| on0.6_L1_strong_harmful_d10_b0.05_s0.1 | yes: H +0.1937 [+0.1831, +0.2044] vs R_family; best_safe (allonset_edetector) - R_law +0.2678 | onset | onset +0.0745, stake +0.0396, interaction +0.0185, residual +0.0591; largest: onset-uncertainty | unverified |
| on0.3_L0.6_strong_harmful_d10_b0.05_s0.5 | yes: H +0.2139 [+0.1943, +0.2334] vs R_family; best_safe (episode_front) - R_law +0.3296 | none (no single axis) | onset +0.0971, stake +0.0578, interaction -0.0080, residual +0.0633; largest: onset-uncertainty | no |
| on0.3_L0.6_strong_harmful_d10_b0.1_s0.1 | yes: H +0.1822 [+0.1658, +0.1986] vs R_family; best_safe (episode_front) - R_law +0.2366 | none (no single axis) | onset +0.0754, stake +0.0387, interaction +0.0027, residual +0.0724; largest: onset-uncertainty | no |
| on0.8_L1_strong_harmful_d10_b0.05_s0.1 | yes: H +0.1064 [+0.1008, +0.1121] vs R_family; best_safe (c1_hmm_cs) - R_law +0.1402 | onset | onset +0.0114, stake +0.0009, interaction +0.0269, residual +0.0698; largest: residual (label count/information) | unverified |
| on0.8_L1_strong_harmful_d10_b0.1_s0.1 | yes: H +0.1104 [+0.1054, +0.1154] vs R_family; best_safe (episode_front) - R_law +0.1271 | onset | onset +0.0479, stake +0.0159, interaction +0.0121, residual +0.0388; largest: onset-uncertainty | no |
| on0.6_L1_strong_harmful_d10_b0.1_s0.1 | yes: H +0.1334 [+0.1264, +0.1404] vs R_family; best_safe (allonset_edetector) - R_law +0.1589 | onset | onset +0.0769, stake +0.0390, interaction -0.0053, residual +0.0339; largest: onset-uncertainty | no |
| on0.8_L0.6_strong_harmful_d1_b0.05_s0.1 | yes: H +0.1119 [+0.1053, +0.1185] vs R_family; best_safe (c1_hmm_cs) - R_law +0.1419 | none (no single axis) | onset +0.0183, stake +0.0021, interaction +0.0342, residual +0.0608; largest: residual (label count/information) | no |
| on0.6_L1_strong_harmful_d50_b0.1_s0.1 | yes: H +0.1146 [+0.1083, +0.1208] vs R_family; best_safe (allonset_edetector) - R_law +0.1706 | onset | onset +0.0703, stake +0.0320, interaction -0.0072, residual +0.0390; largest: onset-uncertainty | no |
| on0.8_L0.6_strong_harmful_d1_b0.05_s0.5 | yes: H +0.1100 [+0.1035, +0.1166] vs R_family; best_safe (no_switch) - R_law +0.1395 | none (no single axis) | onset +0.0182, stake +0.0024, interaction +0.0257, residual +0.0608; largest: residual (label count/information) | no |
| on0.6_L0.6_strong_harmful_d1_b0.05_s0.1 | yes: H +0.1903 [+0.1790, +0.2017] vs R_family; best_safe (allonset_edetector) - R_law +0.2601 | none (no single axis) | onset +0.0866, stake +0.0456, interaction +0.0024, residual +0.0661; largest: onset-uncertainty | no |
| on0.6_L1_strong_harmful_d50_b0.05_s0.1 | yes: H +0.1582 [+0.1444, +0.1719] vs R_family; best_safe (allonset_edetector) - R_law +0.2700 | onset | onset +0.0643, stake +0.0312, interaction +0.0235, residual +0.0383; largest: onset-uncertainty | no |

## 6. Limitations

- R_family is an empirically calibrated Bayes filter that has prior knowledge of the declared family; its kappa was
  calibrated on the same discovery null twins. It is a reference, not a method, and not an anytime-valid test.
- The family is 2-state Bernoulli D only (scripted regime path, onset jitter); no covariates, drift or dependence.
- R6 baselines are missing (section 2).
- `best_safe` is selected on the same seeds it is evaluated on (favours baselines).
- Heuristic validity: `horizon_cusum` uses a fixed finite-horizon threshold, not an anytime-valid level; validity of
  repeated episodes with alpha spending is a research target. `weighted_starts` weights are a declared family-informed prior
  (validity does not depend on them); the straddle schedule used to place them is approximated by the uniform pace.
- The `diag_oracle_*` variants see truth and are evaluator-side diagnostics only; the decomposition is descriptive
  (it depends on the order of ablation, hence the interaction term) and uses `episode_front` as the common decision rule.
- Reference change in cycle 2: R_law/R_family use the promote-then-revert plan value; the demotion rule was made symmetric
  (demote when every revert round u<T has cumulative expected benefit < -margin and staying to T is below -(s+margin)).
  Cycle-2 classes are not directly comparable to cycle-1 beyond the transition table, which is its purpose.
- In cycle 2 no cell is classified `info_limited`; every cycle-1 `info_limited` cell moved (see transitions). That the
  corrected R_law now beats no_switch everywhere is a point to audit, not a result.
- Nothing here is confirmatory: no confirmation seeds were touched; mechanism-validation reuse is logged above.

## 7. Reviewer assessment (2026-10-30)

**Engine: CONTINUE.** The loop works end to end. It discovers, reproduces, decomposes, isolates,
searches typed candidates, and validates with ablation and neighbours, using locked criteria and
logged seed reuse. Two cycles took about 1.5 h of CPU time in total. Cycle 1 surfaced a real
defect in the reference (R_law), which was fixed through an amendment registered before cycle 2.
This is the intended behaviour.

**Failure family 1 (late or transient advantage, strong effect, harmful off state): the failure is
reproducible and explained, but not repaired. PIVOT away from repairing it with the existing
components.**

1. **The failure is real against the declared references.** All 12 reproduced survivors have H CIs
   far from 0.01. In the to-end cells with onset 0.6 or 0.8, every gated baseline sits near
   `no_switch`.
2. **Most of the gap is attributable to known, structural costs of a valid sequential gate:**
   - In most cells, the largest share is onset multiplicity: the start-mixture penalty of about
     log(#starts).
   - The next share is a mismatch between the stake grid and the alternative.
   - In the onset-0.8 cells the residual dominates. The gate sees about 10 favourable labels
     against an analytic requirement of 26 to 29. That is an absolute label shortage, not an
     algorithmic gap.
3. **The residual is mostly the cost of validity, not a repairable mechanism.** The residual is the
   oracle-onset, oracle-stake e-process minus R_family. R_family is a Bayes filter: it knows the
   family prior and is calibrated only empirically, on the same family. That residual should not
   count as avoidable headroom for any method that claims an anytime guarantee. The avoidable part
   is at most the onset plus stake share, roughly 0.02 to 0.16 per round. The onset share is
   close to the multiplicity penalty, which is expected to be unavoidable under a
   false-promotion-probability constraint with unknown onset. That still needs a stated lower
   bound before it can be claimed.
4. **No typed composition of valid components closed 50% of the gap.** The best closed 48%. The
   family-informed `weighted_starts` and `wide_stakes` gave only small gains. So spreading prior
   mass over four onset levels with jitter does not remove the multiplicity penalty.
5. **The info_limited test is uninformative.** With the plan-value fix, R_law knows the law almost
   exactly and can promote nearly blind. It therefore beats `no_switch` in every cell, and no cell
   is info_limited. Avoidability must be judged against a reference that is information-matched
   and validity-matched, not against R_law.

**Next cycle (registered direction, not yet run):**
- (a) Add a validity-matched reference, `R_valid`. It is the best valid e-process gate that is
  given the family prior only as fixed mixture weights (no oracle onset or stake). Redefine
  headroom against it. Cells where `best_safe - R_valid` vanishes are recorded as "cost of
  validity", not as failures.
- (b) State and check a lower bound on the onset-multiplicity penalty under the finite-horizon
  false-promotion constraint, and audit sources first. Recent conformal-martingale and e-detector
  change-detection work is the closest prior art, and the R2 kill rule applies.
- (c) Implement the missing R6 baselines: the Gong–Zhang, Qiu et al. and Ryabchenko delayed
  wrappers, and the online FWER comparator. Until then, no atlas failure counts as shared across
  the strongest methods.
- (d) Open failure family 2 (dependence and recurrent regimes, or boundary nulls with reversals)
  in the same engine.

None of the evidence here is confirmatory. No confirmation seeds were touched.

## Cycle 3

Protocol: `docs/failure_atlas_v1_protocol.md` including Amendments 2, 3 and 4. All numbers below are copied from
`outputs/failure_atlas_v1_cycle3/family1/summary.md`, `outputs/failure_atlas_v1_cycle3/family2/summary.md`,
`outputs/failure_atlas_v1_cycle3/run.log`, `docs/failure_atlas_onset_multiplicity_bound_v1.md` or the protocol
amendments. Nothing here is confirmatory: discovery, development and mechanism-validation seeds only.

### 1. Run record

- Command (repository root; the `run.log` header records only `out=... smoke=False family=both workers=12`, so the
  command is the one supplied with the task):
  `python scripts/run_failure_atlas_loop.py --family both --out outputs/failure_atlas_v1_cycle3/ --workers 12 --reuse-cells-from outputs/failure_atlas_v1_cycle2/state.json --compare-to outputs/failure_atlas_v1_cycle2`
- Commits: `4a8a576` (code; "Add R_valid reference, failure family 2 and triggered_kelly component") and `ba131d6`
  (R6 switching baselines and onset-multiplicity bound audit).
- Family 1 header: git head `ba131d6233`, dirty = True; sources `failure_atlas.py` `24a2542f20`,
  `atlas_components.py` `79f9665b76`, `atlas_r6_baselines.py` `3ebc8dfe67`, `switching_explore.py` `f7a330f595`,
  `eprocess.py` `a9355d3883`, `run_failure_atlas_loop.py` `d235af61bc`; T=1000; smoke=False; method-runs 220480;
  elapsed 2929 s; stopped: completed all stages.
- Family 2 header: git head `4a8a576bd9`, dirty = False; sources `failure_atlas.py` `80bd6bd88f`,
  `atlas_components.py` `79f9665b76`, `atlas_r6_baselines.py` `3ebc8dfe67`, `switching_explore.py` `f7a330f595`,
  `eprocess.py` `a9355d3883`, `run_failure_atlas_loop.py` `8202d9288c`; T=1000; smoke=False; method-runs 103920;
  elapsed 840 s; stopped: no failure survives stage 2/3.
- Per-stage wall time, family 1 (s): stage1_discover 1609; stage2_reproduce 258; stage2b_diagnose 107;
  stage4_isolate 103; stage5_6_mechanism 852 (sum 2929). Family 2 (s): stage1_discover 840.
- Family 1 reuses the sampled and refinement cells and the discovery seeds of cycle 2
  (`outputs/failure_atlas_v1_cycle2/state.json`), so classes are comparable. R6 baselines loaded in both families:
  gong_zhang_paid_obs, qiu_delayed_movement, ryabchenko_capacity, online_fwer_spending.

### 2. Validity checks

- R_valid boundary null (any-promotion rate): 0.0333 for family 1 and 0.0100 for family 2.
- R_valid pooled null twins (discovery seeds, from the summaries; alpha = 0.1):
  family 1 0/1600 = 0.000 (80 distinct twins); family 2 0/1520 = 0.000 (76 distinct twins).
- `triggered_kelly` nulls: 0.0733 on the boundary null and 0.0000 on the harmful-off null.
- `online_fwer_spending` boundary null: 0.005.
- Source of the boundary-null figures above: they were supplied with the task (validity tests,
  `tests/test_atlas_components.py` and `tests/test_atlas_r6_baselines.py`); they do not appear in the cycle-3
  summaries or `run.log`, so they were not re-derived here.
- R_family kappa, family 1: chosen kappa = 0.05 (calibrated=True, 80 distinct twins, seeds [0, 19]).

| kappa | FP count | n | pooled any-FP rate |
|---|---|---|---|
| 0.5 | 1524 | 1600 | 0.953 |
| 0.3 | 1033 | 1600 | 0.646 |
| 0.2 | 650 | 1600 | 0.406 |
| 0.1 | 298 | 1600 | 0.186 |
| 0.05 | 115 | 1600 | 0.072 |
| 0.02 | 37 | 1600 | 0.023 |
| 0.01 | 18 | 1600 | 0.011 |

- R_family kappa, family 2: chosen kappa = 0.2 (calibrated=True, 76 distinct twins, seeds [0, 19]).

| kappa | FP count | n | pooled any-FP rate |
|---|---|---|---|
| 0.5 | 530 | 1520 | 0.349 |
| 0.3 | 158 | 1520 | 0.104 |
| 0.2 | 69 | 1520 | 0.045 |
| 0.1 | 15 | 1520 | 0.010 |
| 0.05 | 5 | 1520 | 0.003 |
| 0.02 | 1 | 1520 | 0.001 |
| 0.01 | 0 | 1520 | 0.000 |

### 3. Lower-bound audit outcome (`docs/failure_atlas_onset_multiplicity_bound_v1.md`)

- The finite-horizon packing bound (Theorem 1) is classical: Huang and Veeravalli (arXiv 2511.12803) Theorem 1 states
  the same `log T + log(1/delta_F)` latency lower bound, and the repository's own finite-horizon QCD audit already holds
  the non-asymptotic version. R2 kill rule: not novel. No novelty is claimed (reviewer note).
- In the harmful-off cells (`q_off = 0.1`, all twelve cycle-2 ledger failure cells) the bound is vacuous. With
  `q' = q0 = 0.55` it is vacuous beyond a few labels; with `q' = q_off = 0.1` it gives only n >= 3 labels, below the
  known-onset floor of 4.65. It therefore does not establish that the family-1 onset share is unavoidable.
- The literal "stop at the first 1 after r zeros" counterexample is valid only against the simple null Bern(q0). The
  project null is the composite conditional null, which contains the harmful off state itself, so the counterexample
  does not show a valid gate exists under the project null (reviewer note).
- The toy history-triggered Kelly bettor is valid under the composite null (predictable stake in [0, 1)); its toy
  detection result (51% versus 0%) stands only as evidence of algorithmic headroom, and it ignores delay, the economic
  check and rollback.
- The cycle-2 ledger section 7 reading ("onset share expected unavoidable") is corrected: it applies to neutral-like off
  states only, and only to the `ln(N/n)` part. Cells whose shortfall is the post-onset label count alone remain
  `cost_of_validity`.

### 4. Family 1 results

Discovery counts by class (stage 1; 360 cells):

| class | cells |
|---|---|
| cost_of_validity | 117 |
| no_headroom | 214 |
| prior_gap | 1 |
| reference_unsafe | 21 |
| shared_failure | 7 |
| total | 360 |

Information-limited cells: none.

Class transitions: cycle 2 (rows) -> cycle 3 (columns). 116 of the 123 shared failures of cycle 2 moved to
`cost_of_validity`; 7 stayed `shared_failure`.

| prev \ now | cost_of_validity | headroom_not_shared | no_headroom | prior_gap | reference_unsafe | shared_failure | total |
|---|---|---|---|---|---|---|---|
| cost_of_validity | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| headroom_not_shared | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| no_headroom | 0 | 0 | 214 | 1 | 0 | 0 | 215 |
| prior_gap | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| reference_unsafe | 0 | 0 | 0 | 0 | 21 | 0 | 21 |
| shared_failure | 116 | 0 | 0 | 0 | 0 | 7 | 123 |

The per-cell list of the 116 cells is in `outputs/failure_atlas_v1_cycle3/family1/summary.md`.

Reproduced failures (stage 2, fresh discovery seeds). Two of the seven candidates reproduced as `cost_of_validity`
(severity 0.0000) and are not pursued; the five `shared_failure` rows are the survivors.

| cell | label | severity | H [95% CI] | best_safe | R_family null FP [Wilson] |
|---|---|---|---|---|---|
| on0.3_L0.6_strong_harmful_d10_b0.05_s0.1 | shared_failure | 0.1965 | +0.1965 [+0.1781, +0.2150] | episode_front | 0.130 [0.078,0.210] |
| on0.6_L0.6_strong_harmful_d1_b0.05_s0.1 | shared_failure | 0.1903 | +0.1903 [+0.1790, +0.2017] | allonset_edetector | 0.070 [0.034,0.137] |
| on0.6_L1_strong_harmful_d50_b0.05_s0.1 | shared_failure | 0.1582 | +0.1582 [+0.1444, +0.1719] | allonset_edetector | 0.110 [0.063,0.186] |
| on0.1_L0.6_strong_harmful_d10_b0.1_s0.05 | cost_of_validity | 0.0000 | +0.1073 [+0.0955, +0.1191] | episode_front | 0.130 [0.078,0.210] |
| on0.1_L0.6_strong_harmful_d50_b0.25_s0.1 | cost_of_validity | 0.0000 | +0.0969 [+0.0842, +0.1096] | episode_front | 0.080 [0.041,0.150] |
| on0.1_L0.6_strong_harmful_d1_b0.05_s0.1 | shared_failure | 0.0694 | +0.0694 [+0.0520, +0.0869] | episode_front | 0.070 [0.034,0.137] |
| on0.1_L0.6_strong_harmful_d10_b0.05_s0.5 | shared_failure | 0.0822 | +0.0822 [+0.0628, +0.1017] | episode_front | 0.090 [0.048,0.162] |

Per-baseline gap to R_family (mean, lower CI bound; cost per round):

| cell | episode_geo | episode_equal | episode_front | allonset_edetector | c2_rho0.75 | c1_hmm_cs | online_fwer_spending | no_switch |
|---|---|---|---|---|---|---|---|---|
| on0.3_L0.6_strong_harmful_d10_b0.05_s0.1 | +0.227 (+0.208) | +0.313 (+0.292) | +0.197 (+0.178) | +0.218 (+0.199) | +0.266 (+0.243) | +0.326 (+0.305) | +0.227 (+0.208) | +0.325 (+0.304) |
| on0.6_L0.6_strong_harmful_d1_b0.05_s0.1 | +0.206 (+0.195) | +0.236 (+0.223) | +0.195 (+0.184) | +0.190 (+0.179) | +0.231 (+0.219) | +0.236 (+0.224) | +0.206 (+0.195) | +0.235 (+0.223) |
| on0.6_L1_strong_harmful_d50_b0.05_s0.1 | +0.171 (+0.158) | +0.186 (+0.171) | +0.160 (+0.146) | +0.158 (+0.144) | +0.184 (+0.169) | +0.186 (+0.171) | +0.171 (+0.158) | +0.185 (+0.171) |
| on0.1_L0.6_strong_harmful_d10_b0.1_s0.05 | +0.128 (+0.116) | +0.240 (+0.227) | +0.107 (+0.095) | +0.287 (+0.278) | +0.170 (+0.151) | +0.282 (+0.265) | +0.128 (+0.116) | +0.357 (+0.346) |
| on0.1_L0.6_strong_harmful_d50_b0.25_s0.1 | +0.100 (+0.092) | +0.159 (+0.147) | +0.097 (+0.084) | +0.242 (+0.236) | +0.125 (+0.113) | +0.390 (+0.375) | +0.100 (+0.092) | +0.367 (+0.362) |
| on0.1_L0.6_strong_harmful_d1_b0.05_s0.1 | +0.099 (+0.083) | +0.193 (+0.171) | +0.069 (+0.052) | +0.243 (+0.226) | +0.154 (+0.128) | +0.183 (+0.156) | +0.099 (+0.083) | +0.205 (+0.181) |
| on0.1_L0.6_strong_harmful_d10_b0.05_s0.5 | +0.107 (+0.087) | +0.197 (+0.172) | +0.082 (+0.063) | +0.254 (+0.236) | +0.155 (+0.128) | +0.234 (+0.211) | +0.107 (+0.087) | +0.203 (+0.178) |

Diagnostic decomposition (stage 2b; evaluator-side, descriptive, 100 seeds, discovery seeds). Cost is per round;
`front` = `episode_front`; the parts are as defined in the cycle-2 ledger (onset, stake, interaction, residual).
Brackets are paired 95% CIs. Kelly stake is 0.778 in all five cells.

| cell | best_safe | gap | best_safe-front | onset | stake | interaction | residual |
|---|---|---|---|---|---|---|---|
| on0.3_L0.6_strong_harmful_d10_b0.05_s0.1 | episode_front | +0.2012 [+0.1782, +0.2243] | +0.0000 [+0.0000, +0.0000] | +0.0992 [+0.0861, +0.1123] | +0.0562 [+0.0479, +0.0644] | -0.0023 [-0.0149, +0.0103] | +0.0482 [+0.0279, +0.0684] |
| on0.6_L0.6_strong_harmful_d1_b0.05_s0.1 | allonset_edetector | +0.1967 [+0.1860, +0.2074] | -0.0040 [-0.0071, -0.0008] | +0.0866 [+0.0746, +0.0986] | +0.0456 [+0.0375, +0.0536] | +0.0024 [-0.0083, +0.0131] | +0.0661 [+0.0508, +0.0814] |
| on0.6_L1_strong_harmful_d50_b0.05_s0.1 | episode_front | +0.1572 [+0.1443, +0.1702] | +0.0000 [+0.0000, +0.0000] | +0.0643 [+0.0565, +0.0720] | +0.0312 [+0.0257, +0.0367] | +0.0235 [+0.0132, +0.0338] | +0.0383 [+0.0240, +0.0526] |
| on0.1_L0.6_strong_harmful_d1_b0.05_s0.1 | episode_front | +0.0882 [+0.0653, +0.1111] | +0.0000 [+0.0000, +0.0000] | +0.1123 [+0.0975, +0.1270] | +0.0482 [+0.0399, +0.0565] | +0.0086 [-0.0068, +0.0240] | -0.0809 [-0.1043, -0.0575] |
| on0.1_L0.6_strong_harmful_d10_b0.05_s0.5 | episode_front | +0.0758 [+0.0562, +0.0954] | +0.0000 [+0.0000, +0.0000] | +0.1076 [+0.0940, +0.1212] | +0.0557 [+0.0474, +0.0641] | -0.0043 [-0.0189, +0.0102] | -0.0832 [-0.1058, -0.0606] |

Isolation (stage 4): does moving one axis to its easiest level remove the failure?

| failure cell | onset | duration | effect | d | budget_frac | s |
|---|---|---|---|---|---|---|
| on0.3_L0.6_strong_harmful_d10_b0.05_s0.1 | keeps (H lo +0.045, shared_failure) | keeps (H lo +0.137, cost_of_validity) | at easiest | keeps (H lo +0.144, shared_failure) | keeps (H lo +0.102, cost_of_validity) | keeps (H lo +0.188, shared_failure) |
| on0.6_L0.6_strong_harmful_d1_b0.05_s0.1 | keeps (H lo +0.015, shared_failure) | keeps (H lo +0.147, cost_of_validity) | at easiest | at easiest | keeps (H lo +0.046, cost_of_validity) | keeps (H lo +0.156, cost_of_validity) |
| on0.6_L1_strong_harmful_d50_b0.05_s0.1 | REMOVES (H lo -0.101, no_headroom) | at easiest | at easiest | keeps (H lo +0.147, cost_of_validity) | keeps (H lo +0.053, cost_of_validity) | keeps (H lo +0.129, cost_of_validity) |
| on0.1_L0.6_strong_harmful_d1_b0.05_s0.1 | at easiest | REMOVES (H lo -0.014, no_headroom) | at easiest | at easiest | keeps (H lo +0.078, cost_of_validity) | REMOVES (H lo -0.009, prior_gap) |
| on0.1_L0.6_strong_harmful_d10_b0.05_s0.5 | at easiest | REMOVES (H lo -0.098, no_headroom) | at easiest | keeps (H lo +0.022, shared_failure) | keeps (H lo +0.085, shared_failure) | keeps (H lo +0.066, shared_failure) |

Candidate and repair table (stages 5-6). Spec decodes:
`8ac25a41d4a8` = uniform + triggered_kelly + none + rollback_monitor;
`891a240116da` = straddle + weighted_starts + none + rollback_monitor;
`b1a17927d9ad` = straddle acquisition + started_mixture + rollback_monitor.

| failure cell | axes removing | proposed/invalid | stage-6 candidate | val cost | gap closure | null FP | closes >=50% | ablation removes gain | neighbours ok | neighbour detail | repair |
|---|---|---|---|---|---|---|---|---|---|---|---|
| on0.3_L0.6_strong_harmful_d10_b0.05_s0.1 | none | 25/0 | 891a240116da | 0.4164 | 0.18 | 0.00 | False | False | False | on0.1_L0.6_strong_harmful_d10_b0.05_s0.1: vs best_safe +0.048 [-0.014,+0.110], ok=False; on0.6_L0.6_strong_harmful_d10_b0.05_s0.1: vs best_safe -0.038 [-0.067,-0.009], ok=True | False |
| on0.6_L0.6_strong_harmful_d1_b0.05_s0.1 | none | 25/0 | b1a17927d9ad | 0.2578 | 0.59 | 0.00 | True | True | True | on0.3_L0.6_strong_harmful_d1_b0.05_s0.1: vs best_safe -0.084 [-0.139,-0.029], ok=True; on0.8_L0.6_strong_harmful_d1_b0.05_s0.1: vs best_safe -0.017 [-0.034,-0.001], ok=True | True |
| on0.6_L1_strong_harmful_d50_b0.05_s0.1 | ['onset'] | 33/0 | 8ac25a41d4a8 | 0.3775 | 0.13 | 0.00 | False | True | False | on0.3_L1_strong_harmful_d50_b0.05_s0.1: vs best_safe +0.035 [-0.005,+0.074], ok=False; on0.8_L1_strong_harmful_d50_b0.05_s0.1: vs best_safe -0.000 [-0.002,+0.001], ok=True | False |
| on0.1_L0.6_strong_harmful_d1_b0.05_s0.1 | ['duration', 's'] | 18/0 | 8ac25a41d4a8 | 0.3994 | 1.09 | 0.00 | True | True | False | on0.1_L0.3_strong_harmful_d1_b0.05_s0.1: vs best_safe -0.030 [-0.049,-0.010], ok=True; on0.1_L1_strong_harmful_d1_b0.05_s0.1: vs best_safe -0.013 [-0.063,+0.036], ok=False | False |
| on0.1_L0.6_strong_harmful_d10_b0.05_s0.5 | ['duration'] | 18/0 | 8ac25a41d4a8 | 0.4332 | 0.93 | 0.00 | True | True | False | on0.1_L0.3_strong_harmful_d10_b0.05_s0.5: vs best_safe -0.024 [-0.043,-0.006], ok=True; on0.1_L1_strong_harmful_d10_b0.05_s0.5: vs best_safe +0.036 [-0.032,+0.105], ok=False | False |

The one stage-6 repair, `b1a17927d9ad` (straddle acquisition + started_mixture + rollback_monitor) on
`on0.6_L0.6_strong_harmful_d1_b0.05_s0.1`, is reclassified as development evidence under Amendment 4. The same
(cell, spec) pair was already viewed on cycle-2 validation seeds, and cycle-3 validation seeds overlap the cycle-1
range; the per-directory validation-seed log cannot see reuse across cycles, so its "first use" entry for this pair
does not establish fresh seeds. Its fresh-seed check is pending and goes in section 7. No stage-6 repair in
cycle 3 counts as validated.

Amendment 3 check: `triggered_kelly` gain over its started-mixture ablation. Gain = ablated cost - triggered_kelly
cost (per round; positive = triggered_kelly better). Dev = development seeds (stage 5), val = mechanism-validation seeds.

| failure cell | off_type | spec | decision | dev gain | val gain | val null FP |
|---|---|---|---|---|---|---|
| on0.3_L0.6_strong_harmful_d10_b0.05_s0.1 | harmful | 8ac25a41d4a8 | rollback_monitor | +0.0406 | +0.0343 | +0.0000 |
| on0.6_L0.6_strong_harmful_d1_b0.05_s0.1 | harmful | 8ac25a41d4a8 | rollback_monitor | +0.0309 | +0.0315 | +0.0000 |
| on0.6_L1_strong_harmful_d50_b0.05_s0.1 | harmful | 8ac25a41d4a8 | rollback_monitor | +0.0407 | +0.0378 | +0.0000 |
| on0.1_L0.6_strong_harmful_d1_b0.05_s0.1 | harmful | 8ac25a41d4a8 | rollback_monitor | +0.0749 | +0.0747 | +0.0000 |
| on0.1_L0.6_strong_harmful_d10_b0.05_s0.5 | harmful | 8ac25a41d4a8 | rollback_monitor | +0.0674 | +0.0704 | +0.0000 |

| off_type | n survivors | mean dev gain | mean val gain |
|---|---|---|---|
| harmful | 5 | +0.0509 | +0.0498 |
| neutral | 0 | - | - |

The neutral-off arm of the Amendment 3 prediction was not testable in this run (0 neutral survivors); it is deferred to
Amendment 4 item 3 (section 7).

### 5. Family 2 results (recurrent regimes and reversals)

Discovery counts by class (stage 1; 200 sampled cells):

| class | cells |
|---|---|
| cost_of_validity | 45 |
| info_limited | 1 |
| no_headroom | 154 |
| total | 200 |

- Calibration: chosen kappa = 0.2 (calibrated=True, 76 distinct twins, seeds [0, 19]); table in section 2. R_valid
  null-twin any-promotion rate (pooled, 76 distinct twins, 1520 runs): 0/1520 = 0.000 (alpha = 0.1).
- Information-limited cell:

| cell | no_switch - R_law [95% CI] |
|---|---|
| f2_r0.02_weak_harmful_d10_b0.25_s0.5 | -0.0072 [-0.0213, +0.0069] |

  The CI includes 0, so this single cell is a weak signal only.
- The run stopped after discovery ("no failure survives stage 2/3"): 0 cells reached reproduction (`[stage2]
  reproducing 0 candidate failure cells`), so no refinement, isolation or mechanism stage ran for family 2. There are
  no family-2 shared failures in this run.

### 6. Explanation ledger (cycle 3, one entry per family-1 survivor)

Avoidable: H = cost(best_safe) - cost(R_family) with paired 95% CI from the table of reproduced failures (R_family's
null-twin FP is in that table). The R_law comparison is not in the cycle-3 summary and is not reported. Decomposition:
largest of onset, stake and residual by mean (stage 2b). Repaired: yes / no / unverified.

| failure cell | avoidable? | isolated axis | decomposition attribution | repaired? |
|---|---|---|---|---|
| on0.3_L0.6_strong_harmful_d10_b0.05_s0.1 | yes: H +0.1965 [+0.1781, +0.2150] vs R_family; best_safe (episode_front) | none (no single axis) | onset +0.0992, stake +0.0562, interaction -0.0023, residual +0.0482; largest: onset-uncertainty | no |
| on0.6_L0.6_strong_harmful_d1_b0.05_s0.1 | yes: H +0.1903 [+0.1790, +0.2017] vs R_family; best_safe (allonset_edetector) | none (no single axis) | onset +0.0866, stake +0.0456, interaction +0.0024, residual +0.0661; largest: onset-uncertainty | unverified (development repair `b1a17927d9ad`; fresh-seed check pending, section 7) |
| on0.6_L1_strong_harmful_d50_b0.05_s0.1 | yes: H +0.1582 [+0.1444, +0.1719] vs R_family; best_safe (allonset_edetector) | onset | onset +0.0643, stake +0.0312, interaction +0.0235, residual +0.0383; largest: onset-uncertainty | no |
| on0.1_L0.6_strong_harmful_d1_b0.05_s0.1 | yes: H +0.0694 [+0.0520, +0.0869] vs R_family; best_safe (episode_front) | duration, s | onset +0.1123, stake +0.0482, interaction +0.0086, residual -0.0809; largest: onset-uncertainty | no |
| on0.1_L0.6_strong_harmful_d10_b0.05_s0.5 | yes: H +0.0822 [+0.0628, +0.1017] vs R_family; best_safe (episode_front) | duration | onset +0.1076, stake +0.0557, interaction -0.0043, residual -0.0832; largest: onset-uncertainty | no |

### 7. Pending checks

### Amendment 4 mechanism checks (fresh seeds 280000-280199)

**Run record.** Command: `.venv/Scripts/python scripts/run_atlas_mechanism_check_v1.py`.

- Code: `scripts/run_atlas_mechanism_check_v1.py`. Output: `outputs/failure_atlas_v1_mechcheck/`. The run ran on git head `089edbb0b9` (dirty=True, from the uncommitted check script).
- 214 s of script time on 12 workers, using seeds [280000, 280200) (200 seeds) and kappa 0.05.
- **Freshness check.** The reviewer grepped all four earlier archives. No mechanism seed falls in [280000, 280200). The one numeric hit, in the cycle-1 archive, is a cost value (0.280165), not a seed.

**Check 1: straddle repair (`b1a17927d9ad` on `on0.6_L0.6_strong_harmful_d1_b0.05_s0.1`). PASS, with a thin margin on closure.**

| quantity | value |
|---|---|
| cost: candidate / ablation (uniform acquisition) / best_safe (`allonset_edetector`) / R_family / R_valid | 0.2781 / 0.3933 / 0.3733 / 0.1838 / 0.3541 |
| gap closure to R_family (ratio of means, no CI) | 0.503 (threshold 0.5) |
| candidate − best_safe | −0.0953 [−0.1051, −0.0855] |
| candidate − ablation | −0.1152 [−0.1245, −0.1059] |
| null-twin FP: candidate / ablation / best_safe / R_family / R_valid | 0.000 / 0.000 / 0.000 / 0.145 / 0.000 |
| neighbour `on0.3_L0.6_strong_harmful_d1_b0.05_s0.1`: candidate − best_safe (`episode_front`) | −0.0823 [−0.0987, −0.0658] |
| neighbour `on0.8_L0.6_strong_harmful_d1_b0.05_s0.1`: candidate − best_safe (`no_switch`) | −0.0197 [−0.0244, −0.0149] |

**Check 2: straddle gain falls as delay grows. PASS.** Gain is ablation cost minus candidate cost.

| d | gain |
|---|---|
| 1 | +0.1152 [+0.1059, +0.1245] |
| 10 | +0.0660 [+0.0565, +0.0755] |
| 50 | −0.0166 [−0.0204, −0.0129] |

gain(d=1) − gain(d=50) = +0.1318 [+0.1218, +0.1418].

**Check 3: `triggered_kelly` (`8ac25a41d4a8`), harmful-off vs neutral-off arms. PASS on the locked criterion, but the explanation is incomplete.**

- Mean gain over the 5 cells: harmful +0.0531 [+0.0498, +0.0564]; neutral +0.0218 [+0.0187, +0.0250].
- Harmful − neutral = +0.0313 [+0.0270, +0.0356].
- The "neutral gain upper bound < 0.01" branch fails. The check passes only through the "significantly smaller" branch.
- The neutral gains concentrate in the two onset-0.1 cells, at +0.0619 and +0.0553. The other three neutral cells are at or below zero.

### 8. Limitations (cycle 3)

- R_valid had a pooled null false-promotion rate of 0 against alpha 0.1 (0/1600 in family 1, 0/1520 in family 2), so
  it may be conservative. Some `cost_of_validity` labels, including the 116 cells that moved from `shared_failure`, may
  reflect a weak valid reference rather than an unavoidable cost.
- The hard-budget pacing comparator is still missing (registry status: missing).
- The R6 wrappers (gong_zhang_paid_obs, qiu_delayed_movement, ryabchenko_capacity, online_fwer_spending) depart from
  their sources as documented in the registry; a shared failure is a failure against the implemented baselines only.
- `best_safe` (including `no_switch`) is chosen on the same seeds it is evaluated on, which favours the baselines.
- The data are 2-state Bernoulli D only; no covariates or drift. R_family is calibrated empirically on one declared
  family, not an anytime-valid test.
- Family 1 was run with uncommitted code (git dirty = True at head `ba131d6233`); family 2 ran from `4a8a576bd9`.
- Nothing here is confirmatory: no confirmation seeds were touched, and the stage-6 repair is development evidence only.

### Cycle 3 reviewer assessment (2026-10-31)

**Engine: CONTINUE.** Cycle 3 did what the loop is for.

- The validity-matched reference reclassified 116 of the 123 cycle-2 shared failures as
  `cost_of_validity`. Most of the family-1 "failure" was therefore the price of a valid gate, not
  a missing algorithm.
- The lower-bound audit corrected an over-reading in the cycle-2 assessment. The onset share is not
  provably unavoidable in harmful-off cells.
- Family 2 (recurrent regimes) produced no shared failure among 200 cells.

**First mechanism to survive fresh-seed validation: straddle acquisition (query only while the
decision is undecided). CONTINUE, as a mechanism finding, not a method claim.**

- On fresh seeds it beats the strongest implemented gated baseline by 0.095 per round in the
  repair cell, and it is no worse in both registered neighbours.
- Its null false-promotion rate is 0.
- The gain disappears when acquisition is ablated to uniform.
- It also beats R_valid (0.278 vs 0.354), even though R_valid uses the declared family prior.
- The gain depends on delay, as the mechanism hypothesis predicts. It is large at d=1, smaller at
  d=10, and negative at d=50. The mechanism is therefore "fast feedback lets the method stop paying
  for labels once the call is clear". It is not a general improvement, and it must be scoped to
  short release delays.

Limits:

- The closure margin is thin (0.503 against 0.5, with no CI).
- The result covers one cell plus its neighbours in a 2-state Bernoulli simulator.
- Undecided-only (uncertainty-driven) querying is a classical idea in active learning and active
  sequential testing. No novelty is claimed until an R2 source audit is done.

**`triggered_kelly`: its mechanism explanation is PARTLY FALSIFIED, so PIVOT the explanation.**

- The locked criterion passes, and the gain is larger in harmful-off cells.
- But the gain is also substantial in the two onset-0.1 neutral cells. "Pre-onset data are
  informative" therefore does not explain all of it.
- A second effect, probably faster re-entry after a window closes and the method rolls back, is
  untested. The explanation ledger records it as incomplete.

**Validity caveats carried forward:**

- R_valid's pooled null false-promotion rate was 0 against alpha 0.1, so it may be conservative.
  Some `cost_of_validity` labels could therefore be an artefact of a weak valid reference.
- `straddle`'s query rule depends on released labels only, so it is predictable, and the
  e-process stays valid under the conditional null. No proof is written down yet for
  delayed-release selection.

**Cycle 4 (registered direction, not yet run):**

- (a) **Straddle mechanism map.** Run straddle against its uniform ablation across the full
  family-1 and family-2 grids on development seeds. This maps where it helps or hurts by d, B, s
  and onset.
- (b) **R2 prior-art audit** of uncertainty-driven acquisition for anytime-valid tests under delay
  and a hard budget. Starting sources:
  - active sequential hypothesis testing (Chernoff, Naghshvar–Javidi);
  - testing by betting with adaptive sampling;
  - the repository's `switching_*_prior_audit` docs.
- (c) **Theory target.** A label-saving bound for straddle as a function of `d`, together with a
  written validity argument for predictable query selection under release delay.
- (d) **Second mechanism test for `triggered_kelly`.** Count re-entries after rollback in the
  onset-0.1 neutral cells.
- (e) **Strengthen R_valid** so that its null false-promotion rate uses its alpha budget, for
  example with wider stakes or Kelly-adaptive weights. Then re-run the `cost_of_validity`
  classification.
- (f) **Add the missing hard-budget pacing comparator.**

None of this is confirmatory. The confirmation seeds remain untouched.
