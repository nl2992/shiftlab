# WP2 protocol: which null should certify deployment under temporal dependence?

The protocol record is dated 2026-11-04 and attributes registration to Agent F (sprint 2,
workstream P2). The available files do not independently establish whether it preceded every WP2
policy run or construction of the v2 twin splits; treat the chronology as protocol-recorded, not
externally timestamp-verified. The protocol states that only the reproduction of the five registered
twin datasets (hash check, no policy) had started before writing and that its choices were not tuned
on WP2 runs. Those process claims likewise cannot be independently verified from result artifacts.

## Question

Sprint 1 showed that every powered conditional-null (V1) certified port promotes at well above alpha on
real exchangeable-twin nulls, while A5b (V2, marginal stationary Markov) mostly holds. It also observed
that twin-null promotions mostly go toward the twin that realised lower loss. WP2 asks which null is the
economically right object: the conditional null V1, the marginal null V2, or economic non-improvement V3.

## Amendment 0 (lead novelty findings, 2026-11-04; protocol-recorded as pre-run, chronology unverified)

* **Framing.** The conditional/unconditional distinction is not new. It is Giacomini & White
  (Econometrica 2006): conditional vs unconditional predictive ability, building on Diebold-Mariano
  1995 and West 1996. Henzi & Ziegel (2022) and Choe & Ramdas (2024) give the anytime-valid
  conditional versions. WP2 is therefore framed as an anytime-valid, label-budgeted,
  actively-queried deployment benchmark with predictive-loss and economic-cost measurement.
  Application-level decision harm is not identified because causal utility is unavailable.
* **Three-null violation matrix.** For every method and stream, the run reports:
  * the V1 error estimate (promote and adv_H <= 0, H = 100/500);
  * the V2 error (promote on a marginal null);
  * the registered first-promotion EI proxy (historically labelled the V3 error).

  Each method is labelled with the null it claims, from `bench2.NULL_TESTED`.
* **Marginal-null baseline.** `DM_HAC_monitor` (fam_f.DMHACMonitor) adapts the sequential
  Diebold-Mariano / Chu-Stinchcombe-White monitoring idea to the label budget. It uses:
  * paced disagreement queries;
  * a Newey-West-studentised CUSUM;
  * a linear Brownian boundary with exp(-2a^2) = alpha.

  Its ablation `DM_HAC_monitor-iid` uses lag 0. Both are marked as adaptations, with asymptotic,
  mixing-based size only. Both are added to panels P and R and are scored as V2 methods.
* **Lower bounds.** Any lower-bound statement is framed as an instance of known non-existence results
  (Bahadur-Savage 1956; Sethi et al., arXiv:2602.17587). WP2 proves no new theorem.

## Quantities (per run = one policy on one episode with one policy seed)

Let d_t = l0_t - l1_t, the paired challenger advantage at event t (incumbent loss minus challenger loss),
T the episode length, c_s = 5 and c_q = .05.

* **Marginal advantage.** This is E[d_t] over the construction's randomisation. It is 0 by construction
  on twin nulls (the split coin and role coin) and on every `*_null`/`*_twin` synthetic regime (the role
  coin U). It is not estimated per run. Check K0 reports the across-split mean as a sanity check.
* **Conditional advantage at a promotion** at event tau. It is estimated from the realised post-promotion
  paired losses adv_H(tau) = mean(d_t, t in [tau, tau+H)) for H in {100, 500, rest}, where rest = T - tau.
  It is computed for every promotion (every 0->1 transition); the primary analyses use the first one.
* **Economically inappropriate (EI) promotion proxy.** This was fixed before running. A promotion at tau is EI
  iff sum_{t >= tau} d_t - c_s <= 0. That is, promoting at tau and holding the challenger to the end of
  the episode does not beat never switching after the switch cost. It is a hold-to-end counterfactual,
  so it does not depend on later rollbacks.
* **Deployment benefit.** DB = sum_t l0_t - realised loss - c_s * switches, i.e. the path-level loss and
  switch effect relative to never switching.
* **All-in excess economic cost.** `J(policy) - J(never-switch) = net - sum l0`. It decomposes into prediction-loss delta, label expenditure, and switching expenditure. This is not application-level decision harm; causal application utility is unavailable. The raw record's `harm` field is a legacy name for this total.
* **Harmful-promotion proxy.** HP = P(promote and EI). The path-level variant is P(promote and DB <= 0); both refer to predictive-loss/switch-cost accounting, not causal application utility.
* **V1 error label at horizon H.** This is promote and adv_H(tau) <= 0, an estimate of "promoted when the
  near-future conditional advantage was not positive".
