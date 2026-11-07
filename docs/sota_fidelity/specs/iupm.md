# Spec: IUPM, Incremental Uncertainty-aware Performance Monitoring with Active Labeling Intervention

Retrieved 2026-11-06 by retrieval subagent. Page numbers are PDF pages of arXiv v1 (20 pp). Text
extracted with `pdftotext -layout` (no code executed). Equations in the paper body are unnumbered;
they are cited by section/page and by name.

## 1. Citation, version, code

- Alexander Koebler, Thomas Decker, Ingo Thon, Volker Tresp, Florian Buettner, "Incremental
  Uncertainty-aware Performance Monitoring with Active Labeling Intervention", AISTATS 2025
  (PMLR 258; proceedings pages reported as 2188-2196 by a secondary index, UNVERIFIED).
- Version read: arXiv 2505.07023v1 (11 May 2025), https://arxiv.org/pdf/2505.07023v1, 20 pages
  (main text pp.1-9, references and checklist, then appendix A-D; appendix pages are cited by section only). The AISTATS camera-ready PDF was not
  separately read (UNVERIFIED identical).
- Official code: https://github.com/alexanderkoebler/IUPM (link in paper Sec. 4, p.5 footnote 1),
  pinned HEAD `8e3a882c0c5d26b6b88dc1abc3d429a87f47b0b6` (2025-03-10, "Adapt figure"), MIT licence.
  Files read at SHA: `iupm.py` (core, lines 1-212 incl. `IUPM` and `NIPM`), `MNIST_example.py`
  (lines 20-125), `README.md`. Not read: `utils.py`, `models.py`, `dataset_utils/*`, requirements.

## 2. Native problem and estimand

- Setting (Sec. 3, p.3): a model f trained on labelled (X_0,Y_0)~P_0 is deployed on a stream
  (X_t,Y_t)~P_t, t=1..T; only unlabelled X_t is available at run time, apart from a small number of
  actively purchased labels. Estimand: the model's loss L_t(f) = E_{P_t} L(f(X_t),Y_t)
  (accuracy in all experiments, p.4 and App. C.2). Shift is assumed gradual (Def. 1, 2 on p.3).
- This is a label-free ESTIMATOR with an uncertainty score, not a hypothesis test. No null, no
  alpha, no sequential validity. Labels exist only at t=0 (free) plus the purchased ones.
- Single-model: it estimates the performance of ONE model f. No paired / two-model comparison
  appears anywhere in the paper.

## 3. Exact algorithm (paper Alg. 1, App. B.1; code at SHA)

Per time step t, with sample set Omega_t (n_t = N points, same N every step in the code):
1. OT coupling (Alg 1 line 6; Sec. 3 p.3; entropic form App. B.2): gamma_t between Omega_{t-1}
   and Omega_t, minimising sum c(x_{t-1},x_t) gamma. Code: `iupm.py:73-102` `update`, uniform
   marginals `ot.utils.unif(N)` (79-80), cost = squared Euclidean (`cost_function='sqeuclidean'`,
   line 51; paper App. C.2), Sinkhorn `ot.sinkhorn(a,b,M,lambd,...)` (88), column
   normalisation to the conditional gamma(X_{t-1}|X_t) (90).
2. Transition map (Sec. 3 p.3): Psi_t(X_0|X_t) = product_{i=1..t} gamma_i(X_{i-1}|X_i), matrix
   product. Code: `self.Psi = self.Psi @ self.gamma_k` (97), column renormalised (102).
3. Label estimate (Sec. 3 p.4): P_hat(Y_t|X_t) = E_{Psi_t(X_0|X_t)}[ P(Y_0|X_0) ], a mixture of the
   t=0 labels. Code `infer_label_distribution` 108-111.
4. Performance estimate (p.4): L_hat_t = (1/n_t) sum_{x_t in Omega_t} E_{P_hat(Y_t|x_t)} L(f(x_t),Y_t).
   Code `infer_performance_distribution` 113-147: per-sample expected loss `sum(tilde_L_p, axis=0)`
   (134), mean over samples (134).
5. Uncertainty (p.4): U(L_hat_t) = E_{P(X_t)} SD_{P_hat(Y_t|X_t)}[ L(f(X_t),Y_t) ], i.e. the mean over
   samples of the per-sample standard deviation of the loss under P_hat. Code: per-sample variance
   `var_xt` (135), `confidence='std'` returns mean of sqrt(var) (137-138, 144). The `'ci'` option
   (139-141) scales by 2/sqrt(N); the MNIST driver uses `'std'` (`MNIST_example.py:105`).
6. Intervention trigger (p.4, Alg 1 lines 10-14): if U > th_U, buy labels for the m samples with the
   largest per-sample uncertainty, "arg top-m" (Uncertainty Intervention, UI). Code:
   `get_critical_instances` 149-170, `np.argsort(self.var_xt)[-M:]` (165).
