# 16 Real-data results: certified switching on 7 chronological streams (B3)

Protocol: `protocols/B3-real-data-certified-switching.md`. Registered at `19f1090`,
sha256 `b17b5a31…ba3a`, before any locked window was read.

The policy code is `b1_certified_switching.py` at `041bc26`, unchanged. The model pairs reproduce
the audit's dev-window statistics exactly (maximum difference 0.0; `results/b3/pairs_check.json`).
The run executed once as a detached process.

The orchestrator recomputed every number below from the per-episode JSONL. Episode CIs use 2,000
bootstrap resamples. The recomputation agrees with `results/b3/summary.json`.

## Decision: **SUCCESS** (registered rule)

- WIN on 3 streams: weather, spam, rialto.
- SAFE on 7 of 7 streams.

## Primary setting (B = 200 labels per 2,000-event episode, c_q = 0.05, c_s = 5)

Mean net cost per episode, averaged over 100 query seeds.

| Stream | K | Never (P0) | Always challenger (P1, hindsight) | Incumbent alarm (P2) | **Certified (P3b)** | Batch test (P6) | P3b − P0 [95% CI] | WIN | SAFE | Headroom captured |
|---|---|---|---|---|---|---|---|---|---|---|
| weather | 3† | 504.0 | 430.3 | 511.3 | **475.8** | 465.6 | −28.2 [−29.3, −27.2] | yes | yes | 38% |
| spam | 1† | 849.0 | 195.0 | 792.2 | **254.1** | 315.9 | −594.9 [−597.8, −591.6] | yes | yes | 91% |
| rialto | 16 | 202.1 | 61.2 | 211.8 | **103.7** | 122.9 | −98.3 [−117.0, −78.5] | yes | yes | 70% |
| airlines | 50 | 776.8 | 859.3 | 786.7 | 781.4 | 775.4 | +4.6 [−0.0, +8.3] | no | yes | — (challenger worse) |
| bank | 8 | 419.4 | 1202.4 | 429.1 | 428.2 | 422.1 | +8.8 [+6.2, +10.2] | no | yes | — (challenger much worse) |
| elec2 ‡ | 4† | 389.5 | 386.5 | 399.3 | 397.6 | 388.0 | +8.1 [+7.8, +8.4] | no | yes | not captured |
| criteo click ‡ | 50 | 693.9 | 671.8 | 703.6 | 699.2 | 692.1 | +5.3 [+3.9, +6.2] | no | yes | not captured |

† K < 5 episodes, so the CI is a seed-level bootstrap and the result is LOW-POWER. The CI
reflects query randomness only, not variation across data.
‡ Partly exposed stream (see `15_*.md`).

## Sensitivity (reported, not used for the decision)

P3b relative to never-switch:

| Setting | weather | spam | rialto | airlines | bank | elec2 | criteo |
|---|---|---|---|---|---|---|---|
| c_s = 20 | −2.6% | −68.3% | −41.2% | +0.8% | +2.1% | +4.0% | +1.1% |
| B = 400 | −6.5% | −70.3% | −49.1% | +1.1% | +4.2% | +2.3% | +0.8% |

These are the same qualitative conclusions as the primary setting. P3b's promotion rates were
1.00 on weather, spam and rialto, 0.12 on airlines, 0.01 on bank, 0.50 on elec2 and 0.18 on
criteo. It never rolled back.

## Fair reading

**When the new model really is better (spam, rialto, weather),** certified switching recovers
most of the available gain:

- Cost reductions are 70%, 49% and 6% relative to never switching.
- That captures 91%, 70% and 38% of what a hindsight "always challenger" choice would have
  gained.
- It does this without knowing in advance which model is better.

**When the new model is worse (bank, airlines),** certified switching does what insurance should
do:

- Blindly deploying the challenger would cost +187% on bank and +10.6% on airlines.
- Certified switching costs +2.1% and +0.6%. That is essentially the label spend.
- On bank it almost never promoted the bad challenger (1% of runs).

**It beats incumbent-alarm switching on all 7 streams** (point estimates). The programme's
central failure pattern holds on real data: an alarm on the incumbent is not evidence that the
challenger is better.

**Where it did not help (elec2, criteo).** The challenger's advantage was small:

| Stream | Challenger advantage (hindsight) | Disagreement rate |
|---|---|---|
| elec2 | about 0.8% | about 5% |
| criteo | 3.2% | 6.6% |

With roughly 100–130 disagreements per 2,000-event episode, certification is too slow to pay
for its labels. The cost is small (+2–5%), but these are honest non-wins.

**Against the fixed-sample batch test (P6):**

- P3b is clearly better on spam (254 versus 316) and rialto (104 versus 123).
- P6 is slightly cheaper on the other five streams, because it stops buying labels after 50.
- P6's error control assumes exchangeable outcomes. P3b's e-process guarantee does not need
  that assumption.

## Limits

- **Episode counts.** Three of the WIN streams have few episodes: weather 3, spam 1. Their CIs
  capture query randomness only, and spam's result is a single 2,000-event episode. The
  strongest evidence comes from rialto (16 episodes) and from the two large insurance cases
  (airlines 50, bank 8).
- **Time order.**
  - spam and bank use the file order as time.
  - airlines' order is inferred.
  - rialto uses image-capture order.
- **Imposed parameters.** Delays and costs are imposed, not taken from real release contracts.
- **Pair selection.** Pairs were selected on dev windows by a fixed rule. Other pairs could
  behave differently.
- **Licence.** The vlosing-repo streams (weather, spam, rialto) have no declared licence, so
  their use is research-only.

## Artifacts

`results/b3/` contains:

- `<stream>.jsonl`, one row per episode and setting, with per-seed costs;
- `summary.json`;
- `provenance.json`;
- `pairs_check.json`;
- `losses/*.npz`, the episode loss arrays;
- `SHA256SUMS.txt`.

The runner is `scripts/promising_directions/b3_real_data.py`. Tests are in
`tests/promising_directions/test_b3_real_data.py`.

The `run_stderr.log` traceback is harmless: joblib's CPU-count probe calls `wmic`, which
Windows 11 no longer ships. The run completed normally.
