# 07 Adversarial review of the monitoring-to-decision-value programme

**Reviewer:** Agent G, same-model (Claude) subagent. **This is self-review (same model), not independent review.**
Date 2026-10-30. Read: docs 00-06, 10, 11, ledger, `src/shiftlab/decision_value/*.py`, `tests/decision_value/test_engine.py`,
`scripts/decision_value/run_type2_tuning.py` (read only; another agent is extending it). No existing file was edited. Falsification
code is in the session scratchpad; outputs are in `outputs/decision_value/development/redteam/` (gitignored: `rt_a_th1_random_env.json`,
`rt_b_p5_proxy.json`, `rt_c_nonbern_gradual.json`, `rt_e_calibration_boundary.json`). All seeds < 7,000,000
(used: 1000, 2000, 5,000,000/1/2, 6,100,001, 800,000, 810,000). Registry max seed-like integer = 5,000,000 (calibration), so the
synthetic confirmation block (>= 7,000,000) is untouched by anything I can see. Development-only evidence; nothing here is confirmatory.

## 0. Bottom line

The programme has built a careful, honest, well-tested engine and an accounting framework, and it has already
downgraded most of its own headline claims. What survives is: (i) exact linear identities (known), (ii) a trivial
Markov-chain bound (known in spirit), (iii) a negative empirical result (monitor systems do not beat tuned simple
policies in 10 synthetic cells) whose "simple policies" are themselves fixed-sample monitors at effective alpha of
0.5-1.0, and (iv) descriptive real-data replay on one series per pair. I do not see a new generalizable insight a
critical ICML reviewer would credit. **Recommended Decision: D (workshop / preliminary), with a credible path to C
(benchmark / TMLR-style) and a narrow, unproven path to B.** A is not supported (there is no method).

## 1. Claim classification

| claim | class | one-line reason |
|---|---|---|
| C1a P1/P4 value is a linear functional of the alarm law | SUPPORTED_BUT_ESTABLISHED | linearity of expectation; doc 04 itself says Bayesian QCD risk is linear in the stopping-time law |
| C1b TH-1 crossing c_s* predicted from alarm CDFs (39/39) | SUPPORTED_ONLY_IN_NARROW_SETTING (near-tautological) | holds only because no controller depends on c_s and Delta is a fixed path; naive CDF-only prediction breaks under random tau (test A) |
| C1c P3/TH-2 incumbent-monitor value affine in fallback; ranking reversible | SUPPORTED_BUT_ESTABLISHED | value of a signal depends on the payoff structure (Blackwell); theorem is "an incumbent-only signal is blind to the fallback" |
| C1d P5/TH-3 precision-at-action-time sufficient; delay-persistence ceiling; r=0.9999, 0/360 violations | SUPPORTED_ONLY_IN_NARROW_SETTING | label-only monitors + fixed Hold(H) + Markov regimes; ceiling removed by any undelayed proxy (test B); r=0.9999 uses evaluator regime so it is an identity check, not a prediction |
| C2 under equal-budget tuning monitors do not beat simple policies (0/10, 3, 7) | SUPPORTED_ONLY_IN_NARROW_SETTING | one Bernoulli generator family, symmetric chain, oracle-tuned grid with optimum on the boundary, "simple" policies are monitors (test D); held in 2 non-Bernoulli cells (test C) but one cell had a monitor point-estimate win |
| C2' untuned reversals are controller-confounded | SUPPORTED_BUT_ESTABLISHED | folklore; and in tension with C1b/C1c, see Objection 3 |
| C3 real data: monitors convert ~0-5% of headroom; static dominates where challenger persistently better | INCONCLUSIVE | one series per pair, pairs/granularity chosen after dev headroom, imposed delays/costs, null violated by design; "5%" is one realisation |

## 2. The 18 questions

1. **Known decision theory?** Mostly yes. P0/P1/P4 are linearity of expectation over the stopping-time law. P2 is a
   rearrangement of a line in c_s. P3 is "a signal that does not depend on payoff-relevant state has decision value set by
   the payoffs" (Blackwell/value of information). P5's affine-in-theta gain is Bayesian QCD with a Markov-modulated state;
   the ceiling is the Markov property (data-processing across a delay). Doc 04's own novelty table says as much; I agree
   with it and would not upgrade any row.
