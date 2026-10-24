# Contextual stratified intervention protocol

## Research question

When a candidate policy is beneficial in some observed contexts and harmful in others, does applying the existing promotion/rollback gate separately within each context preserve useful deployment better than applying one global gate?

This experiment composes the established bounded e-process gate. Each of two visible, balanced context strata receives alpha/2, and each stratum's promotion and rollback stages split that allocation equally. Bonferroni therefore bounds the probability of any false promotion or rollback across the two contexts and two gate stages by the registered familywise level, under each stage's stated bounded conditional-mean null. The experiment is not a new test or a claim of novelty.

## Streaming information and utility

The learner sees an 8-dimensional feature vector before action selection; feature 1 encodes one of two balanced context labels. It receives a binary outcome only when its predictable randomized query requests the label. The evaluator knows the generator and expected paired cost gain. Neither the hidden phase nor the evaluator's expected gain is supplied to the gate. The incumbent and candidate are evaluated on the same outcome; paired gain is incumbent cost minus candidate cost, with false-negative cost 5 and false-positive cost 1. Promotion, rollback, and queried-label costs are 0.05, 0.05, and 0.01.

Each stream has 400 shadow events and 400 deployment events, 200 events per stratum in each phase. The total query cap is `floor(0.40 * 800) = 320` labels in the registered calibration and confirmation. Query probability is 0.80. The candidate acts only where feature 0 is positive. The principal heterogeneous-reversal profile has shadow gain +1.00 per event in each context, then deployment gains +0.40 and -0.47 per event in the two contexts. The global deployment average is -0.035 per event.

Other registered profiles are stationary null, benign nuisance shift, persistent benefit, homogeneous reversal, a global rollback least-favourable boundary, and a stratified rollback least-favourable boundary. The last two set the deployment gain to the boundary for their corresponding rollback null. Their probabilities are derived from the exact paired-cost gain support and configured rollback cost in the generator.

## Development, calibration, and confirmation

The 500-stream development grid uses seed root `80102024`, query rates 0.40 and 0.80, and caps 0.20 and 0.40. It is exploratory and cannot establish error control or select a general winner. Development selected the heterogeneous-reversal case at query 0.80/cap 0.40 for a targeted independent test.

Calibration uses 2,000 streams per scenario at seed root `90102024`. Eight simultaneous one-sided exact Clopper–Pearson cells each receive alpha `0.05/8`: false promotion for both methods under stationary and benign-nuisance nulls; false rollback at the global method's boundary for the global method; false rollback at the stratified method's boundary for the stratified method; and false rollback for both methods under persistent benefit. Rollback risk sets contain streams that were promoted. Every risk set must contain at least 1,000 streams, every upper limit must be at most 0.05, and every label cap must be respected. Calibration is specific to these synthetic nulls and fixed policies.

Confirmation uses 2,000 fresh streams per scenario at seed root `91102024`; it requires the passed calibration manifest. The frozen primary profile is heterogeneous reversal at query 0.80/cap 0.40. It passes only if the paired seed-bootstrap 95% lower bound for stratified minus global utility and for stratified minus continue is positive, the mean harmful-context rollback count is at least 0.5 per stream, mean safe-context retention exceeds 0.9, and all hard caps are respected. Comparisons on other scenarios are descriptive secondary results.

## Reproduction

```powershell
uv run shiftlab-dive-contextual-stratified-grid --seeds 500 --seed-offset 80102024 --horizon 400 --query-rates 0.40 0.80 --budget-rates 0.20 0.40 --device cuda --bootstrap-replicates 2000 --output-dir outputs/contextual_stratified_grid_500
uv run shiftlab-dive-contextual-stratified-calibrate --seeds 2000 --seed-offset 90102024 --horizon 400 --device cuda --output-dir outputs/contextual_stratified_calibration_2000
uv run shiftlab-dive-contextual-stratified-confirm --calibration-manifest outputs/contextual_stratified_calibration_2000/manifest.json --seeds 2000 --seed-offset 91102024 --horizon 400 --device cuda --output-dir outputs/contextual_stratified_confirmation_2000
```

CUDA is used for stream generation when available, with a CPU option retained. The runners save stream-level CSV/Parquet, paired contrasts, reports, source hashes, seed roots, environment details, and manifests. No research visual is required for this tabular experiment. If one is later commissioned, create it with PaperBanana and verify it against the saved metrics; do not substitute another figure generator.

## Limits

The visible contexts are balanced and known in advance. This isolates the benefit of context-local decisions, not learning a partition or dealing with rare/unknown contexts. The conditional-mean guarantees rely on the gate's bounded paired-gain and predictable-query assumptions. These synthetic checks do not address misspecified contexts, changing candidate policies, selection among many stratifications, adaptive external feedback, or application-grounded intervention costs. A pass supports only the registered heterogeneous-reversal case and does not establish general superiority or novelty.
