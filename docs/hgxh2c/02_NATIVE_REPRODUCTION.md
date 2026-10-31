# 02 Stage 1: Native reproduction (A1.1 / A1.9)

Date of runs: 2026-10-31. Clones are untrusted data under `tmp/repro_sources/<name>` (git-ignored); logs and results under
`outputs/hgxh2c/stage1/`. Machine: Windows 11, Python 3.13.1, RTX 4060 not used (all CPU), 16 GB RAM with another heavy job running
concurrently (several first launches died of MemoryError / "paging file too small"; pools were reduced to 1-4 workers).
Unattended driver: `python scripts/hgxh2c/stage1/run_native_repro.py [--list|--only NAME ...|--force]` (idempotent via
`outputs/hgxh2c/stage1/markers/<job>.done`; subprocess + timeout; logs `<job>.log/.err`). The runs below were first launched by
hand as detached processes with the same arguments; markers were then written, so the driver treats them as done (`--force` re-runs).
Registry with equations/assumptions/null/calibration/role/fidelity per method: `03_BASELINE_REGISTRY.md`.

## Status table

| # | Repo @ commit | Experiment run | Status | Reduction vs paper/repo defaults |
|---|---|---|---|---|
| 1 | elad-tolo/betting_on_predictions @ f99e196b0087128d7ffe0291df9e68042255eae8 | `main_label_shift` (4 configs), `main_concept_shift` (2 configs), PPI (Appx E) variants inside both | PARTIAL | 10 reps (label) / 4 reps (concept) instead of 500; 3-4 worker processes instead of 130 |
| 2 | alextimans/risk-monitor @ 4bf66a37dc2a3d7959bb9dcb325b61e8bb3c28e5 | `exp_uci` (Naval propulsion, shipped data) with approx_grapa and grid grapa | PARTIAL; `exp_ood`, `exp_cp` SKIPPED_EXTERNAL_DATA | 3 trials instead of 50; grid-GRAPA only with tracker window 200 (full-history grid is quadratic) |
| 3 | jongharyu/confidence-sequence-via-gambling @ c7411902aac43e7c679e89bf43c871e76b9496eb | `notebooks/tit_exps.ipynb` pure-Python methods + ICML-2024 multivariate classes | PARTIAL; LBUP/Hybrid FAILED (no C compiler) | T=3000, 3 seeds (notebook T=10^4, 5 seeds); multivariate: K=3 only |
| 4 | neilzxu/active-rcps @ a67f85d603df2bb3e32ef007f445191923ebd990 | `simulation.py` | PARTIAL (executes; paper ordering not resolved) | 4 trials (default 100), label_ct 800 (default 2500) |
| 5 | Csillag et al. PPE | - | NOT_AVAILABLE (no public code found) | Algorithm-1 tests are engine work (not duplicated) |
| 6 | Zhang et al. PPRM (arXiv 2602.02229) | independent reproduction `scripts/hgxh2c/stage1/pprm_independent.py` (synthetic stream) | independent reproduction (PARTIAL) | synthetic data; CIFAR10-C / LLM / telecom data not used; no official code found |

## 1. Betting on Predictions (Tenzer, Tolochinsky, Romano; ICML 2026; arXiv 2605.28533)
- Commands (driver jobs `bop_label_shift`, `bop_concept_shift`): `python -u scripts/hgxh2c/stage1/bop_run.py <clone> mains/main_label_shift.py 3 10` and
  `... mains/main_concept_shift.py 4 4`. `bop_run.py` executes the repo main unmodified in memory except `processes=130 -> 3|4`,
  `"num_of_repititions": 500 -> 10|4`, and a stub for `tabpfn` (imported at top of `algs.py`, used only by the health-care experiment, which
  needs a model download; not run). Equivalent to `python -u -m mains.main_label_shift` otherwise. Repo `logs/` dir created (mains write per-process logs).
