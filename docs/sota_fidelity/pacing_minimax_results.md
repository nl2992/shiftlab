# Paper 3 pacing minimax screen — results

Protocol: [pacing_minimax_protocol.md](pacing_minimax_protocol.md), locked in `4d0099f9` before the run.
Machine-readable: [pacing_minimax_results.json](pacing_minimax_results.json); raw arrays gitignored at
`outputs/sota_fidelity/pacing_minimax/`. Calibrated threshold A = 1785.3 (200,000 null sequences).
**Theory-first feasibility screen; not confirmatory. Independent check of the code and of Lemma A's
proof has NOT been done yet.**

## Verdict under the locked rule (d = 100): STOP

| Pacer | Worst-case regret (onset) | Gain vs U (95% bootstrap) | Onset-avg regret | Null rate / Wilson hi |
|---|---|---|---|---|
| U uniform | 60.65 (0) | — | 50.01 | 0.037 / 0.051 |
| TU truncated uniform | 57.00 (0) | +6.0% [+3.9, +6.9] | 47.87 | 0.043 / 0.057 |
| BURST_5 (r=.5, h=log 10; dev-selected) | 58.08 (1200) | +4.2% [+1.7, +7.5] | 42.25 | 0.059 / 0.075 |

Neither clears the 10% bar. At d = 10 (descriptive): TU +3.5%, dev-selected BURST_2 +5.3%. All 22
pacer-delay cells pass the null bound (Wilson hi <= 0.078 < 0.0936). Other burst configurations lose
up to 57% in worst case.

## Reading

1. **Lemma A's prediction held.** It predicted roughly 6% worst-case gain for truncation (G·m·τ/B
   with m inferred from W(U): about 7%); observed 6.0%. Truncation only stops buying labels that
   release too late to repay a switch: benchmark hygiene, not a method.
2. **Evidence-gated bursting trades late onsets for early ones.** BURST_5 cuts regret by up to 19
   for onsets 300–800 (15% lower onset-average regret), but false starts spend the budget, so its
   miss rate at onset 1200 is 0.69 vs 0.24 for U and its worst case moves to late onsets. This is
   the published DE-CuSum / CuSum-AC average-case effect (prior_art/README.md lever a) and the same
   early-vs-late trade seen in track B (M1); it does not improve the minimax target.
3. **Uniform is near-minimax here.** Within this screen no pacer improves the worst case over change
   time by more than about 6%, consistent with the stop rule set in the track B review.

## Lemma A (proof sketch, to be checked)

Fluid model: promotion once m post-change labels are released; schedule N(t), N(T) <= B. If the
worst-case regret is W, every onset ν with G(T−ν) − c_s > W must collect m requests in
[ν, ν + w] with w = W/G − d. Disjoint windows of length w tile [0, T − d − c_s/G], so
m·(T−τ)/w <= B with τ = d + c_s/G, giving W >= G(m(T−τ)/B + d) up to integer rounding; constant-rate
pacing on [0, T−τ] attains it. Uniform on [0, T] gives G(mT/B + d).

## Continue / pivot / stop

Stop the Paper 3 pacing target as a method contribution. Keep Lemma A (truncate pacing by
d + c_s/G) as a baseline-hygiene note and the burst early/late trade as benchmark content.

## Reproduce

See the protocol's commands (`calibrate`, `tune`, `test`, `analyze`).
