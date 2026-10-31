# Final research decision

**Decision: D — WORKSHOP_OR_PRELIMINARY.** No ICML submission is supported by the current evidence.

Branch `research/monitoring-to-decision-value-2026-10-30`; base `ce9d3ca`. Protocol frozen at
`6f63da1`, confirmation configs and hashes at `ca84d30`, confirmation results at `ecc0f46`. All
reviews are same-model self-review, not independent review.

## A. What we found

1. **Deployment value under alarm-driven controllers is an exact linear functional of the alarm law**
   (`04` P1/P4). It is verified to 1e-12 on synthetic data and on real OPSD replay.
   - Consequence: power, delay and value rank monitors differently whenever the benefit weights
     differ. Under incumbent-only monitors, fallback quality alone reverses any detection ranking
     (P3; Kendall τ(power, value) = −0.78 with no useful fallback, `06` TH-2).
   - Status: exact accounting, confirmed numerically. *Established in spirit* (Bayesian QCD, Regol et
     al. 2025); not a novel theorem.
2. **Once controllers are tuned, the value of better monitoring is conditional and small.**
   - Under equal-budget tuning, monitors never beat the best simple policy in symmetric regimes, or
     when the challenger is better most of the time (0/10 wins; `11`).
   - With rare, persistent bad states and no label delay, development showed monitor wins of
     6.5–9.4 cost units (≈1% of cost) in 6/12 cells.
   - Confirmation (seeds ≥7e6, n=2000/cell): the four target cells give +6.58 (one-sided LB 6.07).
     This is positive, but below the pre-set MME of 6.79, so **CF-S1 FAILED** and the "conditional
     win" is **not confirmed**.
   - Delay erosion (CF-S2): +1.87 (LB 1.35) **PASSED**, driven by 2 of 6 regime pairs.
   - Negative control passed.
3. **The untuned "better monitor → worse decisions" reversals are confounded by the controller.**
   - Untuned TH-4 found 16/1620 reversals. Equal-budget tuning finds 0 matched reversals in 23/24
     cells (`11`). H1 is not supported as a robust phenomenon.
   - The historical HG-vs-PH reversal (F2) was not size-matched, and it occurs where acting is
     wrong (`01`).

Real-world status: OPSD dev replay converted ≤5% of hindsight headroom (`10`). The reserved OPSD
2020 window produced **no alarm from any monitor** on the primary pair (value 0 vs MME 7.3), so
**Part R FAILED**. The Monash and Binance controls passed. All delays and costs on real data are
imposed, not measured.

## B. When does better monitoring improve decisions?

All statements are development or synthetic unless marked otherwise.
- **Positive (synthetic, not confirmed at MME):** bad states that are rare and persistent (mean run
  ≥400 steps), a useful fallback, short label delay, and a controller tuned jointly with the
  threshold. The mechanism is P5: value per alarm is affine in precision at action time, and
  precision decays as λ^(d+1) with delay.
- **Negligible:** a static policy is near-optimal (symmetric regimes; persistently better
  challenger, as on real OPSD); headroom is small (S1 L≤400, B=100); delay erodes precision.
- **Reversing:** only under mis-specified controllers. Examples: a c_s-blind permanent switch
  (crossing point c_s*, P2, confirmed out of sample with fixed τ but off by 1.5–2× with random τ,
  `07`), or incumbent-only monitors without a useful fallback. Tuning removes these reversals.
- **Side information** (undelayed proxies) escapes the label-only ceiling: red-team probe,
  V +25..+28 where label-only monitors get 0 (`07`, development). This is the most promising open
  lead.

## C. How much?

The best confirmed contrast is tuned monitor vs tuned simple policy in the target cells:
- Absolute: +6.58 cost units per 3,000-step episode.
- Relative: ≈1.0% of never-switch cost (denominator: never-switch cost, MME = 1%).
- Lower bound: 6.07.
- The monitor captures 33–55% of hindsight headroom vs 27–48% for simple policies (π_b=0.25,
  B≥400, development).
- Label consumption is identical across compared systems (shared acquisition, q=0.2).

There is no faithful comparison with published methods: no PPRM, Shiryaev posterior rule, ADWIN
or Cara/Regol baseline was reproduced. Predictive improvement on real OPSD (challenger better
most of the time) did not translate into monitoring value; always-challenger dominates.

