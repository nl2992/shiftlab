# Adversarial review, round 1

**Recorded 2026-10-28, loop tick 7.**
- **Reviewer:** Codex (`gpt-6.1-sol`, reasoning effort xhigh), run read-only through
  `codex exec` on `REFINEMENT_ROUND_1.md` at commit `d0ed225`, under the brief in
  `REVIEW_BRIEF_1.md`.
- **Independence:** this is an independent cross-model review, from a different model family than
  the author. The four perspectives (theorist, prior-art specialist, empirical ML reviewer, PC
  member) were all written by that one reviewer, so they are four lenses from one model, not four
  independent reviewers.
- **Verdict:** BENCHMARK_PAPER with substantial revision. Scores: ICML main 3/10, NeurIPS D&B
  4/10.

## Lead verification of the fatal items

| # | Objection | Lead check | Accepted? |
|---|---|---|---|
| F1 | The proposal's null `E[Z_t − ε \| F_{t−1}, X_t] ≤ 0` adds current-`X_t` conditioning that the charter does not have. The stationary controls violate it (e.g. `p = 0.4` gives `E[Z \| X] = 1.4`). | The charter states `E[· \| F_{t−1}]` only. The extra `X_t` was introduced by the author in round 1. The boundary-subgroup excess is already documented in `docs/residual_variance_context_null_audit.md`. | **Yes.** It is an author error in the proposal, not in the frozen runs. |
| F2 | Proposition S's corollary ("evidence is set by the number of post-onset informative labels") is much stronger than the algebra. Equal counts do not mean equal loss laws, ordering, initial wealth or calendar delay. Codex's counterexample: at `c = 0.8`, deterministic `Z = 0.2C` gives +0.148 per label, while ±C with the same mean gives −0.291. | The algebra holds only with the conditional loss law and stake fraction fixed. The counterexample is correct by direct calculation. | **Yes.** Keep only a restricted lemma. |
| F3 | DISCERN is mis-described as "theory, not a composed benchmark". Its §6.4 compares gating against sequential-PPI and active-testing adaptations on identical streams, so H1 and H2 overlap existing theory **and** experiments. | Not re-read by the lead in this tick. The B2 full read covered DISCERN Thms 7–9, Prop. 13 and §5.7, not §6.4, so the gap is plausible. **To verify in round 2 (Haiku fetch of §6.4).** | **Provisionally yes.** |
| F4 | H4 does not isolate reference safety. The arms differ structurally: fallback acts at the alarm; candidates deploy only from event 2,400 (`STAGES["scout_cert_end"]`); `q1_fallback` has no rollback; native adaptation starts at 1,600 (`STAGES["monitor_end"]`), exactly when the Q1 window closes. | `src/shiftlab/dive/integrated_pipeline.py:39–40` confirms `monitor_end = 1600` and `scout_cert_end = 2400`; rollback is enabled only for pipeline arms. | **Yes.** H4 is a property of the frozen state machines, not evidence for the reference-safety explanation. |
| F5 | Claim A, as a general two-factor explanation, omits signal magnitude, initial wealth, engine adaptation, onset timing, action availability and rollback capability. "Every screened mechanism failed" does not mean novel mechanisms add nothing. | Follows from F2 and F4. | **Yes.** |

**Accepted majors** (to address in round 2):
- PPI breaks invariance. At ε = 0 the per-label growth is `log(1 + c/(2 − q))`, which depends on
  `q` (lead check: 0.588 at `q = 1` against 0.351 at `q = 0.1` for `c = 0.8`).
- Adaptive engines (GRAPA, EB, plug-in) are outside S.
- The ε remainder can be 11% relative near zero growth.
- The reserve stop preserves validity but not allocation equivalence.
- H1's "growth" is a per-stream best-fixed-stake post-onset diagnostic, not deployed mixture
  wealth. Gated HT is compared against uniform **PPI**, so acquisition, anchor and bound change
  together; a uniform-HT comparator is missing.
- "Matched" needs definitions (common access, cap, realized spend).
- S3 is development evidence. The H4 fallback contrasts are outside the frozen 22-test family.
- E2 is endogenous (labels counted until alarm). E3 matches labels but predicts calendar delay.
- Multiplicity families must be enumerated. A D&B paper needs a reusable benchmark contract.
- A second task with identifiable paired costs is wanted.