* **V2 error label.** This is "any promotion on a marginal null".
* **Registered V3 error label.** This is the first-promotion EI proxy. It is a hold-to-end switch-cost counterfactual, not the full V3 economic objective: it excludes label expenditure and ignores the realized rollback path. All-in excess economic cost versus never-switch is separately summarized as a mean in the registered analysis; its positive-rate and component decomposition are in [`REALIZED_HARM.md`](REALIZED_HARM.md).

## Hypotheses and decision rules

| id | hypothesis | decision rule |
|---|---|---|
| H0 | reproduction | the frozen `twin_null.build` (redirected to scratch) and the WP2 split-parameterised copy reproduce `array_content_sha256` for 5/5 datasets |
| H1a | K1 replicates on new splits | on the v2 splits, >= 5 of the 9 powered V1 ports have promotion > .0936 with split-bootstrap lower bound > .05 on >= 1 dataset whose v2 median rho-hat >= .5 |
| H1b | K2 replicates on new splits | A5b's split-bootstrap upper bound is <= .0936 on every dataset |
| H2 | twin promotions are conditionally informed | pooled over V1-certified ports (11 published ports + QSG, D2 and the 4 RMM hosts), the mean adv_rest at first promotion on v2 twins has a stratified bootstrap lower bound > 0 |
| H3 | harmful-promotion proxies are rare on twins | descriptive: HP and mean all-in excess economic cost per policy and dataset; a policy meets this registered proxy criterion if its HP upper bound is <= .05. This does not establish application-level decision safety. |
| H4 (primary) | the marginal objective tracks EI under mean-reverting persistence, but not under episode-level (fixed-effect) persistence | pi_EI = P(EI given a first promotion), pooled over the V1-certified policies. H4 holds iff pi_EI's lower bound is >= .7 on the **mean-reverting class** (F5_dep_null_r8, F5_dep_null_r95, O_null_semimarkov, O_null_order2, WP2_o2_null, WP2_sm_null, WP2_hs_null), AND pi_EI's upper bound is <= .5 on the **fixed-effect class** (the five v2 real twins pooled, and separately WP2_iid_twin, WP2_m8_twin, WP2_o2_twin, WP2_sm_twin, WP2_hs_twin pooled) |
| H5 | cost of dependence robustness | descriptive, with the comparators fixed now: paired A5b - QSG (same host and acquisition, different evidence) and D5 - D2 (same CAMS host and gate, different certificate). It is reported in J, detection delay (first promotion, never = T), labels and promotion rate, on (i) fresh real episodes with realised adv > 0 and (ii) the synthetic dependent alternatives F0_better, F5_dep_better_r8, S_dep_better_r95, WP2_o2_better, WP2_sm_better, WP2_hs_better |
| H6 | horizon and delay | (a) the pooled V1 twin promotion rate is non-decreasing in T in {1000, 2000, 4000} at each delay multiplier; (b) A5b's upper bound is <= .0936 in every (T, delay) cell. Otherwise descriptive. |

For H4, V1 precision and recall against EI at H = 100 and 500 are also reported. They answer whether a
short-horizon conditional-advantage criterion captures EI. These numbers are descriptive.

## Units and uncertainty

* **Real twins.** The cluster is the (dataset, split). For per-dataset quantities, splits are resampled
  (20 v2 splits). For pooled quantities, splits are resampled within each dataset (stratified). The
  bootstrap uses 2000 resamples and percentile 95% CIs. A run-level rate is first averaged within its
  cluster. For pi_EI, a ratio estimator (sum EI / sum promotions) is resampled at cluster level.
* **Synthetic.** The cluster is the seed (one episode each). The bootstrap is over seeds, stratified by
  regime when classes are pooled.
* **Fresh real.** The cluster is the (dataset, episode). Policy seeds measure run-to-run variability
  only.
* **No mixing of rates.** A conditional (V1) error rate is never compared with a marginal (V2) rate as
  if it were the same hypothesis. Each column is labelled with the null it scores.

## Runs (all seed base 2026110701 = sprint-2 development; WP2 runner `scripts/sota_sprint/wp2_run.py`, which reproduces screen.py pairing exactly)

