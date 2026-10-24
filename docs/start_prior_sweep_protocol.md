# Fixed start-time prior development sweep

**Status:** frozen development design; not a confirmatory comparison.

## Question and mathematical basis

The eight-start equal-weight mixture improved delayed-harm detection across the registered
confirmation grid. The next question is whether a fixed prior over those same starts can improve the
power tradeoff across early and late changes without compromising the conditional-mean e-process
guarantee.

For each start position k, let E_k(t) be the valid bounded-mean e-process that is 1 before its
prespecified start and evolves afterward. For any fixed weights w_k >= 0 summing to one,
E_w(t) = sum_k w_k E_k(t) is an e-process under the same null and filtration by linearity of
conditional expectation. This screen compares fixed start-time weights only. It does not reweight
components after observing the current stream.

The candidate priors put Beta(a,b) probability mass on eight equal-width bins partitioning the
normalized start-time interval [0,1]. The registered set is Beta(1,1) (equal weights), Beta(1,2)
(early), Beta(2,1) (late), Beta(2,2) (middle), and Beta(0.5,0.5) (early/late edges). Every prior is
positive and normalized. Full-stream bounded betting is retained as the non-restart comparator.

## Development design and selection

Use development seeds 20262000–20262029, reused as common random numbers across the 12 cells:
query rates {0.10, 0.25, 0.50} × harm onset fractions {0.20, 0.60} × expected paired-cost increases
{0.12, 0.24}. Each cell has 3,000 prediction events, 30 paired streams, alpha 0.05, materiality
margin 0.02, amplitude 0.60, and fixed-three-step delays. The methods see identical generated
contrasts, query masks, and delays within each cell and seed. CUDA generates streams; monitor paths
are evaluated on CPU.

Select the candidate with the highest unweighted mean detection rate across the 12 alternative
cells; break ties by higher worst-cell detection. This is a development-only rule. The screen makes
no p-value or superiority claim, and the selected candidate must be calibrated on fresh stationary
and benign-variance null seeds and tested on fresh alternatives before it can replace the equal
mixture. Do not reuse these development outcomes for confirmatory inference.

Run from the repository root with:

    uv run shiftlab-dive-start-prior-sweep --device cuda --seeds 30 --seed-offset 20262000 --output-dir outputs/start_prior_development

The runner records the exact start weights, candidate ranking, seed interval, runtime, code hashes
and metric checksum. No figure is required for this table-based development screen. Any later visual
must use PaperBanana as requested by the project owner.
