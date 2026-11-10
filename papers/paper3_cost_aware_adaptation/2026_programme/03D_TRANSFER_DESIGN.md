# 03D Cross-stream transfer of economic switching/acquisition parameters (workstream D) - design

Status: EXPLORATORY. Written 2026-11-09 before any evaluation run. Owner: transfer lead D.
Every stream used here was already exposed by Papers 1/2 (see 02_DATASET_INVENTORY.csv); nothing
below is confirmatory evidence. Paper 1 (EQSDp / Wald switcher + late-label cutoff) is the *base
policy class* and a comparator; it is not claimed here. The claim at stake is only: can the
*parameters* of that class be chosen for an unseen stream from causal information better than
strong baselines at matched supervision cost?

## 1. Task
Base policy class (ported, see Sec. 8): discounted Wald/LCB economic switcher with budget-paced,
disagreement-gated acquisition and a hard late-label cutoff. Parameter vector
theta = (lambda, gamma, H):
- lambda in {0.85, 0.90, 0.95, 0.97, 0.98, 0.99} (evidence discount)
- gamma in {0.10, 0.20, 0.30, 0.45} (Wald hurdle quantile)
- H in {0, 500, 900, 1100, 1300, 1500} (no label purchase when t + delay > T - H)
144 configurations. Contract (Paper 1 C4): T = 2000 events per episode, budget B = 200 labels,
label price c_q = 0.05, switch cost c_s = 5 (primary scenario); a second cost scenario
(c_q = 0.15, c_s = 15) is a cost-shift check. Cost of an episode:
J = sum_t loss_t(deployed) + c_q * labels + c_s * switches (per episode, mean over episodes).

For an unseen stream the *selector* chooses theta from causal information only and then runs it on
the stream's evaluation window. Quantity of interest: J of the chosen theta, not parameter error.

## 2. Causal information, windows and what is charged
Each stream is a chronological list of K episodes. Early window = the first max(2, ceil(0.3 K))
episodes; evaluation window = the rest (min 6 episodes for eligibility, so >= 4 evaluation episodes).
- The task embedding is computed only from the early window, from the *operational log of the
  reference base policy* wald(lambda .97, gamma .2, H 0) run on those episodes: released paired
  outcomes of the labels it purchased (<= B per episode), its label timestamps, the prediction-side
  disagreement indicator for every event (observable without labels), delay, costs, horizon.
  The evaluation window is never read by any selector (leakage tests in tests/paper3/transfer).
- Recommenders train only on streams outside the held-out fold (+ synthetic streams). Targets are
  the economic cost tables J(stream-episode-window, theta) of those training streams.
  Primary training scope = all episodes of training streams; sensitivity = their early windows
  only (guards against calendar-time overlap between different-fold streams; calendar alignment
  of streams is not verified and is a stated limitation).
- Supervision accounting. The early-window operational log costs nothing beyond what the base
  policy already buys (<= B labels per early episode, c_q each) and is shared by every method.
  Methods that need *counterfactual* replay of other thetas on the early window (per-stream
  tuning, Hedge, hierarchical pooling, kNN-on-J) require the paired outcome of all events in the
  replayed episodes; they are charged n_early * T * c_q extra labels (reported), which is a
  conservative (generous-to-baseline) accounting: per-stream tuning is a *more informed* baseline
  than the transfer recommenders, which only use the operational log.

## 3. Splits
- Fold unit = domain family. Real fold set (development): `311` (19 city 311 streams; geographic
  blocks of one family are NOT a family holdout - the whole family leaves together), `traffic_collision`
  (3), `aviation` (2), `uci_sensor` (5), `tabular_misc` (bank, elec2, rialto, weather: singleton
  domains pooled into one fold; heterogeneous, explicitly not a single domain family).
- Synthetic families S1..S5 (regime/persistence/disagreement/autocorrelation generators in
  `synth.py`; evaluator-side truth never given to selectors) are used as extra training data for
  real folds and are held out one-at-a-time for the synthetic folds. Headline numbers are
  real folds only.
- Chronological split inside every stream (Sec. 2) for embedding vs evaluation.
- Time-leak guard: a held-out stream's early window and evaluation window are never in the
  recommender's training set; its own early-window statistics enter only through its embedding.

## 4. Sealed final-test group (NOT opened during development)
Group `civic_records_sealed` = families `animal_shelter` (austin_animal, dallas_animal_shelter),
`permits` (sf_building_permits), `crime` (la_crime). Four streams from `data/c4_sealed`, exposed to
Papers 1/2 but not to this workstream.
group_sha256 (names + array-content sha256 per stream) =
`f37dc40f3bdea96f1e2e54baa212c8a2391fec1ca37f0368108bd8504c7ae460`
(per-stream hashes in outputs/paper3/transfer/seal_hash.json; code: `streams.seal_hash`).
Recorded before any run. `streams.load` raises `SealedAccessError` for these names; no J,
embedding or loss statistic of them is computed in development; opening is the PI's decision.
Disclosure: while surveying the caches for the inventory I printed array shapes and marginal
disagreement/loss rates of *all* c4_sealed files including the sealed ones (descriptive, before any
policy was run); these were not used in any design choice.

