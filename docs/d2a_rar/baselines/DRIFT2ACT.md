# Drift2Act baseline record (WP1a)

Paper: Lamaakal, Yahyati, El Makkaoui, Ouahbi, Maleh, "Drift-to-Action Controllers: Budgeted Interventions with
Online Risk Certificates", arXiv:2603.08578 (v1, 9 Mar 2026; ICLR 2026 CAO workshop).
Read 2026-11-07 via arXiv HTML (WebFetch; full text, sections and appendices through App. E tables).
Code: `src/shiftlab/sota/drift2act/`; tests: `tests/d2a_rar/test_drift2act.py`.

## 0. Source-code status and fidelity tier

- **Author code: NOT FOUND.** The paper text has no repository / artifact statement (only the arXiv build-log link);
  a web search for the title + "github code" (2026-11-07) returned no author or community implementation (unrelated
  repos only); `git grep -i drift2act` over all local refs finds only docs (no code), consistent with the 2026-11-04
  audit (`research/continuation-2026-11-04:docs/sota_sprint/drift2act_reproduction_and_delta_audit_2026-11-04.md`),
  which also recorded that no local Camelyon17/DomainNet stream exists. Nothing was ported; that audit's contract
  comparison is reused as prior analysis only.
- **Fidelity tier: `PAPER_RECONSTRUCTION`.** Exact where the paper is exact (radius, Alg. 1 skeleton, gain table, costs,
  cooldowns, budget, delay, gate); every unspecified item is a labelled choice in section 3.

## 1. Paper specification (with locations)

| Item | Specification | Where |
|---|---|---|
| Latent drift | D in {none, covariate, concept, subgroup} | Sec 3.3 |
| Belief | `b~_t(d)=sum_d' T[d',d] b_{t-1}(d')`, `b_t(d) ∝ p(z_t|d) b~_t(d)` (Eq. 10); b_0 uniform | Sec 3.3, Alg 1 |
| T | only symbolic (`T[d',d]=P(D_t=d|D_{t-1}=d')`, estimator Eq. 121); **no numeric values** | App E |
| Evidence | main model: discriminative multinomial logistic `q_phi(d|z)`, beta=1 (Eq. 122); alt. diagonal Gaussian `p(z|d)` (E.2.5); fitted on synthetic drift episodes; **no parameters** | App E |
| Sensing z_t | `[MMD^2_t, dH_t, dECE_t]` (Eq. 7): kernel two-sample (recent n=256 vs reference n_ref=2048 embeddings), mean-entropy difference, ECE on delayed labels minus ECE_ref | Sec 3.2, App E |
| Window | Sec 4.1: `W_t={t-N+1..t}`; Alg 1: delay-adjusted `{t-d-N+1..t-d}` (paper internally inconsistent); N=1024 | Sec 4.1, Alg 1, App E |
| Audit | `n_t=QueryPolicy(z_t,b_t,U_{t-1},B)`; uniform `Q_t⊆W_t`, `|Q_t|=n_t`; request labels for `J_t=Q_t\labelled`; `B<-B-|J_t|`. QueryPolicy is qualitative only ("more when drift indicated / certificate loose"); constants k_max=64,k_high=32,k_low=8,m_low=0.02,zeta=2.0 given, **formula not given** | Alg 1, Sec 4.5, App E |
| Certificate | `U_t(delta)=R^_t+rad(|Q_t|,delta_t)`, `delta_t=6 delta/(pi^2 t^2)`, `rad(n,delta)=sqrt(log(pi^2 n^2/(6 delta))/(2n))` (Hoeffding + stitched `delta_n=6delta/(pi^2 n^2)`); finite-population variant `sqrt((1-(n-1)/N) ...)`; Thm A.2: `P(∀t: R_t<=U_t)>=1-delta` | Alg 1 step 10, App D |
| Gate | `U_t<=tau`: normal operation; else a_t=A6 (abstain/handoff), schedule rollback if its cooldown passed, otherwise retrain if its cooldown passed | Alg 1 step 11 |
| Utility | `Delta_t(a)=sum_d b_t(d) G(d,a)`; `U_t(a)=Delta_t(a)-lambda c(a)-gamma Viol_t(a)` (Eq. 22; Alg 1 omits Viol - inconsistency); `Viol_t(a)=max{0,U_t-sigma_U Delta_t(a)-tau}`, sigma_U=0.10, gamma=50; **lambda value not stated** | Eq. 22, App E |
| Actions / cost | A0 no-op 0; A1 recalibrate 0.2; A2 TTA 1.0 (5 grad steps, lr 1e-4); A3 query labels 0.05·k_t; A4 retrain 12.0; A5 rollback 1.5; A6 abstain/handoff 0.3 | Table 2 |
| Gain table G(d,a) (H=150, sigma_R=0.10) | none [0,.10,.05,.08,.12,.10,.15]; covariate [0,.35,.70,.25,.85,.40,.55]; concept [0,.20,.30,.75,1.05,.60,.65]; subgroup [0,.25,.35,.85,.95,.55,.80] | App E.6 |
| Budget/cooldowns/delay | B_lab=3000; retrain cooldown 800, rollback 400; label delay d=50 (`o_i=i+d`, Eq. 48); tau=0.20, delta=0.05 | App E, Table 1 caption |
| Streams | M=200 episodes/dataset, L=1500, onset ~U[300,600], 5 seeds; step / logistic / sinusoidal schedules; subgroup prevalence 0.15 | App E |
| Native tasks | WILDS Camelyon17 (hospital stream with return), DomainNet (sketch/clipart/painting/real/quickdraw), SyntheticDrift-CIFAR (corruption severity, class-remap ramp, minority style); also Amazon Reviews (Table 14) | Sec 6, App E/F |
| Metrics | C_tot=Σc(a_t); V=Σ1(R*_t>tau); T_det=min{t>=t0: Alarm}-t0; T_rec=min{t>=t0: R*_t<=tau}-t0; min worst-group accuracy | Eqs 33,39-42 |

