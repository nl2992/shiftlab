# 02 Dependence null definition and failure audit (GATE A)
Code commit at start: `8552911` (branch `research/shiftlab-mandate-gap-closure-2026-10-30`); sprint branch `research/shiftlab-dependence-gates-2026-10-31`. Inputs: stress matrix (`e6_stress_main`), `scripts/dep_sprint/gate_ab.py` → `outputs/dep_sprint/gate_ab.json`. Theorem status: classification only (no new theorem). Seeds: 2000 paths per cell, T=2000, r0=0.3.

## Three nulls
* **H0-cond:** E[L_t - r0 | F_{t-1}] <= 0 for all t (F = everything the monitor may use: past covariates, resolved labels, query history). The e-process supermartingale argument needs exactly this (bets predictable).
* **H0-marg:** E[L_t] <= r0 under a stationary (or declared dependent) process law. Only a statement about the stationary mean.
* **H0-eps:** the same with r0+eps. (Both versions exist for conditional and marginal readings.)
H0-cond ⊂ H0-marg; strictly: a persistent hidden regime with stationary mean r0 satisfies H0-marg and violates H0-cond during every high-loss stretch.

## Audit
| process | H0-cond | H0-marg | monitor false-alarm rate (upper 95% Clopper-Pearson) |
|---|---|---|---|
| iid Bernoulli(0.3) | true | true | pprm 0.037, pprm@20% 0.021, HG@20% 0.044 |
| **dependent** ARCH-like, bounded, conditional mean exactly r0 (variance depends on the past) | **true** | true | 0.036 / 0.027 / 0.041 |
| lazy-resample chain, stationary mean r0 = 0.3, switch rate delta = 0.5 | false | true | pprm@100% labels 0.35; HG@20% 0.14 |
| same, delta = 0.05 / 0.01 / 0.003 / 0.001 | false | true | up to 0.96 (HG@20%, delta=.01); 0.47-0.58 at delta=.001 |
The conditional excess is visible directly: the regression slope of L_t on the previous 50-step mean is 0.34 at delta=.5 and 0.92-0.99 for delta <= .01 (it is ~0 for iid).

## Branch of the decision procedure taken
* The false alarms occur because the process **violates the monitor's stated conditional null** (rows 3-4), while **dependent processes that satisfy it do not inflate** (row 2) and no process satisfying every theorem assumption exceeded alpha. → **null-class mismatch**. The existing theorem is **not** claimed invalid. (The only genuine counterexample found anywhere in the programme remains the earlier covariate-dependent *cap* defect, already repaired.)
* Economic estimand: a deployment decision acts on the *future*; the actionable harm is conditional forward excess risk, which is H0-cond. A retrospective stationary-average is what H0-marg measures. Which one a risk manager needs is decision-dependent; this is carried as an obligation to the switching study, not resolved here.
* Is the weaker (marginal) null testable with useful power? → Gate B.

**GATE A: PASS** (classification: null-class mismatch; conditional-null monitor retained as the validated baseline). Unresolved sub-item: the economic estimand (conditional vs marginal) — see 11.

## Update: economic estimand (resolved for the stylised case; see 11)
`estimand_switching.json`: whether a conditional-null alarm is a "false alarm" or a correct detection depends on whether an action with **regime-local benefit** exists. If so (variant A) conditional-null alarms are net-beneficial (net cost 298-552 vs 595-601 incumbent-only) while the marginal-null monitor never fires; if not (variant B) they lose and the marginal monitor is safest. Gate A stays PASS; the estimand question is reduced to a property of the action set, not of the monitor.
