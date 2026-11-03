# Prior-art check: the result is substantially more exposed than we thought

Four search perspectives, three reported (the mainstream active-model-selection perspective was
still running when this was written and may change the picture further). **Every arXiv identifier
below was independently verified to resolve to the stated title**, because one perspective flagged
an ID/date inconsistency on the most threatening item. It resolves. The work is real.

This document exists to record a finding against our own interest.

## 1. "Stop buying labels once the decision is settled" is NOT novel

This was to be our constructive contribution. It has direct prior art.

**DISCERN — "Pay Only for Disagreement: Certified No-Regression Verdicts for Model Updates with
Matching Label-Complexity Bounds"** (arXiv:2609.17560, verified). Candidate `g` versus incumbent
`f`, a paired risk difference, labels bought **only on disagreement points**, Horvitz-Thompson
weights inside an anytime-valid betting confidence sequence, and the audit **stops as soon as a
verdict fires**. It reports 56% of benign updates certifying with **zero labels** — the same
order of saving we report. It even proves a label-complexity lower bound.

Read plainly: disagreement-only purchasing, anytime-valid paired evidence, and stopping once the
decision is settled are all already there, with theory we do not have.

**Karampatziakis, Mineiro & Ramdas, "Off-Policy Confidence Sequences"** (ICML 2021,
arXiv:2102.09540, verified) is the canonical earlier form: "gated deployment", where a candidate
sits in staging, is deployed when the lower confidence sequence crosses 0 and discarded when the
upper does, with "no need to choose a stopping time in advance."

And classically, stopping once the sign is determined is SPRT and fixed-confidence best-arm
identification. A bandit reviewer will say our rule is a special case.

## 2. The cost formulation is also partly anticipated

**"The Challenger: When Do New Data Sources Justify Switching Machine Learning Models?"**
(arXiv:2512.18390, verified) frames incumbent versus challenger as **optimal stopping with an
explicit one-time switching cost**, with a budget constraint limiting feasible switching times.
Its costs are feature access, collection and retraining rather than labels, and it has no label
budget or delayed release — but the "when is switching worth its cost" framing is published.

**Sawade, Landwehr & Scheffer, "Active Comparison of Prediction Models"** (NeurIPS 2012) is the
standard two-model-under-a-label-budget comparator, deriving the sampling distribution that
maximises test power. It predates everything we ported by over a decade and Model Selector's
authors already use it as a baseline.

## 3. The collapse IS stated — in Sawade 2012, and in Model Picker's own appendix

**This section was written before the fourth perspective reported. It was wrong, and the
correction is the most important finding in this document.**

**Sawade, Landwehr & Scheffer (NeurIPS 2012) state the degeneracy explicitly and name it.**
Confirmed in the extracted text of the paper:

> "Instead of using Approximation 13, an uninformative approximation p(y = 1|x) ~ 0.5 may be used.
> In this case q* degenerates to uniform sampling from the subset of the pool where f1(x) != f2(x).
> We denote this baseline as active!=. This baseline coincides with the A^2 as well as the IWAL
> active learning algorithms, applied to the model space {f1, f2}."

And in their introduction:

> "For the special case of classification with zero-one loss and two models under study, a
> simplified version of the sampling distribution we derive coincides with the sampling
> distribution used in the A^2 and IWAL active learning algorithms."

So the phenomenon was derived, named (`active!=`), and identified with A^2/IWAL fourteen years
ago, for exactly our case: zero-one loss, two models.

**Model Picker's own Appendix B contains our formula.** From Karimi et al. (arXiv:2010.09818v3):

> "Consider a binary classification scenario with two models... the probability of querying the
> label is always w_{t,1} w_{t,2} v eta_t for all t."

That is precisely the `q(1-q)` result we "measured", present in the paper whose code we ported,
used there to bound a query count rather than flagged as a degeneracy.

**The one hedge that still matters.** Sawade's collapse is conditional on an *uninformative*
`p(y|x) ~ 0.5` approximation; with a calibrated `p(y|x)` his `q*` remains instance-dependent.
That is a scope correction we had wrong: our claim holds for **hard predictions**, and methods
operating on calibrated soft scores retain instance information. We must state that boundary.

Two further adjacent facts are textbook:

- **Query-by-committee with two members** queries exactly when the two disagree. That *is* the
  degeneracy, stated as an algorithm's design rather than as a collapse of richer scores.
- **Uncertainty measures coincide in binary classification** (margin, entropy, least-confidence
  are monotone in `p_max`). Lu, Li & Lin (arXiv:2306.08954) state it for binary active learning;
  Settles' 2009 survey is the standard reference for the measures themselves.

Our result is therefore not merely a corollary of textbook facts — it is **a restatement of a
published result**, extended to four methods that postdate it. What remains is the extension and
the demonstration, which is incremental, not foundational.

One supporting detail: Model Selector's own paper reports that on the Drift collection it
"adjusts epsilon to 0.5, effectively mimicking random sampling in these settings" — a
self-reported degenerate regime, attributed to the data rather than to a structural property.

## 4. What is left

Honestly narrowed:

- **The combined problem**: `loss + label price + switching cost`, with delayed release, a hard
  per-episode budget, and exactly two frozen models. No perspective found all of these together.
- **A stopping rule defined on the economic deployment decision** — no label can change the
  deployed action given the switching cost and remaining horizon — rather than on a statistical
  certificate firing. This differs from DISCERN in trigger, though not in spirit, and the
  difference is thin enough that it must be *demonstrated* to matter, not asserted.
- **The collapse demonstration**, now reduced to: Sawade's `active!=` degeneracy also applies to
  Model Picker, Model Selector, variance minimisation, Xu's acquisition-only variant and Online
  LLM Picker, under hard predictions. An extension of a known result to newer methods.

## 5. Comparators we now have to add

A reviewer who knows this literature will require these, and we do not have them:

1. **DISCERN-style**: disagreement-restricted sampling with an anytime-valid stop. Highest
   priority, because it is the closest thing to our own method.
2. **Karampatziakis et al. gated deployment**: deploy when the confidence sequence excludes 0.
3. **Sawade et al. 2012**: power-optimal sampling for two models under a fixed budget.
4. A generic **SPRT / Chernoff-stopping** two-arm rule.

Items 1 and 2 are the ones that could show our rule adds nothing.

## 6. Assessment

**Both halves of the proposed paper are substantially pre-empted.**

The constructive half — stop buying labels once the decision is settled — is DISCERN, with
theory we do not have. The structural half — the acquisition collapse — is Sawade 2012, named
`active!=`, with Model Picker's own appendix carrying the formula.

That is as clear a negative result as a prior-art check can produce, and finding it now costs us
a day instead of a review cycle.

Two defensible routes remain, and the choice is a research decision, not a technical one:

**(a) Narrow and honest.** Position as the *combined cost model* plus the collapse demonstration,
cite DISCERN and Karampatziakis as the stopping-rule precedents, and show empirically whether an
economically-triggered stop beats a certificate-triggered stop under a hard budget and delay. The
contribution becomes modest and precise.

**(b) Reconsider the target.** If the empirical difference against DISCERN-style stopping turns
out to be negligible, there is no paper here, and the right call is to say so.

Either way the next step is the same: **implement the three missing comparators and run them.**
Nothing should be drafted until we know whether our rule beats a certificate-triggered stop.

The gate file stays at `IN PROGRESS — SOTA GATE NOT MET`.