### Published Table 1 (tau=0.20, delta=0.05, d=50), verbatim

| Task / method | C_tot | V | T_det | T_rec | min Acc_wg |
|---|---|---|---|---|---|
| Camelyon17 Alarm-only | 3.2 | 46 | 22 | 210 | 0.71 |
| Camelyon17 Adapt-always (TTA) | 58.0 | 3 | 18 | 74 | 0.79 |
| Camelyon17 Retrain-on-schedule | 41.5 | 9 | 35 | 96 | 0.77 |
| Camelyon17 Selective only | 9.8 | 14 | 24 | 160 | 0.74 |
| Camelyon17 Controller (no cert.) | 18.7 | 7 | 19 | 98 | 0.78 |
| Camelyon17 Controller + cert. | 24.6 | 0 | 20 | 62 | 0.81 |
| DomainNet Alarm-only / Adapt / Retrain / Selective / Ctrl / Ctrl+cert | 4.1/64.0/45.0/12.4/22.5/29.8 | 63/6/14/27/11/1 | 28/21/40/30/23/24 | 260/110/132/205/141/88 | .49/.58/.56/.52/.57/.61 |
| SyntheticDrift-CIFAR Alarm-only | 2.6 | 52 | 16 | 185 | 0.68 |
| SyntheticDrift-CIFAR Adapt-always | 52.0 | 4 | 13 | 66 | 0.79 |
| SyntheticDrift-CIFAR Retrain-on-schedule | 36.0 | 10 | 25 | 92 | 0.77 |
| SyntheticDrift-CIFAR Selective only | 8.6 | 19 | 18 | 148 | 0.72 |
| SyntheticDrift-CIFAR Controller (no cert.) | 16.8 | 8 | 14 | 84 | 0.78 |
| SyntheticDrift-CIFAR Controller + cert. | 21.2 | 0 | 15 | 58 | 0.82 |

(Table 1 values transcribed from the HTML text; units of V/T are per-episode quantities whose aggregation is not
stated precisely. Tables 6-14 — ablations, delay/budget sweeps, FIR, Amazon — were listed but not transcribed.)

## 2. Guarantees versus empirical claims

**Theoretical (only this is a guarantee).** Thm A.2 / App. D: if labelled indices are drawn *uniformly from the window*,
independent of unobserved labels given history (Condition A), losses lie in [0,1], and draws are iid (with replacement;
fp-corrected without), then `P(∀t: R_t(window)<=U_t(delta))>=1-delta`. Adaptive stopping of n_t is permitted;
delay only reduces effective n (D.7). It is a bound on **absolute finite-window risk of the deployed predictor**;
it implies nothing about action optimality, post-action value, regret, paired incumbent-vs-challenger excess loss
(conditional null `E[d_t|F_{t-1}]<=0`), or any-promotion error control.