## 5. Baselines (D0), all at the same causal information or higher
1. Global fixed: theta minimising mean J (equal stream weight) over training streams.
2. Train-domain empirical best: per training family best theta; test stream uses the family whose
   embedding centroid is nearest (nearest-family lookup; the held-out family itself is unavailable).
3. Per-stream tuning on its own early window: argmin_theta of replayed early-window J (144
   configs; labels charged, wall-clock measured). Strongest-information baseline.
4. Recent-window / ESS adaptation: IN_HOUSE_HEURISTIC; lambda from the effective sample size implied
   by lag-1 autocorrelation of released outcomes, lambda = 1 - 1/(20 (1+rho)/(1-rho)) snapped to grid,
   (gamma, H) = global fixed.
5. Online Hedge over the 144 theta (expert tracking), full-information per-episode feedback
   (charged), starting from the stream's first episode, evaluated as the expected J of the Hedge
   mixture over the evaluation window.
6. Bayesian hierarchical pooling: empirical-Bayes normal model per theta; early-window mean
   improvement over the reference theta shrunk toward the training-stream mean with variances
   estimated by moments on training streams (labels charged).
7. CUSUM meta-recommendation analogue (Lopes et al. 2025; ADAPTER of the idea, not their code):
   standardised meta-features of the early window -> k=3 nearest training streams -> theta
   minimising the neighbours' mean J.
Labels: IN_HOUSE_HEURISTIC / DOCUMENTED_ADAPTER; none is a native-source reproduction.

## 6. Methods under test
- D1: causal task embedding (about 12 features, Sec. 2; released-loss statistics, disagreement
  rate, lag-1 autocorrelation of released outcomes, delay histogram summary, costs, horizon) ->
  ridge predictor of the cost curve J(theta | phi), argmin.
- D2: GBDT (sklearn HistGradientBoosting on (phi, theta) rows) and a small MLP policy over the 144
  thetas trained with the *economic* objective (expected J under the softmax over thetas) -
  decision-focused. Training samples are windows (stream, sub-window of early-length episodes,
  cost scenario) whose target J is measured on the following episodes, so a stream contributes many
  chronological samples.
- D3 (GPU): GRU sequential controller over the masked observable history, choosing query and
  switch every event, trained by REINFORCE with an economic reward on synthetic + training-fold
  streams, hard budget reservation (pending labels count at request time; the mask makes
  over-budget requests impossible), compared with an equally sized generic GRU (same hidden width,
  raw observables only, no structured evidence features, budget handled by simulator refusal).
  No validity guarantee is claimed for any D method (no false-promotion gate is evaluated).
  Bounded runs (<30 min each), checkpointed, with wall-clock/peak-memory profiling.
- D4: out-of-distribution fallback: if the held-out embedding's Mahalanobis distance to the
  training embeddings exceeds the 95th percentile of leave-one-out training distances, use the
  global fixed theta. Negative transfer measured as the per-family worst-case and per-stream harm
  of each method relative to global fixed and to per-stream tuning.

## 7. Evaluation
- Per held-out stream: mean J over evaluation episodes for the chosen theta (2 seeds averaged,
  common random numbers across thetas).
- Paired Delta J = J(method) - J(baseline) per stream; aggregate by equal-stream mean and by
  equal-family mean; 95% stream-cluster bootstrap (2000 resamples); family-cluster bootstrap for
  the cross-family contrast; per-family breakdown with within-family stream bootstrap.
- Strongest baselines: per-stream tuning and global fixed. Also reported: hindsight best theta on
  the evaluation window (unattainable diagnostic, labelled), labels used, configs tried,
  wall-clock.
- Effect grading follows the user standard (substantial >= 10%, meaningful 3-10% with CI excluding
  zero, small 1-3%, negligible < 1%); interpretive, not a gate.
- Headline = real dev folds. Synthetic folds and the cost-shift scenario are secondary.

## 8. Provenance of the ported policy
Re-implemented (vectorised over configurations, common random numbers) from
`research/paper1-eqsdp-foundation-2026-11-08@5bda4e73:scripts/qsg_methods_search/eqs_d.py` (EQSD
belief/switch rule), `.../hurdles.py` (WaldLCB quantile with continuity correction),
`.../scripts/paper1_eqsdp/stage1_policies.py` (`Stage1WaldStop`: hard label stop
`t + delay <= T - H`, paced acquisition arithmetic), and
`.../scripts/promising_directions/sota/competitors/controls.py` (`PacedDisagreementAcquisition`)
plus `.../sota/simulator.py` (event order: release, deploy, acquire; delay >= 1). Simplification:
the policy sees the disagreement indicator as `l0 != l1` from the stored loss pair (the stored
caches carry no model predictions). Validation of the port against recorded Paper 1 episode
costs is reported in D_RESULTS.md.
