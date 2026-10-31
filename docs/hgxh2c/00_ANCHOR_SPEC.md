# 00 Anchor spec: H2c and HG (formula-level, for batched re-implementation)

Extracted read-only from worktrees under `C:/Users/nigel/OneDrive/桌面/ICML/` (call it ROOT). Nothing was re-run except reading stored CSVs.
Commits: H2c = `60930a4` (branch research/h2c-strong-baselines-and-generalization-2026-10-30; prereg `e164d63`, results `44119c6`).
HG engine = `8552911` (research/shiftlab-mandate-gap-closure-2026-10-30). HG original and validity docs = `1299c1c` (research/hg-validation-and-novelty-2026-10-30). Restart variants = `d4673d9` (research/h2c-restart-risk-certified-2026-10-30).
Status of every number below: DOC-ONLY (read from stored docs/CSV) unless stated. No comparator is a verified published reproduction.

Paths: H2C = `ROOT/branch-research-h2c-strong-baselines-and-generalization-2026-10-30` (files `src/shiftlab/sota_search/{detectors,generators,harness}.py`, `scripts/sota_search/g5_confirmation.py`). GAP = `ROOT/branch-research-shiftlab-mandate-gap-closure-2026-10-30` (files `src/shiftlab/gap/{engine,worlds,pools}.py`, `scripts/gap/e15_confirm.py`, `configs/gap_closure/frozen_confirmation_v1.json`).

## 0. Shared notation and increment (both methods)

Per step t: covariates x_t ~ N(0,I_4), deployed score p_t, action a_t = 1{p_t >= TAU}, TAU = FP/(FP+FN) = 1/6, FN=5, FP=1, outcome y_t in {0,1}.
- Decision cost (economic, track C): L_t = a_t(1-y_t)FP + (1-a_t)y_t FN, range [0,5]. Brier (predictive, track B): B_t = (p_t-y_t)^2, range [0,1].
- Label-free PROXIES (the "prediction" in prediction-powered inference; model-implied expected loss if p_t were the true P(y=1|x)):
  Brier proxy h^B_t = p_t(1-p_t) (max 1/4). Cost proxy h^C_t = a_t(1-p_t)FP + (1-a_t)p_t FN (max FN/6 = 5/6, attained at p=TAU).
- Query Q_t ~ Bernoulli(q), q = frac constant (0.10 or 0.20), independent of outcome, common random mask across arms. Label of step s usable d=5 steps later (fixed known delay).
- Nominal r0 (the "U_0"; tol = eps = 0): mean of the same loss on an independent large SOURCE-only stream of the same deployed model, treated as KNOWN (no calibration uncertainty). G5: `source_moments("G5:cond")` = means of `loss` (cost) and `brier` over `simulate_g5(cond,"none",100,999,T=4000,source_only=True)` (400k events). Gap engine: `worlds.source_risks` = mean over 60 seeds x T=2000 (seed 31337) of the world's source regime, noise included.
- Prediction-powered (IPW control-variate) increment, NOT normalised to [0,1]; raw loss units:
  X^R_t = h^R_t + (Q_t/q)(R_t - h^R_t) - r0^R - tol,   R in {B, C}.
  E[X^R_t | F_{t-1}] = E[R_t | F_{t-1}] - r0^R - tol. Null H0: E[R_t | F_{t-1}] <= r0^R + tol.
- Predictable one-sided bound ("uniform"/"sup" cap, the cap repair): Bd^R = hmax^R(1/q - 1) + r0^R + tol with hmax^B = 1/4, hmax^C = 5/6. Then X >= -Bd, so 1 + lam X >= 1 - cap whenever lam <= cap/Bd, cap = 0.5. The ORIGINAL cap used the current proxy: `tight = proxy*(1/q-1)+r0+tol` (`_pp_parts` line 265) which depends on the current covariate and breaks validity under the marginal null (exact finite-support counterexample, E[factor] up to 1.13). Repaired version: `uniform_cap=True` (lines 266-269) / engine `cap_mode="sup"` (line 387).
- Delay indexing (sota_search cumsum form): bet lam_s uses X_u only for u <= s-d-1; the factor of step s enters wealth at time s+d: log W_t = sum_{s<=t-d} log(1 + lam_s X_s). Alarm = first t with log W_t >= ln(1/alpha) = ln 20 = 2.9957 (`THEORY_THRESHOLD`). Everything (including unqueried, proxy-only X) is delayed by d in this form (conservative).
- `shift_time(a,d)`: out[:, d:] = a[:, :-d], zeros before. `_ewm_cumsum(x,g)`: c_t = g c_{t-1} + x_t (g>=1 -> plain cumsum).
- Discounted Kelly kernel, gamma in (0,1]: n_s = sum_{u<=s-d-1} gamma^{s-d-1-u}; m1_s = (sum gamma^{s-d-1-u} X_u)/(n_s+1); m2_s = (sum gamma^{s-d-1-u} X_u^2)/(n_s+1); K_s = max(m1_s,0)/m2_s (0 if m2<=0); lam_s = min(K_s, cap/Bd).