* **Panel P (25).** The 11 certified ports (gated_deployment, gated_adaptive_range,
  gated_adaptive_range+front, discern_style, discern_design_floor, SMCS+retain-incumbent,
  xu_acquisition_only, choe_ramdas_eb, choe_ramdas_eb+front, gated_deployment+QCE,
  gated_deployment+QCE+front), A5b, QSG, D2, D5, the 4 RMM hosts, cams_adapter,
  model_picker_adapter, economic_replacement, CONTROL_never_switch, DM_HAC_monitor and
  DM_HAC_monitor-iid.
* **Panel R (12)**, used for the variants: A5b, QSG, D2, rmm:discern_style+RMM, gated_deployment+QCE,
  choe_ramdas_eb, discern_design_floor, xu_acquisition_only, SMCS+retain-incumbent,
  model_picker_adapter, CONTROL_never_switch and DM_HAC_monitor.
* **Run 1, v2 twins.** Five datasets x 20 new splits (s = 20..39) x all episodes, 1 policy seed,
  panel P.
* **Run 2, variants.** All 20 v2 splits. T in {1000, 2000, 4000} are re-windowings of the same
  evaluation events within a split: T=1000 halves each 2000-event window, and T=4000 joins consecutive
  window pairs. Delay multipliers are {.5, 1, 2} of the registered delay. This gives 8 cells on panel R;
  the T=2000 x1 cell is Run 1 restricted to panel R. The hard budget stays B=200 at every T. The
  T=2000 cells reuse Run 1's seed names, so they are paired with Run 1.
* **Run 3, synthetic.** The 11 WP2_* regimes (fam_f.py) plus F0_null, F5_dep_null_r8, F5_dep_null_r95,
  O_null_semimarkov, O_null_order2, F0_better, F5_dep_better_r8 and S_dep_better_r95, with 50 seeds on
  panel P.
* **Run 4, fresh real.** metro, beijing_pm25, bike_hour, appliances and household_power with 3 policy
  seeds on panel P.
* **Re-analysis.** The sprint-1 twin records (outputs/sota_sprint/twin_null, registered splits 0..19,
  seed base 2026110620) get first-promotion EI computed from `first_deploy` and the registered losses.
  This is descriptive, and those streams are development-exposed.

Family P's misspecification generators (fam_p.py) did not exist when this protocol was registered. If
they appear later, they are reported as a separate, post-registration descriptive addition.

## Status of the evidence

* The v2 splits are new model fits on development-exposed evaluation events. They are therefore
  independent replications of the split randomisation, not unseen data.
* All synthetic seeds are development seeds.
* Every result here is development evidence, not Round-5 validation. An empirical rate is never a
  guarantee.

## Post-run audit amendment (2026-11-04)

The original registration above listed `xu_acquisition_only` among published V1 certificate ports.
That classification is incorrect for the implementation evaluated here: it uses Xu et al.'s
acquisition component with ShiftLab's paired-loss certificate, rather than Xu et al.'s published
certificate. Keep the original registration and its numeric results as historical evidence, but
do not interpret the Xu row or any registered pool containing it as evidence for Xu's published
certificate. The original registered tables retain their historical short label “acquisition adapter (no Xu certificate)”. The amended tables now label it “V1 composite (ShiftLab certificate; Xu acquisition adapter)”. The historical H1a, H2, H4, rank, and H6 V1 pools still contain this adapter; an amended sensitivity analysis excluding it from published-certificate rankings is required before any published-certified pooled claim. The audit note
`DECISION_FLAG_AUDIT.md` records the affected outputs and implementation checks.

**A7 (2026-11-04, post hoc comparator-class audit):** the historical “11 published ports” label is
too broad. Those 11 comprise the six ports in `bench.CERTIFIED_PUBLISHED` plus Xu acquisition and
ShiftLab's Choe–Ramdas and QCE adapters. The historical analyses are retained as mixed adapter-panel
results. `wp2_analyze.py --strict-published-dir` provides a separate sensitivity using only the six
shared-pool ports for the pooled V1/powered estimands, retaining other methods as descriptive rows.
Under that sensitivity H1a remains false (4/6 vs the threshold of 5), H2 passes, H4 fails, H6a is
monotone, and H6b fails. The analysis is post-development, reuses the same exposed data and does not
adjust same-sample pooling/selection; details are in `COMPARATOR_CLASS_AUDIT.md`.
