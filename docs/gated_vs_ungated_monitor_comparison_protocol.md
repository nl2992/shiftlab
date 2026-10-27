# Disagreement-gated versus ungated sparse-label harm monitors: verification protocol

**Status:** frozen specification, 2026-10-27. No registered stage has been run at freeze.
The follow-up header records the commit containing this specification before Stage 1.
This study verifies a *predicted* effect from
[G1](adg_growth_prescreen_results.md). It is not a new-method study. Disagreement gating is
DISCERN's contribution ([Balachandran, arXiv:2609.17560](https://arxiv.org/abs/2609.17560)); this
protocol tests whether that established idea changes the repository's own conclusions about
sparse-label monitoring.

## 1. Question and why it matters

On the existing hard-budget development design:
- the deployed and reference policies disagree on about 9% of events;
- the paired cost is exactly zero whenever they agree (Assumption L);
- ungated monitors therefore spend about 91% of their labels on events whose cost is already known.

G1's analytic calculation predicted that gating would raise per-event log-growth at matched spend
by 5–18×, depending on budget. That prediction used a proportional-tilt working alternative, not
the generator's boundary-harm mechanism, and ignored budget exhaustion and proxy updating.

**Question.** On fresh streams from the existing design, does gating improve realised evidence
growth and detection over correctly bounded ungated monitors at matched label-dollar budgets?
Does the size of the improvement match the G1 prediction?

**Why the manuscript needs this.** Several recorded comparisons
([evidence budget 20%](evidence_budget20_comparison_results.md),
[monitor signal diagnostic](monitor_signal_diagnostic_results.md),
[propensity-floor diagnostic](propensity_floor_diagnostic_results.md)) compare only ungated
allocations. If gating matters as much as predicted, the benchmark must include a gated comparator
and qualify those conclusions. If it does not, the G1 prediction must not be cited.

**Baseline correction carried in.** The historic "uniform detects 6/60" result used a shared
support bound of 96.9. With uniform's valid policy-specific bound (45.9 at `q = 0.20`), the same
increments cross in 47/60 (propensity-floor diagnostic). The primary ungated baseline here is
therefore correctly bounded uniform, and every bound is policy-specific.

## 2. Design

**Generator.** The hard-budget DIVE generator (`shiftlab.dive.hard_budget`):
- `n = 3200`, `d = 16`, `epsilon = 0.10`, `fn = 5`, `fp = 1`, `alpha = 0.05`;
- covariate label tariffs in `[0.5, 2.5]` (maximum 2.5);
- a pathwise hard dollar cap calibrated from validation tariffs and shared within each
  seed/scenario/budget;
- the runner stops before opening an event whose maximum tariff the remaining cap cannot cover;
- policies, proxy, and classifier exactly as in the existing runner.

**Scenarios.**
- Primary: `boundary_local_harm`.
- Controls: `stationary`, `benign_nuisance`.
- Stress: `harmful_adaptation`. Here the deployed policy switches to "always 1" at event 1,600,
  which raises disagreement from about 9% to about 42%. This tests what happens to a gated monitor
  whose label rate was calibrated before the policy changed.

**Budgets.** Label-dollar rates `r ∈ {0.02, 0.05, 0.10, 0.20}`. The 0.20 cell is the existing
development operating point.

### Arms

All arms share each seed's stream, the per-event query uniforms (`Q_t = 1[U_t < q_t]`), the dollar
cap, the proxy fit, and the classifier. Bounds are policy-specific and predictable with respect to
`F_{t-1}`; none uses the current covariate.

**Control-null filtration clarification (2026-10-27, before freeze).** The control
generator draws independent current events. Stationary events have an unchanged signal/outcome
law; benign nuisance changes only coordinates 2 onward, whereas both fixed policies and the
outcome law use coordinates 0 and 1. Consequently the registered population expected paired
cost is also the conditional expected cost given prior events, at every monitoring time.
This argument relies on this generator, these actions, and this cost matrix. A finite stream's
oracle average exceeding epsilon is a sampling excursion, not a violation of that conditional
expectation. Count every control alarm as a false escalation; do not condition on its oracle
average. Past-only pacing preserves this filtration even when nuisance tariffs change.