**Empirical (not guarantees).** Table 1 "near-zero violations", cost/recovery gains, label-budget/delay sweeps, belief
and gain-table quality (gain table calibrated offline on synthetic simulations, so transfer is untested).

**Certificate is NOT valid / not claimed when** (audit conditions; our test `test_certificate_not_valid_under_informative_selection`
demonstrates the first):
1. selection depends on loss (informative / margin-based / "interesting-sample" querying; a Q2 policy that picks *which*
   items to label non-uniformly needs an importance-weighted bound, absent here);
2. pooled labels across rounds (our `pool='window'`, used because the literal per-round sample cannot certify at
   tau=0.2 with realistic n) are not an exactly-uniform sample of the *current* window when the window slides, so the pooled
   variant is **heuristic**, exact only for stationary within-window risk;
3. serial dependence / within-window nonstationarity: the bound targets the window-average risk of the *current* model,
   not the instantaneous post-drift risk (a 1024-step window lags a change by hundreds of steps);
4. delayed or outcome-dependent arrival: the delay-adjusted window (Alg 1) avoids it, but with the Sec 4.1 current
   window, selecting only already-arrived labels is index-determined (valid) whereas any rule that drops/waits on
   label values is not; the theorem is silent on label-dependent arrival order;
5. the n_t choice may depend on past labels (permitted), but union over *windows/time* is only covered by the
   `delta_t=6delta/(pi^2 t^2)` term; using rad(n,delta) alone (`delta_mode='mandate'`) is covered per fixed window, not
   simultaneously over time;
6. changing the model (retrain/rollback) alters the loss population: the certificate is for the *current* model, so a
   fresh sample is needed after model changes unless old labels are re-scored (we re-score);
7. covariate/label shift inside the window with importance-weighted or subgroup-conditional claims (selective-risk
   extension D.5) is outside what we implemented.

Vacuity: with Alg-1 `delta_t`, `rad(1024, 6*0.05/(pi^2 t^2))` at t=1000 is ~0.124, and rad(100)>=0.25; certifying
`U<=0.2` needs hundreds of labels and a base error below roughly 0.08 (see tests/numerics). Short certificate
horizons are therefore mostly "uncertified".

## 3. Reconstruction choices (everything not specified by the paper)

| Item | Choice | Reason |
|---|---|---|
| lambda | 0.5 applied to c(a)/12 (cost normalised by max cost) | not stated; raw costs make retrain (12) never worth gain ~1 |
| No-op margin eps | act only if best utility >= 0.15 | with Table-2 gains > 0 under `none`, argmax would act every step |
| QueryPolicy | k_max if (U_prev>tau and drift mass>0.5); k_high if drift mass>0.5 or margin<m_low; else k_low; every `audit_every=4` steps; zeta unused | qualitative text only |
| A3 | selecting A3 boosts next audit to k_high; label cost 0.05 per label charged for every label (all audits), A3 itself costs 0 | avoid double charge; A3 cooldown 50 |
| A6 cost | charged on activation (not every step) | per-step charge makes Table-1 magnitudes impossible |
| Certificate sample | default `pool='window'` (all released labels in window), `delta_mode='mandate'` (delta directly); variants `alg1` (delta_t), and `ctrl_cert_literal` (per-round |Q_t|, delta_t, unconditional scheduling) | literal version is vacuous in 1500 steps |
| Failure branch | on U>tau abstain; schedule rollback (only if a distinct certified checkpoint exists) else retrain (>=30 released labels) when belief drift mass>0.5 or R^>tau (`fail_schedule`; `literal` = unconditional) | blind retrain on an uncertified warm-up wastes cooldown |
| Checkpoint | `theta_safe` = last model with U<=tau | "validated checkpoint" unspecified |
| Evidence | diagonal-Gaussian p(z|d), beta=0.3 tempering, var floor 1e-4, fitted on 12 disjoint calibration episodes; T from transition counts + 2% uniform smoothing | paper gives no values; discriminative model not rebuilt |
| ECE monitor | dECE=0 until >=150 delayed labels in last 512 steps | small-sample ECE bias created false subgroup belief |
| Window | Alg-1 delay-adjusted (`window_mode='delayed'`); `'current'` supported with pending labels | Alg/Sec inconsistency |

