# SOTA fidelity ledger (Opus review decisions)

One entry per method. "Decision" is the lead-session review after the spec (`specs/`) and the
independent check (`checks/`). Registration into `scripts/sota_sprint/bench.py` /
`scripts/failure_atlas_v2_flq/suite.py` is done centrally by the lead session after code review,
so parallel implementers never touch shared registry files.

## Shekhar & Ramdas, ICML 2024 (RCS change detection)

- Spec: `specs/shekhar_ramdas_cs_change_detection.md`; check: `checks/shekhar_ramdas_cs_change_detection.md`
  (ACCEPT WITH CORRECTIONS).
- Sources read: PMLR camera-ready (15 pp), arXiv v2, official code `sshekhar17/SCDtoCS@c3a7ece`.
- Review notes: the check's corrections are accepted. (1) Both printed lambda schedules carry a
  `min(., 1)` cap that the code omits. (2) The author code is not a faithful copy of the printed CS
  (first-observation skip, pseudo-weight initial state, uncapped lambda), so T1 is unavailable.
  (3) Plain level alpha=0.05 gives ARL >= 20 labels and no finite-horizon false-alarm bound; the
  contract adapter must use Remark 2.5 level spending (level 1 - 6 alpha / (pi^2 n^2) for the CS
  started at n), which bounds P(tau < inf) <= alpha. (4) Delay bounds are vacuous at B=200; delay
  is measured, not claimed.
- Decision: **IMPLEMENT.** T2 native core from Def 2.1 + Appendix C Hoeffding CS as printed
  (main-text schedule `i log(i+1)` default, Appendix C `i(i+1)` selectable, both capped at 1), and a
  T3 label-clock partitioned adapter (promotion trigger and post-promotion rollback trigger on the
  rescaled paired loss) using Remark 2.5 spending. Table name: "Shekhar–Ramdas RCS, common-contract
  adapter (T3)".

## Han, Huang & Wang, ICML 2024 (adaptive rolling window, ARW)

- Spec: `specs/han_rolling_window.md`; check: `checks/han_rolling_window.md` (ACCEPT WITH CORRECTIONS).
- Sources: arXiv 2402.08672v2 and PMLR camera-ready (same maths; theorem/equation numbers differ,
  e.g. arXiv Thm 3.1 = PMLR Thm 3.8, so cite with a version label); code `eliselyhan/ARW@c48f830`
  (no licence: re-implement from the paper, do not copy code).
- Review notes: the paper's experiments use M=0 and delta'=0.1, which sit outside the theorem
  (needs M=b-a, delta'=delta/(3t); delta'=0.1 is nominal delta=0.3t, vacuous for t>=4). The code's
  tie rule (`<0`) differs from Algorithm 2 (`<=0`); with 0/1 losses ties are common, so the rule
  matters. No delay, switch margin or sequential validity in the paper.