| Arm | Gated | Anchor | Propensity | Bound / process | Role |
|---|---|---|---|---|---|
| F0 `full_feedback` | — | — | 1 | Bounded-mean mixture, `B = 5.1` | Upper reference |
| U1 `uniform_ppi` | no | ridge proxy | `r` | Fixed-stake mixture, `B = 5.1(2/r - 1)` | **Primary ungated baseline** |
| U2 `uniform_ppi_common96p9` | no | ridge proxy | `0.20` | Same mixture, `B = 96.9` | `r = 0.20` only; reproduces the historic 6/60 |
| U3 `variance_ppi` | no | ridge proxy | existing variance policy, floor `r/2` | Mixture, `B = 5.1(2/(r/2) - 1)` | Strongest existing ungated adaptive allocation |
| G1 `gated_ht_paced` | yes | 0 | online-paced `q_t` (below) | `PredictableBoundMeanEProcess`, `B_t = 5/q_t + 0.1` | **Primary gated arm** |
| G1f `gated_ht_fixed` | yes | 0 | fixed `q_D = min(1, r·mean(tariff_val)/mean(A·tariff_val))` | Mixture, `B = 5/q_D + 0.1` | G1's analytic arm; sensitivity |
| G2 `gated_ppi_paced` | yes | ridge proxy | as G1 | `B_t = 5.1(2/q_t - 1)` | Whether a proxy helps after gating |
| G3 `gated_eb_paced` | yes | 0 | as G1 | Predictable plug-in empirical Bernstein on `(Hhat_t + B_t)/(2B_t)` | Closest to DISCERN's CS engine (adaptation; no official code) |

Every mixture uses the existing stakes `(0.05, 0.1, 0.2, 0.4, 0.8)` with equal weights.

### Mandatory published/composed panel (added before freeze, 2026-10-27)

