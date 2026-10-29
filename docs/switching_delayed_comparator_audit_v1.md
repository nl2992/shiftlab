# Delayed-switching extension audit and reference implementation

2026-10-28. Previous goal turn: **progress**, resolving source access and rejecting the
elementary sample-age gate. This continuation adds direct delay-reduction comparisons and a
correctness-tested reference. G1 and the methodological objective remain open.

## Additional primary-source evidence

### Yang et al., NeurIPS 2023

[Paper](https://proceedings.neurips.cc/paper_files/paper/2023/file/915125efea950af378435518b3542e6a-Paper-Conference.pdf).
Sections 2–4, Algorithms 1–2 and Theorem 1 were inspected. Multi-batched policies are computed
from previous batches and held as a policy sequence while collecting sufficient feedback.
Their reduction extends each batch to wait for labels. The theorem bounds delayed regret by
the base regret plus a batch-count-dependent delay penalty, under IID delays (and an additional
subexponential assumption for one displayed bound). A batch may itself contain policy changes;
the paper explicitly distinguishes batch count from switch count. The model is not our
nonstationary safe paired-loss query problem. Nevertheless, delayed low-switch learning is
established; defeating interleaved BOLD is not a sufficient separation. Repeated sampling during
waiting also needs explicit request accounting before any adaptation to a hard query cap.

### Quanrud and Khashabi, NeurIPS 2015

[Paper](https://papers.neurips.cc/paper/5833-online-learning-with-adversarial-delays.pdf).
Theorems 2.1 and 3.1, their proofs and the paper-organization statement were inspected.
Direct delayed gradient and perturbed-leader updates admit total-delay-dependent regret;
multi-instance interleaving is not necessary. The main PDF refers lazy-leader extensions to
an appendix not contained in this downloaded nine-page paper. Do not cite an uninspected
lazy-leader switch-count theorem. A standard convex/linear reward bound also does not by
itself prove a hard-budget statistically safe switching result.

### Chick, Forster and Pertile, JRSS B 2017

[Accepted manuscript](https://eprints.whiterose.ac.uk/110768/1/delaypaperDriver.pdf),
[publication metadata](https://eprints.whiterose.ac.uk/id/eprint/110768/).
Sections 2–2.2, Bellman equations (8)–(9) and Proposition 2.2 were inspected; full proofs were
not independently verified. Their Bayesian two-technology problem already combines normal
paired net benefit, sampling cost, a maximum sample size, delayed pipeline observations and
one-time adoption cost. Sampling cannot restart after stopping; pending observations are
followed before terminal adoption. The unknown effect is stationary. This is direct precedent
for economic acquisition with pending outcomes, so that framing is not a new method. It does
not establish our repeated-switching, nonstationary finite-sample safety target. A generic
finite-horizon Bellman recursion would nevertheless be an established approach, not sufficient
novelty merely because it is applied to model governance.

**Direct one-switch reduction.** In the stationary one-change special case, set their pairwise
incremental net monetary benefit `X_i` equal to ShiftLab's queried paired gain
`l_i(0)-l_i(1)`, use their Gaussian prior on the unknown mean `W`, map the maximum number of
pairwise allocations `T_max` to the hard label cap `B`, their delay in allocation periods `tau`
to our fixed delay, their per-allocation cost `c` to the query charge, and their adoption cost `I`
to the one-time deployment switch charge `k`. Their terminal population size `P` supplies the
economic hold horizon, with adoption value `P W-I`; their optional online participant reward
can be set to zero to match a post-experiment hold objective. This is a precise model-class
overlap for stationary one-shot acquisition and adoption, not a claim that their Bayesian
objective gives the ShiftLab conditional-null guarantee. The unresolved target must require
recurrent changes and reversible deployment together with the global anytime risk contract; a
new result cannot be only a delayed one-switch sampling policy.

Extended PDF URL/hash provenance: `switching_source_manifest_v2.json`. Earlier v1 is preserved.
Local third-party caches remain ignored. These scoped reads do not amount to an exhaustive
novelty search or faithful quantitative reproductions of the papers.

## Concrete reference: delayed budgeted two-action Hedge

Implementation: `src/shiftlab/dive/delayed_switching_reference.py`.
Contract, pre-execution checks and proof: `switching_reference_protocol_v1.md`.

The reference queries one uniform event per equal-length block, incorporates arrived paired
losses at block boundaries and uses one deployment uniform variable independently of all
query randomness. It keeps one global deployed action process. A fixed-comparator bound
accounts explicitly for the hard query cap, delayed samples, query charges and actual global
switching costs. This construction combines standard ingredients and **is not nominated as
the methodological contribution**. It is an adaptation/reference, not Cheng's original algorithm.

Important limitation exposed by the proof: if a new acquisition policy depends on deployed
actions, then its observation path can disclose the deployment random variable. Conditioning
on that path no longer leaves the coupling coin uniform. A claimed low-switch acquisition
controller must address this dependence rather than reuse the independent-query proof.
The reference has neither a dynamic-oracle regret bound nor a false-promotion guarantee.
It must not be compared as an equally safe method until a matched risk contract is implemented.

## Decision

Continue the methodological search with a narrower technical obligation: find an acquisition
rule whose coupling to deployment survives budget, delay and statistical-safety accounting,
and prove an advantage over compatible direct methods. Do not nominate 'account for pending
labels', 'batch to handle delay', an ordinary Bellman policy, or 'add a confidence sequence'.
These are now explicit exclusions. No efficacy or real-data evidence has been generated.
