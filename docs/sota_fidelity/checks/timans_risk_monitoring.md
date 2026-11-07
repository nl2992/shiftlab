# Check: Timans et al., UAI 2025 (risk monitoring under unknown shift)

Independent check of `specs/timans_risk_monitoring.md`, 2026-11-06. No downloaded code was executed. The replay
test named by the repo could not be run (torch missing); an independent numpy replay was done instead (below).

## Sources actually read

- PMLR camera-ready: `https://raw.githubusercontent.com/mlresearch/v286/main/assets/timans25a/timans25a.pdf` (23 pp;
  proceedings page meta: pages 4204-4226, published 2025-07-11). arXiv 2506.16416v1 (19 Jun 2025, 23 pp) re-fetched.
  Word-level diff: identical except the arXiv watermark, page numbers, two reference entries/citations (PMLR cites
  "Koolen and Grunwald, 2022" in the GRO sentence where arXiv v1 cites "Grunwald et al., 2024"; one reference
  label), and reference-list ordering. Equations, lemmas, settings unchanged. The spec's "PMLR not read" item is
  closed; the PMLR PDF's own bib line misprints the volume as "PMLR 244" (the proceedings volume is 286).
- Code: `alextimans/risk-monitor`. Full SHA `4bf66a37dc2a3d7959bb9dcb325b61e8bb3c28e5` (2026-03-25 "resolve merge
  conflict floaters"; CONFIRMED). **History correction:** the repo's only commits before 2026-03-24 are `7a248f4b`
  "Initial commit" (2025-06-09) and README edits; all source files arrive in `a4f91d78` "latest local"
  (2026-03-24), 9 months after the paper. The code at the pinned SHA is therefore post-publication and the code
  actually used for the paper is UNVERIFIABLE (the spec only said "not inspected"). I read `exp/tracker_ood.py`,
  `tracker_uci.py`, `tracker_cp.py`, `config/cfg_exp.py`, `exp/exp_ood.py` (grep) at the pinned SHA via `gh api`.
- Repo side: `src/shiftlab/hgxh2c/baselines.py`, `engines.py`, `contract.py`; `src/shiftlab/dive/comparison_betting_engines.py`;
  `scripts/reproduce_timans_risk_monitor_paired_cost.py`; `tests/test_timans_unknown_shift_monitor.py`,
  `tests/test_comparison_betting_engines.py`, `tests/test_hgxh2c_engine.py`; `docs/hgxh2c/01_BASELINE_AUDIT.md`,
  `03_BASELINE_REGISTRY.md`.
- Scratch: `/private/tmp/claude-501/-Users-nigelli-Desktop-ICML-Shift-lab--claude-worktrees-shiftlab-methods-strategy-dba13e/06bf436b-d27c-42d6-9116-89f769a07352/scratchpad/check_watch/` (`pmlr_timans/`, `arxiv_timans/`, `code/tim/`, `replay.py`).

## Claim-by-claim (paper)

| # | Spec claim | Verdict | Evidence / location |
|---|---|---|---|
| 1 | Citation UAI 2025, PMLR 286:4204-4226 | CONFIRMED | `timans25a.html` meta: first page 4204, last 4226, 2025-07-11 |
| 2 | Not called GRAPA; bet named AGR | CONFIRMED | p.7 "lambda^AGR"; text says "approximately GRO" |
| 3 | Null Eq. 3: `E_{P_t}[z_t \| F_{t-1}] <= eps` for all t; alternative: exists t with `>` | CONFIRMED | p.4 (PMLR 4205-4206), Eq. 3, both labelled "risk controlled/violated" |
| 4 | Filtration `F_{t-1} = sigma((z_i, pi_i)_{i<t})` | CONFIRMED | p.4 forecasting game text; defined in App. A.1 |
| 5 | Wealth Eq. 4 `prod(1 + lambda_i (z_i - eps))`, M_0=1, lambda predictable, lambda in [0,1/eps) | CONFIRMED | p.4 Eq. 4; Lemma 4.1 p.5 |
| 6 | Lemma 4.1 = test supermartingale (not martingale) | CONFIRMED | Lemma 4.1 text: "valid test supermartingale for the predictable betting rate" |
| 7 | Lemma 4.2: `P(exists t: M_t >= 1/delta) <= delta`, per psi, not across psi | CONFIRMED | p.5 Lemma 4.2; p.4 "Practical considerations": guarantee "across time for every threshold, and not across thresholds" |
| 8 | psi-CS Eq. 5 `C_t = {psi : M_t(psi) < 1/delta}`; shrinkage to zero means model update; updating is future work | CONFIRMED | p.4 |
| 9 | Betting rate AGR: `max{0, min{(mu-eps)/(sigma^2+(mu-eps)^2), (1/2)/eps}}` with running mean/variance over i<t | CONFIRMED | p.7 displayed formula; code `tracker_ood.py` `get_bets` (approx_grapa branch): `c = 0.5`, jitter 1e-10 on mu, var and term (not in paper), `torch.var` unbiased over `losses[ts_start:ts]` (excludes current step: predictable) |
| 10 | Grid bet (spec: "argmax over lam in arange(0.1, 1/eps, 0.1)") | CONFIRMED | `get_bets` grapa branch: `torch.arange(0.1, 1.0/EPS, 0.1)`, mean past log growth, `argmax`. Paper only says "exhaustive root-finding over a fine grid" (App. C) and Def. 4.4. The code's `arange` at eps=0.5 gives {0.1,...,1.9}; floating-point end-point behaviour of `arange` is not specified by the paper |
| 11 | Burn-in `t_burn = floor(100/B)`; bets zero before | CONFIRMED | p.7 "Batching, sliding window and burn-in": no testing for any tracker "aside of the true risk"; code `burn_in = int(NR_BURNIN/BATCH_TIMESTEP)` and `if ts < burn_in: bet = zeros` (`NR_BURNIN = 100`, `cfg_exp.py:79`). Semantics: in the code the e-value factor is exactly 1 during burn-in (zero bet); the first-step e-process is set to ones regardless (`get_eprocess`, ts==0). The paper says only "does not test", so zero-bet is the code's reading |
| 12 | Sliding window S bets only; product over full history | CONFIRMED | `ts_start = max(ts - window, 0)`, `get_eprocess` multiplies the previous full-history process; `TRACKER_WINDOW = [0,0,0]` default (`cfg_exp.py:81`) |
| 13 | Batching by arithmetic mean of per-sample factors | CONFIRMED | `get_evalues(reduction="mean")`; paper App. C |
| 14 | Defaults eps = delta = 0.1; psi grid 0:0.01:1; T=1500 (outlier), 2000 (FMoW); S=50 / 365 / 50; R=50 | CONFIRMED | `cfg_exp.py:57,59,65,67-70`; paper Sec 6.1 (T=1500, ResNet-50, CIFAR-10 vs SVHN), 6.2 (FMoW DenseNet-121 T=2000, S=365; Naval RF, S=50, ~12,000 rows, psi in [0,0.05]); figure captions (R = 50) |
| 15 | Direction one-sided (upward risk) | CONFIRMED | Eq. 3 |
| 16 | No missing/delayed/selective feedback; loss observed each step | CONFIRMED (by absence) | Sec 2: stream "covariate -> decision -> label -> loss"; no treatment of delay or missingness |
| 17 | Shift assumptions: none, dependence allowed given the null | CONFIRMED | Sec 2 p.3 and Remark, App. A |
| 18 | Lemma 4.3 asymptotic consistency; Prop 4.5 delay bound is approximate | CONFIRMED | Lemma 4.3 p.5, stated for "finitely many" non-violating steps then violation; Prop 4.5 uses summation process (proofs not re-derived) |
| 19 | Covariate-dependent bet not covered by the stated filtration | CONFIRMED (and harmless) | `F_{t-1}` is generated by past (z, pi) only. If a ShiftLab null `E[Z_t \| G_{t-1}] <= 0` holds for a finer filtration G, the tower rule gives the same inequality for the coarser one, so the loss-only filtration is the weaker requirement. Recorded as: no gap in that direction |
| 20 | Code identity across trackers | CONFIRMED | `diff tracker_ood.py tracker_uci.py` and `tracker_cp.py`: differences confined to `get_risk` methods of other classes; `EProcessTracker.get_bets/get_evalues/get_eprocess/check_stop_time` identical |
| 21 | `check_stop_time` records first crossing, process continues | CONFIRMED | `check_stop_time`: marks `stop_time == -1` entries only; at the last step unstopped psi get `T` |
| 22 | Stop counter for point-risk tracker 5; e-process 0 | CONFIRMED | `cfg_exp.py:84` `[5, 25, 0]` (comment: 0 = stops immediately on crossing); `stop_counter` marked "not used" in EProcessTracker |
| 23 | psi selection `min` is a convenience without guarantee | CONFIRMED | `exp_ood.py` `get_valid_psi` (default `psi_select="min"`, call at ~468); paper p.4 |
| 24 | Spec section 1: "newest commit ... README/merge commits only; code equals paper code UNVERIFIED" | CORRECTED | All code is from 2026-03-24 onward (see Sources). Equality with paper-time code is not merely unverified; it is unverifiable from the public history |

## Claim-by-claim (ShiftLab replay audit of `timans_*`)

Audit location: `docs/hgxh2c/01_BASELINE_AUDIT.md` section 3 (and registry rows 4-5, `03_BASELINE_REGISTRY.md:20-21`).
It names `tests/test_timans_unknown_shift_monitor.py`, `tests/test_comparison_betting_engines.py::test_timans_engines_match_existing_verified_replay`
and `scripts/reproduce_timans_risk_monitor_paired_cost.py::verify_upstream_replay`; recorded errors 0.0
(approx) and 1.86e-7 (grid), tolerance 2e-5.

| # | Claim | Verdict | Evidence |
|---|---|---|---|
| R1 | A test exists and can be re-run | UNVERIFIABLE here | `.venv/bin/python -m pytest tests/test_timans_unknown_shift_monitor.py`, `uv run pytest -k timans`: collection errors, `ModuleNotFoundError: No module named 'torch'` (the repo imports torch at module level via `shiftlab.dive.risk_proxy_monitor_grid`; torch is the optional `neural` extra, `pyproject.toml:16`). 94 test modules fail collection for the same reason; `tests/test_hgxh2c_engine.py` and `tests/test_comparison_betting_engines.py` also need torch. I did not install torch (large download). The three Timans test files are NOT run |
| R2 | `verify_upstream_replay` compares to the official `EProcessTracker` | CONFIRMED (code read) | `reproduce_timans...py:150-181` imports `exp.tracker_uci.EProcessTracker` from a supplied checkout, 137-point stream, tolerance 2e-5 |
| R3 | Recorded replay report exists (max error 0.0 / 1.86e-7) | UNVERIFIABLE | `outputs/` is gitignored; `outputs/shiftguard_unified/sota_reproductions/` in the main checkout lists 6 directories and none is `timans_unknown_shift_paired_cost_v1`; no copy found. The audit doc itself says "NOT re-run in this audit" |
| R4 | The recorded replay stream exercises the bet | CORRECTED (important) | The replay stream is `np.linspace(0.02, 0.98, 137)` with eps = 0.5 (`reproduce_timans...py:~163`). I ran `_timans_logs` (extracted by `ast`, numpy only) on it: approx-GRAPA bets are identically zero (0 nonzero bets, log wealth 0 at every step), so a recorded error of 0.0 is vacuous (0 vs 0) for approx-GRAPA; grid-GRAPA picks lambda = 0.1 on 37 steps and never exceeds 0.1. The replay therefore does not test the cap, the variance term, or large bets. The 1.86e-7 grid error is the float32-torch vs float64 difference on a lightly exercised path |
| R5 | `_timans_logs` equals the upstream rule | CONFIRMED by my independent port | I wrote a float64 numpy port of `EProcessTracker.get_bets/get_evalues/get_eprocess` from the code as read (unbiased variance, 1e-10 jitters, cap 0.5/eps, burn-in 100, `arange(0.1,1/eps,0.1)` grid) and compared with the repo's `_timans_logs` on 5 streams x 2 rules (including iid Beta mean 0.6 and 0.7, a mid-stream shift, and a null mean 0.45) where bets reach the cap (approx max bet 1.0 = 0.5/eps, grid max 1.9): max |difference| <= 1.4e-13 everywhere (0 where bets are zero). This validates the repo formula against my reading of the upstream source, not against executed upstream (torch) code |
| R6 | hgxh2c `timans_*` engines are replay-verified | CORRECTED | Two separate implementations exist. (a) `_timans_logs` / `comparison_betting_engines.replay_engine` (src/shiftlab/dive): the replay-checked path. (b) `src/shiftlab/hgxh2c/engines.py` (lines 398-413 streaming scan, 686-699 step path) used by `hgxh2c/baselines.py:212-235` `timans_approx_C/B`, `timans_grid_C/B`. `grep` finds no test comparing (b) with `_timans_logs` or upstream: `tests/test_hgxh2c_engine.py` only checks causality (`timans_grid_C` in `test_stake_never_uses_unreleased_labels`, line 193), null FAR, and GPU/CPU agreement (lines 279-280). Algebra check by reading: engines compute `mu = mean(x)/(2 bx) + 1e-10`, `var = var(x)/(4 bx^2) + 1e-10`, `bet = clamp(mu/(var+mu^2) + 1e-10, 0, 1)`, `lam = bet/(2 bx)` with z = 0.5 + x/(2 bx), eps = 0.5, so cap 1 = 0.5/eps: the same formula in the shifted frame, with the jitter added to (mu-eps) not to mu (1e-10 effect). Not numerically replayed (needs torch) |
| R7 | Engines use burn-in of 100 labelled events not rounds | CONFIRMED | `engines.py`: `torch.where(cn >= tr.burn_in, ...)`; `TrackSpec.burn_in = 100` (line 116); `cn` is the count of released active (queried) events. Native paper: 100/B rounds. UNVERIFIABLE how many labels this consumes under the contract |
| R8 | Two score maps | CONFIRMED | (a) `replay_engine`: `0.5 + 0.5*values/bounds` (`comparison_betting_engines.py:95`, `tests/...:69`); (b) engines: `bx = max(bd, 1/qfl)` sup-scale (`engines.py:566`, `contract.py:64`) applied to the prediction-powered increment, not to a fully observed Z. They are different affine maps of the same increment (equal only when bx equals the Z bound) |
| R9 | Engines test a PP/queried-only increment, so Lemma 4.1 does not transfer | CONFIRMED | `corr` default `"pp"` in `TrackSpec`; registry note at `03_BASELINE_REGISTRY.md:43` already says the guarantee needs a predictable score map. The honest label is Timans-style, T3 |
| R10 | Sprint comparator pools use `timans_*` | CORRECTED (new) | `grep -rl timans` over `scripts/sota_sprint`, `scripts/failure_atlas_v2_flq`, `scripts/promising_directions/sota`, `src/shiftlab/sota_search` returns nothing. `timans_*` live only in the hgxh2c baseline registry and in `dive` comparison/prescreen scripts |

## Own numerics

`check_watch/replay.py` (numpy, repo function extracted by `ast`, independent upstream port written from the read
source). Results (max abs log-wealth difference, final log wealth, max bet):
linspace137 approx 0.0 / 0.000 / 0.000; linspace137 grid 2.2e-16 / 1.282 / 0.1; Beta(6,4) approx 1.8e-15 / 24.40 / 1.0;
Beta(6,4) grid 3.6e-15 / 40.32 / 1.9; Beta(7,3) approx 1.4e-14 / 54.42 / 1.0; shift stream approx 1.4e-13 / 28.53 / 1.0;
null Beta(4.5,5.5) approx 0.0 / 0.000 / 0.000 (bets zero because the running mean is below eps). Grid-rule bets on the
null stream are 0.1 throughout (log wealth -1.25): the grid rule always bets at least 0.1 whereas approx-GRAPA bets 0
below eps; this is a property of `arange(0.1, ...)` (no zero candidate) in both upstream and repo.

## Tier call

Spec: T1-claimed for the scalar rule on a full-observation stream, T3 for `timans_*_C/B` on the budgeted, delayed
streams. AGREE with the T3 call. The T1 claim is downgraded to "T2-verified, T1 unverified": the formula matches
the printed equation and my independent port of the upstream source, but (i) upstream code is post-publication,
(ii) the recorded upstream replay is unavailable and its approx-GRAPA stream is degenerate (bets zero), (iii) no
test ties the hgxh2c engines to the replay-verified function. Recommended fixes before relying on it: add a test
that runs `hgxh2c` `timans_approx_C/grid_C` on a fully observed, propensity-1 tape and equals `_timans_logs` on a
stream whose running mean exceeds eps; change the replay stream so bets hit the cap.

## Remaining UNVERIFIABLE

- Paper-time upstream code; native `exp_uci` numbers (3-trial re-run in `docs/hgxh2c/02_NATIVE_REPRODUCTION.md`) and supplement Tables 1-5 (not transcribed).
- The recorded replay report values, and execution of any torch-based test (environment lacks torch).
- Validity of the Timans proof under delayed release and propensity-selected queries (outside the paper).

## Verdict

ACCEPT WITH CORRECTIONS. Apply rows 24, R3, R4, R6, R10 to the spec and LEDGER; keep the T3 designation and the
"Timans-style" naming for budgeted variants.