2. **Just "switching costs exist"?** Largely, for C1b. The crossing exists because cost is linear in c_s along fixed alarm paths.
   Any controller that sees c_s (StaticThreshold already does; tuned alpha/H do) changes the alarm law and removes the
   crossing: Type II finds 0 protocol reversals once tuned. So "ranking by detection can be reversed by c_s" is a statement
   about c_s-blind monitor design, which the textbook Bayes-risk formulation does not make.
3. **Hand-picked fallback?** Yes in the sense that matters. The fallback has a fixed constant advantage/disadvantage
   (strong p0+0.05, weak, none, common-shock, reversing are five hand-built regimes). P3's reversal needs mu(1) to move
   while the incumbent alarm law stays fixed; the common_shock/reversing constructions (fallback degrades with the
   incumbent) are the cases that make reversals larger than MME (21/90). Fallback quality is a free parameter, so
   "reversal by fallback alone" is true by construction (doc 04 P3b proof is correct but trivial).
4. **Detector advantage comparable?** Not really. Matching is P(any alarm by T)=0.05 at one point of a composite null (test E):
   at the engine's alpha=0.05 threshold calibrated on the interior null (E[x]=-0.05), the boundary null (E[x]=0) false-alarm rates are
   CUSUM 0.389, SR betting 0.340, Kelly 0.224, batch 0.217, Page-Hinkley 0.037. So "matched" monitors differ by a factor
   of 10 in false alarms on the null the composite hypothesis actually contains. Power comparisons at this match are not
   like for like. The "power" axis also mixes late alarms (doc 06: power_T counts late alarms, tau 0.24, while delay gives 0.96).
5. **Unrecognized false-alarm guarantee difference?** Yes (test E above). Docs 05/06 acknowledge matched-on-one-generator
   vs nominal e-process, but not that the empirically calibrated detectors lose the guarantee as soon as the null moves to
   its boundary or acquires dependence, while SR/Kelly nominal thresholds retain it (Kelly threshold 0.921 on the log
   scale vs nominal log 20 = 3.0, a threshold ~3x lower, is exactly what costs validity at E[x]=0). Calibration is also done by
   simulating the true generator (true p0, delta, q, d, T), which a deployed monitor cannot do.
6. **Weak baselines?** Yes. CUSUM/PH/batch/SR are textbook with untuned defaults (k=0.02, delta=0.005, n_b=50);
   Kelly-H2c is the group's own method; no PPRM (even as FORMULA_ADAPTATION), no ADWIN/DDM, no Shiryaev posterior-threshold
   rule with decision costs (the obvious decision-theoretic anchor, listed as missing in doc 02 3c and still missing), no
   Cara/Regol-style cost-aware retraining. No row in doc 02 is VERIFIED_REPRODUCTION. Reviewers will say "you compared
   against strawmen of the 5% false-alarm paradigm and found it loses to cost-aware rules" which is Regol/Cara's thesis.
7. **Could a batch test match?** Already yes: doc 01 F3 says batch captures most of P3b; `batch|hold` is among the 5 monitors
   and, in TH-2, ph_d03/batch variants are the only monitor to ever beat the calendar rule. The deeper point is test D: the
   winning "simple" policies are batch tests.
8. **Simulator truth in deployment?** The operational code is clean: monitors/controllers/simulate import no truth (tested),
   r0 is estimated from the first 300 released labels. Residual leakage is design-level, not code-level: (a) thresholds are
   calibrated by simulating the exact generator, including p0, delta, q, d and T (an oracle null); (b) Type II tunes Hold H, alpha
   and horizon per cell with knowledge of L/rho, which doc 11 admits is an upper bound for monitors; (c) Setting A hands the monitor
   both losses of every queried event regardless of the deployed action (shadow deployment) at c_q=0, so information cost is never
   paid; (d) TH-3's "prediction" plugs in the evaluator regime Z_S (doc 06 section 4), so r=0.9999 verifies algebra, not a
   deployable forecast; (e) StaticThreshold uses horizon T and c_s (fine, declared). I found no code-level leak.
9. **Real counterfactual losses identifiable?** Yes in OPSD/Monash/Binance because Setting A replay computes both models' loss from
   one realised outcome and actions do not change the data stream. This is the easy case; no real Setting B result exists, so no
   claim about logged feedback or counterfactual identification is supported.
