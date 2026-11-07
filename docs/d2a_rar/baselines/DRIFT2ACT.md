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

## 5. Reproduction

(see below; filled after runs)
