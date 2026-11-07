# GAVE-R WP5: integration (Gap-Mix x delay-gated PAVE) — results

Branch `research/gave-r-2026-11-06`. Development/screening only; no confirmation seeds.

## 0. Pre-declaration (written and committed BEFORE any WP5 run)

**Post-switch factor dropped.** The WP3 rerun (docs/gaver/30_FRESHCHECK_RESULTS.md) found FreshCheck
fails on value (equal-weight mean J/T: CUSUM .488, E_rb .489, FreshCheck .496). WP5 is therefore a
2x2 with the existing default rollback controller (Page-CUSUM, kappa=2, alpha spending
`alpha*2^-(j+1)`) in every arm. `GaverMethod` keeps an unused `rollback_hook` for later work.

**Frozen choices (from WP1/WP2, not tuned here).**
- Evidence: Gap-Mix `exact0.8_s4` (declared rho_bar=0.8, 4-start restart mixture); ablation: envelope
  `env0.8_s4`. Baseline evidence: frozen DSS spec `5b5c77b635e5` started-mixture e-process.
  Restart starts in episode j: `ep_start + f(T-ep_start)`, f in {0,.25,.5,.75}.
- Acquisition: frozen DSS acquisition (with its delay switch); or delay-gated PAVE = WP2 governor,
  reserve OFF, kappa=0.1, q=0.03, active only when `d >= 2T/(B+2)` (exactly where DSS falls back to
  uniform), DSS straddle rule otherwise. `uniform` is a reference arm.
- Everything else is the unchanged DSS shell (promotion, econ check, rollback, hard budget clamp).
  Gap-Mix therefore runs inside the DSS shell with alpha_0 = alpha/2 = 0.05 (not WP1's full alpha).

**Arms.** evidence {dss, gapmix, env} x acquisition {dss, pave} = `gaver:<ev>:<acq>`; plus
`uniform` (alt cells). 2x2 primary = {dss,gapmix} x {dss,pave}; envelope arms are the ablation.
By construction delay-gated PAVE == DSS wherever the gate is off (all d in {1,10} with B/T<=0.1);
the acquisition factor is therefore identifiable only in gate-on cells (d=50, and d=10 with B=250),
and the interaction contrast is identically 0 elsewhere. Null cells with the gate off run only the
`:dss` arms (equality is asserted in tests/test_gaver_integrated.py).

**Alternative cells (60 paired seeds each, seeds 101190000+100*i).** The WP2 31-cell set: the 16
cycle-7 primary cells (5 family-1, 11 family-3) plus `fa.neighbours` of the two regression cells
(`on0.6_L1_strong_harmful_d50_b0.05_s0.1`, `f3_rho0_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1`),
de-duplicated. All have rho <= 0.8 (family-3 alternatives never include rho=0.95).

**Null cells (500 streams each, seeds 101170000+500*i), 29 cells.** Atlas dependence-null twins
(boundary null, favourable prob .55, autocorrelation rho): rho in {0,.5,.8,.95} x
{d in {1,10}, B/T in {.05,.1}} (16, gate off), {d=50, B/T in {.05,.1}} (8, gate on),
{d=10, B/T=.25} (4, gate on), plus the family-1 null twin of the d50/b.05 regression cell (iid).
rho=0.95 is out-of-class stress (Gap-Mix declared 0.8) and reported separately.

**Step 0 (PAVE null completion).** Raw ungated PAVE (reserve off, kappa .1, q .03) and DSS on the 16
dependence-null cells with B/T<=0.1, d in {1,10}: 500 fresh streams per cell, seeds
101160000+500*i (WP5 range; WP2's earlier 120-140 streams/cell used WP2 seeds and are not pooled).

**Metrics.** J/T = (loss + c N_q + s N_s)/T and its three components; null false-promotion (any
promotion with regime mean < -h... i.e. the Atlas `fp_regime`), reported with Clopper-Pearson 95%
one-sided upper bound (UCB); detection = promotion while the on-regime is active, and delay from
onset; labels used (queries). Paired bootstrap 95% CIs (4000 resamples over seeds within cell;
pooled contrasts = equal-weight mean over cells, seeds resampled independently per cell).
Relative gain = reduction of mean J/T relative to the reference mean. Grades: substantial >=10%,
meaningful 3-10% with CI excluding 0, small 1-3%, negligible <1%.

**Interaction contrast.** With J_ea = mean J/T of arm (evidence e, acquisition a), gain of evidence
= J_dd - J_gd, gain of acquisition = J_dd - J_dp, joint gain = J_dd - J_gp; interaction = joint -
(evidence gain + acquisition gain) = J_gd + J_dp - J_dd - J_gp (positive = synergy), per seed,
bootstrap CI, reported on gate-on cells and on all cells.

**Screening bar (00_PLAN).** Null UCB <= 0.1 at rho <= 0.8; at least a small paired gain over the
strongest in-repo comparator in target cells; not materially worse in neighbours; rho=.95 reported.

**Compute.** <= 8 workers, resumable partial CSVs in `outputs/gaver/wp5/{pavenull,null,alt}/rows.csv`.

**Amendment A1 (POST-HOC, added after the alt results were seen, before the null stage ran).**
On the planner's request a *valid* evidence reference is added: the existing Atlas Markov-LR
e-process (`atlas_dependence_baselines.MarkovLREProcess`, the evidence of `markov_lr_gate`) inside
the same DSS shell, arms `gaver:mlr:dss` and `gaver:mlr:pave`, on the same alt seeds and null
streams. Reason: DSS evidence is not valid under dependence (WP2: null UCB 0.269 at rho=.8), so
Gap-Mix's cost against it must also be read against a valid comparator. `episode_front` was also
added to the alt references (it was listed in the runner's references after the first alt pass).
These contrasts are labelled post-hoc in every table. Nothing else in Section 0 changed.