10. **Model pairs selected after outcomes?** Yes, and the docs say so: pairs and daily granularity chosen after seeing phase-1
    dev headroom; OPSD 2018-19 inspected; ridge penalty tuned on 2017; the proposed primary CUSUM+Hold7 is the only positive actual-series
    cell. Monash and Binance are controls, not selected, which is to the programme's credit.
11. **Costs chosen to manufacture results?** Not manufactured, but arbitrary and decisive. c_s in {2,5} with Delta=0.15,
    delta=0.05; L=100 makes H_T=0 by construction (10 = 2 c_s); OPSD primary c_s=5 is "the value at which headroom is clearly above
    noise" (doc 10 6.5), i.e. chosen on dev outcomes. Value-vs-c_s results flip sign across the grid by design. No application cost is
    anchored to money anywhere (Binance 0.1% fee unused).
12. **CIs valid under dependence?** Synthetic: episode bootstrap is valid for i.i.d. episodes, but cells share seeds and monitors, so "39/39",
    "0/360", "16/1620" are not independent replications (the docs say so). 39/39 is also weak: the 39 pairs share two episode sets and,
    since V is exactly linear in c_s, agreement across seed sets is a law-of-large-numbers statement. Real: one series per pair; the rolling-origin
    bootstrap is degenerate (block 53 = number of origins); block bootstrap breaks persistence; effective sample ~2. No real CI supports a claim.
13. **Confirmation set exposed?** Synthetic: no (registry max 5,000,000; seed guard in `run_synthetic.py`). Real: OPSD 2020 window
    unopened but the forking path (COVID demand disturbance is public) is disclosed; EIA, Elec2, Gas, NOAA, CRSP are exposed. The confirmation
    design is also already narrowed to one primary cell chosen for having been positive on dev. Not exposed in the strict sense; weakly
    informative in the substantive sense.
14. **Economically meaningful?** Not shown. Costs are in loss units; headroom is 30 (L=400) to ~220 loss units per 3000 steps against
    never-switch costs of 660-900, i.e. 4-25%, with MME = 1% by fiat. Nothing ties c_s or c_q to a real operating cost.
15. **Generalizes beyond one generator?** Unproven. All synthetic losses are Bernoulli with piecewise-constant means, i.i.d. conditional on a
    regime, symmetric chain in all Type II S2 cells (pi_b=0.5, where "always" is near-optimal; the asymmetric extension is in progress by another agent).
    My test C adds Beta-with-outliers and gradual drift (2 cells), where the C2 pattern held weakly (below).
16. **Theorems nontrivial?** No. P0/P1/P4: linearity. P2: algebra given c_s-blindness. P3(a): irrelevant signal makes acting harmful.
    P3(b): the proof is correct but constructs mu(1) path adversarially. P5: the affine step is linearity; the ceiling is one line of Markov algebra and
    holds only for label-only Hold(H) (not for adaptive hold/revert from labels, not for any side information). P6 is Lai/Lorden and says so.
    Doc 04 already makes this judgment; I concur.
17. **Already in closest work?** Qualitatively yes: Regol et al. (ICML 2025) shows detector-triggered retraining over-triggers and that cost-aware
    forecasting beats ADWIN/KSWIN with a DP oracle; Cara does the same; Bayesian QCD with decision costs gives the posterior-threshold rule and linear Bayes
    risk. What is not in those: the fixed-controller power sweep at matched alarm rate, and exact crossing prediction. Both are small and, per test E,
    depend on a calibration convention that is itself fragile. Doc 02 also admits it did not read QCD originals or Regol proofs in full.
18. **Would a critical ICML reviewer see a new generalizable insight?** No, at present. The reviewable story is "calibrating alarms at 5% is the wrong
    knob for decisions; tune the threshold to the economics" (tuned alpha went to 0.5 boundary in 8/10 cells), which is the Bayes-risk
    / cost-aware retraining message, supported on one synthetic family and with no method to propose.

## 3. Falsification tests