The [phase comparator panel](agent_goal_stratified_monitor_phase.md#3a-state-of-the-art-comparator-panel-mandatory)
and [pre-run regime map](stratified_monitor_regime_map.md) apply. The historic engine above
remains for fidelity and the two original verification endpoints. It is not the only engine
used to assess the strongest applicable incumbent.

| Added arm | Information and construction | Fidelity label |
|---|---|---|
| Timans full-feedback approximate/grid GRAPA | Score `(Z-epsilon+5.1)/(2*5.1)`; existing replay-verified implementation, epsilon 0.5, burn-in 100 | Official-replay-verified formula; paired-score adaptation, unmatched upper reference |
| Timans gated HT approximate/grid GRAPA | G1/G1f increments mapped by their history-predictable bounds; same query path as the corresponding fixed-stake arm | Selective-label adaptation |
| PPE uniform and gated | Existing factor-level PPE with source nonnegativity shrinkage; ridge anchors and the same U1/G2 query paths | Paired-score adaptation; factor-level audit required |
| Xu active predictor betting | Section 2.2 predictor correction after the paired-score sign/affine map; square-root residual-moment allocation with the existing validation-calibrated multiplier, floor r/2 and ceiling 0.8 | Adaptation; not the population allocation optimizer or full RCPS reproduction |
| Conservative no-action | Never alarms; no queried labels | Deterministic reference |
| Feature ADWIN sentinel | River ADWIN per coordinate on `Phi(X_j)`, warmed on events 0–799; defaults except delta `0.05/(16*3200)`; common G1/U1 processed prefix only | Bounded-feature adaptation; feature-mean target, not harm |

**Engine parity.** Every compatible full-feedback, pooled, and gated HT/PPI path is replayed with
the historical five-stake mixture, the same grid extended to stake 1, predictable plug-in bets
(existing rule, cap 0.99), and Timans approximate/grid GRAPA (existing settings above).
All replays use the exact same increments, labels, propensities, and processed horizon.
No candidate-only engine improvement is permitted. G3 is already an empirical-Bernstein engine;
its base HT query path is also available to the other engines. PPE and Xu fixed-factor source
adaptations are recorded alongside the equally equipped compositions; algebraic duplicates are
reported as such rather than counted as independent victories.
The fixed-factor PPE and Xu rows use 0.9 times their support-implied source stake cap.
On the same paths their factors equal `1+0.9*Hhat/B`; formula-level checks verify this.
The stronger shared-engine compositions are reported through their U1/U3/G2 path aliases.

**Scope/exclusions.** Group-wise tests and SR/CUSUM are mandatory in WP2/WP3 but are not
WP1's gating-isolation endpoint: they respectively change the null or start-time construction.
Comparecast's weak running-average null and PPRM's predictive-risk target do not test the
eventwise paired-cost null, so neither can support a same-null WP1 ranking. Q2 certification
(MOPE, OPI, Wang) is outside this monitoring phase. The feature-shift sentinel is reported only
as a distribution-shift diagnostic with its own null/calibration; it cannot serve as a calibrated
harm detector. Its fixed nominal delta is conservative across coordinates/calendar positions,
but is not asserted to prove pathwise 5% control. Check stationary-null crossings with the same
calibration seeds and simultaneous exact bounds across the four budgets. Benign nuisance is
an alternative for its feature target. Record feature detection/false alarms and harm-alarm
coincidences separately. It is excluded from same-null harm rankings.

**Regime predictions.** At budget 0.20, expect gated fixed/anchored alternatives to tie when all
disagreements are labelled. At 0.02–0.05, any anchor gain is expected to be modest and must be
compared with equally equipped gated adaptive betting, Xu, and PPE. After policy adaptation,
expect past-paced gating to preserve more horizon than fixed gating; this is descriptive robustness.
No new-method claim follows from verifying that gating beats an ungated path. The primary
thresholds in Section 5 remain unchanged; panel rankings, ties and losses are reported separately.

**Online pacing (G1, G2, G3).** Before event `t`, let `c_hat_t` be the mean of `A_i · tariff_i`
over the most recent 200 events.
- Events from the validation slice seed the window.
- Only actions and tariffs enter, never labels, so this is unlabelled and predictable.
- `q_t = clip(r · mean(tariff_val) / max(c_hat_t, 1e-6), 0.10, 1)`.
- The floor 0.10 is registered so that `B_t` stays bounded.
- Under a policy change (harmful adaptation), pacing cuts `q_t` instead of exhausting the cap.

`q_t` and `B_t` depend only on `F_{t-1}`, so the event-specific bound is valid under the
history-conditional null. Lemma 1 of the
[ADG protocol](anchored_gated_harm_monitor_development_protocol.md) gives unbiasedness:
agreement events contribute exactly `-epsilon`, and the gating indicator is known before the
outcome.

## 3. Endpoints

**Realised growth.** For a fixed-stake component `s`, take the post-onset log-wealth gain divided by
the number of post-onset events. Count only the **common processed prefix**, i.e. events processed
by both arms of a contrast, and continue past any alarm. A stream's realised growth is the best
fixed stake, matching G1's `G*`. For G1, G2, and G3 the components use the `B_t` sequence. G3 is
excluded from growth endpoints, because the empirical-Bernstein process is not a fixed-stake
mixture.

**Co-primary endpoints** (Bonferroni: each tested one-sided at 0.025):
- **P1 (growth ratio at the existing operating point).** At `r = 0.20` in `boundary_local_harm`:
  `R = mean_seeds(growth_G1) / mean_seeds(growth_U1)`, with a paired seed-bootstrap 97.5%
  one-sided lower bound (10,000 resamples). If `mean(growth_U1) <= 0`, the ratio is undefined:
  report the paired difference and make no ratio claim.
- **P2 (detection at a scarce budget).** At `r = 0.05` in `boundary_local_harm`: the paired
  difference in post-onset detection by the horizon, G1 minus U1. Pre-onset alarms and
  budget-censored onsets count as non-detections. Report the paired bootstrap interval and a
  one-sided exact McNemar test.

**Secondary endpoints.**
- `R` and the detection differences in every budget cell; G1f, G2, G3, and U3 contrasts.
- Censored detection delay.
- Labels and dollars spent, and the share of the cap used.
- Processed horizon.
- Excess decision loss before alarm.
- Control-scenario crossings (descriptive).
- Harmful-adaptation behaviour: detection, cap exhaustion, and realised `q_t` path for paced
  versus fixed gating.
- Comparison of measured `R` with the G1 prediction in each cell.

**G1 predictions to compare against** (ratio of means, `mu = 0.277`):

| `r` | 0.02 | 0.05 (interpolated) | 0.10 | 0.20 |
|---|---:|---:|---:|---:|
| Predicted G1f/U1 growth ratio (G1 `A3/A1`) | ≈ 18 | ≈ 18 | ≈ 15 | ≈ 7.5 |

The 0.05 entry interpolates the 0.04 and 0.06 cells (both ≈ 17.7).

## 4. Stages and gates

| Stage | Seeds | Work | Pass if |
|---|---|---|---|
| **S0** implementation | — | New runner `src/shiftlab/dive/gated_monitor_comparison.py` reusing the hard-budget generator. Unit tests (Section 6). | Tests, Ruff, mypy, and the full suite pass. |
| **S1** fidelity replay | Existing `20373024–20373083`, `r = 0.20`, boundary harm | Run U1 and U2 on the historic seeds. | U2 reproduces 6/60 and U1 reproduces 47/60 exactly. Otherwise stop and reconcile with the existing runner before any fresh seed. |
| **S2** null calibration | `58500000–58501999` per cell; `stationary` and `benign_nuisance`; all four registered budgets; all applicable panel/engine rows | 2,000 streams per scenario × budget cell | For each arm/engine, the simultaneous Bonferroni exact one-sided 95% upper bound across its 8 cells is ≤ 5% (2 cells for U2, which exists only at 0.20). A failing arm is excluded from Stage 3 claims. If G1 fails, stop (assumption or implementation error). |
| **S3** fresh comparison | `58400000–58400099` (100 per scenario × budget) | All arms, all scenarios and budgets | Section 5 decision rules. |

**Smoke run first.** Before Stage 2 or 3, run 5 seeds on a disjoint smoke block (`58600000–04`) to
check runtime and integrity. Smoke outputs are discarded from inference.

**Fidelity input clarification (2026-10-27, before freeze).** S1 replays the saved uniform
increments in `outputs/monitor_signal_diagnostic_20_60_v2/metrics/event_traces.parquet` on CPU,
after checking its SHA-256 against that run's manifest. This preserves the historic
CUDA-generated paths and query coins. Check the full common-bound log-wealth trajectory
against the saved trajectory, then replay those identical increments at 45.9. Require exactly
the registered 60 seed IDs and the registered crossing counts. This is a fidelity replay,
not a fresh CPU regeneration of a CUDA random stream. S0 separately checks the shared runner
integration before fresh streams.

The 58M sub-blocks used here (`584xxxxx`, `585xxxxx`, `586xxxxx`) do not appear in `scripts/`,
`src/`, `configs/`, `docs/`, or `papers/` (checked 2026-10-27). They are disjoint from the G1
pre-screen block `58000000–58000019` and from the ADG blocks `581/582/583xxxxx`, which will not be
used now that ADG has stopped.

## 5. Decision rules for the manuscript

1. **Gating verified as material.** Requires all of:
   - Stage 2 passes for G1;
   - P1's lower bound is ≥ 2 (with `mean(growth_U1) > 0`);
   - P2's lower bound is > 0.

   Then the manuscript may state that, on this design, disagreement gating (credited to DISCERN)
   multiplied realised evidence growth by the **measured** factor and raised scarce-budget
   detection by the **measured** difference. The prior ungated allocation conclusions must be
   qualified accordingly.
2. **Prediction verified.** Requires (1), plus the measured `R` in each of the four budget cells
   lying within a factor of 2 of the G1 prediction (`0.5× ≤ measured/predicted ≤ 2×`). Then the
   manuscript may say the analytic pre-screen anticipated the effect. Otherwise report the
   mismatch, and never cite the predicted 5–18× range as a result.
3. **Partial.** P1 passes and P2 fails, or the reverse: report both endpoints with their
   uncertainty. Claim only the endpoint that passed.
4. **Not verified.** Both fail, or G1 fails Stage 2: report this as a negative result. Remove any
   gating-gain statement from the manuscript draft. Record why the analytic prediction failed
   (expected candidates: harm mechanism, budget exhaustion, proxy updating).
5. **Harmful-adaptation stress.** Descriptive only. If fixed gating exhausts the cap early while
   paced gating does not, report that as a deployment caveat for gating, consistent with DISCERN's
   own drift limitation.

No arm, budget, stake, or threshold may be changed after Stage 3 outputs exist. Any follow-up
needs a new protocol.

## 6. Implementation and test checklist

**Runner** (`gated_monitor_comparison.py`)
- [ ] Reuse `_generate`, the hard-budget policy and proxy fits, tariffs, and cap logic.
- [ ] Gated arms skip query draws on agreements, return `-epsilon` exactly there, and never charge
      a tariff for them.
- [ ] Online pacing uses only past actions and tariffs, seeded from validation.
- [ ] `PredictableBoundMeanEProcess` for paced fixed-stake arms. A plug-in empirical-Bernstein
      adaptation for G3, with the predictable affine map `(Hhat + B_t)/(2B_t)`, documented as an
      adaptation.
- [ ] Record per-stream: crossings and time, per-stake post-onset log-wealth on the common prefix,
      labels, dollars, cap status, processed horizon, `q_t` summary, realised disagreement before
      and after onset, and pre-alarm excess loss.
- [ ] No event traces by default. Evaluator-only fields must stay out of learner structures.

**Tests** (`tests/test_gated_monitor_comparison.py`)
- [ ] Agreement events: zero labels, zero spend, increment `-epsilon`.
- [ ] Pacing never reads labels: perturbing outcomes leaves `q_t` unchanged.
- [ ] `|Hhat_t| <= B_t` on all events.
- [ ] Exact conditional-mean identity on enumerated cases.
- [ ] At `q = 1`, the gated HT increments equal full feedback restricted to disagreements.
- [ ] Hard cap never exceeded.
- [ ] U1 and U2 match the existing hard-budget runner on one fixed seed (byte-identical crossing
      times).
- [ ] Oracle perturbation does not change learner outputs.

**Analysis** (`scripts/analyze_gated_monitor_comparison.py`)
- [ ] P1/P2 statistics as registered.
- [ ] Per-cell secondary tables, with exact binomial intervals for crossings.
- [ ] The predicted-versus-measured table.
- [ ] Manifest with source, output, and protocol hashes, the Git HEAD, hardware, and runtime.

**Reporting**
- [ ] Write `gated_vs_ungated_monitor_comparison_results.md`, including failures.
- [ ] Add a research-log entry with a continue/pivot/stop assessment.
- [ ] Update the claim-to-evidence map only after rules 1–4 are applied.
- [ ] No figures are planned. Any figure must be made with PaperBanana from validated outputs.

## 7. Compute and limits

**Compute estimate (unmeasured; the smoke run replaces it).** The mandatory-panel expansion
and all-budget null calibration were registered before freeze, with no new outcomes inspected.
- Stage 3: 100 seeds × 4 scenarios × 4 budgets × 7–8 arms, about 12,000 stream-arms of 3,200
  events.
- Stage 2: 2 scenarios × 4 budgets × 2,000 seeds = 16,000 shared paths, with the panel/engine
  rows above replayed on each path. U2 is present only at 0.20. Matched engine replays add CPU
  work without additional labels or generated streams.
- Use CUDA generation and parallel workers. CPU-only execution may take hours.

**Limits.**
- One synthetic family with binary costs and a fixed 9% disagreement rate (except the stress
  scenario).
- Immediate feedback only. Delays and the prefix argument are out of scope here.
- Gating's advantage scales with `1/rho`, so real tasks with frequent disagreement will gain less.
- The G3 arm is an adaptation, not a DISCERN reproduction.
- This study supports a benchmark finding, not a new method or a novelty claim.

## 8. Reproduction (to be finalised at freeze)

```powershell
uv run --no-sync pytest tests/test_gated_monitor_comparison.py -q
uv run --no-sync python scripts/run_gated_monitor_comparison.py --stage fidelity
uv run --no-sync python scripts/run_gated_monitor_comparison.py --stage smoke
uv run --no-sync python scripts/run_gated_monitor_comparison.py --stage null
uv run --no-sync python scripts/run_gated_monitor_comparison.py --stage compare
uv run --no-sync python scripts/analyze_gated_monitor_comparison.py
```