**Codex's verification limits:** it checked code, protocols, CSV/JSON values and manifest hashes,
including both integrated event logs, and they matched. It could not run Python, so Parquet-level
statistics were not recomputed.

---

## Full review (Codex, verbatim final answer)

Recommendation: **BENCHMARK_PAPER, with substantial revision.** The headline numbers largely survive inspection. The strongest objections concern the stated null, the scope of Proposition S, the novelty comparison with DISCERN, and the attribution of H4’s rankings.

I reviewed commit `d0ed2256e7af462b3f077fb6159840a33df75ff5`, the relevant protocols, implementations, artifacts and primary literature. No files were modified. “Fatal” below means that the particular claim cannot stand as written; it does not necessarily invalidate the entire project.

**Reviewer 1: Statistical theorist**

**FATAL 1 — The stated null does not match the registered synthetic null controls.**

The proposal states
\[
\mathbb E[Z_t-\epsilon\mid\mathcal F_{t-1},X_t]\leq0,
\]
and attributes this to the charter. The charter conditions on prior history, without conditioning on current \(X_t\). These are different hypotheses.

This difference matters in the actual generator. Under stationary conditions, the deployed policy uses probability threshold \(1/2\), while the reference uses the cost-sensitive threshold \(1/6\). At a context with source probability \(p=0.4\), deployed action is 0 and reference action is 1. With false-negative cost 5 and false-positive cost 1,
\[
\mathbb E[Z_t\mid X_t]=5p-(1-p)=1.4>0.1.
\]
Thus the nominal stationary control violates the proposal’s current-context conditional null. The repository already documents positive excess in a boundary subgroup. See [the source policy definition](C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/src/shiftlab/decision_harm_experiment.py:161) and [the context-null audit](C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/docs/residual_variance_context_null_audit.md:5).

This does **not** demonstrate an invalid implementation. The registered gating protocol deliberately uses history-dependent bounds and pacing, supporting a weaker conditional-on-past argument. It demonstrates that the proposal has changed the hypothesis without reconciling the evidence.

**Remedy and resolving evidence:** Choose the primary null explicitly. For the conditional-on-past null, provide an arm-by-arm proof that the propensity correction is unbiased and the bet and normalizing bound are measurable with respect to the required history. Current-context-dependent bounds require a separate argument. If retaining the stronger null, construct controls that actually satisfy it and label the existing controls accordingly.

**FATAL 2 — Proposition S’s corollary is substantially stronger than its valid algebra.**

The restricted zero-anchor HT identity is correct. Condition on a disagreement event and pre-query information \(\mathcal H\), assume the query coin is conditionally independent of the outcome, and define
\[
V=GZ/q-\epsilon,\qquad B=C/q+\epsilon,\qquad \lambda=c/B.
\]
Define “per label” as \(\mathbb E[\Delta\log W\mid\mathcal H]/q\). Its exact value is
\[
\mathbb E\!\left[
\log\!\left(1+\frac{c(Z-\epsilon q)}{C+\epsilon q}\right)
\middle|\mathcal H
\right]
+\frac{1-q}{q}\log\!\left(1-\frac{c\epsilon q}{C+\epsilon q}\right).
\]

At \(\epsilon=0\), this becomes
\[
\mathbb E[\log(1+cZ/C)\mid\mathcal H],
\]
independent of \(q\), **holding the conditional loss law and stake fraction fixed**.

That does not establish that evidence at calendar time \(t\) is determined by the number of post-onset informative labels:

- Different allocation rules can sample different loss distributions, especially when allowed to depend on current covariates.
- Equal label counts do not imply equal magnitudes, signs or ordering of labelled losses.
- Pre-onset wealth matters.
- Positive expected excess does not guarantee positive expected log-growth at a particular stake.
- Equal labels by the horizon do not imply equal calendar-time detection delay.

For example, at \(c=0.8\), deterministic \(Z=0.2C\) gives per-label log-growth \(0.1484\). A distribution with \(Z=C\) with probability 0.6 and \(Z=-C\) otherwise has the same mean, but log-growth \(-0.2911\).

**Remedy and resolving evidence:** Retain a restricted lemma about HT wealth in label time. State precisely what must be matched: conditional loss law, initial wealth, stake rule and stopping contract. Any delay approximation must additionally require positive log-growth, an arrival-rate model, finite log moments, and allowance for initial wealth and overshoot.

**MAJOR — The extensions have different answers; they should not be bundled.**

