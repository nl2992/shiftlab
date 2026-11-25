# Paper 1: contributions (working draft, 2026-11-23)

**Working title:** When does paired disagreement gating pay? A pre-registered growth-rate analysis of
selective-label harm monitoring. Target: TMLR.

## Contributions

1. **Disagreement gating multiplies evidence growth at matched label spend.** On the registered
   block (100 streams per cell), the paced gated monitor grows evidence 7.20x faster than a
   correctly bounded uniform monitor at r = 0.20 (95% interval 6.88-7.55), and wins 100 to 0
   in discordant detection comparisons at r = 0.05 (McNemar p = 7.9e-31). Null calibration passed on
   2,000 streams per cell.
2. **The gain has a closed form that predicts it.** Per-event log-growth of an IPW betting
   e-process, with each arm's own support bound (5/q + eps for gated HT, 5.1(2/r - 1) for uniform)
   and the registered stake grid, gives gated/uniform growth ratios of 20.0 / 19.7 / 15.5 / 7.6 on
   the real paths at r = 0.02 / 0.05 / 0.10 / 0.20. The registered prediction was 18 / 18 / 15 / 7.5
   and the measured ratios 17.5 / 20.6 / 14.7 / 7.2. The same range penalty (bound growing as 1/q)
   explains both the gating gain and the pacing result below.
3. **Pacing converts label budget into reserve horizon, not detection.** Across 5 intervention
   strengths x 4 budgets x 100 seeds, fixed and past-paced gating detect equally often (pooled
   difference +0.005, CI -0.006 to +0.016; Timans GRAPA -0.006, CI -0.018 to +0.006). Pacing keeps
   the monitor running 1.9x longer (2,111 vs 1,136 events at r = 0.05, full strength) at identical
   label counts, and lengthens censored delay 1.4-2x (1,166 vs 598 at r = 0.10; 637 vs 401 at
   r = 0.20). Fixed gating is the faster detector whenever the budget covers the disagreements.
4. **A detectability map over budget and intervention strength.** Gated monitors reach 0.95-0.99
   detection at r = 0.20 for strengths >= 0.50 (0.87-0.99 across fixed and paced) and 0.56-0.86 at r = 0.10 for strengths >= 0.75;
   at r <= 0.05 they reach at most 0.29 at every strength while uniform labelling detects 0.00.
   Disagreement rises from 8% to 41% under the full intervention, which sets where the label reserve
   runs out.
5. **A registered regime map with tested predictions.** Eight regimes, each with a registered
   prediction and falsification criterion, evaluated against a published/composed comparator panel
   (Timans GRAPA, Xu active betting, PPE, empirical-Bernstein engines, SR/CUSUM). Gated HT/PPI with
   adaptive engines are the strongest selective-label arms; the PPI proxy adds nothing after gating.
6. **Real-data behaviour on EIA.** All 68 registered per-path null cells passed (0/1,000 alarms;
   largest exact upper bound 0.30%). Under injected under-procurement, fixed disagreement gating
   matched the full-feedback median delay in all 10 harm cells from a 5% budget upward using 338-701
   labels; uniform HT was slower or missed.

## Related-work framing (by what this paper adds)

- DISCERN: label-complexity theory for paired audits; this paper adds growth-rate and detection-delay
  behaviour at matched spend, and behaviour under policy adaptation.
- Xu et al. (active anytime-valid RCPS): IPW e-processes and optimal labelling; this paper adds the
  paired zero-cost-on-agreement setting and the pacing analysis.
- Zrnic & Candes; Sfyraki & Wang: active inference for estimation with fixed distributions; this paper
  treats sequential testing under a distribution shift caused by the policy itself.
- Choe & Ramdas; Timans et al.: anytime-valid paired comparison and risk monitoring; this paper adds
  selective labels.

## Sections

1 Intro (contributions 1-4). 2 Setup and related work. 3 Growth-rate prediction (contribution 2).
4 Registered protocol and calibration. 5 Gating results (1, 5). 6 Pacing and the label reserve
(3, 4). 7 EIA (6). 8 Limitations (one paragraph).

## Evidence locations

docs/gated_monitor_comparison_results.md; docs/r7_adaptation_strength_sweep_results.md;
scripts/g1_kelly_check.py; docs/eia_real_data_validity_results.md; docs/stratified_monitor_regime_map.md.
