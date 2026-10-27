# WILDS CivilComments PACE candidate gate — exploratory protocol

**Status:** frozen protocol, 2026-10-26. **Purpose:** task-specific Q2
development reproduction of the paired anytime-valid acceptance rule in PACE
on WILDS CivilComments. This is an offline exchangeable-instance replay, not a
live deployment or independent real-data confirmation.

## Primary question and estimand

For one binary classification policy selected from a fixed 15-member
model/threshold bank, does a PACE gate accept it over a fixed incumbent using
fresh paired article-level validation outcomes, and what decision cost does
the resulting choice attain on the official test partition?

The primary outcome is correctness on an instance under symmetric 0/1
classification loss. This is the setting where PACE's original McNemar-style
discordant-pair construction applies: on a certification instance where the
policies disagree in correctness, the candidate's outcome is a win or a loss.
Asymmetric false-positive/false-negative costs are not part of this PACE
reproduction because discordant correctness outcomes are not fair under an
arbitrary weighted-cost null.

## Data and split contract

- Use local processed WILDS CivilComments v1.0, version
  `c4f79606707951bcba11`; verify the pinned raw-source and processed-file
  checksums before reading observations.
- Fit the same three hashed-text logistic models using only the official train
  split and the frozen settings in `wilds_candidate_selection_protocol.md`.
  The candidate bank is the Cartesian product of the three penalties and five
  thresholds. The incumbent is penalty `1e-4`, threshold `0.5`.
- On the official validation partition, split article IDs once into disjoint
  scout and certification groups with seed `20261027`. Randomly select one
  comment per article, without looking at text or labels, for each group.
  Select the candidate with highest scout accuracy; ties resolve by penalty
  order `(1e-5, 1e-4, 1e-3)` then threshold `(0.25, 0.35, 0.50, 0.65, 0.75)`.
- Randomly order certification articles with seed `20261028`. Each article is
  one paired evaluation instance. No article contributes to both scout and
  certification; no identity metadata enters fitting, selection, testing or
  the PACE score.
- Do not use official test labels until the selection and certification
  decisions are frozen. Use the test partition only for evaluator-side,
  aggregate outcome summaries. Its prior use in repository diagnostics has
  not been ruled out, so these summaries are exploratory.
- WILDS provides no row-level event, feature-release or label-release times.
  The randomized certification order is an analysis order over independent
  article units, not a recovered historical chronology.

## Frozen methods

1. **Incumbent:** deploy the fixed penalty-`1e-4`, threshold-`0.5` rule.
2. **Scout/greedy:** deploy the highest-accuracy candidate from the scout
   sample without a certification gate.
3. **Fixed-n paired test:** evaluate the selected candidate on all
   certification articles and promote only when the one-sided exact McNemar
   binomial test on discordant pairs rejects at `alpha=0.05`.
4. **PACE:** evaluate the incumbent and selected candidate on the same
   certification articles. Ignore concordant correctness pairs for betting.
   On each discordant pair set `z=+1` if only the candidate is correct and
   `z=-1` if only the incumbent is correct; update `E <- E*(1+0.5*z)`. Promote
   at the first crossing `E >= 1/0.05 = 20`, then stop. If no crossing occurs,
   retain the incumbent after exhausting the certification pool.

Only one candidate is tested in this frozen run, so the PACE per-candidate
level is `0.05`. This does not provide run-level familywise control over a
sequence of future candidates. Candidate selection on scout data is separated
from certification; this run does not claim validity if the certification
stream is dependent, selectively filtered after outcomes, or reused by later
candidate proposals.

The fixed-n McNemar comparator uses the same candidate and full certification
pool. Report its decision and the fact that it evaluates the complete pool;
do not call the full-pool decision anytime-valid.

## Evaluation and resources

Evaluate the incumbent, greedy choice, fixed-n choice and PACE choice on the
entire official test partition after all decisions are frozen. Report accuracy,
error rate, Brier score/log loss for the selected model, test cost under
symmetric 0/1 loss, and paired accuracy gain versus the incumbent with a
2,000-draw article-cluster bootstrap interval. Report scout articles,
certification articles, certification comments evaluated, discordant pairs,
PACE wins/losses, stopping point, and query-independent evaluation counts.
The run does not simulate paid label queries: all split labels are observed
offline. Do not convert these counts to a label-cost superiority claim.

The primary method-output checks are deterministic source/data hashes, exact
split disjointness, recomputation of the scout winner, recomputation of the
PACE wealth path from aggregate win/loss counts in order, correct crossing and
stop semantics, and test-score recomputation from frozen decisions.

## Interpretation and limits

This is a paper-rule adaptation of PACE's binary correctness gate to one
article-clustered text-classification task. It tests one candidate selected
from a frozen bank; it does not reproduce the paper's self-evolving agent
proposer, multiple sequential commits, or benchmark tasks. The optional-stop
argument depends on the discordant article outcomes being conditionally fair
under the non-improvement null. Article-level sampling reduces within-article
dependence but does not prove the dataset is an i.i.d. sample of a deployment
population. The official test set is exploratory because prior exposure is
not audited. Costs are symmetric classification error, not application
utility. No temporal-shift, intervention-value, delayed-feedback, run-level
FWER, or real deployment guarantee follows.

## Reproduction command

```powershell
uv run python scripts/evaluate_wilds_pace_gate.py --device cuda --bootstrap-replicates 2000
```

Outputs contain aggregate candidate scores, certification summary, test
metrics, source/data hashes and a manifest; they contain no text or
per-comment records. If CUDA is unavailable, the run must be explicitly
repeated with `--device cpu` and labeled as a CPU run.
