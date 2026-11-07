# Check: Regol et al., "When to retrain a machine learning model" (spec: specs/regol_when_to_retrain.md)

Independent check, 2026-11-06. Re-read PMLR PDF (36 pp, SHA-256 a4eaccfa...c138) and arXiv v1 (36 pp, SHA-256 b2144679...350d),
downloaded fresh to my own scratchpad; both hashes equal the spec's. Page numbers are PMLR pages (main text pp.1-9).
Marks: CONFIRMED / CORRECTED / UNVERIFIABLE. Spec claims not listed below were not re-examined.

## Code search (independent)
- PMLR landing page (fetched): only links are PDF and OpenReview (X7X4YLMneu); no code, no supplementary. CONFIRMED.
- Web search for title + "github"/UPF: only paper, Cash App blog, mirrors; no repository. OpenReview not opened (bot challenge, not bypassed).
- Verdict: no official code found (UNVERIFIABLE that none exists; OpenReview supplementary unchecked). T1 not achievable; spec's tier call stands.

## Claim-by-claim
| Claim | Mark | Evidence |
|---|---|---|
| Eq. 1-3 objective, alpha=c/(eN), C=eN(alpha*\|\|theta\|\|_1 + sum pe_{r(t),t}) | CONFIRMED | Sec.3 p.3. |
| I_<t = offline data + D_1..D_{t-1} + only models actually trained; Eq.4-5 | CONFIRMED | Sec.3.1 p.4. |
| UPF features r=[i,j,j-i,z_shift], Beta via Gaussian approx, constant sigma, MLE for mu = least squares | CONFIRMED | Sec.4.1 p.4-5, Eq.10-14. |
| Beta params Eq.51-52, z_shift=\|\|xbar_t - xbar_{t-1}\|\|_1 (Eq.53), "clipping if needed" | CONFIRMED | A.7 p.20. |
| Keep/retrain recursion Eq.17-20, rule Eq.16/21-22 strict "<", delta quantile, MC "bootstrapping" Eq.23 | CONFIRMED | Sec.4.2 p.5-6. |
| delta=0.95 default; delta=0.5 = median/PF | CONFIRMED | p.7 ("standard value ... confidence intervals"); A.1 p.13 PF = UPF-50%. |
| ElasticNetCV, other sklearn parameters default | CONFIRMED | p.7. |
| w=7, T=8, \|M_<0\|=21, alpha_max/\|D\| by dataset | CONFIRMED (and the "inferred column alignment" caveat is RESOLVED) | Table 4 p.19, checked on the rendered page image: Gauss .5/5000, circles .25/5000, electricity 1/2000, yelpCHI .1/4000, epicgames .1/1000, airplanes .7/3000, iWild 1/40,605. |
| Which pair convention gives \|M_<0\|=21 | UNVERIFIABLE | 21 = C(7,2) (strict i<j over 7 datasets) fits; 28 (i<=j, 7 periods) or 36 (8 datasets) do not. Paper silent. |
| sigma_phi estimator, clipping rule, MC draw count, draw sharing, quantile estimator | UNVERIFIABLE (not in paper) | Only "constant sigma_phi" (p.5); Gaussian MLE of sigma^2 would be the in-sample MSE, so the repo's choice is the natural MLE reading, but the paper does not say it, and ElasticNetCV is a penalised fit, not the MLE. Spec's "optimistic" critique is fair but it is a choice, not a deviation. |
| Log-Normal replacement for unbounded losses (Eq.54-56) | CORRECTED (detail) | Printed Eq.55 reads v=sqrt(ln(1+mu/sigma^2)) and Eq.56 m=ln(v)-v^2/2 (rendered p.23). Dimensionally these should be sigma^2/mu^2 and ln(mu); the paper's formulas look mistyped. Not used by repo. |
| Table 1 numbers (UPF row, oracle row) | CONFIRMED | p.8. NOTE: on airplanes UPF 2.2865 is NOT best; CARA 2.2753* is. The "best across all baselines and datasets" is the paper's wording for overall; do not read it per-dataset. |
| Table 2 numbers and identity C_hat=alpha*#retrain+8*(1-acc) | CONFIRMED within rounding | alpha=0.9 UPF: 0.09+8*0.32=2.65 vs 2.69 printed; oracle 0+8*0.34=2.72 vs 2.68; alpha=0.1 UPF 0.25+2.00=2.25 vs 2.24; oracle 0.56+1.36=1.92 vs 1.93. Gap up to 0.04 is rounding of accuracy (x8); use tolerance 0.05, not exact identity. |
| Table 3 (PF vs UPF) values; "significant on all but electricity" | CORRECTED | Values confirmed (airplanes 2.3688 vs 2.2688; circles .0697 vs .0670). But on electricity PF (2.5884*) is the starred, better row, so it is significant in PF's favour, not "no difference". Also Table 3 UPF values differ from Table 1 UPF values (electricity 2.6056 vs 2.5782; Gauss .3643 vs .3829; airplanes 2.2688 vs 2.2865; yelp .1175 vs .1293, below Table 1 oracle .1275). Different trials; Table 3 cannot be a reproduction target against Table 1. |
| No guarantee for decision rule; conclusion "primarily suited to gradual changes" | CONFIRMED (guarantee); gradual-change quote not re-searched | no theorem on UPF. |
| Prop. 3.1 printed as r* <= T - sqrt(alpha/L) (Eq.7/25/46) | CONFIRMED as printed; the printed bound is FALSE | see below. |
| arXiv vs PMLR | CONFIRMED (no substantive difference) | same pages and hashes as spec; unique-token diff shows only plot tick labels and equation-number tokens (101-104) that the PMLR extraction drops; Prop 3.1, 0.96, delta, ElasticNetCV text identical. Appendix tables not diffed line by line. |

