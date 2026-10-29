# Switching source audit v2: theorem boundaries

> Additional primary-source reads and an implemented reference are recorded in
> [the delayed-switching extension audit](switching_delayed_comparator_audit_v1.md).
> The interleaving counterexample below is a warning about one reduction, not a gap claim.

2026-10-28. **Decision: broad combinations are not a contribution; narrow mechanism search
continues.** The previous turn was progress (contract, source-access record, preservation anchors).
This checkpoint resolves PDF access and inspects selected method/theorem/proof passages. It is
not an exhaustive literature review or an independent proof verification of these papers.

## Source provenance and reading scope

Seven PDFs were downloaded directly from primary hosts and extracted with `pdftotext -layout`.
The reproducible URL, byte count and SHA256 records are in `switching_source_manifest_v1.json`.
Local cache: `outputs/switching_source_audit_v1/` (ignored; do not commit third-party PDFs).
Cheng p.7 and Lindon p.8 were rendered and visually inspected to verify formulas and theorem labels.
Numbers below refer to printed PDF pages/section labels, not browser search snippets.

### Cheng, Zhou and Ji (ICML 2023)

[Primary source](https://proceedings.mlr.press/v202/cheng23f/cheng23f.pdf).
Read Section 2, Section 4, Algorithm 1, Proposition 2 and its Appendix C proof. The adversary is
oblivious; regret includes unit switching costs against the best *fixed* action. Section 4 counts
individual action-loss observations, not common-outcome labels. Theorem 2 characterizes minimax
regret as soft-Theta(T sqrt(K/B)). Batched mirror descent with shrinking dartboard, uniform
within-batch sampling and full-information feedback gives Proposition 2's O(T sqrt(K log K/B)).
The proof combines an unbiased batch-loss estimate, a mirror-descent bound and a switch bound.

For two common-outcome policies, B labels reveal 2B action losses; translate budgets explicitly.
This paper defeats a claim of novelty from observation budgets plus switching costs alone.
It does not by itself supply our delayed, dynamic-comparator, statistically safe switching theorem.
Changing all three dimensions is a research burden, not proof of an open gap.

### Digalakis et al., The Challenger (arXiv v2)

[Primary source](https://arxiv.org/pdf/2512.18390v2).
Read Sections 3.2–3.3 and EC.1.3's proof of Theorem 2, supplementing the repository fidelity audit.
Adoption/discard is irreversible in the core model. The meta-regret theorem uses finite VC
dimension, ERM, bounded binary gain and high-probability conditions on terminal timing and
decision consistency. Its proof bounds generalization error, sunk evaluation cost and terminal
decision error; the theorem does not require the power-law learning curve assumption.

Therefore the refinement matrix's statement that the regret guarantee needs a parametric
learning curve is too strong. The parametric assumption concerns the oracle timing analysis.
Costed look-ahead switching is established prior work. Reversals, a hard query cap and label
delay are not established by this theorem. A confidence sequence replacing epoch bounds alone
would not substantiate a methodological advance.

### Lamaakal et al., Drift2Act (arXiv v1)

[Primary source](https://arxiv.org/pdf/2603.08578).
Read Section 5.2–5.3, Appendix D.1–D.4 and D.7, including Theorem A.2's proof. Appendix **D**,
despite the theorem's A.2 numbering, is the correct proof location. The label cap is explicit.
The action objective uses a calibrated gain table and one-step cost/violation utility, rather
than solving the sequential control problem. Its proof uses bounded-loss concentration under
uniform window auditing and summable error allocation over sample counts and windows.

The certificate concerns a window's risk, not future post-switch economic gain. Delayed arrived
subsets still require the stated sampling/representativeness conditions: Appendix D.7's eventual
sample-size argument must not be transplanted into arbitrary outcome-dependent arrival ordering.
Do not assert their theorem is invalid or claim a new delay theorem without an exact counterexample.

### Lindon and Kallus (arXiv v2, corresponding ICML paper)

[Primary source](https://arxiv.org/pdf/2603.25971).
Read Theorems 4.4, 4.6, 4.9, Proposition 4.8 and Appendix A.1–A.2's relevant proof steps.
The target is design-based cumulative counterfactual reward by calendar time. Theorem 4.4
characterizes event-time martingale-preserving augmentations. Theorem 4.6 explicitly gives an
**asymptotic** confidence sequence using strong approximation and a Gaussian-mixture boundary;
Theorem 4.9 combines arm intervals. Proposition 4.8 supplies a cross-time covariance obstruction
to treating the generic treatment-effect error as a martingale under one filtration.

Correct the earlier broad summary: this displayed boundary is not a finite-sample guarantee.
That distinction alone is not our contribution: bounded-martingale finite-sample tools already
exist. The future switching-benefit target is also distinct from their calendar-time reward target.

### Gafni, Iyengar and Zeevi (arXiv v2, corresponding ICML paper)

[Primary source](https://arxiv.org/pdf/2602.11406).
Read Section 2, Theorems 4.1–4.2 and their proof sketches. Observations are independent,
piecewise IID with sub-Gaussian noise. The learner predicts an unknown changing mean using
the full observed history; the objective is cumulative squared tracking error. ATC controls
missed-change contamination and obtains near-minimax change-count-dependent regret.
These theorems do not directly establish a two-policy costed switching guarantee under a hard
query cap. Mean-estimation success is not economic intervention success. Full appendix proof
verification remains unperformed; no new claim depends on contradicting their theorem.

### Ginart, Zhang and Zou, MLDemon (AISTATS 2022)

[Primary source](https://proceedings.mlr.press/v151/ginart22a/ginart22a.pdf).
Read the Lipschitz deployment formulation, algorithm bias correction and Appendix B.2.2,
especially Lemma B.19. It already corrects label-based concentration for drift using average
sample age times a drift bound. The theorem programme concerns monitoring risk and query cost.
Our candidate's simple sample-age correction is inherited mathematics, not a new mechanism.
Adaptive selection conditions must be separately justified for any new use of the bound.

### Joulani, Gyorgy and Szepesvari (ICML 2013)

[Primary source](https://proceedings.mlr.press/v28/joulani13.pdf).
Read Section 3.1, Algorithm 1 (BOLD), Theorem 1 and its proof. It routes rounds to available
base instances; the regret proof sums their individual rewards. Delay is independent of the
prediction in that theorem. Switching costs depend on *adjacent global actions* and do not
decompose this way. A direct black-box application does not retain Cheng's switch accounting.
This is a missing composition proof, not evidence that no published delayed-switch method exists.

## Exact composition obstruction

**Elementary proposition, no originality claim.** Suppose fixed delay requires two interleaved
instances, used alternately. Losses for both actions are identically zero. Each instance's shrinking
dartboard initializes independently uniformly on {0,1}, and never switches internally (zero loss
makes its retention probability one). Each has zero decision regret and zero internal switch cost.
With probability 1/2 their initial actions differ; then the global sequence switches on every
round after the first. Expected global switch cost is k(T-1)/2. Thus summing internal switch
counts cannot bound global switch cost. This does not refute BOLD's theorem, whose loss model
is not this global path-dependent cost. It does not separate us from all delayed-switch algorithms.

## Consequences for mechanism search

1. Reject 'budgeted switching + e-process + delay buffer' as the contribution.
2. Reject 'past confidence bound + sample-age drift penalty + economic hurdle' alone: MLDemon
   already supplies the drift correction and challenger economics supplies the costed decision.
3. Do not import asymptotic inference as a finite-budget statistical safety theorem.
4. A possible substantive target is a single deployed action process whose acquisition decisions
   exploit pending evidence and economically useful time, with a *joint* hard-budget and global
   switch-cost proof. A generic multi-instance reduction cannot be the whole derivation.
5. Still open: strongest direct delayed-switching algorithms, active sequential decision design,
   their dynamic-comparator bounds and whether they already implement this coupling.

**Gate state:** source-access obstacle cleared. G1 is not passed: the precise new advantage
and strongest equally equipped algorithm are not yet established. Next perform the analytical
mechanism pre-screen in `switching_mechanism_screen_v1.md` and audit direct delayed-switching
prior art. Do not advance to a paper or claim novelty from these distinctions.