Hooks: `LabelRequestPolicy.request_size(ctx)` (Q2: decides only *how many*; index choice and certificate untouched,
tested) and `EvidenceModel.log_lik(z, gap)` (Q1: swap belief evidence; `gap` argument carried for gap-aware work).

## 4. Implementation map

`certificate.py` (rad, rad_fp, gate) · `belief.py` (filter, Gaussian evidence, T estimator) · `audit.py` (LabelStore with
release/budget enforcement, WindowedAuditor, QueryPolicy) · `actions.py` (action table, G, costs, Config) ·
`controller.py` (Alg 1 step + full audit log: z, belief, requested/new indices, release times, budget, pending, R^, rad, U,
feasible set, utilities, executed actions, costs) · `synthetic_env.py`, `runner.py`, `aggregate.py` (reproduction).

## 5. Reproduction (Suite A, `PAPER_RECONSTRUCTION`, synthetic stand-in only)

Fidelity tier: **PAPER_RECONSTRUCTION** (no author code). Camelyon17 and DomainNet are **NOT reproduced** (no local data; nothing
was downloaded). The only task attempted is a CPU-sized *synthetic stand-in* for SyntheticDrift-CIFAR. It is not that task, and its
numbers must not be read as a reproduction of the paper's SyntheticDrift-CIFAR row. Suite A numbers are never used to rank methods
against other baselines (BENCHMARK_CONTRACT.md Suite A rule 5).

### 5.1 What `synthetic_env.py` simulates

Binary classification stream of length L=1500, 8-d Gaussian class-conditionals (class means +-1.6 along axis 0, unit noise, clean
Bayes error about 0.055), 15% minority group. The deployed predictor is a logistic regression fitted on 2000 clean samples. One hidden
drift type per episode, drawn uniformly from {covariate: input mean shift of 2.0 along the class axis; concept: class direction
rotated up to 70 degrees toward axis 1; subgroup: minority-group class separation scaled by 1-1.8*alpha, i.e. reversed at alpha=1}.
Onset ~ U[300,600]; schedule drawn from {step, logistic (centre onset+100, scale 25), periodic (period 300-600)}. Label delay 50,
B_lab=3000, tau=0.20, delta=0.05. Sensing z_t = [MMD2 (96 recent vs 192 reference points of the raw features), dH (mean predictive
entropy minus reference), dECE (delayed-label ECE minus reference; 0 until 150 labels)]. Evaluator-side truth R*_t = group-reweighted
(0.85/0.15) error of the model in force on 600 fresh stratified samples from the drifted law at step t; an abstained sample counts as
correct when its confidence is below theta_sel=0.6. T and p(z|d) are fitted on 12 disjoint calibration episodes (seeds 50000-50011).
It is *not* CIFAR: it has no corruption/remap/style semantics, and M=40 episodes x 1 seed replace the paper's M=200 x 5. In the
40 episodes the drift types are 21 concept, 8 covariate, 11 subgroup; schedules 11 step, 13 logistic, 16 periodic.

Baselines in `runner.py`: alarm_only (max |z-score| of the three sensors > 2.5 vs a no-drift reference; 0.3 per alarm onset),
adapt_always (TTA every 25 steps, 1.0 each), retrain_schedule (one retrain at t=1200), selective_only (always abstain, 0.3 once).
Baselines request 2 uniform labels per step while budget remains (about 967 labels, label cost 48.35); controllers pace their own
audits (about 1360-1385 labels). All eight methods run on identical episode seeds 1000-1039.

### 5.2 Results (40 episodes, mean +- s.e. over episodes; source `results/d2a_rar/drift2act/summary.md`)

`C_tot = C_act + C_label` (C_label = 0.05 per label requested; the paper's Eq. 33 sums action costs c(a_t) and it is unclear whether
its baselines include label cost, so C_act is the closer analogue). V = number of steps in the episode (L=1500, about 1075
post-onset) with R*_t > tau. T_det is defined in 5.5. T_rec_post_harm is the time from the first harmful step to the first later
recovered step (NaN, hence dropped, in episodes that never become harmful).