## Proposition 3.1: own re-derivation
Proof structure (A.4, pp.15-17): M_r = cost excluding alpha*r with exactly r retrains (Eq.33-35); Lemma A.1 (Eq.39): M*_r - M*_{r+1} <= L(T-r)^2
(chain Eq.41-45); then Eq.40: "L(T-r*)^2 < alpha  =>  r* < T - sqrt(alpha/L)".
1. Lemma A.1 is fine (loose): M*_r <= M_r(first r times) = M*_{r+1} + sum_{s after t_{r+1}} (pe(t_r,s)-pe(t_{r+1},s)); each term <= L(t_{r+1}-t_r) by telescoping adjacent indices; a*b <= (a+b)^2/4 <= (T-r)^2. (Eq.44-45: step holds with room to spare; "r in {1,T-1}" in the lemma statement is a typo for the range.) Note the proof's M counts model t_i from s>t_i, whereas Eq.26 uses the model trained at t at time t itself; that shifts a+b by 1 but (T-r+1)^2/4 <= (T-r)^2 for r<T, so the lemma survives.
2. Eq.40 is a logical error. L(T-r)^2 < alpha is a condition on r (the marginal gain of retrain r+1 is below its cost), so it implies r* <= r, i.e. any r with r > T - sqrt(alpha/L) is an upper bound. It does not make r* < T - sqrt(alpha/L); it gives the opposite direction.
3. Correct derivation: optimality gives C_{r*} <= C_{r*-1}, so alpha <= M*_{r*-1} - M*_{r*} <= L(T-r*+1)^2, hence r* <= T + 1 - sqrt(alpha/L). Integer form: **r* <= max(0, floor(T - sqrt(alpha/L)) + 1)**. The spec's corrected bound is RIGHT. The refined version r* <= T + 2 - 2 sqrt(alpha/L) also holds empirically (0 violations); the bound T+1-2sqrt(alpha/L) (proof's M convention applied to the true objective) is false (594 violations), which is the same off-by-one.
4. Counterexample to the printed text: T=1, pe=[[.],[.]] with pe(0,1)=1, pe(1,1)=0, L=1, alpha=0.25: optimum retrains (cost .25 < 1), r*=1 > 1-0.5=0.5. Reproduced (repo's counterexample is valid).

Brute force (script: /private/tmp/claude-501/-Users-nigelli-Desktop-ICML-Shift-lab--claude-worktrees-shiftlab-methods-strategy-dba13e/06bf436b-d27c-42d6-9116-89f769a07352/scratchpad/check_regol/prop31.py, not committed): objective of Eq.26 (model trained at t used at t), exhaustive over all theta in {0,1}^T for T=1..7; random triangular pe (uniform, binary, trending), L = true max adjacent gap, alpha random scaled to L(T+1)^2; both min-count and max-count optimizers checked (ties).
29,099 instances: printed bound violated 5,225 (18%) times; corrected floor+1 bound violated 0 times; the floor+1 bound is met with equality in 1,323 instances (so it cannot be tightened to the printed form); refined T+2-2sqrt bound 0 violations. Numerical sanity check plus the hand proof above, not a formal proof for general pe.
Verdict: printed Prop. 3.1 is wrong; spec's corrected bound is correct.

## Spec discrepancies vs repo (file:line verified)
1. upf_retraining.py:106 ElasticNetCV(cv=cv, random_state=seed, max_iter=50_000), cv=min(max_cv,n) (line 104): CONFIRMED non-default max_iter/random_state; low impact.
2. upf_retraining.py:108-109 in-sample residual variance; line 77 floors at epsilon^2: CONFIRMED. See sigma row: it is a defensible MLE reading, an unstated choice.
3. upf_retraining.py:73-81 clipping (mean clip epsilon, variance cap .99 mu(1-mu), alpha/beta floors): CONFIRMED, paper says only "appropriate clipping".
4. MC draws 20,000 (spec) vs MONTE_CARLO_DRAWS=10_000 (evaluate_upf_eia_frontier.py:36): CONFIRMED count not stated by paper; I did not re-verify the 20,000 default line.
5. Strict "<": upf_retraining.py:258 CONFIRMED.
6. Training set 28 vs paper 21: evaluate_upf_eia_frontier.py:292-293 `range(model_period, N_OFFLINE)` gives i<=j over 7 periods = 28: CONFIRMED; paper's 21 convention UNVERIFIABLE.
7. :288 z_shift per training pair set to shift at evaluation period: CONFIRMED (via _offline_observations: feature_shift_l1=shifts[evaluation_period]); paper silent.
8. N_PERIODS=15, N_OFFLINE=7 (evaluate_upf_eia_frontier.py:29-31) gives 8 online periods: CONFIRMED matches paper w=7,T=8.
9. audit_upf_retrain_count_bound.py:40-61 tests printed bound (claimed_upper_bound = horizon - sqrt(cost/L)); its convention (retrained model used at the same step) matches Eq.26: CONFIRMED. It does not add the floor+1 corrected audit: CONFIRMED gap.
10. PRIOR_ART_AND_NOVELTY_MATRIX.md:362: "cost C = eN(1 + alpha * sum_t pe...)" CONFIRMED WRONG (Eq.3 is eN(alpha*\|\|theta\|\|_1 + sum pe)). Line 363 says "I re-read the statement... matches the repo's transcription": true for the printed statement, but the matrix does not say the printed statement is false. Line 919 "risk-averse quantile rule mentioned only in a vendor blog": CONFIRMED WRONG, the rule is Eq.16, 21-22 in the paper (p.5). Suggest also correcting line 366 "Verification: FULL" (superseded).

## T3 "cost-aware switch timing" adaptation: fairness judgement
Fair and honest if labelled as spec says (T3, not "UPF"). Concerns to add: (a) in the paper pe cells are free full-label means and the Beta spread models forecast error from only ~21 cells; with m-round periods and IPW cells under B=200 the sampling noise is of a different kind and sigma from in-sample residual will understate it, so the delta=0.95 quantile loses its meaning; fix by using IPW variance explicitly as an extra, declared deviation. (b) Frozen models make i and j-i uninformative; the forecaster is then a time-trend regressor with a shift feature, which is much weaker than UPF; say so. (c) Reversible switching changes the DP (no model-age); the recursion Eq.17-20 maps cleanly, but the "retrain" branch must include A_{other,t} rather than A_{t,t}. (d) Labelling must be fixed and shared, as spec says, else the comparison confounds UPF with label allocation. (e) Eq.16's nested quantiles are not a coherent risk measure (spec's note) and it has no type-I control, so it belongs in the uncertified class. With these caveats the mapping is an honest T3; the strong claim "UPF baseline" must not appear in result tables.

## Other spec statements flagged
- Spec says Table 4 alignment UNVERIFIED: now resolved (page image).
- Spec's "Wilcoxon significant differences on all but electricity" (Table 3): corrected above.
- Lemma A.1 "{1, T-1}" typo reading: agreed.
- Offline RL baseline (A.11.1), Appendix A.10 per-dataset tables, A.12 CARA relation: not re-read by me (UNVERIFIABLE here).

## Verdict
ACCEPT WITH CORRECTIONS. Corrections: Table 3 significance direction and Table 1 vs Table 3 inconsistency; Log-Normal Eq.55-56 printed formulas dubious; airplanes UPF is not best; Table 4 alignment now confirmed; |M<0|=21 convention still open. Spec's Prop. 3.1 correction and tier call (T1 impossible, T2 for native, T3 for ShiftLab) are correct.
