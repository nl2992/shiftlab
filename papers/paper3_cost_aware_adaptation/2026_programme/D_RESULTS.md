# D results: cross-stream transfer of economic switcher parameters (EXPLORATORY, development families only)

Design: `03D_TRANSFER_DESIGN.md`. Sealed group `civic_records_sealed` (animal_shelter, permits, crime; 4 streams;
group_sha256 `f37dc40f3bdea96f1e2e54baa212c8a2391fec1ca37f0368108bd8504c7ae460`) was NOT opened: no loss, J or embedding was computed
for it. All 33 dev streams were exposed by Papers 1/2. Full tables: `D_RESULTS_tables_d0d2.md` (copy of
`outputs/paper3/transfer/analysis.md`), `outputs/paper3/transfer/analysis_d3.md`, raw rows `d0d2_results.csv`,
`d3_results_main.csv`; every run is in `ledger/transfer.jsonl`. Code state: uncommitted worktree, base 8af33afe.

## Port check
Vectorised Wald/LCB + paced acquisition + cutoff vs recorded Paper 1 `wald_l0.97_g0.2` episode costs (same episodes):
sf_311 449.1 vs 450.0, kc_311 597.0 vs 593.2, dc_311 394.1 vs 393.4; per-episode correlation 0.98. Labels used are ~4%
lower in the port (190 vs 198-200): pacer details differ slightly. Disagreement is `l0 != l1` (caches lack predictions).

## D0/D1/D2/D4 (real dev folds, 33 streams, primary scenario, train scope = all episodes of other folds + synthetic)
Delta J = J(method) - J(baseline) on the evaluation window (later 70% of episodes); negative = method better.
Stream-cluster bootstrap 95% CI, 2000 resamples. Mean J: per-stream tuned 428.5, global fixed 429.1, hindsight best
424.3 (unattainable), never-switch 522.6.

| method | vs per-stream tuned | vs global fixed | streams worse than global | extra labels/stream |
|---|---|---|---|---|
| D1 ridge | +4.03 [+0.17,+7.53] (+0.9%) | +3.43 [+1.24,+5.68] | 24/33 | 0 |
| D2 GBDT | +2.64 [+0.03,+5.62] | +2.04 [+0.04,+4.24] | 21/33 | 0 |
| D2 MLP (economic loss) | +2.94 [+0.82,+5.41] | +2.34 [+0.06,+5.46] | 16/33 | 0 |
| D2 MLP + OOD fallback (D4) | +1.65 [-1.57,+4.84] | +1.06 [-0.18,+2.56] | 14/33 | 0 |
| global fixed | +0.59 [-2.41,+3.28] | 0 | - | 0 |
| nearest-family best | +0.35 [-2.64,+2.85] | -0.24 [-0.64,+0.09] | 6/33 | 0 |
| kNN meta (CUSUM analogue) | +0.69 [-2.36,+3.77] | +0.09 [-0.95,+1.24] | 14/33 | 0 |
| ESS heuristic | +1.79 [+0.06,+4.09] | +1.19 [-0.09,+3.51] | 9/33 | 0 |
| Hedge (expert tracking) | +2.76 [+1.18,+4.19] | +2.16 [-0.23,+4.38] | 27/33 | 122,848 |
| hierarchical pooling | -0.21 [-0.57,+0.07] | -0.80 [-3.45,+2.45] | 10/33 | 38,000 |
| per-stream tuned | 0 | -0.59 [-3.37,+2.29] | 9/33 | 38,000 |