- Env: main env (numpy 2.4.2, pandas 3.0.1, scikit-learn 1.6.1; repo asks >=1.7). Nothing installed.
- Appendix-E PPI comparator (`sequential_tests/ppi.py`, Eq. 9; one-sided variant E.3) runs inside every simulation (`PPI`, `PPI_no_unlabeled`, `PPI_positive_lambda`).
- Summaries: `python -I scripts/hgxh2c/stage1/bop_summarize.py tmp/repro_sources/betting_on_predictions/results/simulations`.
- Paper values: the paper reports power-vs-step curves only (Figs. 2, 5); no tabulated powers. Paper claims being checked:
  (C1) the combined e-process including the imputed statistic has higher power than the one without; (C2) one-sided PPI beats two-sided PPI (E.3);
  (C3) PPI with unlabeled data beats PPI on labeled data only (Fig. 5).
- Results: final-step power (rejection fraction at step 500; 10 reps label shift, 4 reps concept shift, so +-0.15 to +-0.25 sampling error). `base` = best-of baselines
  (LRT/PPI combination), `+imp` = the same combination including the imputed e-process; `+1s` = with one-sided PPI.

| Setting | n_test, corr | imputed only (`NB`) | LRT-Y | PPI (2-sided) | PPI (1-sided) | base | +imp | base+1s | +imp+1s |
|---|---|---|---|---|---|---|---|---|---|
| label shift | 30, low (0.30) | 0.40 | 0.60 | 0.50 | 0.70 | 0.70 | 0.80 | 0.80 | 0.80 |
| label shift | 30, high (0.71) | 1.00 | 0.60 | 0.80 | 0.80 | 1.00 | 1.00 | - | - |
| label shift | 135, low (0.30) | 0.60 | 0.80 | 0.70 | 0.90 | 1.00 | 1.00 | - | - |
| label shift | 135, high (0.71) | 1.00 | 0.80 | 0.80 | 0.90 | 1.00 | 1.00 | - | - |
| concept shift | 135, low | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| concept shift | 135, high | 1.00 | 1.00 | 0.50 | 0.75 | 0.75 | 0.75 | 1.00 | 0.75 |

  (The low-corr 30 row also had `baselines_positive_lambda` 0.80 and `imputed_with_baselines_positive_lambda` 0.80; `-` = columns not tabulated here, all 1.00 in the pkl.)
- Comparison: (C2) holds in all 6 settings (one-sided >= two-sided, strictly higher in 4); (C1) the imputed statistic raises power in one setting (label shift, 30, low:
  0.70 -> 0.80) and is neutral elsewhere (ceiling at 1.00) or lower in one concept-shift cell (1.00 -> 0.75, 4 reps, within sampling noise); this reduced run cannot
  confirm or refute the paper's "significant gain". (C3) not separately tabulated (the `PPI_no_unlabeled` entries are in the pkls). No type-I-error run was made.
- Discrepancies: reps 10/4 vs 500; one wide sampling-error band; scikit-learn 1.6.1 vs >=1.7.
- Status: PARTIAL (native code executes end to end and gives qualitatively consistent power ordering for LRT/PPI/one-sided PPI; imputed gain not resolved).

## 2. Risk monitor (Timans et al., UAI 2025; arXiv 2506.16416)
- `commands.txt`/`run.sh` list exp_ood (CIFAR-10/SVHN + a pretrained ResNet from an external repo), exp_cp (FMoW images, Wild-Time checkpoints from Google Drive)
  and exp_uci. Only exp_uci runs on shipped data (`data/uci-cbm/data_aug.csv`, 11.9 MB; the RF is fitted on the fly). exp_ood, exp_cp: SKIPPED_EXTERNAL_DATA.
- Env: venv `tmp/repro_sources/venvs/risk-monitor` (`--system-site-packages` + yacs, pyyaml). Config overrides in `scripts/hgxh2c/stage1/risk_monitor_cfg/cfg_uci_{approx,grapa}.yaml`
  (output/data paths, NR_TRIALS=3, BET_TYPE). Quirk: `--cfg_dir` must use forward slashes, otherwise `os.path.join(OUTPUT_DIR, exp_type)` collapses to the cfg path.
- Commands (driver jobs `rm_uci_approx`, `rm_uci_approx_w200`, `rm_uci_grapa_w200`): `python -X utf8 -I exp/exp_uci.py --cfg_file=cfg_uci_{approx|grapa} --cfg_dir=<cfgdir> --exp_suffix=... [--get_pred|--no-get_pred] --save_file --batch_ts=1 --tracker_window 0 W W --stop_counter 5 25 0 --device=cpu`
  with W = 0 (approx, full history) and W = 200 (approx and grid). The first grid run (W = 0) was stopped: step cost is quadratic in history (about 6 h estimated per trial).
  Window 200 is one of the settings in the authors' `commands.txt`.