7. Correction (Alg 1 line 13; p.4): the purchased label is imposed so P_hat(Y_t|x_t) puts all mass on
   it. Code `correct_critical_instances` 172-179: for each queried column c, multiplies by
   `correction_factor` the Psi entries of sources whose class differs, then renormalises columns.
   Default factor 0.0 (172); the MNIST driver passes 1e-5 (`MNIST_example.py:112`), so the
   imposed label is not exactly a point mass in that driver (discrepancy with "fixed label").
   Because Psi is carried forward by `Psi @ gamma_k` (97), corrected columns affect later steps.
   Corrections are applied the same step the label is obtained (no delay in the algorithm).

Baselines defined in the same paper (p.5): Random Intervention (RI: m random samples),
Cross Entropy Intervention (CEI: top-m by expected cross-entropy under P_hat, after Kossen et al.
2021; code samples proportional to it without replacement, `iupm.py:157-162`, a minor
top-m vs sampling difference vs the paper text), and NIPM (non-incremental direct coupling gamma(X_0|X_t)).

## 4. Hyperparameters and defaults used in the paper's experiments

- Uncertainty threshold th_U = 0.1 (App. D: chosen from the Table 9 saturation of gain per
  intervention between 0.08 and 0.12); m = 50% of Omega_t per intervention (p.6 and App. C.2:
  "relabel 50%"); code `intervention_th = 0.1`, `M_ratio = 0.5` (`MNIST_example.py:43-44`).
- OT: entropic Sinkhorn (POT library), squared Euclidean cost; regularisation: 1e-4 (synthetic and
  ImageNet-C), 1 (MNIST), 1e-3 (yearbook) (App. C.3). Code default `lambd=1.0` (51),
  MNIST driver `lambda_ = 1`, `numItermax=10000` (`MNIST_example.py:42,58`).
- Matching space: raw 2-D for synthetic data; penultimate/second-FC activations for MNIST/ImageNet-C
  /yearbook (p.6, App. C.3).
- Sample sizes: Omega_0 and each Omega_t = 200 points (synthetic, MNIST), 500 (ImageNet-C), 100 per
  step in the Lipschitz-estimation study; steps = 100 (synthetic, 2 deg rotation or 0.02 shift per
  step), 20 (MNIST, ImageNet-C) (p.5-6, App. C.3). Five seeds.
- Loss criterion: accuracy (0/1). Models: RF/XGB (50 trees, depth 5)/MLP; LeNet; ResNet-50.
- Budget: no hard cap exists. The number of labels is endogenous, set by the threshold:
  Table 2 (p.7) reports n_I about 10 to 15 interventions per 100 steps for UI vs 19 to 35 for
  RI/CEI; Table 9 (App. D) maps threshold to n_I (0.10 gives 12.67 average, 0.02 gives 57).
  Since each intervention labels 50% of a 200-point set, one intervention is about 100 labels.

## 5. Guarantee

- Def. 2 (p.3, restated App. A): shift is "gradually Lipschitz smooth in X_t" with cost c:
  W(P_t(X_t),P_{t-1}(X_{t-1})) <= eps_t and W(P_t(Y|x_t), P_{t-1}(Y|x_{t-1})) <= L_t c(x_t,x_{t-1}).
  Prop. 1 (p.3): this implies the joint shift is gradual with Delta_t = (1+L_t) eps_t.
- Thm 1 (p.4, proof App. A): if L is 1-Lipschitz in its second argument and the shift is
  gradually Lipschitz smooth, then |L_t - L_hat_t^IUPM| <= sum_{i=1..t} L_t eps_t (as printed). The
  proof's last lines carry the index i inside the sum, so the intended bound is almost certainly
  sum_i L_i eps_i; the printed L_t eps_t is a notational slip in both statement and proof (my
  reading, not stated by the authors). Error is linear in t (p.4 remark).
- Cor. 1 (p.4, proof App. A end): composing OT-optimal incremental couplings minimises the upper bound
  among incremental couplings.
- Assumptions that matter: the couplings in the proof are POPULATION optimal couplings between
  consecutive marginals; the bound is for the population estimator. The experiments use
  finite-sample entropic Sinkhorn couplings on n=100 to 500 points; the paper cites an OT
  sample-complexity result (App. B.2) but states no finite-sample or entropic-regularisation error
  term in Thm 1. Needs labelled t=0 data from P_0(Y|X). Exact label noise-free conditionals are
  used in the Lipschitz study (p.8-9).
- NOT covered: any guarantee for the uncertainty score U (calibration, coverage), for the UI
  selection rule, for the trigger, for the number of labels needed, for abrupt / non-gradual
  shift (the conclusion p.9 says it "may not be optimal"), for two-model comparisons, for
  delayed labels, or for any error rate of a decision. Empirical Lipschitz check (p.8-9, Table 5 p.9):
  Pearson rho = 0.86 and 0.56 on the yearbook data, a plausibility diagnostic only.

## 6. Mapping to ShiftLab's deployment contract

