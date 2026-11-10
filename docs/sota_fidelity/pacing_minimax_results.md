# Paper 3 pacing minimax screen — results

Protocol: [pacing_minimax_protocol.md](pacing_minimax_protocol.md), locked in `4d0099f9` before the run.
Machine-readable: [pacing_minimax_results.json](pacing_minimax_results.json); raw arrays gitignored at
`outputs/sota_fidelity/pacing_minimax/`. Calibrated threshold A = 1785.3 (200,000 null sequences).
**Theory-first feasibility screen; not confirmatory.** Independent check (2026-11-10):
[PACING_CHECK.md](PACING_CHECK.md). Code matches the protocol, all numbers reproduce exactly, and the
STOP verdict stands; **Lemma A as originally stated is wrong** (corrected below).

## Verdict under the locked rule (d = 100): STOP

| Pacer | Worst-case regret (onset) | Gain vs U (95% bootstrap) | Onset-avg regret | Null rate / Wilson hi |
|---|---|---|---|---|
| U uniform | 60.65 (0) | — | 50.01 | 0.037 / 0.051 |
| TU truncated uniform | 57.00 (0) | +6.0% [+3.9, +6.9] | 47.87 | 0.043 / 0.057 |
| BURST_5 (r=.5, h=log 10; dev-selected) | 58.08 (1200) | +4.2% [+1.7, +7.5] | 42.25 | 0.059 / 0.075 |

Neither clears the 10% bar. At d = 10 (descriptive): TU +3.5%, dev-selected BURST_2 +5.3%. All 22
pacer-delay cells pass the null bound (Wilson hi <= 0.078 < 0.0936). Other burst configurations lose
up to 34% in worst case at d = 100 (up to 57% at d = 10).

## Reading

1. **Truncation gives a small, explained gain.** Observed 6.0%. The protocol's prediction
   (G·m·τ/B) matches only after m is fitted from W(U) (5.8–7.1% for m ≈ 54–66), so it is a loose
   consistency check, not a sharp prediction. Truncation only stops buying labels that release too
   late to repay a switch: benchmark hygiene, not a method.
2. **Evidence-gated bursting trades late onsets for early ones.** BURST_5 cuts regret by up to 19
   for onsets 300–800 (15% lower onset-average regret), but false starts spend the budget, so its
   miss rate at onset 1200 is 0.69 vs 0.24 for U and its worst case moves to late onsets. This is
   the published DE-CuSum / CuSum-AC average-case effect (prior_art/README.md lever a) and the same
   early-vs-late trade seen in track B (M1); it does not improve the minimax target.
3. **Uniform is near-minimax only within the tested family** (U, TU, evidence-gated BURST). The
   check found that periodic rate-capped bursts, which were not tested, beat constant-rate pacing
   by about 8–10% in Lemma A's own fluid model (see below). Whether that survives a noisy detector is
   untested. The repo's earlier paced-epoch screen (`docs/exhaustive_evaluation/PACED_EPOCHS_REPORT.md`)
   tested evidence resets with quota pacing, not scheduled bursts at the rate cap.

## Lemma A (corrected after the independent check)

**Original statement (protocol) is wrong.** It claimed the minimax worst-case regret over
deterministic schedules is G(m(T−τ)/B + d), attained by constant-rate pacing on [0, T−τ].

- The tiling step gives m·⌊(T−τ)/w⌋ <= B, not m(T−τ)/w <= B. The correct deterministic lower bound
  is W >= G((T−τ)/(⌊B/m⌋+1) + d), τ = d + c_s/G. Rounding matters here because B/m ≈ 3.
- Constant-rate pacing does not attain it. In the fluid model with m = 66, end-loaded periodic bursts
  at the rate cap (3 bursts, period 542) give W = 51.4 vs 56.5 for constant rate; at m = 54 they do
  not win (50.2 vs 47.7), so the effect is sensitive to integer effects.
- Randomised-phase periodic bursts give worst-case expected regret 46.1 (m = 54) and 51.9 (m = 66),
  so the deterministic restriction is material: every tested pacer is randomised.
- What survives: labels that release after T − τ cannot pay for a switch (the truncation hygiene),
  and uniform pacing on [0, T] has worst case G(mT/B + d) in the fluid model. The lemma ignores
  label cost.

## Continue / pivot / stop

Stop the tested pacing family as a method contribution (locked rule). Keep truncation by
d + c_s/G as a baseline-hygiene note and the evidence-gated early/late trade as benchmark content.
**One untested class remains:** scheduled periodic bursts at the rate cap (deterministic or
random-phase), which beat constant-rate pacing in the fluid model by about 8–10%. Testing it needs
a new locked protocol and the user's approval. Prior art to check first: optimal sampling-interval
recursions (Geng–Bayraktar–Lai) and duty-cycled sensing in quickest detection.

## Reproduce

See the protocol's commands (`calibrate`, `tune`, `test`, `analyze`).
