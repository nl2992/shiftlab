# Check: IUPM (Koebler et al., AISTATS 2025)

Independent check of `specs/iupm.md`, 2026-11-06. Nothing executed; sources only read.

## Sources actually read

- PMLR camera-ready: `https://raw.githubusercontent.com/mlresearch/v258/main/assets/koebler25a/koebler25a.pdf`
  (linked from the PMLR v258 page), 20 pp, via `pdftotext -layout`.
- arXiv 2505.07023v1 (11 May 2025, 20 pp), re-fetched. A word-level diff of the two extractions differs
  only by the arXiv watermark line (5 tokens): the PMLR PDF is text-identical to arXiv v1. The spec's
  "camera-ready UNVERIFIED" item is now VERIFIED identical.
- Code: `alexanderkoebler/IUPM@8e3a882c0c5d26b6b88dc1abc3d429a87f47b0b6`: `iupm.py` (212 lines),
  `MNIST_example.py`, `README.md`, `LICENSE`, git tree (also lists `utils.py`, `models.py`, `dataset_utils/`,
  `requirements.txt`; the latter not read). Commit dated 2025-03-10 "Adapt figure".
- Local copies in `/private/tmp/claude-501/-Users-nigelli-Desktop-ICML-Shift-lab--claude-worktrees-shiftlab-methods-strategy-dba13e/06bf436b-d27c-42d6-9116-89f769a07352/scratchpad/check_han_iupm/`.
- Proofs: I read the full Appendix A proof of Thm 1 / Prop 1 / Cor 1 in the PMLR text.

## Claim-by-claim