- Summaries: `python -I scripts/hgxh2c/stage1/rm_summarize.py <run_dir>` (false-alarm rate, mean delay relative to the point-risk stop time, psi-confidence-set size).
- Paper values: UAI paper (Naval propulsion, Tab. 5 and figures) is qualitative in the text available: running risk shows false positives for small windows; the wealth process M_t(psi) has the lowest
  detection delays among trackers with false-alarm guarantees; the psi-CS shrinks as degradation worsens. No numbers were extractable.
- Results (3 trials, eps=0.1, delta=0.1, 15000 steps; delay in steps after the point-risk crossing; false-alarm rate over psi grid):

| Tracker | approx_grapa W=0 delay | approx_grapa W=200 delay | grid grapa W=200 delay | false alarms (all runs) | psi-CS size at t=12500 (approx W=0 / approx W=200 / grid W=200) |
|---|---|---|---|---|---|
| running risk (heuristic) | 1366.7 | 298.1 | 298.1 | 0.000 | 46.0 / 32.3 / 32.3 |
| e-process (M_t) | 1412.9 | 409.5 | 604.8 | 0.000 | 46.0 / 34.0 / 35.7 |
| naive (SUM) e-process | 1465.0 | 494.5 | 569.4 | 0.000 | 47.0 / 34.3 / 35.0 |
| PM-EB e-process | 3527.3 | 1175.4 | 1175.4 | 0.000 | 79.3 / 41.0 / 41.0 |

- approx_grapa vs grid GRAPA: at the same window the approx rule alarms about 195 steps sooner (409.5 vs 604.8) with a slightly smaller psi-CS (34.0 vs 35.7); both sit
  between the running-risk heuristic and the PM-EB baseline, with zero false alarms. A shorter window helps all trackers (fewer stale observations). Consistent with the paper's
  qualitative claims; the false-positive claim for running risk is not reproduced here (it showed no false alarm relative to the point-risk stop in 3 trials).
- Status: PARTIAL. Plots at `outputs/hgxh2c/stage1/risk_monitor_out/risk_monitor_cfg/uci_cbm_abs_res_12500/*/plots/*.png` are the repo's own native plots (not PaperBanana).

## 3. Gambling confidence sequences (Ryu & Bhatt TIT 2022; Ryu & Wornell ICML 2024, arXiv 2402.03683)
- Official repo: https://github.com/jongharyu/confidence-sequence-via-gambling @ c7411902 (branches `main`, `unbounded`). Its only notebook is `notebooks/tit_exps.ipynb`
  (scalar bounded processes); the brief's `exps.ipynb` does not exist. The ICML-2024 multivariate classes exist (`MultiHorseRaceCI`, `MultiStockInvestmentCI`, `MultiWoRCI`, `Sanov`)
  but no notebook/driver uses them, so setups follow the paper text; parameters not stated there are our choices.
- Cython/LBUP: `lbup.py`, `hybrid.py` import the compiled `lbup_integrand`; no C compiler (cl/gcc) on this machine -> LBUP and Hybrid-UP FAILED (environment). `pyximport` not installed either.
  The universal portfolio itself (`StockInvestmentCI`, pure Python) ran.
- Scalar commands (driver job `gambling_cs`): `python -I scripts/hgxh2c/stage1/gambling_cs_run.py <clone> <out.json> 3000 3` (re-implements notebook cell 13 for CB, HR, PRECiSE_CO96/A_CO96/R70, UP).
  Notebook typo: Beta(1,3) mean is listed as 0.2 (true 0.25); 0.25 used.
- Multivariate (job `gambling_cs_multivariate`): `gambling_cs_multivariate_run.py` on a 60-grid of the interior of the 3-simplex (1711 points).
- Paper values (ICML 2024, from the paper text; figures only): Fig. 1, K in {3,4,5}, T=100, 100 runs: KT(K) relatively tighter than the per-coordinate baselines as K grows; baselines win in the long run.
  Fig. 3, Dirichlet i.i.d.: UP(K) much tighter than KT(K) when concentrated. Fig. 2 (WoR 600/250/150): KT decides ranking ~26% faster than PPR (not run: no driver).