| method | C_tot | C_act | C_label | V | T_det | T_rec_post_harm | min Acc_wg |
|---|---|---|---|---|---|---|---|
| alarm_only | 50.44 +- 0.35 | 2.09 +- 0.34 | 48.35 +- 0.09 | 549.85 +- 69.87 | 269.80 +- 17.19 | 653.80 +- 81.17 | 0.53 +- 0.04 |
| adapt_always | 108.35 +- 0.09 | 60.00 +- 0.00 | 48.35 +- 0.09 | 426.32 +- 71.67 | 226.60 +- 16.73 | 483.72 +- 89.46 | 0.54 +- 0.04 |
| retrain_schedule | 60.35 +- 0.09 | 12.00 +- 0.00 | 48.35 +- 0.09 | 410.88 +- 49.78 | 269.80 +- 17.19 | 472.31 +- 54.67 | 0.53 +- 0.04 |
| selective_only | 48.65 +- 0.09 | 0.30 +- 0.00 | 48.35 +- 0.09 | 468.38 +- 70.26 | 269.80 +- 17.19 | 602.82 +- 85.56 | 0.57 +- 0.04 |
| ctrl_no_cert | 171.23 +- 28.80 | 102.67 +- 28.97 | 68.56 +- 0.28 | 363.10 +- 66.86 | 7.25 +- 4.59 | 352.33 +- 82.02 | 0.54 +- 0.04 |
| **ctrl_cert** (headline) | 97.84 +- 0.79 | 29.86 +- 0.79 | 67.98 +- 0.30 | 353.90 +- 66.60 | 3.50 +- 3.33 | 201.42 +- 36.70 | 0.54 +- 0.04 |
| ctrl_cert_alg1 (adds delta_t = 6 delta/(pi^2 t^2)) | 96.59 +- 0.07 | 27.38 +- 0.04 | 69.21 +- 0.07 | 463.25 +- 70.52 | 0.00 +- 0.00 | 277.32 +- 37.33 | 0.56 +- 0.04 |
| ctrl_cert_literal (per-round Q_t, delta_t, unconditional scheduling) | 96.60 +- 0.05 | 27.30 +- 0.00 | 69.30 +- 0.05 | 468.00 +- 70.19 | 0.00 +- 0.00 | 270.68 +- 37.39 | 0.56 +- 0.04 |

Paired differences vs alarm_only (same episode seeds; mean +- s.e. of the per-episode difference):

| method | dV | dC_tot | dT_rec_post_harm | d min Acc_wg |
|---|---|---|---|---|
| adapt_always | -123.53 +- 48.14 | +57.91 +- 0.34 | -156.64 +- 65.09 | +0.01 +- 0.01 |
| retrain_schedule | -138.97 +- 25.95 | +9.91 +- 0.34 | -170.00 +- 27.61 | -0.00 +- 0.00 |
| selective_only | -81.47 +- 38.19 | -1.79 +- 0.34 | -18.39 +- 2.94 | +0.03 +- 0.00 |
| ctrl_no_cert | -186.75 +- 51.22 | +120.79 +- 28.67 | -301.47 +- 75.05 | +0.00 +- 0.00 |
| ctrl_cert | -195.95 +- 47.15 | +47.40 +- 0.90 | -445.70 +- 69.28 | +0.01 +- 0.00 |
| ctrl_cert_alg1 | -86.60 +- 38.37 | +46.16 +- 0.36 | -343.89 +- 55.05 | +0.03 +- 0.00 |
| ctrl_cert_literal | -81.85 +- 38.17 | +46.16 +- 0.35 | -350.54 +- 58.03 | +0.03 +- 0.00 |

Further paired numbers from the same shard JSONs (inline check, 2026-11-07): ctrl_cert minus adapt_always on V is -72.4 +- 68.2 (not
distinguishable from zero; ctrl_cert has fewer violations in 70% of episodes); both controllers use about +20 label cost over
alarm_only. By drift type (n = 8 covariate, 11 subgroup, 21 concept; last table of `summary.md`): ctrl_cert V = 521 +- 148
(covariate), 0.8 +- 0.6 (subgroup), 475 +- 95 (concept) against alarm_only 701 +- 110, 100.7 +- 100.7, 728 +- 81. Subgroup drift is
rarely harmful under the group-reweighted R* (only 15% of the stream is affected), so its V carries little information. Episodes with
V=0: 25% for alarm_only, 22.5% for ctrl_cert.