| # | Spec claim | Verdict | Evidence |
|---|---|---|---|
| 1 | Citation AISTATS 2025 (PMLR 258); arXiv v1 20 pp | CONFIRMED | PMLR PDF 20 pp; proceedings page range 2188-2196 still UNVERIFIED (not shown in PDF text) |
| 2 | MIT licence, Siemens copyright | CONFIRMED | `LICENSE` and `iupm.py` header "Copyright 2024 Siemens AG ... Permission is hereby granted, free of charge"; `gh api .../license` returns `MIT`. Vendoring is allowed with the notice retained |
| 3 | Setting: f trained on labelled P_0; only unlabelled X_t at run time plus purchased labels; accuracy as loss | CONFIRMED | Sec. 3 Problem Setup; Sec. 4.1 "we consider the model accuracy as the loss criterion" |
| 4 | Single-model estimator, no paired comparison anywhere | CONFIRMED | no two-model quantity in Sec. 3-5 or Appendix; code estimates one `f` |
| 5 | Def. 1 (W bounded by Delta_t), Def. 2 (gradually Lipschitz smooth in X_t), Prop. 1 (Delta_t = (1+L_t) eps_t) | CONFIRMED | Sec. 3, Appendix A proof of Prop 1. Detail missed: Prop. 1 proof assumes a separable product cost c_xy = c_x + c_y and unit W weights |
| 6 | Psi_t = product_{i=1..t} gamma_i(X_{i-1}|X_i); P_hat(Y_t|X_t) = E_Psi[P(Y_0|X_0)]; L_hat_t = mean over Omega_t of expected loss | CONFIRMED | Sec. 3; Alg. 1 lines 6-8 (App. B.1); code `iupm.py:96-102`, `108-111`, `133-134` |
| 7 | Uncertainty U = E_{P(X_t)} SD_{P_hat(Y_t|X_t)}[L]; code mean of per-sample std | CONFIRMED | Sec. 3 "expected standard deviation (SD) of the sample-wise loss"; `iupm.py:135,137-138,144`. `'ci'` branch scales by 2/sqrt(N) (`:139-141`); MNIST driver uses `confidence='std'` (`MNIST_example.py:105`) |
| 8 | Trigger U > th_U = 0.1; chosen from Table 9 saturation 0.08-0.12 | CONFIRMED | Sec. 4.1 "U(L_t) > 0.1"; App. D "begins to saturate between 0.08 and 0.12"; code `intervention_th = 0.1` (`MNIST_example.py:43`). The text also glosses 0.1 as "10% in accuracy deviation" (Sec. 4.2): that gloss is loose, U is a mean per-sample SD (max 0.5 for 0/1 loss), not an accuracy error |
| 9 | UI = arg top-m by per-sample uncertainty; code `np.argsort(var_xt)[-M:]` | CONFIRMED | Sec. 3 "arg top-m"; `iupm.py:164-165`. Note it sorts the VARIANCE, equivalent to sorting SD |
| 10 | m = 50% of Omega_t per trigger | CONFIRMED | Sec. 4.2 "we relabel 50% of Omega_t"; App. C.2 "relabeling of 50% of the samples in step t"; `M_ratio = 0.5`, `M = int(M_ratio * X_shift.shape[0])` (`MNIST_example.py:44,90`) |
| 11 | Correction: queried column puts all mass on the imposed label; code factor default 0.0, MNIST driver passes 1e-5 | CONFIRMED | `iupm.py:172-179` (`self.Psi[filter,c] *= correction_factor`, renormalised); `MNIST_example.py:93` `correction_factor=0.00001`. Paper Alg. 1 line 13 and Sec. 3 say "assigns a fixed label", so the 1e-5 leaves residual mass: confirmed discrepancy. Additional hazard missed: with factor 0.0 a column whose sources contain no sample of the imposed class would be all-zero and renormalise to NaN (`:179`); 1e-5 avoids that |
| 12 | Corrections carry forward via Psi @ gamma | CONFIRMED | `iupm.py:97` |
| 13 | Entropic Sinkhorn, squared Euclidean cost, uniform marginals, column-normalised conditional | CONFIRMED | `iupm.py:51,79-90`; App. C.2 "squared Euclidean distance throughout". The MNIST driver uses `ot_method='sinkhorn_log'` (`MNIST_example.py:42`) and numItermax 10000 |
| 14 | Regularisation 1e-4 synthetic and ImageNet-C, 1 MNIST, 1e-3 yearbook | CONFIRMED | App. C.3 |
| 15 | Sizes: 200 (synthetic, MNIST), 500 (ImageNet-C), 100 per step in Lipschitz study; 100 steps synthetic (2 deg / 0.02 per step), 20 steps MNIST/ImageNet-C; five seeds | CONFIRMED | Sec. 4.2, App. C.3; five seeds from Tables 1 and 6 captions |
| 16 | Matching space raw 2-D synthetic; penultimate/FC2 activations for images | CONFIRMED | Sec. 4.2; App. C.3; `MNIST_example.py:37,66` use `get_latent_features(... 'self_lenet')` (fc2 hook, `iupm.py:31-32`) |
| 17 | Table 1 Moons/RF: IUPM 0.0781, IUPM_UI 0.0250, NIPM 0.2482, ATC 0.3788; Circles/MLP IUPM 0.0359, UI 0.0138 | CONFIRMED | PMLR Table 1 and Table 6 |
| 18 | Table 2 UI n_I = 10 / 13 / 15 vs RI 22-35 | CONFIRMED | PMLR Table 2 (RI 22-35, CEI 19-35, UI 10-15). Over 100 steps |
| 19 | Table 3 MNIST rotation IUPM 0.0985, UI 0.0719 | CONFIRMED | PMLR Table 3 and Table 7 |
| 20 | Table 9: threshold 0.10 gives n_I 12.67, MAE 0.0221; 0.02 gives 57 | CONFIRMED | PMLR Table 9 |
| 21 | Thm 1 as printed: sum_{i=1..t} L_t eps_t; typo claim: intended L_i eps_i | CONFIRMED (typo) and extended | The camera-ready main text and Appendix A both print `L_t eps_t` inside the sum over i, in the statement and in the last two proof lines. The proof's own derivation uses a different cost term per step i (`c_x(x_i, x_{i-1})`) and Def. 2 gives a separate constant at each step, so L_i eps_i is the intended bound. Also, in Sec. 4.2 the empirical check uses `sum_{i=0..t} L_hat_i eps_hat_t` (eps with index t), a second index slip in the Table 5 label. The authors do not state either as a correction |
| 22 | Error linear in t; Cor 1 optimal incremental couplings minimise the upper bound | CONFIRMED | Sec. 3 remark; Appendix A end ("optimizes an upper bound", not the error itself) |
| 23 | Table 5 Pearson 0.86 and 0.56 on yearbook | CONFIRMED | PMLR Table 5 |
| 24 | Budget: no hard cap, endogenous number of labels | CONFIRMED | Sec. 3 says "label only m samples" per trigger but no total cap; Alg. 1 has no budget input |
| 25 | `metric='acc'` code path has tilde_L of shape (N,1) | CORRECTED | `iupm.py:122`: `(N,1) == (N,)` broadcasts to an (N,N) boolean matrix; entry [i,j] is source label i compared to the prediction at target sample j. This is what makes `tilde_L * Psi` (`:133`) work column-wise. Requires one-hot `ys` (uses `ys.shape[1]`, `np.argmax(ys,axis=1)`) |
| 26 | CEI "samples proportional to it without replacement" vs paper top-m | CONFIRMED | `iupm.py:157-162` `np.random.choice(... p=q, replace=False)`; Sec. 4.1 writes `arg top-m`. Also the code's RI takes `idxs[-M:]` after global-RNG shuffle (`:154-156`) |
| 27 | Pinned SHA date and message | CONFIRMED | `gh api commits/8e3a882c`: 2025-03-10 "Adapt figure" |

## Missed by the spec (add to the record)

- N1. Reporting order in the official driver. In `MNIST_example.py:86-93`, the IUPM_UI estimate for step i is
  computed FIRST (`:86`), appended to results (`:99-101`), and the label correction (`:93`) only changes
  Psi for later steps. So the paper's MAE for IUPM_UI at a trigger step is the PRE-intervention estimate;
  labels help the next steps only. A faithful port must reproduce this order or note the change.