Per family (vs global fixed, mean over streams [stream CI]); D2 MLP: 311 +1.6[+0.1,+3.7], aviation +1.1[-0.5,+2.8],
tabular_misc -0.1[-1.0,+0.6], traffic -1.3[-1.9,-0.7], uci_sensor +9.7[-1.9,+26.3]. D1 ridge worst family
(tabular_misc) +11.0 vs global, +12.6 vs per-stream tuned. Family-cluster CIs are wide (5 families).
OOD (Mahalanobis) fallback triggered on appliances, bank, elec2 and cut the worst-family harm of MLP/GBDT/ridge to
+3.5/+4.9/+10.4 vs per-stream tuned; it does not make any recommender beat global fixed.
Sensitivity: train scope = early windows only (no calendar overlap): no recommender beats global/per-stream tuning
(D1+ood -0.5 [-3.4,+1.8] vs per-stream tuned, a tie). Cost-shift scenario (cs 15, cq .15): the reference log from
cs=5 makes the cost features OOD, D4 falls back to global fixed on all streams (+0.0); un-gated recommenders are
+1.7 to +2.4 worse than per-stream tuned. Hedge is worst (+7.4).
Synthetic held-out families (30 streams, secondary): recommenders DO beat global fixed: MLP -11.7 [-19.0,-5.3]
(-2.3%), ridge -9.7 [-16.5,-3.0], GBDT -5.6; pooling -9.2; versus per-stream tuned MLP +2.3 [-0.5,+5.0] (tie).
The synthetic families differ in persistence/regime, so parameter heterogeneity exists there; on real streams the
optimum parameter varies little (global fixed is within 4.8 of hindsight best on average, 1.1%).

## D3 (GPU GRU controller; bounded, 3 folds, 7 min training each, REINFORCE, 27 held-out streams, <=30 eval episodes)
| variant | dJ vs global fixed | vs per-stream tuned | vs reference Wald (l.97,g.2) |
|---|---|---|---|
| structured (evidence features + hard reservation cap + Wald-gain skip) | +2.0 [-3.8,+6.4] | +3.5 [+1.4,+5.3] | -0.3 [-1.3,+0.8] |
| generic GRU (raw observables, no reservation) | +123.9 [+70,+190] | +125.4 [+70,+190] | +121.6 |
structured - generic: -121.9 [-189.7,-65.3]. Training reward barely moved for structured (488->486 on 311) and the
policy stayed ~ the Wald-gain follower it was initialised as; generic improved (646->552) but stayed far worse than any
fixed rule. Only 46-91 updates fit in 7 min (about 8-9 s/rollout of 2000 steps x 768 episodes; GPU 12-16% utilised,
launch-bound). Peak CUDA memory 7.9-8.0 GB of 8 GB (caching allocator; rollout buffers 768x2000xF). Checkpoints in
`outputs/paper3/transfer/ckpt`. The generic/structured gap measures the value of the encoded Wald structure, not of
learning. No validity claim is made. Under-trained: not evidence that a longer-trained controller fails.

## Honest verdict
No attributable cross-family gain on real streams. Every learned recommender (D1, D2, D3) is worse than global fixed
and than per-stream tuning on average (grade: negligible to small, +0.5% to +1.0%, CIs mostly exclude 0 on the harm
side); the only wins are single-family cases (traffic_collision, -1.3 vs global, 3 streams) and synthetic families.
The strongest baselines are global fixed (zero extra supervision) and per-stream tuning/pooling, which are tied;
labelled-replay methods differ from global fixed by <=0.2%. Interpretation: within this grid the optimum is flat
across real streams (hindsight-vs-global gap 1.1%), so there is little transferable headroom; the earlier
"synthetic-tuned hyperparameters transfer poorly" failure is consistent with this. Negative transfer is real and
measurable (worst-family harm +10 to +12 for ridge, +3.5 to +4.9 for MLP/GBDT with OOD fallback). Recommendation:
stop/pivot D as a headline; keep as a negative-transfer result plus the OOD-fallback guard. A longer-trained D3 and
a wider parameter space (where hindsight gap is larger) are the only untested levers.

Limitations: only 33 dev streams / 5 folds (one fold is a pooled heterogeneous bin); all streams already exposed;
model/recommender defaults were fixed before seeing results but dev folds were inspected, so no number here is
confirmatory; calendar-time alignment between streams unverified; D3 evaluation capped at 30 episodes/stream and
compared to table values from a different RNG; the synthetic generators are my own; per-stream tuning is charged
38,000 labels per stream (conservative, more informed than the recommenders).