## D. Real data

See `03`, `10`, `13`.
- **OPSD DE load (Setting A, daily):** incumbent/challenger pairs frozen-ridge, sliding-refit and
  TSO forecast.
  - Splits: fit 2015–16, validation 2017, dev 2018–19, reserved 2020-01..09.
  - c_s and d are imposed.
  - Dev: dynamic headroom exists in hindsight, but monitors capture 0–5%.
  - Reserved: no alarms; FAIL.
- **Monash electricity:** a do-nothing control; passed.
- **Binance ETH 1h:** a null control; passed.
- **Excluded:**
  - Gas, EIA and Elec2: exposed or lacking a clock.
  - CRSP: retrospective only.
  - Open Bandit: Setting B with no untouched window.
  - Criteo: simulated delays, or not accessible.

## E. Theory

- **Known or accounting:** P0, P1, P4.
- **Elementary corollaries:** P2 crossing point and P3 invariance / no universal proxy. Valid
  under their stated assumptions; novelty unverified and likely low.
- **Elementary Markov bound:** P5 precision sufficiency and delay–persistence ceiling. Holds for
  label-only monitors, fixed Hold, two-state chains. Numerically checked (0/360 violations), but the
  r=0.9999 fit uses evaluator θ.
- **Direct corollary of Lai/Lorden:** P6. Its conversion number κ did not out-predict power in
  development.
- **Unproved:** a sufficient condition for monitoring dominance to imply decision dominance under
  random benefit paths.

## F. ICML assessment

- **Originality:** low. The qualitative thesis is known (Regol et al. ICML 2025; Bayesian QCD).
- **Soundness:** good engineering (tested information flow, frozen confirmation, hashes).
- **Significance:** small effects.
- **Baselines:** textbook reimplementations; key published comparators missing.
- **Breadth:** one Bernoulli generator family, plus a red-team non-Bernoulli probe.
- **Real data:** a negative result.

Main remaining objection: the conclusions concern controller form and threshold selection, which
cost-aware QCD already covers.

## G. Next actions (ranked)

1. **Side-information vs label-latency study.**
   - Test whether undelayed proxies convert monitoring into value where label-only monitors
     provably cannot (P5 ceiling).
   - Experiment: proxy quality × delay × persistence, with tuned controllers.
   - Alternative explanation: the proxy is a near-oracle.
   - Stop if value under realistic proxy noise is below MME.
   - Done when: `14_SIDE_INFORMATION.md` plus a frozen confirmation.
2. **Add faithful published baselines.**
   - Shiryaev posterior rule with action costs, ADWIN (river), PPRM (code), Cara/Regol
     cost-aware retraining.
   - Stop if any matches the tuned monitors (then the controller-form conclusion is just
     Bayesian QCD).
   - Done when: a fidelity table in `05`.
3. **Composite-null calibration.** Recalibrate on worst-case boundary nulls; `07` (e) shows false
   alarms of 0.22–0.39 at interior thresholds. Done when: re-run Type II with boundary-calibrated
   thresholds.
4. **Second real task with a measured feedback clock.**
   - For example Criteo attribution maturity (retrospective), or an OPE task with untouched data.
   - Stop if no measured release times exist.
5. **Workshop write-up** of the accounting framework plus the negative and conditional findings.
   No new compute is needed.

## H. What was completed

- **Implemented:** engine, adapters, monitors, controllers, oracles, statistics, registry
  (`src/shiftlab/decision_value/`).
- **Tested:** 31 pytest tests. Verify with
  `PYTHONPATH=src python -m pytest tests/decision_value -q`.
- **Reproduced:**
  - F1, F3 and F4 from stored artifacts.
  - F3 and F4 on fresh seeds.
  - F5 was not reproducible across library versions.
- **Confirmed:** CF-S2 and CF-S3. **Failed:** CF-S1 and Part R.
- **Proven:** elementary propositions P0–P5 (`04`).
- **Reviewed:** self-review only.
- **Not attempted:**
  - Setting B experiments.
  - PaperBanana figures. No figure was produced because no claim passed the evidence gate; the
    PaperBanana dependency was not exercised.
  - A manuscript, which the evidence does not warrant.
- **Outputs:** gitignored, under `outputs/decision_value/{development,real_data,confirmation,manifests}`.
- **Failure Atlas:** untouched.