## 1. H2c

### 1.1 Null
COST null (track C): E[L_t | F_{t-1}] <= r0^C + tol (conditional excess decision cost; filtration = released labels; context-free cap, fixed known delay; `docs/h2c_next/COST_NULL_VALIDITY.md`). Not a Brier test: Brier only steers the stake ("guidance"). Wealth factors use the COST increment X^C.

### 1.2 Exact recursion (`pp_cost_guided`, mode="guided_disc", gamma=0.995, cap=0.5, delay 5)
Bd_b = 0.25(1/q-1)+r0^B+tol; Bd_c = (5/6)(1/q-1)+r0^C+tol; hib = cap/Bd_b; hic = cap/Bd_c (scalars per condition, constant in t).
 K^B_s = discounted Kelly ratio (gamma=.995) on BRIER increments X^B.
 rel_s = min(K^B_s, hib)/hib in [0,1]    (Brier bet's relative position in its allowed interval)
 lam_s = rel_s * hic = min(K^B_s, hib) * Bd_b/Bd_c      (re-expressed on the cost interval; ceiling hic = cap/Bd_c)
 log W_t = sum_{s<=t-d} log(1 + lam_s X^C_s); alarm when log W_t >= ln 20. No restarts, no mixture, no gate.
Reduction (sweet-lovelace `d1b173b` X1, DOC-ONLY): identical to discounted Kelly on cost with the moment ratio replaced by the Brier moment ratio (max |dlogW| 8.9e-16). Guidance helps +.03..+.14 only when Brier co-shifts; loses up to .59 when Brier is flat/opposed.

```
# H2C/src/shiftlab/sota_search/detectors.py:579-592
xc, _q, _l, bc = _pp_parts(sim, frac, lseed, "cost", None, None, tol, uniform_cap=True)
xb, _q2, _l2, bb = _pp_parts(sim, frac, lseed, "brier", None, None, tol, uniform_cap=True)
S, T = xc.shape
hic, hib = cap / bc, cap / bb
if mode == "guided_disc":
    ones = np.ones_like(xb)
    n = shift_time(_ewm_cumsum(ones, gamma), delay + 1)
    m1 = shift_time(_ewm_cumsum(xb, gamma), delay + 1) / (n + 1)
    m2 = shift_time(_ewm_cumsum(xb**2, gamma), delay + 1) / (n + 1)
    rel = (np.minimum(np.where(m2 > 0, np.maximum(m1, 0) / np.maximum(m2, 1e-12), 0.0), hib) / hib)
    lam = rel * hic
    return np.cumsum(shift_time(np.log1p(lam * xc), delay), 1)
```
```
# detectors.py:250-270 (_pp_parts) essentials
proxy = act*(1-p)*FP + (1-act)*p*FN  (cost)  |  p*(1-p)  (brier);   r = sim["loss"] | sim["brier"]
r0 = source_moments(family)["loss" | "brier"][0]
x = proxy + (qm/qv)*(r - proxy) - r0 - tol
tight = (0.25 if brier else 5/6)*(1/qv - 1) + r0 + tol      # uniform_cap=True
```
```
# H2C/scripts/sota_search/g5_confirmation.py:10-20 (arms; delay=5, tol=0, frac in {.1,.2})
"F1_H2c": ("pp_cost_guided", {"mode": "guided_disc", "gamma": 0.995}),
"F2_guided_ONS": ("pp_cost_guided", {"mode": "guided"}),
"F3_multi_guided": ("pp_cost_multi", {"guided": True}),  # equal-weight mixture over gamma in (.9,.99,.999,1.0), log-mean-exp
"C0_cost_parent": ("pp_cost_tight", {}),
"C1_cost_disc": ("fix_cost", {"gamma": 0.995, "uniform_cap": True}),
"C2_cost_ONS": ("pp_cost_guided", {"mode": "cost_ons"}),
"C7a_cost_SR": ("sr_cost_tight", {}),
"HG_unifcap": ("fix_brier", {"gamma": 0.99, "gate_w": 100, "uniform_cap": True}),
"ONS_Brier": ("pp_ons", {}),
```
(Function defaults gamma=0.99 / mode="cost_ons" are NOT what the frozen run used; the run passes gamma=0.995.)

### 1.3 Information use
Fixed known delay d=5 applied to every term, including proxy-only parts. Labels queried Bernoulli(q), q constant and predictable (context-free), independent of outcome. Proxy = the deployed model's own score (no extra model). Nominal r0^B, r0^C known from 400k source events. Bets are measurable w.r.t. labels resolved by s (indices <= s-d-1). Random independent delay: proved/simulated in a separate release-time re-implementation (`src/shiftlab/sota_search/g6.py`, not in the detectors.py quoted here; null FA <= .015). Outcome-dependent delay: NOT covered (observed null FA .025-.045 at 20% labels, margin thin).

### 1.4 Comparators (all cost null, same X^C, same delay, threshold ln 20 unless stated)
- C0 `pp_cost_tight` = `pp_eprocess(risk="cost", tight=True)` (lines 273-304): pooled (gamma=1) Kelly, lam_s = min(max(m1,0)/m2, cap/Bd_ctx_s) with context-dependent Bd_ctx_s = h^C_s(1/q-1)+r0+tol; m1,m2 = plain cumsums over u<=s-d-1 divided by (n+1), n = max(s-d,0). Proved only under the pointwise null.
- C1 `fix_cost` = `pp_fix(risk="cost", gamma=0.995, uniform_cap=True)` (lines 357-407, 414): the discounted Kelly kernel of Sec 0 applied to X^C itself, lam_s = min(K^C_s, cap/Bd_c); no gate. Same code with risk="brier" is the Brier "disc_only" arm.
- C2 `cost_ons` (lines 593-610): Online-Newton-step bet on X^C. c = 2/(2-ln 3) (~2.2). State cur=0, a=1, acc=0. For s=0..T-1: lam_hist[s]=cur; r=s-d; if r>=0: acc += log1p(lam_hist[r] X_r); z = X_r/(1+lam_hist[r] X_r); a += z^2; cur = clip(cur + c z/a, 0, hic); logW[s]=acc. (F2 "guided" ONS: ONS runs on X^B with hib and the applied bet is lam_hist/hib*hic.)
- C7a `sr_cost_tight` = `sr_edetector(risk="cost")` (lines 307-326): Shiryaev-Roberts R_t = (1+R_{t-1}) f_t, f_s = 1 + lam_s X^C_s shifted by d (fill 1), lam_s = pooled Kelly capped by the CONTEXT cap cap/(h^C_s(1/q-1)+r0). Threshold EMPIRICAL (`harness.calibrate`, line 69-75): 95% quantile of max_t R_t over 400 null G5 streams of the same condition (`simulate_g5(cond,"none",400,99000+ci)`, lseed 77). No guarantee (null FA .045-.055 dev; .052 confirmation).
- ONS_Brier `pp_ons` (488-511): same ONS on X^B with hi = cap/Bd_b; Brier-null.
- HG (Brier) arm: Sec 2.

### 1.5 Restarts (branch `d4673d9`, `src/shiftlab/sota_search/restart.py`)
Valid restart mixture: shared factors f_t = 1 + lam_t X^C_t; predetermined start weights w_j >= 0, sum w = 1 (single, uniform 1/T, front, geometric .995^j normalised, coarse8); S_t = (S_{t-1}+w_t) f_t, M_t = S_t + sum_{j>t} w_j; P(sup M >= 1/alpha) <= alpha (Ville). Uniform w = SR/T, i.e. SR threshold ~T/alpha (SR at 1/alpha only has ARL >= 1/alpha, finite-horizon FA ~1.0). Result: no power gain (+.003/.009/.023, noise); empirical-threshold SR variants more powerful (.270/.416/.555 vs ordinary .075/.174/.327 at 5/10/20% labels, 18 dev worlds) but thresholds do not transfer (.03-.13, up to .30 under strong dependence). Unknown nominal: upper bound U0 (Hoeffding / empirical Bernstein) from n_cal labelled source events, alpha_cal=.01, alpha_test=.04 (threshold 25): power ~0 for n_cal <= 1000; EB with n_cal=50,000 gives .535/.850 vs .603/.902 (known nominal; delta=2, 10%/20% labels).

## 2. HG (Brier discounted Kelly gated by recent decision-cost excess)

### 2.1 Null
BRIER / predictive null (track B): E[B_t | F_{t-1}] <= r0^B + tol with X^B as in Sec 0. The cost increment X^C is used ONLY as a gate on the stake ("decision-aware component"). Hence benign predictive change is only partly suppressed (benign FA .159/.274 at 10/20% labels on G5; near 0 on G3).

### 2.2 Recursion (sota_search form `pp_fix(risk="brier", gamma=0.99, gate_w=100, uniform_cap=True)`; arm HG_unifcap)
 K^B_s: discounted Kelly ratio (gamma=.99) on X^B; lam^disc_s = min(K^B_s, cap/Bd_b).
 Gate: gg = 1 - 1/gate_w = 0.99; gm_s = (sum_{u<=s-d-1} gg^{s-d-1-u} X^C_u)/(n^gg_s + 1); g_s = 1{gm_s > 0} (same labels, same mask, same delay).
 lam_s = lam^disc_s g_s; log W_t = sum_{s<=t-d} log(1 + lam_s X^B_s); alarm at ln 20. Cap 0.5; no restart.
```
# H2C/src/shiftlab/sota_search/detectors.py:391-407 (pp_fix)
c1 = shift_time(_ewm_cumsum(x, gamma), delay + 1)
c2 = shift_time(_ewm_cumsum(x**2, gamma), delay + 1)
n = shift_time(_ewm_cumsum(ones, gamma), delay + 1)
mean, second = c1 / (n + 1), c2 / (n + 1)
lam = np.minimum(np.where(second > 0, np.maximum(mean, 0) / np.maximum(second, 1e-12), 0.0), cap / tight_b)
if gate_w is not None:
    xc, _q, _l, _t = _pp_parts(sim, frac, lseed, "cost", qv if alloc is not None else None, qm, tol)
    gg = 1.0 - 1.0 / gate_w
    gmean = shift_time(_ewm_cumsum(xc, gg), delay + 1) / (shift_time(_ewm_cumsum(ones, gg), delay + 1) + 1)
    lam = lam * (gmean > 0)
return np.cumsum(shift_time(np.log1p(lam * x), delay), 1)
```
### 2.3 Gap-closure engine form (`GAP/src/shiftlab/gap/engine.py`, `Cfg(risk="brier", gamma=0.99, gate_w=100)`; defaults cap_mode="sup", release="prefix", cap=0.5; frozen arm in `frozen_confirmation_v1.json`)
Same mathematics, event loop over t, vectorised over seeds; differences in information timing:
```
# engine.py:382-396
X = theta * pt + (Q / qs) * (rt - theta * pt) - r0 - cfg.tol            # theta = 1 for HG
bound = theta * pmax * (1.0 / max(qmin_eff, 1e-9) - 1.0) + r0 + cfg.tol  # cap_mode="sup"; qmin_eff = frac
lam = np.minimum(lam_raw, cfg.cap / bound) * bet_scale
if cfg.gate_w:
    gmean = g1 / (gn + 1.0); lam = lam * (gmean > 0)
logf = np.log1p(lam * X)
# engine.py:440-449 wealth release ("prefix": in-order)
rel = np.maximum(rel_prev, arr); rel_prev = rel
Wrel[np.minimum(rel, NB - 2), ar] += logf;  logW = logW + Wrel[t]
```
- Arrival: queried event arrives t + D_t (D_t may be an (S,T) array); UNQUERIED events arrive at t (`unq_delay=False`), so proxy-only increments enter the moments with no delay. Moments absorb buckets with arrival <= t-1 (lines 197-204); discount gamma^{count of arrivals in that bucket} per event (not per calendar step).
- Release: `prefix` (rel_t = running max of arrivals; valid for any delay mechanism by Ville on the event-indexed martingale); `arrived` naive subset (invalid under outcome-dependent delay); `legacy` t+d.
- pmax: brier 0.25, cost FN/6; r0 from `source_risks`. `Cfg(cap_mode="x", release="legacy", unq_delay=True)` reproduces the legacy cumsum code bit-for-bit.
- Optional, NOT in anchor HG: `lrv` (Bartlett LRV inflation; failed prereg, informational), `alloc/pacing/rel` (S03-S06, rejected after development), `HG_robustmix` (variance/uniform 0.5/0.5 mixture, conservative).

### 2.4 HG comparators
- parent `pprm_tight` = `pp_eprocess(risk="brier", tight=True)` (pooled Kelly, context cap); engine `pprm` = Cfg(risk="brier") (gamma=1, no gate, sup cap).
- disc_only = `fix_brier(gamma=.99, uniform_cap=True)` (no gate).
- ONS `pp_ons` (Sec 1.4, Brier). mixture8 `pp_mixture(k=8)`: equal-weight mixture over constant bets lam_j = (cap/Bd_b)(j/8), j=1..8 (valid under marginal null).
- engine `cost` arm: Cfg(risk="cost", gamma=.99): discounted Kelly on X^C (analogue of C1).
- PH / CUSUM (empirical thresholds, `e15_confirm.classical`, lines 96-120, 212-233): on queried decision losses, z = (L-mu)/sd with mu, sd from an independent null stream of the same world family; CUSUM stat <- max(0, stat+z-0.25); PH m <- m+z-0.05, stat = m - min m; updated on arrival of each queried label; threshold = 95% quantile of horizon max on the null stream; same Bernoulli mask (seed 10015) and delay.

## 3. Synthetic generators

All: x ~ N(0,I_4), W_SRC=(1.5,1,0,0), B_SRC=0; true logit = x.(W_SRC+dw) + B + db + dsub*1{x_2>1} (x_2 is 0-indexed third coordinate), y ~ Bern(sigmoid(logit)). Shift kinds (`_delta_terms`): prior db=+delta; concept dw=(-delta,+delta,0,0); cov_benign dmu[2]=+delta; cov_inform dmu[0]=+delta; subgroup dsub=-delta. Evaluator-only truth ("harm" = expected deployed-policy cost minus source cost; harmful iff >= 0.10; population values from 300k samples seed 910 for G5, 30k for gap worlds); never passed to monitors.

### 3.1 H2c: G5 (`generators.py:270-349`; runner `g5_confirmation.py`)
Deployed (possibly defective) model p = sigmoid(a*(x.W_SRC) + b + c*1{x_2>1}); true source model is a=1,b=0,c=0. Conditions (a,b,c): accurate (1,0,0); biased (1,.8,0); overconfident (2,0,0); underconfident (.5,0,0); subgroup_failure (1,0,-3); anti_informative (-.3,0,0); biased_neg (1,-.8,0); over_subgroup (2,0,-3). Held out for the confirmation: biased_neg, over_subgroup, shift concept1.5.
Shifts: none; prior1 (db=+1); concept2 (delta 2); concept1.5 (delta 1.5). T=2000, abrupt at t0=700, N=600 seeds/cell, 8x4 = 32 cells. Threshold-calibration nulls: 400 seeds `simulate_g5(cond,"none",400,99000+ci)`. Cell stream seed 90000+k (k = running index over conds then shifts in dict order, 0..31); label-mask seed lseed = 95000+k with k ALREADY incremented (so 95001+k_cell). frac in {0.10,0.20}; delay 5; tol 0.
Roles: shift=none -> null; else harm if post-shift cost harm >= 0.10 else benign. fh = 700 for harm cells, T otherwise. detected = alarm in [700,T) & harmful; false alarm = alarm < fh (benign/null: any alarm). Cells: 14 harm / 10 benign / 8 null.
Post-shift cost harm (read from `H2C/outputs/h2c_next/g5_confirmation_cells.csv`): accurate c2 .233, c1.5 .168, prior1 -.035; biased c2 .110, c1.5 .076 (benign), prior1 -.121; biased_neg c2 .370, c1.5 .277, prior1 .153; over_subgroup c2 .373, c1.5 .280, prior1 .223; overconfident c2 .369, c1.5 .277, prior1 .153; subgroup_failure c2 .242, c1.5 .176, prior1 .082 (benign); underconfident c2 .038, c1.5 .024, prior1 -.150 (benign); anti_informative all <= 0 (benign).
H2c power at 10% labels (read from CSV): accurate c2 .613, c1.5 .398; biased_neg c2 .720, c1.5 .450, prior1 .165; overconfident c2 .688, c1.5 .437, prior1 .070; over_subgroup c2 .575, c1.5 .343, prior1 .155; subgroup_failure c2 .342, c1.5 .173; biased c2 .217. Worst benign FA: biased c1.5 .110, underconfident c2 .102, subgroup_failure prior1 .057.
Frozen protocol: D1 = H2c minus per-cell better of {C1, C2} >= +0.05 with cluster-bootstrap CI (resample cells then seeds, 4000) lower > 0; D2 H2c >= guided-ONS - .02 and >= multi-horizon - .02; D3 null FA <= .07 in every null cell and pooled benign FA <= .07; D4 descriptive vs C7a. Execution note: runner crashed in analysis (name clash), per-seed results saved; analysis rerun from parquet (`g5_confirmation_analysis.py`).
Dev generators (not confirmation): G1/G2 `simulate(World(kind, delta, shape in abrupt|gradual|transient|recurrent), T=2000, t0=800)`; G3 Markov 3 regimes; G4 AR(1) signal sigma 1.5 rho .6 with regime-dependent beta/sigma.

### 3.2 HG: gap-closure worlds (`GAP/src/shiftlab/gap/worlds.py`, `pools.py`; confirmation `scripts/gap/e15_confirm.py`)
`LogitWorld(regimes=(Regime(kind,delta,fn),...), T=2000, t0, ar_rho, ar_sigma, cluster_len, cluster_sigma)`: deployed model fixed p = sigmoid(x.W_SRC); cost uses regime-dependent FN `fn` (policy unchanged). Latent-logit noise u added before the y draw: AR(1) u_t = sigma z_t, z_t = rho z_{t-1} + sqrt(1-rho^2) e_t; cluster: N(0,sigma^2) constant per block of `cluster_len` steps. Markov regime path: regime 0 for t<t0, then chain P from `transition(K, persistence, structure)` (jump: off-diagonal (1-p)/(K-1); cycle: k -> k+1 with 1-p).
Confirmation pool (seed = SEED0 + 1000*world_index, SEED0=900000; harm worlds 400 seeds, null worlds 1000; alpha .05; frac .1 and .2; delay 5; T=2000; round 2 seeds 1,100,000+):
- C3 K3_jump_p0.99: regimes (source, concept 2.5, cov_benign 2.5), jump p=.99, t0=500. C3 K4_cycle_p0.985: (source, cost fn=15, concept 1.6, prior 1.2), cycle p=.985. Null K2_null: (source,source), p=.99.
- C4 finance (`FinWorld`: GARCH(1,1) omega .05, a .10, b .85 default, t4 innovations, return = beta_regime*kappa*signal*sqrt(h)+sqrt(h)*z, action thresholded signal, tc .02, loss clipped [0,1] with clip_c=2, harm_thr .03, t0 500): fin_reversal_cycle betas (1,-.6), cycle p=.985, kappa .35; fin_K3 betas (1,.5,-.7), p=.99, a .12, b .84; null fin_null betas (1,1), p=.99, a .12, b .84.
- C5 proxy defects: abrupt concept delta 2.5 at t0=800 (`logit_sched_spec`), proxy modes accurate; anti (after shift: pmax - proxy); bias_after_shift (proxy+0.4 pmax, clipped); subgroup (x_2>1: pmax - proxy); calibration (pmax*(proxy/pmax)^0.35); oracle_adapt (proxy from true label law); null `C5|null|static_bias` (kind none, proxy + .25 pmax, t0=0). `apply_proxy` clips to [0,pmax]; r0 not recomputed.
- C6 delay worlds: abrupt concept 2.5 at t0=700; delay kinds (`worlds.delays`, d=5, seed 21): uniform U{0..10}; geometric mean 5; outcome (loss>0 -> 2 else 30); heavy (Pareto 1.3 *10, cap T); burst (batches every 20 steps). Nulls: ar0.9_s1.3 (rho .9, sigma 1.3), cluster120_s1.3, delay=outcome (no shift).
Results (round 1, frac .1 / .2 power over harm worlds): HG .701/.808, pprm .672/.756, cost .434/.759, PH .767/.918, CUSUM .683/.847; HG null FA mean .023/.045 (max .050/.137). HG minus parent +0.029 [.012,.046] and +0.052 [.020,.090] (Holm p .004/.003; recomputed from `outputs/gap_closure/e15_confirm/perseed.parquet`, analysis-level VERIFIED); HG vs PH/CUSUM -0.066/-0.110 (n.s.): not a win over classical detectors.
hg-validation G3 (sota_search `simulate_g3`, `G3_P=[[.997,.0015,.0015],[.003,.995,.002],[.003,.002,.995]]`, regimes none / concept 2 / cov_benign 3, 1000 seeds, 960 reach harm): HG_unifcap minus parent +.050 [.028,.073] @10%, +.131 [.106,.158] @20%; ONS .375/.539 and disc_only .334/.561 match or beat HG power.

## 4. Known results and limits
H2c:
- Frozen G5 power (10%/20% labels): H2c .382/.640 vs C1 .265/.545, C2 .296/.491, C0 .156/.402, C7a .572/.773 (empirical threshold, 2-3x FA, no guarantee), HG .483/.774 (benign FA .159/.274), Brier ONS .578/.769 (benign FA .257/.329). H2c benign FA .036/.067, null FA <= .027. D1 +.086 [.059,.113] / +.094 [.063,.125] PASS.
- Mechanically a discounted cost Kelly whose moment ratio is replaced by the Brier moment ratio; advantage vanishes or reverses when Brier does not co-move; on exposed Gas real-data replay H2c alarmed 242-824 events later than cost-only Kelly/ONS (DOC-ONLY, sweet-lovelace `d1b173b`).
- Validity PROVED only for fixed known delay (and independent random delay), context-free cap, known nominal; no unit test of the supermartingale. Outcome-dependent delay: no proof. Dependence: cost-null methods were NOT re-run under AR in these branches (G6 doc says so). The only dependence evidence is for Brier-null e-processes (below) and the gap-closure "cost" arm (discounted Kelly on cost) under cluster-400 (FA .163 > alpha). Treat H2c as not valid under dependence; no direct H2c measurement exists in these branches.
- Nominal risk assumed known; estimated nominal with n_cal <= 1000 gives power ~0.
HG:
- PROVED e-process under E[B_t | F_{t-1}] <= r0+tol with uniform/sup cap, predictable q, fixed delay (`docs/hg_validation/02_VALIDITY_PROOF.md`); the context-cap version is FALSIFIED under the marginal null (exact counterexample, `tests/gap/test_engine.py::test_exact_finite_support_cap`, 18 tests pass). `prefix` release valid for any delay mechanism; gate and discounting preserve validity (resolved labels only).
- INVALID under slowly varying conditional risk. AR(1) covariate null FA at 20% labels (rho=.98): parent .17, HG ctx-cap .27, HG unif-cap .295, ONS .36; at 10%: .077/.117/.125/.177. Moderate dependence (rho<=.9) harmless except ONS at 20% (.072). Gap engine: cluster-400 sigma 1.5: HG .190, pprm .121, cost .163; GARCH fin null: HG .089, pprm .130, cost .030. Discounting plus gating are worse than the undiscounted parent. LRV repair (F2) failed prereg.
- Gains: improves its parent; not better than ONS or plain discounting; not better than PH/CUSUM.

## 5. Re-implementation checklist (batched PyTorch)
1. Streams (S,T): x, y, p; precompute h^B, h^C, B, L, r0^B, r0^C from an independent source stream; mask Q = U<q with common random numbers across arms.
2. X^R = h^R + (Q/q)(R - h^R) - r0^R - tol. Bd^B = .25(1/q-1)+r0^B, Bd^C = (5/6)(1/q-1)+r0^C.
3. Discounted sums c_t = g c_{t-1} + v_t for v in {X, X^2, 1} (scan or lfilter); shift by d+1; divide by (n+1).
4. H2c: lam = min(K^B, cap/Bd^B) * Bd^B/Bd^C. HG: lam = min(K^B, cap/Bd^B) * 1{gate_mean^C > 0} (gate gamma .99 on X^C). logW = cumsum(shift(log1p(lam X^{C or B}), d)). Alarm at first t with logW >= ln 20.
5. C1/C2/C7a per Sec 1.4 (ONS is a sequential scan over t, vectorised over S); C7a threshold from a 400-seed null quantile.
6. Sanity checks: gamma=1, no gate, uniform cap -> HG = uniform-cap Brier Kelly; H2c with K^C in place of K^B = C1; shuffled/permuted Q keeps null FA <= .05 on iid streams.