### 5.3 Comparison with the paper's Table 1 (SyntheticDrift-CIFAR row)

Paper: Alarm-only / Adapt-always / Retrain / Selective / Ctrl / Ctrl+cert: C_tot 2.6/52.0/36.0/8.6/16.8/21.2; V 52/4/10/19/8/0;
T_det 16/13/25/18/14/15; T_rec 185/66/92/148/84/58; min Acc_wg .68/.79/.77/.72/.78/.82. The paper's units for V and T are not stated
precisely. Our environment is a stand-in, so only qualitative agreement is testable; absolute magnitudes are not comparable.

**Reproduces (direction only):**
- Every intervention has lower mean V than alarm_only; ctrl_cert has the largest paired V reduction vs alarm_only (-196 +- 47) and
  the smallest T_rec_post_harm (201 vs 654 for alarm_only; paired -446 +- 69).
- ctrl_cert is cheaper in action cost than adapt_always (C_act 29.9 vs 60.0), as in the paper (21.2 vs 52.0).

**Does NOT reproduce:**
1. **V approx 0 for Controller+cert** (paper 0 on SyntheticDrift-CIFAR). Ours is 353.9 +- 66.6 steps (about a third of post-onset
   steps), and not distinguishable from adapt_always (paired -72.4 +- 68.2) or retrain_schedule. ctrl_cert does *not* have more
   violations than adapt_always, so no "certificate hurts" finding either; the "near-zero violations" claim is just not reproduced here.
2. **Certificate raises cost** (paper: ctrl+cert 21.2 > ctrl 16.8). Ours is reversed: C_act 29.9 vs 102.7. In the 12-episode log
   (seeds 1000-1011, `mech_diag.json`) ctrl_no_cert repeats A2 TTA on 271-570 steps of every covariate-drift episode (the paper
   specifies cooldowns only for retrain and rollback, so A1/A2 have none in our reconstruction), while ctrl_cert spends on about
   1.9 retrains + 1.7 rollbacks per episode and per-activation abstain.
3. **Accuracy.** min Acc_wg barely differs across methods (0.53-0.57, s.e. 0.04); the paper's 0.68 to 0.82 spread is not reproduced.
   Ours is dominated by the minority group in subgroup-drift episodes (about 0.11 for every method) -- a property of the stand-in.
4. **T_det** of the baselines is about 230-270 steps (paper 13-25): our alarm is an untuned z-score threshold on three noisy
   low-dimensional sensors, right-censored at L-onset (no tuning split was used; recorded, not tuned away).
5. selective_only has the best min Acc_wg here (0.57); the paper has it between alarm-only and the adaptive methods.

### 5.4 Why V is large for ctrl_cert (descriptive; `mech_diag.json`, 12 episodes, seeds 1000-1011)

* **The gate is closed for most of the stream at tau=0.2.** Certification needs R^_t + rad(n, 0.05) <= 0.2. With rad(100)=0.252,
  rad(300)=0.158, rad(500)=0.126, rad(1024)=0.092 and a clean base error near 0.055, at least about 370 released labels inside the
  window are needed even before any drift. The gate was open on 1.5% of pre-onset steps and 30% of all steps (means over the 12
  episodes); in 3 of 12 episodes it never opened (median first-open step 388 where it did). With the gate closed the controller
  abstains (A6): ctrl_cert chose A6 on 98.6% of steps (1358-1500 of 1500 per episode).
* Abstaining only helps R* where confidence is below theta_sel=0.6, so most harmful steps stay harmful: per episode on average 388
  harmful steps, of which 380 were abstained steps, 341 had a closed gate and 47 an open gate (certified yet harmful; the pooled
  window-average bound lags a change, section 2 conditions 2-3).
* Retraining is limited by the 800-step cooldown (about 2 per episode) and needs >= 30 released labels; with delay 50 and window 1024
  the re-scored post-retrain model sees mixed pre/post-drift labels.
* This is the short-horizon / low-tau vacuity of section 2. It is a property of our reconstruction plus stand-in; the paper's sensor
  models, T, G calibration, lambda and discriminative evidence are unknown, so we cannot say whether its V approx 0 holds in its own
  environment. We do not claim the paper's result is wrong.

