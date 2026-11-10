# A results: joint action-conditioned VOI (dev only; no confirmation/model-selection seeds opened)

Protocol: `03A_JOINT_VOI_DESIGN.md`. Raw: `outputs/paper3/joint/` (tuning/, dev_eval/, dev_ablate/,
dev_matched_*, tiny_exact.json, dev_summary.json, a4/q_net.npz). Ledger: `ledger/joint.jsonl`.
Reproduce: `scripts/paper3/joint/{tune,dev_eval,analyze,tiny_exact,train_a4}.py`, PYTHONPATH=src.
Dev-eval = 30 seeds (dev offset 100) x 24 regimes, T=300. Delta J = method - baseline (negative good).

## 1. Tiny exact check (TRUE model given to every planner; 4000 HMM tapes, paired to exact DP policy)
Gap to exact optimum (% of optimum), 95% half-width about 0.3-1.1%:
| instance (T,B,d,k) | never | wald_default | A0 | A1 | A1 no-batch | A2 (gated) | A3 | A5 |
|---|---|---|---|---|---|---|---|---|
| 8,2,1,.6 | 14.6 | 14.3 | 0.4 | 0.9 | 0.9 | 16.3 | 0.9 | 0.0 |
| 10,3,1,1.0 | 7.7 | 9.1 | 0.4 | 1.1 | 0.8 | 9.2 | 1.9 | 1.1 |
| 12,3,2,1.0 | 10.1 | 8.5 | 1.1 | 1.1 | 1.1 | 11.8 | 1.6 | 1.1 |
| 12,3,3,1.5 | 3.4 | 5.0 | 2.0 | 2.2 | 2.2 | 4.5 | 2.3 | 2.7 |
With the true model all planners are within about 0-2.7% of the exact optimum, i.e. planning error is
small and the KG* batch lookahead is not needed there. The core default HMM was not used because its
exact optimum is "always challenger" (information worthless); instances use harmful/beneficial regimes.
Gated A2 loses ~4-16%: the e-process needs several positive labels and B is 2-3.

## 2. Dev: tuned methods vs strongest tuned deployable baseline (wald_cut, chosen by tuning score)
Pooled equal-weight J (never = 75.24): wald_cut 68.72. Delta J vs wald_cut, seed-cluster 95% CI:
A0 +0.82 [+0.21,+1.46] (+1.2%, worse); A1 +4.84 (+7.0%); A2 +7.01 (+10.2%); A3 +4.34 (+6.3%);
A4 +8.45 (+12.3%); A4+gate +6.49 (+9.4%); A5 +3.79 (+5.5%). Baselines vs wald_cut: wald_paced +1.0%,
wald_any +0.1% (CI spans 0), cusum +1.9%, page_hinkley +4.7%, gate_wald +7.6%. NO method beats the
tuned Wald family pooled. Best A (A0, 22.8 labels vs 37.7) wins significantly in stationary_worse
-8%, delayed_onset -7%, expensive_switch -3% and loses in long_persistent +12%, random_delay +11%,
informative_delay +9%, gradual_harmful +3%. Matched labels (Wald re-run with B = A0 mean queries per
regime): A0 - Wald = +0.37 [-0.38,+1.04] (+0.5%), a tie; A3 matched: +4.43 (+6.5%, worse).
Tuning: 32 configs each (default + 31 random), 6 seeds x 24 regimes; for A0/A1/A3/A5 the default
config remained best (random draws all worse); A2/A4/A4_gate/baselines improved over default.
Wall/CPU seconds: A0 601/7025, A1 275/3212, A2 201/2339, A3 71/804, A5 109/1239, A4 16/156,
wald_* 8-12/50-90, cusum 7/30, PH 7/29, gate_wald 11/81 (14 or 12 workers).

## 3. Secondary (dev-eval means)
Mean labels/switches: wald_cut 37.7/0.99, A0 22.8/0.68, A1 12.6/0.33, A3 39.7/0.50, A5 27.4/0.49.
Global-null false promotion (mean of stationary_null and dep_null_rho_0.95): wald_cut 0.72, A0 0.65,
A1 0.27, A3 0.45, gate_wald 0.37, A2 0.23, A4_gate 0.27. On independent stationary_null: wald_cut 0.60,
A2 0.00, gate_wald 0.17, A0 0.57. On dep_null_rho_0.95 gated methods exceed alpha (0.47-0.57):
the e-process null needs conditional-mean<=0, which the AR(1) copula violates in finite runs,
so no gate guarantee applies there (contract section 5). Hindsight regret (UNATTAINABLE): wald_cut
13.9, A0 14.7, A1 18.8, A3 18.3.

## 4. Ablations (parent tuned A1; Delta = ablated - parent)
no delay queue -0.56 [-1.05,-0.04] (ablation slightly better; no attribution to the queue);
no continuation +1.67 [+0.96,+2.40] and no switch penalty +1.75 [+1.05,+2.44] (these keep A1 from
degenerating to never/under-querying: labels 0 and 3.6 vs 12.6); no KG* batch +0.27 [-0.30,+0.80];
Wald-style paced acquisition in place of VOI acquisition -0.21 [-0.75,+0.37] (labels 53.6 vs 12.6,
no loss of value: VOI acquisition adds nothing). A3: the tuned config has eta=0 and lam_sw=0, so the
"static duals" and "no switch price" ablations are identical to the parent (dynamic duals and the
switch price were not selected). A0 vs A1 (same belief model): A0 better by 4.0 J (planner choice
matters more than VOI decomposition).

## 5. Verdict
No attributable gain. Tractable controllers are near the exact optimum when the model is known
(<=2.7%) but under learned misspecified models none beats the equally tuned Wald+cutoff baseline
(best A0 +1.2% worse, tie at matched labels). Grade: negligible/negative; label savings (A0 uses ~40%
fewer labels at equal J) are the only positive signal and are removed by label matching. Consistent
with memo A (ALREADY_COVERED) and the settled finding that joint planners give no headroom.
Recommendation: stop A as a standalone method; keep A0 as the control-theoretic baseline.

## 6. Caveats, limits, bugs
- Two-stage history: a first tuning round without the hazard-persistence/pi0 prior (A3 0.948, A5 0.940
  vs Wald 0.874) was discarded and re-run with persist/pi0 added to the A search spaces
  (`outputs/paper3/joint/tuning_v1_noprior/`); the final A tuning is the second round.
- A4 TRAIN data use realised simulator outcomes as regression targets (training only; inference is
  causal). A4 default is poor (1.355), tuned 1.001 (never-like); A4 behaves badly in expensive_switch.
- Belief grid is a coarse misspecified 2-regime model (4 p-levels x 3 hazards for table policies);
  a finer grid or learned prior may help but was not tried (no post-hoc dev tuning beyond protocol).
- Tuning objective (relative J) and the hypothesis prior knobs favour no method by construction, but
  A has more tuned dimensions than the baselines.
- Core issues observed (not edited): `Gate` only blocks the first 0->1 promotion (documented); core
  `SimulationEvaluator.global_null_false_promotion` counts only regimes with mu<=0 throughout, so
  dep_null_rho_0.95 is a "null" in mean but the e-process validity does not hold there. No bugs found.
- Learned-model gap to the exact optimum was not measured in the tiny instances (T<=12 gives no
  learning room); it appears only in the dev comparison.