1. **Mixture over stakes: survives at \(\epsilon=0\), under the restricted conditions.**  
   The implemented grid contains fixed *fractions* \(c_j\), rather than fixed raw stakes \(\lambda_j\). For the same ordered labelled losses,
   \[
   W_n=\sum_j w_j\prod_{k=1}^{n}(1+c_jZ_k/C)
   \]
   is exactly independent of the propensities and intervening unlabelled events. Mixing itself is not a counterexample.

2. **PPI: the invariance does not generally survive.**  
   At \(\epsilon=0\), the implemented symmetric PPI bound is \(C(2/q-1)\). Even with anchor zero and deterministic \(Z=C\), per-label growth is
   \[
   \log(1+c/(2-q)).
   \]
   At \(c=0.8\), it is \(0.5878\) for \(q=1\), versus \(0.3514\) for \(q=0.1\). Nonzero anchors also create unqueried-event updates. A general PPI extension is therefore false.

3. **The \(\epsilon\) term needs a quantitative bound.**  
   With \(a=c\epsilon q/(C+\epsilon q)<1\), the remainder after the displayed linear correction is exactly
   \[
   R=\frac{1-q}{q}\{\log(1-a)+a\},
   \quad
   -\frac{(1-q)a^2}{2q(1-a)}\leq R\leq0.
   \]
   Small absolute error does not imply small relative error when net growth is near zero. On the stated scratch-check grid, \(C=5,\epsilon=0.1,\mu=0.2,c=0.05,Z\in\{-5,5\}\), exact per-label gains are approximately \(-0.0002219\) at \(q=1\) and \(-0.0002470\) at \(q=0.1\): an 11% relative difference.

4. **Hard reserve stopping preserves stopped-process validity, not allocation equivalence.**  
   The stop before opening an unaffordable event is predictable. That is sound. Different rules nevertheless exhaust their reserves at different times and admit different labelled prefixes.

**Does “fixed fraction of the cap” match the code?** Yes for each component of the default HT mixture: [the process](C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/src/shiftlab/dive/eprocess.py:154) uses \(1+c_jV_t/B_t\). It does not describe every benchmark engine: plug-in, empirical-Bernstein and GRAPA rules adapt their bets, and GRAPA has calendar-event burn-in. See [the engine interface](C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/src/shiftlab/dive/comparison_betting_engines.py:42).

**Resolving evidence:** An explicit theorem-to-engine applicability table, with exact identities or counterexamples for each row. The restricted lemma can be proved now; simulation is unnecessary to establish it.

**MAJOR — Multiplicity and composition language remains too compressed.**

S2’s simultaneous confidence family is scenario × budget **within each arm**, not the whole panel. WP4 reports per-cell bounds. Holm correction of experimental comparisons is distinct from operational error control across monitors or intervention stages. The proposal correctly disclaims monitor–certify–promote composition validity; preserve that limitation.

**Remedy and resolving evidence:** Enumerate each error event, probability measure, family and correction. For WP4’s primary zero-alarm results, a conservative correction across all 68 cells would still pass: the upper bound would be about 0.72%. This is a reporting repair, not evidence of a failed calibration.

---

**Reviewer 2: Prior-literature specialist**

**FATAL — The description of DISCERN as supplying “gating theory, not a composed benchmark” is inaccurate.**

