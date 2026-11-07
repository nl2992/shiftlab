# Research success criteria v2 (discovery-first)

**Status:** Governing standard for deciding *whether to pursue* a paper candidate. Adopted 2026-11-07 at
the user's instruction. It replaces the stricter acceptance filters used in earlier sprints (fixed
improvement margins, two-domain real-data gates before drafting, two-mechanism/three-variant caps,
"stop unless a theorem exists"). It does **not** relax the scientific-integrity rules in Section 8,
`AGENTS.md`, or the data agreements. Earlier documents keep their historical verdicts; a verdict
reached under the old filter may be re-classified under this standard, and the re-classification must
cite the original evidence rather than re-describe it.

## 1. Objective

Find at least one plausible, defensible research contribution from the existing infrastructure and
new evidence. Narrow algorithmic improvements, regime-specific wins, gains on any important endpoint,
explanatory empirical findings, mechanism-backed combinations of existing components, and benchmark,
diagnostic or negative-results papers all count. Universal superiority, large effects, multiple
theorems and dominance over every SOTA method are **not** required.

## 2. Benchmark contribution — pursue when

1. At least one meaningful ranking inversion is reproducibly observed in a clearly defined environment;
2. the comparison includes relevant, credible baselines;
3. the inversion has a plausible practical consequence or exposes a mismatch between monitoring and
   deployment objectives;
4. it adds an evaluation dimension, mechanism, observation or reproducible resource not adequately
   covered by the closest prior work.

There is no minimum inversion frequency; a rare but consequential inversion can matter more than a
frequent trivial one. Synthetic evidence alone can justify a benchmark candidate and a first draft.

## 3. Methods contribution — pursue when

1. a clearly defined failure or limitation of an existing approach is observed;
2. a modification or new decision rule plausibly addresses it;
3. it shows an advantage over an appropriate strong comparator on at least one relevant endpoint;
4. the advantage reproduces in the identified operating regime;
5. there is a defensible novelty argument.

No mandatory effect-size threshold. Eligible endpoints include total deployment cost, harm before or
after a switch, detection delay, label efficiency, power, false or harmful promotions, rollback
responsiveness, robustness to feedback delay, behaviour under limited budgets and cost–risk
trade-offs. A statistically uncertain but directionally promising gain may advance to further testing
and drafting **if labelled preliminary**. A confirmatory superiority claim still needs independent
evidence with uncertainty reporting; an inconclusive result is never reported as a win. Losing to other
baselines, or outside the intended regime, is reported as a limitation, not grounds for automatic
rejection.

## 4. Metric discovery

Exploration may use any scientifically relevant metric and may surface new metrics and hypotheses
(e.g. lower cost but later detection; more power but more harmful deployments; fewer labels at similar
power; fewer unnecessary switches when switching is expensive; better under delayed than instantaneous
feedback). Once something interesting is found: label it **exploratory**, then **freeze the hypothesis
and metric** before a fresh confirmation run. A metric found by searching is never presented as
independently confirmed.

## 5. Real data

One relevant chronological real dataset is useful support; two or more independent domains are
desirable for generalisation claims. A strong synthetic finding can justify continued development when
real-data results are inconclusive, and an instructive counterexample can itself be a contribution.
Not every dataset must support the method; report **every** dataset tested and where the method helps,
shows no detectable advantage, or is worse. Regime-specific effectiveness is a legitimate claim.

## 6. Candidate exploration

No fixed cap on mechanisms or variants. Budgets are computational and value-of-research based.
Required discipline:

* record every tested candidate in the candidate registry (`research/candidate_registry_v2.md`);
* reuse cached computation; do not repeat near-identical runs without a new hypothesis;
* keep development and held-out evaluation separate, and never re-query held-out data to optimise a winner;
* prefer interpretable, mechanism-matched modifications over arbitrary combinations.

## 7. Outcome categories

| code | meaning | action |
|---|---|---|
| **A** main-track candidate | defensible novelty argument + supporting evidence for ICLR/ICML/NeurIPS, more evaluation may be needed | develop toward submission; this is not a prediction of acceptance |
| **B** promising paper | nontrivial result; novelty, uncertainty, baseline strength or external validity need work | keep developing |
| **C** workshop / specialised venue | useful, reproducible, appropriately scoped; significance or generality limited | draft for that venue or a preprint |
| **D** empirical / diagnostic | no algorithmic advance, but benchmarks, failure mechanisms, counterexamples or negative results | assess for a benchmark, empirical or reproducibility paper |
| **E** inconclusive | evidence supports no clear claim | preserve artifacts; name the smallest experiment that would resolve it |

Abandon a direction only when its hypothesis is clearly invalidated, it is demonstrably non-novel, or
it is no longer worth the research cost — and say which.

## 8. Minimum success condition

The programme meets its discovery objective with **any one** of:

* **Option A (algorithmic):** a reproducible, plausible, nontrivial improvement over an appropriate
  baseline in one well-motivated regime, with a defensible novelty hypothesis;
* **Option B (benchmark):** a reproducible decision-ranking inversion with practical consequences and a
  potentially novel evaluation or explanatory contribution;
* **Option C (empirical):** a useful, insufficiently documented finding about how existing SOTA methods
  behave under realistic deployment constraints;
* **Option D (theory):** a defensible new analytical result, structural observation, bound or
  counterexample relevant to costly online model selection.

Meeting one option warrants **developing a paper candidate**. It does not make the claim proven or the
manuscript submission-ready.

## 9. What stays strict (unchanged)

Never fabricate findings or novelty; never conceal failed datasets; never present a common-contract
adaptation as a native SOTA implementation; never claim statistical superiority without sufficient
evidence; never use future outcomes in deployment decisions; never relabel previously exposed data as
independent confirmation; never claim guarantees without justification; never generalise beyond tested
conditions. Keep full provenance and transparent uncertainty. The evidence vocabulary (PROVED,
CONFIRMED, DEVELOPMENT_ONLY, EXPLORATORY, FALSIFIED, UNVERIFIED) remains in force.

## 10. Agent posture

Be constructive rather than reflexively conservative. Do not reject an interesting result for failing
to dominate every baseline, win on every dataset, deliver a large number or clear an arbitrary
threshold. Seek the smallest credible contribution that can become a defensible paper: narrow results
get narrow claims; preliminary results get a provisional manuscript and a list of remaining tests; a
failed method with an informative benchmark becomes a benchmark paper; a specialised-venue fit is
recommended as such. Every programme ends by naming **the most promising paper buildable now**, even if
the evidence is incomplete. Incomplete research is not failed research.

## 11. Sub-agents for expensive work

Long or broad tasks should be delegated to the project sub-agents in `.claude/agents/` so the main
session keeps its context for decisions: `evidence-surveyor` (read-only inventory across branches and
reports), `source-auditor` (primary-literature reading for novelty matrices), `experiment-runner`
(executing an already-frozen protocol and recording provenance), and `adversarial-reviewer` (read-only
red-team of a specific claim). The main session remains responsible for freezing protocols, choosing
hypotheses and making every classification; a sub-agent's report is evidence to check, not a verdict.
Delegated runs follow Section 6 and the frozen-protocol rule: a sub-agent never edits a protocol after
seeing results and never reads held-out outcomes it was not asked to produce.
