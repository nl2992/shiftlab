# Search for a sixth case study: outcome

Undertaken 2026-11-02 to replace **uci_occupancy**, whose evidence is concentrated in a single
episode (`B3_PLUS_CASE_VALIDATION.md`). Method unchanged and frozen at `e846107`. **No sixth case
was found. The accessible candidate pool is exhausted.**

## What was tried

### 1. Insects reoccurring-concept variant — screened, discarded

The six non-abrupt Insects variants had been marked `USELESS_DUPLICATE` on the stated grounds that
the family "is represented by `insects_abrupt_balanced`". That was **misapplied**: that variant was
itself discarded (`USELESS_NO_HEADROOM`), so the family held no SUCCESS, and the duplicate rule in
`screen()` fires only on an existing SUCCESS in the family. One variant was therefore reopened.

The reason was recorded in the registry **before** the run (commit `9d4ca38`): the
reoccurring-concept variant is the only accessible candidate that plausibly exhibits
**post-promotion reversal**, the one failure mode of P7s characterised so far only in simulation.
It was screened for that reason whatever the cost outcome. Multiplicity was controlled: exactly
**one** further variant was screened, chosen for that stated reason and not by trying variants
until one passed; the other five remain `USELESS_DUPLICATE`.

**Result: `USELESS_NO_HEADROOM`, on the dev-window precheck, locked window never read.** The
challenger is *worse* than the incumbent on dev under both pair options:
option A (HGB 0-30%) `adv*T = -9.58`; option B (LR 15-30%) `adv*T = -16.09`; both need `> 5.0`.
So this stream offers no switching decision to make.

**Correction (verified from saved records).** The justification given above for screening this
variant -- that post-promotion reversal was untested on real data -- was **wrong**, and the error
was mine. `openml_ldpa` already exercises it: `P7s` records rollbacks in 5 of 32 episodes (mean
0.0172) where P3b's mean is 0.047, deployment loss differs in 7 of 32 episodes (max
`|dloss| = 25.58`) and the switch count in 5. So P7s on ldpa is **not** a strict Pareto
improvement, and the reversal failure mode is observed on real data, not only in simulation. See
`B3_PLUS_RESULTS.md` section 12. The search below therefore rested on a false premise; its
findings about source availability stand, but the reversal argument for prioritising it does not.

### 2. OpenML `concept_drift` tag — exhausted

All 18 tagged datasets were accounted for. Four are synthetic generators (Hyperplane, LED,
RandomRBF, SEA) and excluded as not real-world. Already handled: electricity (exposed), airlines
(exposed), covertype, Run_or_walk, KDDCup99 subsets (all `USELESS_INELIGIBLE`, no defensible
order), ldpa (**SUCCESS**). Too small for a 2,000-event episode plan: GesturePhaseSegmentation
(9,873 rows), spellman_yeast. Not temporal: poker-hand, news20. CovPokElec is an artificial
concatenation that embeds the exposed electricity stream.

Two genuinely new large candidates were registered and screened: **openml_imdb_drama** (did=273)
and **openml_vehicle_sensit** (did=357). Both are sparse ARFF and the loader requires
`as_frame=True`, so both are recorded `NOT_RUN`. Independently, both were declared with chronology
basis `none` *before* the attempt, because neither ships a timestamp or documented acquisition
order, so both would have been ruled `USELESS_INELIGIBLE` on the chronology requirement had they
loaded. Fixing the reader would not have produced a case.

### 3. Named stream benchmarks — not locatable

`powersupply`, `sensor`/sensor-stream and `usenet` are not on OpenML under any of the names
searched; the API returns HTTP 412 (empty filter) for every spelling tried. BETH's river source URL
now 302-redirects to an Imperial repository landing page. MaliciousURL has 3,231,961 features in a
2.2 GB archive and is not CPU-tractable here.

## Standing

| | Count |
|---|---:|
| Datasets considered (29 registered candidates + 7 original programme streams) | 36 |
| Reached a screening verdict | 29 |
| Reached locked-window evaluation | 11 |
| **Selected case studies** | **5** |
| `NOT_RUN` (inaccessible / intractable; never a verdict on the method) | 7 |
| `USELESS_DUPLICATE` | 7 |
| Queue remaining | **0** |

These counts are recomputed from `dataset_registry.json` and supersede the "22 screened" figure
in the first version of this file. `B3_PLUS_FIVE_CASE_STUDIES.md` currently states "34 datasets
considered" and "4 `NOT_RUN`", which were correct before two further candidates were registered
and the Insects variant was reopened. **The two documents must be reconciled to 36 / 29 / 11 / 5
before submission**, by a single owner, since both are being edited.

## What this means, and the options

The five cases stand as pre-registered. uci_occupancy's weakness is **not** repaired, and it
cannot be repaired by further screening of the sources reachable here. Three honest options:

1. **Report five with the disclosure already in place.** uci_occupancy is labelled one-episode
   evidence and is not given equal weight. Two cases (openml_ldpa `K=32`, rialto `K=16`) carry
   episode-level bootstraps and do the real work.
2. **Report four.** Drop uci_occupancy; the paper keeps two properly powered cases and two
   low-power ones, and loses a case a reviewer would have discounted anyway.
3. **Unlock new data.** The raw data root (a Windows path on another machine) would enable the S5
   alternative-pair configuration and additional streams from the original audit set. This is the
   only route that adds genuine episode-level power. It is **not** needed for a reversal stream:
   openml_ldpa already supplies one (see the correction above).

Option 1 or 2 is a presentation choice; option 3 is the only one that changes the evidence.