DISCERN §6.4 explicitly compares disagreement gating against sequential PPI-style and active-testing adaptations on identical streams with identical confidence-sequence machinery. Its Theorem 9 and Corollary 10 establish the \(\Theta(1/\rho)\) label-complexity separation for the stated pairing-blind class. Its experiments also test the predicted label economics. H1–H2 therefore overlap with both existing theory **and existing comparative experiments**. [DISCERN, §§5.3 and 6.4](https://arxiv.org/html/2609.17560v1)

The paper does not cover the complete H1–H4 intervention suite. I have not established that the narrower proposed benchmark already exists. The fatal issue is the present positioning, not proof that no benchmark contribution remains.

**Remedy and resolving evidence:** Replace the contrast with a source-specific delta: nonstationary incumbent monitoring, finite reserves, temporal allocation, and intervention comparisons. Provide a table identifying which experimental dimension is absent from DISCERN, rather than describing it as theory-only.

**MAJOR — Proposition S is explanatory algebra, with little apparent standalone novelty.**

The exact zero-tolerance cancellation follows immediately from the HT increment and reciprocal-propensity support scaling. I did not locate an identical named proposition, but a new name would not make this a substantial statistical contribution.

Timans already supplies the conditional bounded-risk betting framework and comparisons among betting engines. Waudby-Smith et al. explicitly discuss direct policy-value differences, adaptive logging and time-varying values. Their targets differ in relevant ways, but these are established foundations for the proposal. [Timans et al.](https://arxiv.org/html/2506.16416), [Waudby-Smith et al., §3.1](https://arxiv.org/html/2210.10768)

**Remedy and resolving evidence:** Present S as a credited explanatory lemma. A theory contribution would need something stronger: for example, a sharp finite-budget detection result or a nontrivial bound quantifying when the approximation fails. Neither currently exists in the proposal.

**MAJOR — H4’s qualitative message has substantial precedent.**

Using a safe reference to constrain an untested policy, and reverting toward baseline behaviour under uncertainty, are established principles in Conformal Policy Control and safe policy improvement. These sources do not establish H4’s exact sequential utility ranking under changing regimes. They do prevent “a safe fallback can beat costly certification” from carrying much novelty alone. [Conformal Policy Control](https://arxiv.org/html/2603.02196), [SPIBB](https://proceedings.mlr.press/v97/laroche19a/laroche19a.pdf)

**Remedy and resolving evidence:** Identify a quantitative, previously unresolved operating region: reference deterioration, certification latency, rollback delay and intervention cost. Show that the resulting recommendation survives matched action opportunities. Otherwise H4 is a useful illustration of established principles.

**MAJOR — The remaining literature distinctions require precision.**

Ahmed et al. already audit failures of label-free monitoring and adaptation under temporal shift. The proposal’s paired-cost estimand distinguishes it, but “failure analysis of monitoring under shift” does not. Also, correlated collapse is not a counterexample to correctly measured *relative* harm: if both policies take the same action, their paired cost difference really is zero, even when both perform badly. Absolute safety is a separate endpoint. [Ahmed et al.](https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2026.1928858/full)

Existing sequential comparisons also include Comparecast, whose weak running-average null should remain distinct from the proposed eventwise null. [Choe and Ramdas](https://arxiv.org/abs/2110.00115)

**Remedy and resolving evidence:** Rewrite the novelty matrix around exact estimands, guarantees, feedback and experimental coverage. Avoid both “already solved” and “first benchmark” conclusions based on broad topic similarity.

---

**Reviewer 3: Empirical ML reviewer**

**Headline artifact check**

| Finding | Assessment |
|---|---|
| **H1** | `decision.json` reports 7.2014, interval [6.8845, 7.5512], and 100 paired wins with zero losses at \(r=0.05\). The quoted numbers match. |
| **H2** | Measured ratios are 17.4677 / 20.6148 / 14.7336 / 7.2014 against registered predictions 18 / 18 / 15 / 7.5. They pass the registered factor-of-two criterion. |
| **H3** | 0.86 versus 0.76 is correct for the default mixture. GRAPA gives 0.94 versus 0.91. EIA fixed gating matches full-feedback **median** delay in all ten detectable cells at each of \(r=.05,.10,.20\). |
| **H4** | All quoted means match the integrated summary, including the distinction between standalone fixed certification and the Q1-gated fixed-candidate pipeline. |

The checksummed sources are [S3’s decision artifact](C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/outputs/gated_monitor_compare/analysis/decision.json), [S3’s summary](C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/outputs/gated_monitor_compare/analysis/summary.csv), and [the integrated summary](C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/outputs/shiftguard_unified/integrated_confirmation/efficacy_100_v1/integrated_pipeline_summary.csv).

**FATAL — H4 does not isolate reference safety as the explanation for the rankings.**

The implementation gives fallback and certification substantially different opportunities:

- Fallback changes actions immediately after the Q1 alarm.
- Candidate deployment starts at event 2,400, even when certification crosses earlier.
- `q1_fallback` holds the reference thereafter without rollback monitoring.
- The full pipeline can roll back; standalone `fixed_candidate_certification` cannot.
- Native adaptation starts at event 1,600, exactly when the Q1 monitoring window closes.

Consequently, native fallback’s zero benefit is mechanically induced by its monitoring window. The reversal comparison also changes rollback capability. Boundary-harm gains include a large difference in available intervention time. These are valid findings about the frozen state machines, but they cannot establish that reference safety governs the rankings.

See [the monitoring window](C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/src/shiftlab/dive/integrated_pipeline.py:685) and [deployment, rollback and fallback logic](C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/src/shiftlab/dive/integrated_pipeline.py:804).

**Remedy and resolving evidence:** Separate response choice, response latency, monitoring coverage and rollback availability. Compare fallback with and without rollback, and candidate policies with matched deployment opportunities. Randomize or sweep onset independently of stage boundaries. Report opportunity-loss decomposition before attributing H4 to reference safety.

**MAJOR — H1’s “evidence growth” is a specific retrospective diagnostic.**

`paired_growth` takes the maximum average component log-gain over the stake grid, separately for each stream, on the common post-onset prefix. This is not directly the growth of the deployed mixture wealth. The statistic is registered and useful, but “evidence grows 7.20× faster” obscures what was measured. See [the calculation](C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/src/shiftlab/dive/gated_monitor_comparison.py:125).

The headline also compares gated HT against uniform PPI. Acquisition, anchor and support bound change together. At \(r=.20\), zero-anchor uniform HT would use bound \(25.1\), versus uniform PPI’s \(45.9\). “Correctly bounded” does not mean these constructions are equally efficient.

**Remedy and resolving evidence:** Name the registered growth diagnostic exactly. Add actual mixture-log-wealth summaries and a uniform-HT comparator using the same engine. Cross acquisition and estimator choices where compatible. H1’s strong detection difference may remain; its complete attribution to label waste has not yet been isolated.

**MAJOR — “Matched information and budgets” needs operational definitions.**

Shared streams and query uniforms are strengths. A shared cap does not establish equal realized expenditure, equal monitoring duration or identical information access.

At \(r=.05\), the headline gated and uniform arms use approximately 118 versus 114 labels and 177 versus 171 dollars. This is reasonably close, but should be described as comparable spending under a common cap. In H4, labels are separate resources rather than monetized utility costs; the protocol explicitly says so.

**Remedy and resolving evidence:** Distinguish common access, identical feedback replay, common resource cap, and matched realized expenditure. Report utility–resource frontiers or prespecified matched-spend operating points. Preserve source-adaptation labels and avoid counting PPE/Xu algebraic aliases as independent methodological wins.

**MAJOR — The real-data and oracle evidence is narrower than Claim A.**

Evaluator-side expected utility is legitimate synthetic evaluation; I found no basis here to allege that oracle utility drives the decisions. It reduces outcome noise, but does not validate the chosen cost scale or identify real operational utility.

EIA uses imposed costs and injected policy changes. Three paths have only 1–7 original disagreements. Random orientation constructs an exact conditional randomization null; it does not demonstrate that natural deployment streams satisfy the scientific harm null. The ten detectable injection cells are conditional on four exposed paths, not ten independent deployments.

**Remedy and resolving evidence:** Retain these panels as stress tests. Add a materially different task with identifiable paired costs and defensible utilities, ideally on a locked, previously unused evaluation split. Vary reference quality, disagreement frequency, cost asymmetry and signal persistence. Report absolute reference risk separately from relative harm.

**MAJOR — Selection history and statistical comparisons remain consequential.**

- S3 is explicitly a **development comparison**. A new verifier does not convert it into fresh confirmation.
- H4’s fallback contrasts were not in the frozen 22-test primary family. Holm correction for that family does not support newly selected fallback comparisons.
- The 100%-versus-0% paired bootstrap difference interval degenerates to [1,1]. The exact McNemar result is strong; the degenerate interval should not imply certainty about population effect size.
- H3 needs paired uncertainty if promoted beyond a descriptive result.
- WP3’s temporal comparator changes intensity at monitor index 1,200, exactly the secondary onset and before the primary onset. Its registered advantage is valid for that late-prior design, not an onset-agnostic scheduling conclusion.
- The inventory records historical seed overlaps and Target-Scout source-hash drift. These do not establish contamination of H1–H4, but they preclude blanket disjointness claims.

**Remedy and resolving evidence:** Freeze the new claim family, use fresh stream seeds for confirmation, and record generator versions and stream fingerprints alongside seed namespaces. Reproduce historical Target-Scout outputs with their executed source or demonstrate equivalence. Separate reused development evidence from fresh confirmation.

**MAJOR — E1–E3 do not currently constitute a sufficient falsification programme.**

- **E1** can falsify transcription or reproducibility claims. It cannot establish novelty or the proposed mechanism.
- **E2** risks an endogenous relationship: label counts measured until alarm naturally depend on stopping time. A high within-cell \(R^2\) could be mechanically induced. S3 also stores summaries rather than the event histories required for exact post-onset accounting.
- **E3** matches expected post-onset labels but predicts equal calendar delay. Front-loaded and back-loaded schedules can spend the same number of labels and detect at different times while satisfying the HT identity exactly. Conversely, a difference caused by PPI, adaptive bets or \(\epsilon>0\) does not falsify the restricted zero-tolerance HT lemma.

**Remedy and resolving evidence:** First test label-time wealth on a common ordered loss sequence. Then separately test calendar-time detection under specified arrival and onset models. For E2, use fixed-window explanatory quantities and held-out prediction across cells. For E3, preregister confidence-based equivalence tests and power calculations; point estimates inside the margins are insufficient.

---

**Reviewer 4: Sceptical programme-committee member**

**One-sentence takeaway:** Buy labels where policy losses can differ, and evaluate simple fallback against certification under the same intervention and monitoring opportunities.

A practitioner might change behaviour by adding a disagreement-gated comparator and testing fallback before building a larger pipeline. Those are useful recommendations. The evidence does not yet support a general rule for choosing pacing, certification or rollback.

**FATAL — Claim A cannot stand as a general two-factor explanation.**

The proposed explanatory variables omit signal magnitude and variability, initial wealth, engine adaptation, onset timing, action availability and rollback capability. Several of these visibly determine the current results.

“Every screened candidate failed its margin” also does not imply that novel mechanisms add nothing. It establishes failure to advance those particular configurations. The screened set must be named; the repository contains positive Target-Scout component results elsewhere.

**Remedy and resolving evidence:** Replace Claim A with a bounded empirical statement and explicit predictions for unseen cells. Show that its explanatory model predicts rankings outside the cells used to formulate it, and identify where it fails.

**MAJOR — The contribution currently resembles a correction to this repository’s experimental practice.**

H1 repairs an omitted strong baseline. H2 validates a working-law prediction in one generator family. H3 exposes a particular pacer’s failure. H4 exposes consequential state-machine choices. These can support a valuable benchmark paper, but combining them does not automatically establish a broad scientific contribution.

**Remedy and resolving evidence:** Demonstrate that the benchmark reveals reproducible limitations of widely used evaluation practice across independent tasks, rather than primarily explaining earlier project results.

**MAJOR — Datasets & Benchmarks needs a reusable benchmark contribution.**

The proposal emphasizes reanalysis and writing. It says less about what another research group can use to evaluate a genuinely new monitor or controller.

**Remedy and resolving evidence:** Release a documented benchmark contract, task and feedback taxonomy, evaluator separation, baseline adapters, immutable splits, resource accounting, uncertainty procedures and reproducible reference results. Establish that it evaluates methods beyond the authors’ own adaptations. Synthetic data are acceptable when the generator coverage and scientific utility are demonstrated.

---

**Joint assessment**

| Venue | Score for the current proposal |
|---|---:|
| ICML main track | **3/10** |
| NeurIPS Datasets & Benchmarks | **4/10** |

**Decision: BENCHMARK_PAPER.** Continue after narrowing the claims and repairing the validity statement. The evidence does not justify NEW_METHOD. NO_GO would discard useful, reproducible negative findings prematurely; the benchmark direction remains plausible but is not submission-ready.

The three changes that would strengthen it most are:

1. **Repair the mathematical contract first.** Reconcile the null with the controls; prove the restricted HT identity; state the mixture result; explicitly exclude unsupported PPI and adaptive-engine extensions.
2. **Replace post-hoc explanation with discriminating comparisons.** Include uniform HT, match intervention opportunities and rollback capabilities, vary onset independently, and confirm prespecified predictions on fresh registered streams.
3. **Make the benchmark’s distinct value concrete.** Correct the DISCERN comparison, release a reusable evaluation contract, and add a substantially different task with identifiable paired costs and defensible utility assumptions.

Verification scope: I checked code, protocols, CSV/JSON values and artifact hashes, including both integrated event logs. Those hashes matched their manifests. I did not independently recompute every Parquet-level statistic because Python execution was unavailable in this environment. The Git working-tree status remained unchanged.