### 5.5 Metric definitions, and two artifacts

* **V** (`runner.py`): `int((R > tau).sum())` over all L=1500 steps, R_t the evaluator-side error of the model in force: a count of
  steps, including pre-onset ones. The paper's V values (0-63) cannot be a same-definition step count over 1500 steps; its unit is
  presumably coarser (unstated).
* **T_det = 0 for controllers is a metric artifact, not early detection.** The controller alarm flag is
  `belief[none] < 0.5 or action != A0_noop`, and the controller abstains almost always: pre-onset alarm fraction 0.998 (ctrl_cert)
  and 0.795 (ctrl_no_cert) in the 12-episode log. The gate is closed from t=0 (U_t = inf with no released label), and the belief
  starts uniform. Baselines' alarm is a sensor threshold, so T_det is not comparable between the families; read the controllers'
  T_det as "alarm already on at onset" (pre-onset false-alarm rate about 1), not a detection delay.
* **T_rec = 0 is a metric artifact.** `T_rec = min{t >= onset : R_t <= tau} - onset` is 0 whenever the model is still fine at the onset
  step. That holds for 77.5% (alarm_only) to 82.5% of episodes (alarm_only: 100% of logistic and periodic schedules, 18% of step
  schedules). The summary therefore reports `T_rec_post_harm` (first harmful step to first later recovered step; censored at the
  episode end if it never recovers; NaN if never harmful). Raw T_rec stays in the shard JSONs (means: alarm_only 243.5, ctrl_cert 87.0).

### 5.6 Bug history

A first 40-episode run (`results/d2a_rar/drift2act_v0_stratified_bug`) used the stratified 300/300 evaluation sample unweighted
(50% minority). It is archived and not used; fixed by reweighting to the 0.85/0.15 stream prevalence (`truth_eval`).
`aggregate.py` had `paired` defined after its `__main__` block (NameError as a script); fixed 2026-11-07 and `C_label` added to the
table.

### 5.7 Reproduce

```
WT="C:/Users/nigel/OneDrive/桌面/ICML/shiftlab-d2a-rar-2026-11-07"; cd "$WT"
export PYTHONPATH="$WT/src" PYTHONIOENCODING=utf-8
PY=C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/.venv/Scripts/python.exe
# 8 shards x 5 episodes (~890 s each, CPU): shard k covers episode seeds 1000+5k .. 1004+5k
for k in 0 1 2 3 4 5 6 7; do "$PY" -m shiftlab.sota.drift2act.runner $((5*k)) $((5*k+5)) results/d2a_rar/drift2act/shard$k.json > results/d2a_rar/drift2act/shard$k.out & done; wait
"$PY" -m shiftlab.sota.drift2act.aggregate results/d2a_rar/drift2act > results/d2a_rar/drift2act/summary.md
"$PY" results/d2a_rar/drift2act/mech_diag.py     # 12 episodes with logs (several minutes); writes mech_diag.json
```
Code version: `git log -1` = `2920475663330701cff5a23cf269a96fda87b244` (branch `research/drift2act-rar-autoresearch-2026-11-07`)
**plus uncommitted working-tree changes**: the Drift2Act sources were not committed when the runs were made. The 2026-11-07
lint/aggregate edits do not change run behaviour (10 unit tests pass after them). Config: `Config()` defaults (printed in every shard
JSON). Calibration seeds 50000-50011; episode seeds 1000-1039. `results/` is gitignored; the shard JSONs are the primary evidence.

### 5.8 Assessment

Continue as a baseline host (certificate + gate + belief/utility selector + `LabelRequestPolicy`/`EvidenceModel` hooks all run and are
tested), but expect it to be a weak performer on streams like ours: the paper's headline V approx 0 is not reproduced here.
Camelyon17, DomainNet and the paper's Tables 6-14 (ablations, sweeps, FIR, Amazon) are not reproduced; no claim is made about them.

## 6. Contract port (`COMMON_CONTRACT_PORT`)