- Decision: **IMPLEMENT.** T2 core from the printed equations/algorithms (two-model tournament =
  one pairwise match), two named constant sets: `theory` (M=b-a, delta'=delta/(3t), default) and
  `paper_experiments` (M=0, delta'=0.1); tie rule per Algorithm 2 by default, code rule selectable.
  T3 label-clock adapter ("label-clock ARW, common-contract adapter"). No validity claim.

## IUPM, Koebler et al., AISTATS 2025

- Spec: `specs/iupm.md`; check: `checks/iupm.md` (ACCEPT WITH CORRECTIONS).
- Sources: arXiv 2505.07023v1 = PMLR text; code `alexanderkoebler/IUPM@8e3a882` (MIT).
- Review notes: IUPM estimates one model's performance under covariate shift via optimal transport
  and triggers labelling when its uncertainty exceeds 0.1; it has no test, no alarm and no paired
  comparison, and queries ~50% of a 200-point batch per trigger. ShiftLab benchmark streams carry no
  covariates (`context` is None) and no labelled reference set.
- Decision: **EXCLUDE from the synthetic deployment suite (inapplicable, not weaker).** Record as a
  novelty constraint on any acquisition-only claim. Revisit only for a real-data stream with
  covariates, as a T3 acquisition component paired with an explicit decision rule.

## Regol, Schwinn, Sprague, Coates & Markovich, ICML 2025 ("When to Retrain", UPF)

- Spec: `specs/regol_when_to_retrain.md`; check: `checks/regol_when_to_retrain.md` (ACCEPT WITH CORRECTIONS).
- Sources: PMLR PDF and arXiv v1 (hashes match between spec and check). No official code found
  (PMLR links none; OpenReview not opened because of a bot challenge, so "no code" is unverified).
- Review notes: equations, defaults and Tables 1–2 confirmed. Table 3 is not a reproduction target
  (its UPF values disagree with Table 1). The repo's in-sample sigma^2 is a natural reading of the
  Gaussian likelihood (the paper does not specify it), not a deviation. **Proposition 3.1 as printed
  is false**: Eq. 40 reverses an implication; optimality gives alpha <= L (T - r* + 1)^2, so
  r* <= max(0, floor(T - sqrt(alpha/L)) + 1). Independent exhaustive check (T <= 7, 29,099
  instances): printed bound fails 5,225 times, corrected bound 0 times. The paper's decision rule
  does not depend on Prop. 3.1.
- Fixed now: `docs/research_refinement_v1/PRIOR_ART_AND_NOVELTY_MATRIX.md` mis-stated the
  objective (line ~362) and claimed the quantile rule was blog-only (line ~919); both corrected
  with a dated note.
- Decision: **IMPLEMENT (T3 only).** Contract comparator `upf_style_switch_timing_T3` as in spec
  section 6 (period length m locked before runs; IPW period cells from matured labels under a fixed
  shared labelling rule; forecaster sigma must include IPW noise; 0.95-quantile keep-vs-switch rule,
  reversible). Uncertified class. Never labelled "UPF" or "Regol et al." in result tables. The
  existing `src/shiftlab/dive/upf_retraining.py` stays the T2 native port.

## Model Selector, Okanovic et al., AISTATS 2025

- Spec/check: `specs/model_selector.md`, `checks/model_selector.md` (ACCEPT WITH CORRECTIONS).
- Sources: arXiv 2410.13609v2 and PMLR camera-ready (same algorithm; camera-ready adds App. D.4,
  a heuristic eps range [0.45, 0.49]); code `RobustML-Lab/model-selector@6aa57e57`.
- Review notes: `ModelSelectorNative` is a T1 claim resting on author-parity tests that are
  **skipped** because `vendor_sota/` is empty in both checkouts; T1 is therefore not currently
  re-verified. `model_selector_causal` is T3 (record gate); with two models and two classes it
  reduces to paced disagreement sampling. The record gate used exact `!=`, which with >= 3 classes
  rejects events on ~1e-16 rounding differences.
- Fixed now: record gate compares with a 1e-12 tolerance
  (`scripts/promising_directions/sota/competitors/model_selector.py`); binary benchmark streams
  unaffected. `tests/promising_directions/test_sota_model_selector.py`: 21 passed, 8 skipped
  (author parity, vendor absent).
- Decision: **KEEP** (native T1-pending-parity, causal adapter T3). Re-run parity once vendor clones
  are restored (needs user go-ahead; see open actions).

## Tenzer, Tolochinsky & Romano, ICML 2026 (betting on predictions)

- Spec/check: `specs/tenzer_ppi_betting.md`, `checks/tenzer_ppi_betting.md` (ACCEPT WITH CORRECTIONS).
- Sources: arXiv 2605.28533v1 = PMLR text; code `elad-tolo/betting_on_predictions@f99e196b`.
- Review notes: the paper's test uses the Eq. 2 soft-rank statistic over M=128 resampled null
  datasets and needs a samplable null (label/concept shift) with n free labels per step. ShiftLab's
  `tenzer_*` entries are a different statistic (Gaussian LR, proxy as label): inspired-by only.
  In the author code gamma barely moves (AdaGrad eta0=1e-4), and the simulations sample only the
  alternative.
- Fixed now: stale "not implemented" note in `docs/hgxh2c/01_BASELINE_AUDIT.md` updated to say the
  entries exist but are inspired-by only.
- Decision: **RELABEL, DEFER implementation.** Any HG/H2c novelty claim (track C) must first get a T1
  port of the authors' simulation setting plus a T3 known-null binary slice. Not needed for tracks
  A/B.

## CAMS / CAMS-MAX, Liu et al., NeurIPS 2024

- Spec/check: `specs/cams_status.md`, `checks/cams_status.md` (ACCEPT WITH CORRECTIONS).
- Review notes: pinned SHA `6cbcc62f` equals upstream HEAD; positions match. Correction: the
  paper's stochastic rule recommends argmax of w_t (the author code samples), so `deploy="argmax"`
  follows the paper, not an adapter choice. Paper-vs-code gaps to disclose: eta = sqrt(P/t) in code
  vs sqrt(ln m / t) in paper; code sets u_t = 0 with no 1/sqrt(t) floor when the entropy score is 0.
  Parity tests skipped (vendor absent).
- Decision: **KEEP** (native T1-pending-parity, adapters T3); docstring correction queued with the
  central registration pass.

## Open actions needing the user

- Restore pinned author clones under `vendor_sota/` (CAMS, Model Selector, Model Picker, SMCS,
  variance-min) so the skipped author-parity tests run again. This downloads and executes
  third-party research code, so it waits for an explicit go-ahead.

### Han ARW — Opus code review (2026-11-06)

- Files: `scripts/promising_directions/sota/competitors/han_arw.py`, `tests/sota_fidelity/test_han_arw.py`,
  `docs/sota_fidelity/impl/han_arw.md`. 20 tests pass.
- Review: every core line maps to a printed equation with version labels; deviations complete;
  no author code copied. Fixed one bug: the adapter cast delivered losses with `int()`, which would
  truncate non-0/1 losses on real streams; now `float()`.
- Smoke finding (5 seeds, descriptive only): on the label clock `paper_experiments` (M=0) always
  picks window length 1 (zero variance proxy with one label), and `theory` (M=2) never shrinks the
  window over 60–140 labels, so it acts as a whole-history mean that flips on noise (17–21 switches
  on the null with margin 0). This is the method's honest behaviour under B=200, not a bug.
- Status: **APPROVED for central registration** as `han_arw_label_clock` (T3, uncertified class),
  default constants `theory`, margin 0. A margin-tuned variant counts as an equally-tuned baseline
  only if tuned on development seeds under the same budget as any candidate.

### Regol-style T3 switch timing — Opus code review (2026-11-06)

- Files: `scripts/promising_directions/sota/competitors/upf_style_switch_timing.py`,
  `tests/sota_fidelity/test_upf_style_switch_timing.py`, `docs/sota_fidelity/impl/upf_style_switch_timing.md`.
  11 passed, 2 skipped (cross-checks against the torch-based T2 port; torch is absent from the uv
  environment; both pass under the conda interpreter per the implementer). The adapter itself does
  not import torch.
- Review: uses only released labels; IPW cells on disagreement rounds (agreement loss is common to
  both arms); sigma = residual MSE + mean Horvitz–Thompson variance (conservative); reversible
  backward recursion per Eqs. 17–20 with the Eq. 16 strict quantile comparison. Period completeness
  uses the task delay, which `suite.build_suite` passes to every comparator as a public contract
  parameter; acceptable, recorded as a deviation.
- Behaviour (descriptive, not evidence): switches on 8/20 null seeds (F0_null and V_null) with
  untuned m=100, delta=0.95. Consistent with a decision rule that has no error control and
  extrapolates a noisy arm coefficient; not a bug. Cheaper than never-switch on F0_better, dearer on
  F3_reversal_800 (switches at round 400, never returns).
- Status: **APPROVED for central registration** as `upf_style_switch_timing_T3`, uncertified
  class. It cannot serve as a safety comparator; for a cost claim it must be compared with m, delta
  locked on development seeds before any confirmation run.

### Shekhar–Ramdas — Opus code review (2026-11-06)

- Files: `scripts/promising_directions/sota/competitors/shekhar_ramdas.py`,
  `tests/sota_fidelity/test_shekhar_ramdas.py`, `docs/sota_fidelity/impl/shekhar_ramdas.md`. 19 tests pass.
- First review: core (Def 2.1, Appendix C Hoeffding CS with capped lambda, Remark 2.5 spending)
  and promotion/rollback orientation approved. **Required change:** the paper's joint-emptiness
  rule is proved for i.i.d. pre-change data; under ShiftLab's composite, drifting conditional-mean
  null two CSs can be mutually disjoint while each stays inside Theta0, giving false alarms.
- Resolution: added `stop_rule="any_excludes"` (ShiftLab deviation): stop when a single CS's
  *instantaneous* interval is disjoint from Theta0. The implementer found that using the running
  intersection (Remark 1.5, which presumes constant theta) is wrong under drift (98% false alarms);
  the instantaneous Hoeffding CS covers the lambda-weighted average of conditional means, which lies
  in Theta0 by convexity, and the union bound over Remark 2.5 levels gives P(false alarm) <= alpha.
  Constructed drift test (Y-mean 1.0 for 60 labels, then 0.5; alpha=.05, 300 reps): joint 1.00,
  any_excludes 0.00. Any any_excludes alarm is also a joint alarm; the rules coincide for singleton
  Theta0 (Prop 3.1); Remark 3.2 confirmed in the independent check.
- Status: **APPROVED for central registration**: `shekhar_ramdas_rcs_t3` (paper joint rule) and
  `shekhar_ramdas_rcs_t3_anyexcl` (composite-null-safe deviation). For harm/safety claims, the
  `_anyexcl` variant is the appropriate comparator; both are reported. The F5 serial-dependence
  null (0.0375 over 400 episodes) is outside the stated null and carries no validity claim.

## WATCH, Prinster et al., ICML 2025

- Spec/check: `specs/watch_prinster.md`, `checks/watch_prinster.md` (ACCEPT WITH CORRECTIONS).
- Sources: arXiv 2505.04608v4 = PMLR (one table cell differs); code `aaronhan223/watch@3d17fca5`
  and paper-era commit `3b10510`.
- Review notes: WATCH monitors one deployed model's conformity with weighted conformal test
  martingales (two-sided "jumper" betting, Eqs. 6–7; SR and CUSUM variants) and adapts after mild
  shift. Thm 3.1 holds only at t_ad; Props 3.2/3.3 concern a modified null (Eq. 28). Author code
  issues: X-CTM alarm overwritten (`main.py:154-157`, also in paper-era code), SR threshold
  hard-coded 1e4 vs ARL 20,000, classifier differs from the paper's MLP, and the composite jumper
  shares capital across jumpers (not an exact martingale; null drift positive in 64% of steps in
  the checker's numpy test). **The sprint comparator streams carry no covariates** (loss tapes
  only); `PublicEvent.x` exists only in `src/shiftlab/contract` / `real_tasks`. So the covariate
  weights cannot run on the sprint pool, and only an unweighted CTM is possible there.
- Existing `src/shiftlab/sota_search/detectors.py::watch` uses power calibrators on |y-p| with a
  calibration set from a default simulation: **inspired-by** (already labelled
  SOURCE_INSPIRED, weights omitted); must not be reported as WATCH.
- Decision: **IMPLEMENT NEXT (not done in this pass).** T2 port of the unweighted conformal test
  martingale with jumper betting (paper equations, not the shared-capital code) as a post-promotion
  degradation sentinel for track A, T3 on the label clock. The weighted version only on a real
  stream with covariates and a source sample.

## Timans et al., UAI 2025 (risk monitoring under unknown shift)

- Spec/check: `specs/timans_risk_monitoring.md`, `checks/timans_risk_monitoring.md`
  (ACCEPT WITH CORRECTIONS).
- Sources: arXiv 2506.16416v1 = PMLR (two reference entries differ); code
  `alextimans/risk-monitor@4bf66a37` (all files first committed 2026-03-24, after the paper).
- Review notes: the null E[z_t | F_{t-1}] <= eps matches ShiftLab's paired excess-cost null under
  an affine map. The repo's T1 claim for `timans_*` is **not currently supported**: the recorded
  replay report is absent (gitignored outputs), and the replay stream used makes approx-GRAPA bets
  identically zero, so its zero error is vacuous. The checker's independent float64 port of the
  upstream tracker matches `_timans_logs` to 1.4e-13 on streams where bets reach the cap, but the
  hgxh2c `timans_*` engines have no replay test against it. The repo's replay test needs torch,
  which is absent from the uv environment. `timans_*` are not in the sprint pools.
- Decision: **DOWNGRADE to T1-pending** until a non-vacuous replay test (bets reaching the cap)
  is added for the hgxh2c engines; then consider a T3 label-clock entry for the sprint pool.

## Shin, Ramdas & Rinaldo, NEJSDS 2024 (e-detectors: e-SR / e-CUSUM)

- Spec/check: `specs/shin_edetectors.md`, `checks/shin_edetectors.md` (ACCEPT WITH CORRECTIONS).
- Sources: NEJSDS vol 2 pp 229–260 and arXiv 2203.03532v4 (side-by-side on the passages read);
  code `e_detector_paper@2fbf585`, `stcp@c9ff9a6`, `stcpR6@9eaafb4`.
- Verified: no two-sided construction in the paper (stcpR6 `two.sided` = 50/50 mixture, alpha/2
  each); the M_0 = 1 initialisation typo sits before (3.5)/(3.6) on NEJSDS p238; Remark 2.7 (p234)
  is unproved in the paper (the checker supplies a proof in the check file). The checker's own port
  of Algorithm 3 reproduces the paper's NBA (Cavaliers) e-SR alarm at game 378 (2015-03-10) only
  with the Eq. (70) increment the code uses; Eq. (72) gives game 427. e-CUSUM gives 445 vs the
  paper's 444 (unexplained). Bernoulli Delta_U is 0.41 in the text vs 0.49 in the paper repo.
- **Track-A consequence.** `scripts/failure_atlas_v2/restart_monitor.py:72-102` (RMM) is e-SR
  (Def 2.6) with Remark 2.7 start weights over a 3-bet grid, starts every 10 labels, on the label
  clock; the sign flip after promotion is already in RMM (`:212`). `fam_e.py:62-85` SRRDetector's
  CUSUM variant is max-over-starts of the bet mixture (never larger than the paper's
  mixture-of-CUSUMs). E_rb adds an alpha=0.10 rollback detector over a remaining-budget start grid,
  a horizon gate and halving of the base alpha. The statistic is therefore Shin et al.'s; what is
  ShiftLab-specific is system-level (host alpha split + host restart, post-verdict acquisition
  under the shared budget, delayed-feedback ordering, E_rb's gate), with no joint guarantee proved.
  `docs/sprint2/novelty/NOVELTY.md:118` already calls RMM "a composition". **The matched simple
  competitor (start-at-every-label two-sided e-SR with Remark 2.7 weights, restart at switch) has
  never been run.**
- Existing `horizon_edetectors.py` / `paired_edetectors.py`: recursions match the paper; stake
  grids are ad hoc (not Algorithm 3); the H/alpha horizon threshold = Remark 2.7 with weights 1/H.
- Decision: **IMPLEMENT NOW (highest priority for track A).** `two_sided_esr_label_clock` (T3):
  Algorithm 3 bounded-mean e-SR with the Eq. (70) increment as the code does (T1 reproduction test
  on the NBA example where the data are public), two one-sided detectors at alpha/2 each (stcpR6
  construction), start at every label, restart at each switch, common pacer. Any E_rb/RMM claim must
  beat it on development seeds before a novelty claim is made.

## Saha & Ramdas, arXiv 2607.28322v1 (non-partitioned e-detectors)

- Spec/check: `specs/saha_ramdas_nonpartitioned.md`, `checks/saha_ramdas_nonpartitioned.md`
  (ACCEPT WITH CORRECTIONS). Preprint only; author code `Aytijhya/Nonseparated-e-detector@1966da8`.
- Review notes: ShiftLab's `check_nonpartitioned_pfa.py` covers the Gaussian Eq. (6) with a
  numerical infimum (anti-conservative in direction, but the checker measured log D lower by at most
  0.0033 on a finer grid; crossing unchanged). The bounded-mean universal portfolio is not
  implemented. It is a sentinel (detects any change), not a promotion/rollback certificate.
- Decision: **NOVELTY CONSTRAINT ONLY, no comparator now.** Any claim of a new detector structure
  must be positioned against it.

## Page–Hinkley (classical; river / scikit-multiflow)

- Spec/check: `specs/page_hinkley.md`, `checks/page_hinkley.md` (ACCEPT WITH CORRECTIONS).
- Review notes: ShiftLab's `detectors.page_hinkley` equals `cusum(slack=delta)` centred on source
  moments, with no forgetting, `min_instances` or reset, and delta 0.1 (river defaults: min_instances
  30, delta 0.005, threshold 50, alpha 0.9999). It is not Page–Hinkley in the river sense.
  `pyproject.toml` pins `river==0.26.1` in the optional `drift` extra, so a T1 entry is possible by
  calling river itself. Page 1954 / Hinkley 1971 were not read (unverifiable).
- Decision: **RELABEL** the existing entry as "one-sided CUSUM with slack (PH-style)" in any new
  table; add a river-backed T1 entry with the two-sided e-SR work (cheap, same harness).

### Two-sided e-SR and river Page–Hinkley — Opus code review (2026-11-06)

- Files: `competitors/shin_esr.py`, `competitors/river_page_hinkley.py`,
  `scripts/sota_fidelity/smoke_shin_esr.py`, `tests/sota_fidelity/test_shin_esr.py`,
  `tests/sota_fidelity/test_river_page_hinkley.py`, `docs/sota_fidelity/impl/shin_esr.md`; registry
  entries `two_sided_esr_label_clock`, `river_page_hinkley_t3` (river imported lazily; registration
  test skips optional-package entries when absent).
- Reproductions: Algorithm 3 e-SR alarms at game 378 (2015-03-10) on the paper's NBA example,
  matching the paper; e-CUSUM at 445 vs the paper's 444 (recorded, not tuned). The NBA test reads
  the CSV as data and skips when it is absent (set `SHIFTLAB_NBA_CAV_CSV`). river 0.26.1 reproduces
  its own docstring alarm (1006, 5) → detector T1; wrappers T3.
- Review: Remark 2.7 calibration with start weights summing to 1 and threshold 1/alpha_side per
  side (alpha/2 each, stcpR6 split); `rmm_matched` (default) mirrors RMM's finite-horizon form
  (weights 1/B over the budget) so a comparison isolates start spacing and restart behaviour. Each
  restart after a switch is a fresh detector with its own budget (as in RMM); there is no joint
  guarantee across phases. Null false alarms over the full budget ~0.008 per side vs 0.025 target.
  Page–Hinkley is a change detector, not a sign test: it never promotes when the challenger is
  better from the first label (recorded property, not a bug).
- Smoke (5 seeds, descriptive): no resolvable difference vs RMM / E_rb / LRMD_k1; the ARL variant
  promotes on 5/5 null seeds; every-label starts promoted less often than 10-label spacing on
  F0_better (0.6 vs 1.0), mechanism untested.
- Status: **APPROVED for central registration.** Not done: Algorithm 2 (adaptive e-SR), the
  Bernoulli psi_B grid, numerical comparison with the R code.
- Next step for track A: development-seed comparison (>= 100 fresh dev seeds, reversal and late
  regimes) of E_rb and RMM against `two_sided_esr_label_clock` (both calibrations, both bet grids)
  before any novelty claim.

## Development comparison E_rb / RMM vs two-sided e-SR (2026-11-07)

- Protocol locked in `70a84679` before the run; results in `esr_vs_erb_dev_results.md` / `.json`.
- Primary (reversal, 4 regimes × 4 hosts, 100 seeds): E_rb − e-SR = +1.90 [−1.01, +4.80]. **Not
  favourable to E_rb** under the stated rule. RMM − e-SR on reversal = +9.40 [+6.36, +12.44].
  E_rb − e-SR on F0_better = −18.66 [−23.20, −14.13] (e-SR promotes more slowly). Late regimes
  unresolved (−1.41 [−3.44, +0.62]); E_rb = RMM on every late seed.
- Every valid adaptive method is costlier than never-switch on all four reversal regimes.
- Null safety passes for all valid policies; `esr_arl` is invalid (promotes on ~100% of nulls).
- Decision: **pivot within track A** (stop claiming the rollback statistic; test economic gating
  or a promotion-speed component directly). Track B (late change) becomes the next priority.

## Track B mechanism diagnosis (2026-11-07)

- Protocol locked in `a69878c4`; results in `late_change_diagnosis_results.md` / `.json`.
- Supported drivers of late-change failure: **stale evidence** (dominant; published hosts miss
  every late improvement, single-start RMM nearly as bad) and **budget exhaustion / front-loaded
  pacing** (k=3 vs k=1 harmful at change 800/1200/1500). Delay supported descriptively (benefit
  gone at delay 400). Post-verdict stopping **not supported** (hosts keep acquiring).
- Reinterpretation: RMM's "continued acquisition" stacks a second acquisition stream on the host
  (`restart_monitor.py:179-194`), spending the budget faster; it helps early changes and hurts late
  ones. Host restart has exactly zero effect in late regimes. `rmm:LRMD_k1` ≈ e-SR with full
  promotion alpha; its edge over the default two-sided e-SR is the alpha allocation, not start
  spacing.
- Side note: `restart_monitor.py:199` casts losses with `int()` (fine on 0/1 loss tapes; would
  truncate non-0/1 losses on real streams). Not changed, because historical results depend on this
  file; flag for any real-data use.
- Decision: stop pursuing RMM as a contribution. Track B continues only via adaptive pacing under
  change-time uncertainty or delay robustness, after a prior-art check. Comparator for any
  candidate: `esr_rmmbets_fullalpha` / `rmm:LRMD_k1`.