- Results (delta=0.05):

| Experiment | Quantity | Ours | Paper (qualitative) |
|---|---|---|---|
| scalar Bern(0.25), T=3000, 3 seeds | final width CB / HR / CO96 / A-CO96 | 0.137 / 0.0545 / 0.0546 / 0.056 | coin betting widest, HR/PRECiSE tighter |
| scalar Beta(1,3) | CB / HR / CO96 / A-CO96 / R70 / UP | 0.139 / 0.059 / 0.025 / 0.028 / 0.026 / 0.0229 | UP tightest |
| scalar Beta(10,10) | same | 0.139 / 0.069 / 0.0142 / 0.0166 / 0.0141 / 0.0122 | UP tightest |
| all scalar runs | anytime coverage violations | 0 of 9 problem-seeds per method | valid |
| categorical K=3, mu=(.5,.3,.2), 20 runs | fraction of simplex in CS at t=10/30/100: KT | 0.674 / 0.387 / 0.160 | KT tighter early |
| same | Sanov baseline | 0.883 / 0.638 / 0.124 | baseline wins in long run |
| same | coverage over all t (KT / Sanov) | 1.00 / 1.00 | valid |
| Dirichlet(8,8,8), T=40, 3 runs | set fraction UP / KT; coverage | 0.024 / 0.354; 1.00 / 1.00 | UP much tighter |

- UP cost: about 16 s per scalar run (T=3000) and 4 s per K=3 run (T=40); PRECiSE 1-2 s.
- Status: PARTIAL (qualitatively matches every available claim; reduced; LBUP/Hybrid not run; WoR experiment not run; no multivariate bounded-vector reduction (eq. 16) run).

## 4. Active anytime-valid RCPS (Xu, Karampatziakis, Mineiro; NeurIPS 2024; arXiv 2406.10490)
- Env: venv `tmp/repro_sources/venvs/active-rcps` (`--system-site-packages` + dill, multiprocess, seaborn; `pickle5.py` shim `from pickle import *` since pickle5 cannot be built on py3.13).
- Local source patches in the clone (diff saved at `outputs/hgxh2c/stage1/active_rcps_local.patch`): (a) `Predictor.py:230` syntax error `self._beta_knots. if` -> `self._beta_knots if` (branch used only with `add_pretrain=True`, i.e. ImageNet, not the simulation); (b) `simulation.py` `mp.Pool` -> `multiprocess.pool.ThreadPool` because spawn workers on Windows lose the `__main__` globals (`label_ct` NameError).
- Command (driver job `active_rcps_sim`): `python -u -X utf8 simulation.py --processes 1 --trials 4 --label_ct 800 --out_dir outputs/hgxh2c/stage1/active_rcps_sim` (defaults: 100 trials, label_ct 2500). Runtime 83 min. ImageNet experiment SKIPPED_EXTERNAL_DATA.
- Paper values: theta=0.1, alpha=0.05, B=0.3, 100 trials to 2500 labels; "pretrain" and "learned" reach lower beta-hat than "all" and "oblivious" at equal labels; all methods keep the safety-violation rate under 0.05; beta* quoted as 0.5578.
- Results (final beta-hat when 800 labels are reached; mean +- sd over 4 trials):

| Method | beta-hat |
|---|---|
| label all | 0.578 +- 0.024 |
| optimal | 0.586 +- 0.032 |
| oblivious | 0.598 +- 0.040 |
| cv only | 0.601 +- 0.010 |
| cv + learn_var | 0.601 +- 0.021 |
| learned | 0.621 +- 0.025 |

  All values exceed beta* = 0.5578, i.e. no risk-control violation in 4 trials (consistent with validity, which needs far more trials to test at alpha = 0.05).
  The paper's ordering (learned/pretrain < all, oblivious at equal labels) is NOT reproduced: at 800 labels with 4 trials differences are within one sd, and "label all" spends labels on
  the first 800 points only, so this comparison is not equal-label in the sense of the paper's figure (which plots beta-hat against labels queried). Inconclusive, not a refutation.
