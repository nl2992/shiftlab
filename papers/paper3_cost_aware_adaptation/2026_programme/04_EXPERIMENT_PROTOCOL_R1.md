# Registration R1: payback certificates on real paired-loss streams

Registered 2026-11-10 before `scripts/paper3/payback/run_real.py` exists or any certificate is
run on real data. Tier: **exploratory real-data evidence**. Every c4 stream was used before by
Papers 1/2, and the four `civic_records_sealed` streams were opened once for H5. This is not a
fresh-data confirmation, and no result from it may be described as one.

## Question
H2 showed that repeated-look recent-window payback hurdles (B0a, B0w, B0b) certify the wrong
sign on a synthetic flat null, while the time-uniform drift-class certificate B2 does not. Does
this cost realised payback on real streams? Or does B0's speed earn more than its invalidity
loses?

## Data and episodes
All usable streams in `../shift-research-starter/data/c4_sealed/*.npz` (keys `l0`, `l1`,
`starts`, `delay`). Each episode uses the paired losses ell(0)=incumbent and ell(1)=challenger,
with Z = ell(0) − ell(1). The npz row/episode semantics follow the existing loader
(`src/shiftlab/paper3/transfer/data.py`); the stream's recorded `delay` is the label delay d.
Streams with fewer than 6 episodes are excluded and listed. The exclusion list is fixed by this
rule, not by results.

## Frozen certificates and parameters
B0a, B0w, B0b, B1, B2 exactly as in `03B_PAYBACK_CERTIFICATION_DESIGN.md` (pilot1 parameters):
B=150, k=3, α=0.1, declared v=0.002, batches of `plan_batch_size`, request-time booking,
single switch then hold. Hold horizons h ∈ {50, 100}; h=100 is primary. Each certificate starts
at the episode start, queries per its schedule, and on certifying switches to the challenger
and holds for h rounds. Episodes too short for certification time + h rounds are truncated to
the available rounds; they are reported but not excluded.

## Endpoints (evaluator-side, ex post; never visible to certificates)
- Realised net payback of an episode = Σ over the hold window of Z_t − k − c_q·labels. c_q = 0 is
  primary; c_q = 0.05 is secondary. An uncertified episode scores −c_q·labels.
- **Primary:** mean realised net payback per episode, B2 minus B0x, for each x ∈ {a, w, b}
  separately (three pre-declared contrasts). Use a stream-cluster bootstrap with 10,000
  resamples and equal stream weights.
- Secondary: wrong-sign fraction among certifications (realised hold payback ≤ 0),
  certification rate, delay to certification, labels used, and per-stream table.

## Decision rule
- **R1-SUPPORTED** (H2 matters on real data): for at least one of B0w, B0b, the B2 − B0x
  contrast has a 95% CI lower bound > 0 at h=100 (B2 realises more).
- **R1-REVERSED:** for every x, the CI upper bound < 0 (B0 earns more despite invalidity).
- Otherwise **R1-INCONCLUSIVE**.

Report the decision exactly per this rule. Holm-adjust the three primary contrasts as a
secondary view.

## Consequence (declared in advance)
- SUPPORTED: Paper 3 continues as a benchmark/limits paper anchored on H2, and needs a fresh
  real batch to confirm.
- REVERSED: the limits paper loses its practical anchor; Paper 3 stops as a paper, with the
  results archived.
- INCONCLUSIVE: no anchor; fresh data are required before any decision.
