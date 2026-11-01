# 16 Real-data results: successful datasets (B3)

Certified switching reduced mean net cost by **70% on spam, 49% on rialto, and 6% on
weather**, capturing **91%, 70%, and 38%** of the available hindsight gain, respectively.
The run evaluated **7 preregistered streams: WIN on 3, SAFE on all 7**, meeting the
registered SUCCESS rule. This section focuses on those three wins; the
[full seven-stream report and non-wins](16_REAL_DATA_RESULTS_APPENDIX.md) remain available.
SAFE is the registered empirical criterion: cost no greater than never-switch cost plus
query spend and a 2% margin; it does not mean zero excess cost or a general safety guarantee.

## Successful datasets

Primary setting: 200 labels per 2,000-event episode, label cost 0.05, switching cost 5.
Costs include deployment errors, labels, and switches, averaged over 100 query seeds.
Cost reduction is relative to never switching (P0). Headroom captured compares the gain
with always deploying the challenger (P1), a hindsight reference.

| Stream | Episodes | Never switch | Certified switching | Cost reduction | Headroom captured | Paired cost difference [95% CI] |
|---|---|---|---|---|---|---|
| spam | 1 | 849.0 | 254.1 | 70% | 91% | -594.9 [-597.9, -591.8] |
| rialto | 16 | 202.1 | 103.7 | 49% | 70% | -98.3 [-116.6, -79.2] |
| weather | 3 | 504.0 | 475.8 | 6% | 38% | -28.2 [-29.3, -27.2] |

**Spam.** Certified switching lowers mean net cost from 849.0 to 254.1, recovering 91%
of the hindsight gain. The fixed-sample paired batch test costs 315.9. This is the
largest reduction, but comes from one episode: its interval reflects query-seed
randomness, not variation across independent data episodes.

**Rialto.** Across 16 episodes, certified switching lowers cost from 202.1 to 103.7,
recovering 70% of the hindsight gain. It also improves on the batch test's 122.9.
Among these three wins, rialto provides the broadest episode-level evidence.

**Weather.** Across three episodes, certified switching lowers cost from 504.0 to
475.8, recovering 38% of the hindsight gain. The batch test is cheaper at 465.6;
this is a win against never switching and incumbent-alarm switching, not against
every comparator. Its interval, like spam's, is a low-power seed-level bootstrap.

All three satisfy the preregistered WIN criterion: the paired 95% interval versus
never switching is below zero, and mean cost is no higher than incumbent-alarm
switching. Promotion rates were 100% on these streams, with no rollback. Intervals
use 2,000 bootstrap resamples; rialto resamples episodes.

## Safety context and scope

Bank and airlines illustrate the value of declining a worse challenger: blind
challenger deployment costs about 187% and 11% more than never switching, while
certified switching costs about 2.1% and 0.6% more, with promotion rates of 1% and
12%. Both pass SAFE but are not wins. Elec2 and criteo also pass SAFE without
winning; their small challenger advantages did not repay certification costs.
Full costs, uncertainty, sensitivity settings, and negative results are retained
in the [appendix](16_REAL_DATA_RESULTS_APPENDIX.md).

These are results under imposed costs and delays and dev-selected frozen model
pairs. Spam uses file order, rialto image-capture order, and weather has only three
episodes. The source repository for these three streams declares no licence;
use remains research-only. The results do not establish validity under arbitrary
temporal dependence or superiority to all competing methods.

## Provenance and reproduction

- Frozen protocol: [B3 registration](protocols/B3-real-data-certified-switching.md),
  registered at `19f1090`; SHA256
  `b17b5a318e65be5ed7729357fb1f0692c0764b6444a4f686797756fb420cba3a`.
- Policy implementation: `b1_certified_switching.py` at `041bc26`; completed run
  and original report committed at `475bf47`. This write-up does not rerun or tune it.
- Source numbers: [summary.json](results/b3/summary.json); episode records,
  provenance, pair checks, and checksums remain in `results/b3/`.
- Runner: `scripts/promising_directions/b3_real_data.py`; inspect its CLI with
  `python scripts/promising_directions/b3_real_data.py --help` before reproducing
  the registered run with the required local data.
- Relevant verification: `python -m pytest tests/promising_directions/test_b3_real_data.py -q`.

**Assessment: continue** with these scoped positive findings and the preserved
seven-stream evidence; broader efficacy and stronger dependence claims need
further preregistered evaluation.
