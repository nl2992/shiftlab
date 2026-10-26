# Fixed-delay PPI predictable uniform-mixture development grid

**Status: frozen before execution; development screen only.** The prior dose/onset grid found that evidence-directed allocation saves labels but can lose power for early, strong harm. This screen tests a direct, established-design remedy: convexly mix its query propensity with the fixed uniform rate. It does not claim a new sequential test.

## Mathematical specification

Let `q_e,t` be the existing evidence-directed propensity, predictable from learner-visible history before the current label is queried, and let `q_u = budget_rate = 0.20`. For fixed `lambda` in `{0.25, 0.50, 0.75}`, use

`q_t(lambda) = (1 - lambda) q_e,t + lambda q_u`.

The endpoints are the existing evidence-directed rule (`lambda=0`) and uniform querying. Each `q_t` remains predictable and lies in the same registered support `[q_min, q_max]`. The existing PPI contribution uses the realized propensity: `G_t = h_t + I_t (Z_t - m_t) / q_t`, with eventwise absolute bound `B_t = (M + epsilon) (2/q_t - 1)` under the same bounded-outcome and conditional-mean assumptions. Thus the sampler changes; the monitor's validity conditions and bound construction do not. The convex blend is fixed before the stream and does not use evaluator truth.

## Design

- Compare the pure evidence-directed rule, fixed blends 0.25/0.50/0.75, and uniform querying on the same generated streams and query uniforms.
- Cross paired-cost harm shifts 0.10/0.20/0.30 with onset fractions 0.25/0.50/0.75 over 2,400 target events. Use 100 matched seed clusters per cell, seeds 20450000–20450099, fixed 12-event feedback delay, 1,200 source events, alpha 0.05, epsilon 0.05, and a 480-label hard cap.
- Generate data on CUDA and replay streams in parallel across four CPU workers. Continue after alarms and drain all delayed labels.
- Primary development summaries are the equal-weight macro paired detection differences versus uniform for each fixed blend, with seed-cluster bootstrap intervals. Also report cellwise detection, label counts, pre-onset alarms, delays, cap and event-prefix checks. This is a selection screen: cellwise intervals are descriptive and no confirmatory claim is permitted.

## Nomination rule and limitations

A blend is nominated for a new independent null calibration and disjoint harm confirmation only if its macro detection interval is strictly above zero, it uses no more labels than uniform on average, and no cell's detection point estimate is worse than uniform by more than five percentage points. The three blend contrasts are a development family; the report must disclose all tried weights, the selection rule, and that inference is post-selection. If none passes, do not confirm the grid winner. A passing development screen still does not establish validity: each selected sampler needs independent null calibration under the registered conditional-mean null, followed by disjoint harm confirmation.

No visual is planned. Use PaperBanana for any future research visual and verify it against saved metrics.

## Reproduction

```powershell
uv run shiftlab-dive-delayed-ppi-uniform-mixture-grid --device cuda --output-dir outputs/delayed_ppi_uniform_mixture_grid_100
```