`src/shiftlab/bench/contract/adapters_drift2act.py` (policy `Drift2ActContractPolicy`, adapter `Drift2ActAdapter`, claimed null
`abs_risk`); tests `tests/d2a_rar/test_adapter_drift2act.py`. The coordinator wires it into `adapters.py` (not edited here).
Action map: A0 -> continue; A3 -> query (windowed uniform audit, one query per round, size from the swappable
`LabelRequestPolicy.request_size`); A2 (TTA) -> switch(CANDIDATE); A4 -> retrain; A5 -> rollback (only if `prev_m` is the last
certified model); A6 -> abstain; certificate-failure transition -> alert (rate limited). **Unmapped: A1 recalibrate** (the contract
has no in-place model edit); `route` and switching to the retrained model are not used.
Deviations: `ObservableState` has no embeddings or predictive probabilities, so z_t is computed from the scalar monitor `x` and
released losses: z1 = mean-shift z-score (MMD proxy), z2 = log-scale z-score (entropy proxy), z3 = recent-vs-reference released-loss
z-score (dECE proxy). Evidence p(z|d) and T are hand-specified and untuned (no calibration data in the contract), so the belief
separates none vs drift only. The abstain price is charged per abstained round (native: per activation). The audit window reaches back
only `ClockSpec.max_lookback` rounds (default 0 degenerates to labelling the current round). The certificate pools released labels in
the window (heuristic unless within-window risk is stationary). Claimed null `abs_risk`: valid only for uniform window sampling; not
under informative delay/missingness, serial dependence or non-uniform round choice. The Q2 hook swaps only the request size; round
choice stays uniform inside the host (tested: non-query actions before the first label release are identical, N_q and c_q differ).
Smoke (not a performance claim): on `iid_shift_d10`, balanced costs, label_cap 300, max_lookback 200, 3 seeds, the adapter abstained
on 774-859 of 1000 rounds because the gate at tau=0.5 is mostly closed, mirroring 5.4.

## 6. Q1 label-outcome evidence seam (added 2026-11-07)

The legacy Q1 hook `EvidenceModel.log_lik(z, gap)` sees only the three monitor proxies, never the label chain, so kernel / envelope /
restart / hazard evidence was NOT_IMPLEMENTED. The seam (`src/shiftlab/bench/contract/evidence_seam.py`) delivers RELEASED labelled
observations only, as `ReleasedOutcome(label_id, request_round, label_round, release_round, losses, d, gap, order, selection)`:
`d = loss(candidate) - loss(incumbent)` (None if not identifiable, e.g. `obs_mode='deployed'`), `gap = t_i - t_{i-1}` in event rounds
against the previous in-order outcome, `order in {first, in_order, out_of_order, unidentified}`, `selection = (declared propensity,
serving model, delay)`. Out-of-order outcomes keep their own `label_round` but get `gap=None`; the Q1 processes drop and count them.

* (a) Drift2Act host: `Drift2ActContractPolicy(evidence=OutcomeAugmentedEvidence(ProxyEvidence(), outcome_evidence))`. The host calls
  `bind_env(env)` at reset and `outcome_sink(state)` each round before the belief update; belief gets `base.log_lik + beta*[0,d,d,d]`
  with `d` the increment of the outcome process' log e-value (a modelling choice, not a validity claim). Objects without those
  attributes (the default `ProxyEvidence`) are never touched: default behaviour is bit-identical (golden `tests/d2a_rar/golden/`).
* (b) Contract-native shell: `adapters_evidence.EvidencePromoterPolicy` / `promoter_adapter(identity)` queries on a declared schedule
  (`calendar`, `cyclic_gaps`: regime `predictable`; `bernoulli`: `exogenous`, propensity declared), feeds the seam, switches on alarm.
* Identities: `evidence_q1.build_evidence(registry_identity)`; implementation registry `docs/d2a_rar/registry/Q1_EVIDENCE_IMPLS.json`
  (filtration, transition model, stopping, parameter uncertainty, target null, selection requirement, validity class per entry).

Validity scope: P^{g_i} (and the conditional bets) hold only if the choice of `t_i` is G_{i-1}-measurable or exogenously randomised
with a declared propensity. **The Drift2Act host does not satisfy this**: its request size depends on belief/certificate state using the
current monitor x_t and its queries carry no propensity, so the augmented evidence declares `monitor_adaptive` and
`contract_status()` returns OUT_OF_CONTRACT there; Q1 validity is scored on the promoter shell only, and host runs are descriptive.
Informative delay/missingness and `rho > declared_rho_bar` cells are flagged out-of-contract by `contract_status(stream_spec)` (harness side).