- Status: PARTIAL (code runs after two local patches; validity not contradicted; efficiency ordering unresolved at reduced budget).

## 5. Csillag et al. (prediction-powered e-values, ICML 2025)
- GitHub repo/code searches on 2026-10-31 (title keywords, "prediction-powered e-values", author account dccsillag) found no official code. Status NOT_AVAILABLE (re-check later).
  The repo's formula implementation and the Algorithm-1 tests (full-label limit, unqueried labels, exact conditional expectation by enumeration, factor nonnegativity at the floor 1 - a/b,
  step-by-step Algorithm 1) belong to the engine work and were not duplicated.

## 6. PPRM (Zhang, Cai, Yu, Simeone; ICML 2026; arXiv 2602.02229): independent reproduction
- No official code found. Script `scripts/hgxh2c/stage1/pprm_independent.py` (written from the paper's equations without importing `src/shiftlab/dive`): Eq. 16-19 estimators,
  betting source UCB (App. A.2), Eq. 22 variance process and CM-EB lower CS (uniform mixing density; psi_E(l) = -log(1-l) - l; bisection), Eq. 23 alarm, Eq. 26-28 reliance
  (window L = 60, clip to [0, eta_max=1]), fixed eta = eta_0 = 1 vs adaptive, SRM baseline (labeled only, Hoeffding source bound). delta_S = 0.05, delta_T = 0.2, n_t = 1, N_t = 15.
- Data are synthetic binary-loss streams (monitored model error ramping 0.08 -> 0.30 over t in [300, 900]; synthetic labels from a strong predictor), eps_tol = 0.04, source sample n_0 = 500 (our choice).
  The true running risk crosses R_0 + eps_tol at t = 688. 60 replications each for drift and nominal streams, T = 1500. Driver job `pprm_independent`.
- Not implemented: Ideal-PPRM and URM baselines, squared-loss variant, CIFAR10-C / LLM / telecom data.

| Quantity | Ours (synthetic) | Paper (real data) |
|---|---|---|
| PPRM alarm time, adaptive eta | 1025.2 +- 97.8 (alarm rate 1.00) | CIFAR10-C: ~760 (true crossing 600); LLM: ~500 (crossing 280) |
| PPRM alarm time, fixed eta | 1026.0 +- 107.7 (1.00) | Table 1 (LLM): fixed 460.7-527.8 |
| SRM alarm time | 1329.4 +- 101.1 (alarm rate 0.72) | CIFAR10-C: ~800; LLM: ~530 |
| paired PPRM - SRM | -313.7 steps | about -40 (CIFAR10-C), about -30 (LLM) |
| paired adaptive - fixed | -0.8 steps | -11 to -21 steps (Table 1: 519.1->498.3, 527.8->508.8, 460.7->449.9, ...) |
| false alarms under nominal stream | 0/60 for SRM, fixed, adaptive | guarantee: P <= delta_S + delta_T = 0.25 |

  Orderings that reproduce: PPRM alarms earlier than SRM; no false alarms. Not reproduced: the adaptive-vs-fixed reliance gain (ours is zero because the synthetic predictor is nearly
  perfectly aligned, so eta = 1 is already near-optimal), and the absolute delays (our gap to the true crossing, ~340 steps, is larger than the paper's 160 for CIFAR; synthetic stream,
  eps_tol and n_0 differ). Label: independent reproduction, not official code, not paper data.

## PaperBanana
Plots for these tables: **PaperBanana unavailable**. `tmp/papervizagent` exists but needs `GOOGLE_API_KEY`/`ANTHROPIC_API_KEY`/`OPENAI_API_KEY` (none set) and packages
`google-genai`, `streamlit` (not installed). No other plot generator was substituted; tables above are the deliverable, native repo plots are pointers only.

## Housekeeping
- `outputs/hgxh2c/stage1/` holds logs, pkl/pt/csv results and `markers/`; `tmp/` is git-ignored but `outputs/` is not (large `.pt` risk-monitor files; do not commit).
- Re-run everything: `python scripts/hgxh2c/stage1/run_native_repro.py --force`. Venv recipes are in the driver docstring.