### Test A (executed): TH-1 crossing under a random-Delta environment
Setup: S3 strong, Permanent, q=0.2, d=50, c_s-blind monitors (the 5 engine monitors), n=1000, set 1 seed 1000 predicts, set 2 seed 2000
checks; calibration null at 5,000,000. "Naive" = prediction from alarm CDFs and the *marginal* mean advantage path, `D0 = sum_t E[Delta_t] g(t)`;
"exact" = per-episode Delta (needs evaluator truth). Empirical crossing on set 2 with a 400-resample episode bootstrap CI (this CI is narrower than a
difference-of-estimates CI, so counts below are conservative against the programme).

| environment | pairs | naive CDF-only prediction inside set-2 CI | per-episode (exact) inside CI |
|---|---|---|---|
| tau fixed = 1000 (programme's TH-1 design) | 10 | 10/10 | 10/10 |
| tau ~ U[100, 2800] (random Delta path correlated with alarm times) | 10 | **3/10** | 7/10 |
| S2 Markov rho=0.995 useful | 10 | 9/10 | 8/10 |

Examples (wide tau): cusum vs page_hinkley predicted 114.5 naive vs 207.8 exact vs 195.9 empirical [176.5, 218.4]; cusum vs sr_betting 101.3 / 210.0 / 203.8;
batch vs cusum 86.1 / 139.2 / 128.5. The CDF-only prediction under-states D0 by about 1.5-2x because Cov(Delta_t, 1{S<=t-1}) > 0 (alarms happen after tau).
**Result:** the claim "c_s* is predictable from alarm CDFs" is valid only when Delta is deterministic or independent of the alarm path (doc 04 P4 already says
the covariance is what matters; doc 06 TH-1 uses a fixed tau, which hides it). The exact version needs Delta_t per episode, i.e. is not deployable. Also
note the c_s-blindness: the crossing is the realised-cost line, not a discovery. **Verdict: weakens C1b to a narrow, evaluator-side accounting statement.**

### Test B (executed): P5 ceiling with an unlabelled proxy
Setup: two-state Markov chain, Hold(H), c_s=2, Delta_bad=0.15, delta=0.05; label-only monitor = exact HMM filter on losses delayed by d, predicted forward
d+1 steps; proxy monitor = exact filter on an undelayed binary proxy of Z with accuracy 0.8; alarm when predicted posterior > h; n=3000, T=3000.

| setting | theta_max (ceiling) | max_H G_H(theta_max) | label-only theta at alarm, V | proxy theta at alarm, V |
|---|---|---|---|---|
| pi_b=0.1, B=400, d=800 | 0.197 | **-4.0** (no positive value possible) | no alarm fires for h >= 0.5 (predicted posterior never exceeds ceiling), V=0 | theta 0.88-0.997 (**> ceiling**), V = **+25 to +28** at H=100, +15 to +17 at H=50 |
| pi_b=0.5, B=500, d=200 | 0.723 | +87.1 | theta 0.62-0.71 (<= ceiling, consistent), V up to 89.5 (H=200) | theta 0.86-0.997, V 157-170 (H=200) |

**Result:** the ceiling is correct (label-only never exceeds it, and with a threshold above it the monitor never acts) and also not binding on any system with
undelayed side information, where it is exceeded by 4x and flips the sign of value. The scope statement must be: "no *label-only, fixed-Hold* monitor in a
two-state Markov environment". The programme's own sentence "the obstacle is persistence and delay, not detection power" becomes "the obstacle is label latency";
the 0/360 check cannot falsify a proven inequality and its tightness only at d=200 (where value is ~0) shows the check is mostly vacuous elsewhere.
**Verdict: C1d is narrow; the r=0.9999 result is an identity check with evaluator state.**

### Test C (executed): C2 with non-Bernoulli, heavy-tailed, gradually drifting losses
Setup: new generator (read-only engine reused, my own family class): losses Beta (kappa=3) with 3% U(0.8,1) outlier contamination, incumbent mean p0+0.15*ramp,
challenger constant p0+0.05, tau ~ U[800,1200], T=3000, q=0.2, d=50, c_s=5. Mini Type II: 5 monitors x {Permanent, Hold100, Hold400, Reverse} x alpha in
{0.05, 0.2, 0.5, 0.8} (80 configs) vs 20 simple configs, tune n=300 (seed 800000), evaluate n=1000 (seed 810000), 2000-resample paired bootstrap. Not Holm-corrected, 2 cells.

| cell | best monitor (tuned) | cost | best simple (tuned) | cost | simple - monitor [95% CI] | MME | never / always / dynamic oracle |
|---|---|---|---|---|---|---|---|
| gradual persistent ramp (R=800) | sr_betting, Permanent, alpha=0.8 | 706.2 | statm:100:0.0 | 710.8 | **+4.5 [4.0, 5.1]** (monitor ahead) | 8.4 | 840.0 / 755.0 / 698.3 |
| gradual transient bump (R=800) | page_hinkley, Hold100, alpha=0.05 | 663.0 | never | 660.0 | -3.0 [-3.3, -2.7] (simple ahead) | 6.6 | 660.0 / 755.0 / 643.3 |

**Result:** both cells are ties under the programme's MME rule, so C2 is not contradicted, but the monitor point estimate is ahead in the persistent-drift cell with
CI excluding 0, at alpha=0.8, i.e. the same direction as before (the useful monitor is nearly an act-early rule) yet not "0 wins" in spirit. Per-monitor, 4 of 5
monitors lose to the best simple policy in the ramp cell and all 5 lose in the bump cell. Two cells with n=300 tuning cannot replace a confirmatory grid, and the
tuned alpha is again at or near the top of the grid (0.5-0.8), so the monitor is hardly constrained by a false-alarm criterion. **Verdict: C2 survives, still INCONCLUSIVE
outside the Bernoulli piecewise-constant world; claim a result only per-generator.**

### Test D (executed by code inspection plus null simulation): are the "simple" policies themselves fixed-sample monitors?
Yes.
- `CalendarMargin(K, m)` (script) / `CalendarBatch(K)` (engine): every K steps compare window means of released l0, l1 and move to the challenger if the paired
  mean difference exceeds m, back if below -m. That is a non-overlapping fixed-window one-sided test on the paired stream with threshold m on the mean, two-sided
  hysteresis, no reset. The engine `BatchTest` monitor is the same statistic standardised by sd with a null-calibrated threshold.
- `StaticThreshold/StaticMargin(W, m)`: moving-window paired mean x (T - s) > c_s and > m, permanent. That is a windowed-mean detector with a **cost-aware threshold**
  (c_s/(T-s)) and the economic horizon built in; the monitors do not get this.
- Their implied false-switch probability on the interior null (challenger strictly worse by 0.05, c_s=5, q=0.2, d=50; n=2000): calm:100:0 1.00, calm:100:0.02 1.00,
  calm:200:0 0.98, calm:400:0 0.79, statm:50:0 1.00, statm:100:0 0.93, statm:100:0.02 0.82, statm:200:0 0.51. These are alarm-equivalent alpha of 0.5-1.0; the tuned
  monitor alphas (0.5 boundary; 0.8 in Test C) are the same regime.
**Result:** C2 is a statement about *controller form and threshold selection* (tune the threshold to economics, allow reverting, use the horizon) versus *calibrated
alarm-to-action*, not about "monitoring vs no monitoring". The headline "simple policies beat monitors" is misleading wording; "cost-aware fixed-sample monitors with
effective alpha ~ 0.5-1 beat 5%-alpha alarm systems" is accurate and is Regol/Cara/Bayes-QCD territory.

### Test E (executed): the "matched" false-alarm constraint (also bears on Q4/Q5)
n_cal=2000 at seed 5,000,000 (interior null, E[x]=-0.05) fixes the alpha=0.05 threshold; fresh seed 5,000,001 rates:

| monitor | P(any alarm by T), interior null | boundary null E[x]=0 |
|---|---|---|
| cusum | 0.062 | **0.389** |
| page_hinkley | 0.049 | 0.037 |
| batch | 0.054 | 0.217 |
| sr_betting | 0.056 | 0.340 |
| kelly_h2c_inspired | 0.050 | 0.224 |

So the matched ordering (CUSUM most powerful etc.) depends on testing against a null in the interior of the composite null. Every "useless"/"none"/"common-shock" cell is
at or near the boundary, which is exactly where the programme reports reversals and false switches, so false-alarm composition (H4 mechanism 4) is confounded with
detector choice. Only the engine's nominal e-process thresholds keep a stated guarantee, and they are reported separately.

### Other proposed tests, not executed
- F. **Asymmetric, rare-persistent-regime Type II with Shiryaev posterior and a c_s-aware controller** (in progress by another agent; I would add the Shiryaev rule as a monitor
  and a cost-aware posterior threshold as a "simple" rival; falsifies C2 if a posterior rule wins).
- G. **Hidden-covariate (side-information) Type II**: give monitors the unlabelled proxy of Test B and re-run C2; prediction: monitors win by a large margin, showing C2 is label-latency-specific.
- H. **Adaptive-controller P3 check**: let the controller observe c_s and fallback quality estimates; P3(b) reversals should vanish, showing they are controller-misspecification artifacts.
- I. **Non-stationary calibration**: re-run the real OPSD replay with thresholds from an in-sample sliding null instead of a validation-window bootstrap, to see whether the 5% conversion is threshold-driven.

## 4. Top objections (ranked)

1. **The positive theory is identities and one Markov bound; the numerical "confirmations" confirm the implementation, not a claim** (ledger says this itself). TH-1 is
   linearity in c_s with c_s-blind controllers; TH-3's r=0.9999 uses evaluator regimes; 0/360 ceiling violations is a proven inequality.
2. **Test D: "simple policies" are monitors at alpha ~ 0.5-1 with cost-aware thresholds.** C2 is controller-form/threshold-selection, which Bayes-risk QCD and Regol/Cara already say.
3. **C1 and C2 conflict.** C1 says rankings can be reversed exactly (c_s-blind monitors); C2 says reversals vanish once the system is tuned. Together: "do not use untuned c_s-blind
   monitors", which is not a research contribution.
4. **Test E: "matched alpha" is a point-null artifact.** Boundary-null false alarms differ 10x across monitors (0.037 to 0.389); calibration needs the true generator.
5. **Single generator family and arbitrary costs; real data is one series per pair with post-hoc pair choice.** C3 cannot carry a claim; "0-5%" is one realisation; Test C is the only
   robustness evidence beyond Bernoulli and it is two cells. Baselines are textbook with untuned defaults; no Shiryaev, ADWIN, PPRM, or Regol/Cara comparator.

Lesser issues: kelly-H2c is the group's own method and the only SOURCE_INSPIRED one; the 10 TH-2 monitors include five parametric variants, so Kendall tau and "21/90" are not 10 independent
monitors; Reverse reuses the main threshold (not separately calibrated); the oracle "regime clairvoyant" is not optimal (rho=0.98) and is only a label; `power_T` counts late alarms.

## 5. ICML verdict and Decision

**Reject as the paper stands.** Contribution: an exact accounting identity, a small Markov bound, and a negative empirical result of limited scope and ambiguous interpretation.
Related work (Regol et al., Cara, Bayesian QCD) covers the message; the new elements (fixed-controller power sweep, exact crossing) are small and fragile.

**Decision: D (workshop / preliminary).** What would change it:
- **To C (benchmark / TMLR):** freeze a benchmark (generators with random Delta, asymmetric rare-persistent regimes, non-Bernoulli and drifting losses, side-information setting,
  Setting B), include Shiryaev posterior, ADWIN/DDM, PPRM (adapted), Cara/Regol-style cost-aware retraining, c_s-aware tuned versions of every monitor; report false-alarm at
  boundary and interior nulls; run the frozen confirmation seeds and the single OPSD/Monash/Binance window once; report the accounting identities as the evaluation protocol, not as results.
- **To B (empirical):** only if a regularity beats the Bayes-QCD/Regol baseline, e.g. a robust, predictable map from (c_s/Delta, persistence, delay, side information) to the
  optimal alpha and to the fraction of headroom convertible, validated out of sample across several generators and one confirmatory real window. Test B (label latency vs side information)
  is the most promising seed of such a map.
- **To A (method):** no path today; it would need a monitor or controller that beats the cost-aware Shiryaev/Bayes rule in a confirmatory comparison.
- **To E:** if asymmetric-regime Type II shows a posterior rule matches or beats every monitor system, and the confirmatory window shows no conversion, the honest outcome is E for ICML and a short negative-results note.

## 6. Limitations of this review
Same-model self-review, not independent. I did not run the programme's Type II or real-data pipelines, only small checks on top of its engine (read-only). Tests A, B, C and E use n of 1000-3000
or n=300 tuning and two cells in Test C, and are falsification probes, not evidence for a claim. Prior-art judgments rely on doc 02, not on my own reading of Regol, Cara or QCD sources.