- IUPM is estimation + acquisition-trigger only. It is NOT a decision rule: there is no alarm on
  harm, no switch rule and no test. The only "alarm" is U > th_U, which means "my estimate is
  unreliable, buy labels", not "the model is harmful". Any switching decision (e.g. deploy the
  candidate when L_hat(incumbent) - L_hat(candidate) exceeds a margin, optionally gated by U)
  would be ShiftLab's own addition and is not in the paper (UNVERIFIED as a design; no theory).
- Inputs required that the contract may not supply: covariates X_t as vectors (or embeddings) for
  OT, and labelled reference data Omega_0 with labels. Whether `PublicEvent`/`Event.context`
  carries usable features in bench.py was not established
  (`sota/simulator.py:47-54` allows `context: Any = None`). If context is None, IUPM is
  inapplicable. UNVERIFIED.
- Batching: IUPM works on sets Omega_t (size N) at each step and couples consecutive sets. T=2000
  single events must be grouped into blocks (e.g. 100 blocks of 20 rounds); coupling quality
  with n=20 is untested (paper's smallest n is 100). Any block size is a deviation.
- Two models: run IUPM once per frozen model (code estimates one `f`); the gap estimate's error
  is bounded only by the sum of two Thm-1 bounds, a ShiftLab-derived statement (not in paper).
- Budget: the paper has no cap; hard B=200 over T=2000 forces a fixed m_t schedule (the paper
  uses m = 50% of Omega_t per trigger, about 100 labels per trigger) and truncation when budget
  runs out: the pacing/cap rule and the "label top-m uncertain samples" rule must be separated.
  A faithful acquisition-only variant: compute per-sample uncertainty, request the top-uncertainty
  events inside the budget pacer (`controls.py:28-50`). Selecting by uncertainty makes
  queries propensity-dependent on past labels; propensities `q` must be logged by the
  harness (`MonitorV2.propensity`, `interface_v2.py:90`) and the paper gives no IPW correction.
- Labels cost 0.05 each and switching 5: not modelled by IUPM; labels-cost ordering and the trigger
  threshold are the only levers. Delayed labels: the paper applies the correction in the same
  step; for a late label from block s the corrected Psi columns of block s must be re-propagated
  (`Psi @ gamma` chain) to later blocks, or it is dropped. Re-propagation is a deviation.
- Tiers: core estimator + UI on the paper's setting (batched, immediate labels): T1-portable from
  MIT-licensed `iupm.py` at the pinned SHA (port or vendor, then check numerically against the
  code on its MNIST/synthetic drivers). On the ShiftLab contract: T3, acquisition-and-estimation
  only; name it "IUPM-style uncertainty acquisition", and never present it as an alarm or a
  harm test. Without a decision rule it cannot enter a switching comparison on its own.

## 7. Existing ShiftLab code

- `grep -ril "iupm" src scripts` returns nothing relevant (only the two unrelated rolling-window
  hits listed in the Han spec). No OT-based or label-free estimator exists in the repo.
- Reusable: pacer `scripts/promising_directions/sota/competitors/controls.py:28-50`; adapter
  pattern (`request_labels` -> `QueryRequest`, `observe(list[ReleasedFeedback])`)
  `competitors/model_selector.py:354-385`; `ReleasedFeedback.model_losses` gives per-model
  0/1 loss for the labelled event (`sota/simulator.py:67-76`). Dependencies `POT`, torch are not
  assumed installed (UNVERIFIED; `ot.sinkhorn` could be replaced by a small numpy Sinkhorn).
- Honest current tier: not implemented.

## 8. Reproduction tests

- Printed numbers (5-seed MAE between true and estimated accuracy): Table 1 (p.7) Moons/RF:
  IUPM 0.0781, IUPM_UI 0.0250, NIPM 0.2482, ATC 0.3788; Circles/MLP: IUPM 0.0359, IUPM_UI 0.0138;
  Table 2 (p.7) UI n_I = 10 (Moons), 13 (Circles), 15 (Clusters) vs RI 22-35;
  Table 3 (p.7) MNIST rotation: IUPM 0.0985, IUPM_UI 0.0719; Table 9 (App. D) threshold 0.10 gives
  n_I = 12.67, MAE 0.0221. Confidence intervals in App. D Tables 6-7.
- Identities usable without data: Psi columns sum to 1 after every update (`iupm.py:102`);
  after correction with factor 0, the queried column is a point mass on the imposed class
  (`iupm.py:178-179`); per-sample variance is zero for such columns, so they drop out of U.
  Thm 1's bound is checkable on a synthetic 1-D Gaussian-translation shift where W, L_t and the
  exact coupling are known (to be designed; not in paper).

## 9. Open questions / UNVERIFIED

- Whether the AISTATS proceedings version differs from arXiv v1.
- Camera-ready proofs: only App. A of v1 was read; the L_t vs L_i index issue is my reading.
- `utils.py` (softmax) and the synthetic/ImageNet drivers were not read; `m` for non-MNIST
  experiments is taken from the paper text (50%), not from code.
- Whether events in bench.py expose features suitable for OT.
- Behaviour of the code for `metric='acc'`: `tilde_L` shape (N,1) broadcast (line 122); read, not run.
- Sensitivity of OT coupling at n=20 per block: unknown.