- N2. Table 1 vs Table 2 disagree on the same method: IUPM_UI MAE is 0.0322/0.0307/0.0331 (Clusters),
  0.0250/0.0250/0.0230 (Moons) in Table 1 but 0.0270/0.0272/0.0265 and 0.0244/0.0242/0.0222 in Table 2.
  The paper does not explain this (likely different evaluation protocol or seeds). Reproduction should target
  Table 1 and Table 6 with CIs, and treat Table 2/8 as a separate protocol. Table 8 (equal-budget ablation) UI
  row equals Table 2.
- N3. The estimator does not use the model's predictions to move mass: P_hat(Y_t|x_t) is a mixture of the t=0
  labels via Psi only; labels from interventions at step t correct only the queried columns. Only the
  `infer_performance_distribution` step touches f.
- N4. Theory-vs-implementation gaps beyond the finite-sample one the spec noted: (a) Thm 1 is for exact optimal
  W1 couplings under a metric cost; the code uses entropic Sinkhorn with squared Euclidean cost (not a metric)
  at regularisation 1 on MNIST, which is heavy smoothing; Cor 1 (optimality of OT couplings) does not apply to
  the regularised plan; (b) the Lipschitz constant is on conditional label laws, which for a classifier-embedding
  match is not controlled by the embedding distance; (c) the proof assumes the same cost c in Def. 2 and in the
  coupling; (d) uniform weights `unif(N)` impose equal block sizes N at every step.
- N5. The IUPM_UI monitor reuses the IUPM monitor's coupling (`MNIST_example.py:74`
  `m.update(X_shift_emb, gamma=monitors['IUPM'].gamma_k)`): the OT is solved once, not per monitor.
- N6. `get_critical_instances` calls `infer_performance_distribution(xt, metric)` with positional args wrong
  (`iupm.py:151`: second positional is `f`) if the flag is unset; the driver avoids this by calling the estimate
  first. A vendored copy would need this fixed.
- N7. Unrelated to ShiftLab but relevant to a port: `update` initialises with `if not np.sum(self.Psi)` while
  `self.Psi` is None on first call (`iupm.py:99`); I did not run it, so whether `np.sum(None)` behaves is
  UNVERIFIED. Treat the first-step branch as needing a unit test.

## Contract questions resolved

- Hard budget: B = 200 is a label COUNT in the simulator contract (`scripts/sota_sprint/bench.py:25`
  `CONTRACT ... budget=200`; `scripts/promising_directions/sota/simulator.py:163` `remaining = int(budget)`,
  `:202` `remaining -= 1` per granted query, price charged separately at `:235`). One IUPM trigger at m = 50% of
  N=200 is ~100 labels, so B=200 permits only about two triggers at the paper's setting.
  Different from `src/shiftlab/contract/interface.py:25,50` (`label_budget` / `remaining_budget` in price units).
- Covariates for the optimal-transport step: NOT AVAILABLE in the benchmark contract that matters.
  `simulator.py:54` allows `Event.context: Any = None`, and the benchmark harness builds streams with
  `stream_from_losses` (`scripts/failure_atlas_v2_flq/suite.py:96-100`: labels random, predictions =
  label XOR loss) and calls `run_episode` without `contexts` (suite.py:106), so the context is `None`; the one
  script that passes `contexts` (`scripts/sota_sprint/wp1_clock_ablation.py:191`) passes an integer time stamp.
  In the separate `src/shiftlab/contract/interface.py` contract `PublicEvent.x` is a vector (line 54), but for
  the real tasks it "holds calendar fields only" (`src/shiftlab/real_tasks/__init__.py:6`). Neither carries the
  model-input features IUPM needs, and there is no labelled reference set Omega_0 with class posteriors
  (labels are random in the synthetic suite). IUPM is therefore INAPPLICABLE to the sota-sprint synthetic
  streams, and can only be run on a task that supplies model-input features or embeddings plus an initial
  labelled reference batch.
- Sinkhorn replacement: `ot` (POT) and torch are imported at module top (`iupm.py:11-12`); the estimator itself
  needs only numpy/Sinkhorn. Whether POT is installed here: UNVERIFIED.

## Fidelity-tier call

- Core estimator plus UI on the paper's batched, immediately-labelled setting: T1-portable (MIT; vendor with the
  Siemens notice; fix N6/N7 first; validate against `MNIST_example.py` order of operations, N1).
- Inside the ShiftLab sota-sprint contract: no features, no reference labelled set, no paired loss, no decision
  rule. It cannot be a comparator there at any tier above "inspired-by". A T3 "uncertainty-acquisition only"
  variant would need to drop the OT step, i.e. would not be IUPM. Recommend: exclude from the synthetic
  comparator pool; include only in a feature-bearing real-data track, as an acquisition/estimation component
  paired with a ShiftLab switching rule, and never describe the trigger as a harm alarm.

## Verdict

ACCEPT WITH CORRECTIONS. Nearly every spec claim is confirmed against the camera-ready (text-identical to
arXiv v1) and the code. Corrections: `metric='acc'` tilde_L is (N,N) not (N,1) (item 25); the Thm 1 typo is
confirmed and also present in the Table 5 label; the optimistic "T1-portable" call stands only for the paper's
own setting. Add N1 to N7, and record that the open question on features is answered in the negative for the
sota-sprint synthetic contract (no covariates, no labelled reference set), making IUPM inapplicable there.
