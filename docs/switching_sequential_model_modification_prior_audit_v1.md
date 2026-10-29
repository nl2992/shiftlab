# Sequential model modification with reusable test data: novelty boundary

**Date:** 2026-10-29. **Status:** primary-source theorem-scope audit; no new method claim.

## Source and inspected results

Feng, Pennllo, Petrick, Sahiner, Pirracchio and Gossmann, “Sequential Algorithmic Modification with
Test Data Reuse,” UAI 2022, PMLR 180:674–684. I inspected the full PMLR paper, Algorithm 1,
Theorems 1–2, its two approval-path constructions, and the supplementary proof of the adaptive
strategy reduction and FWER argument.

The paper studies sequential model updates selected adaptively using a one-bit approve/reject report
from a reusable IID holdout set. Each update tests whether its expected loss is no worse than a
reference (the initial or most recently approved model), optionally with a meaningful-improvement
margin. The update choices form a binary history tree. Algorithm 1 uses sequentially rejective
graphical procedures (SRGPs) to allocate and recycle alpha across this adaptively explored tree.
Theorem 1 gives FWER control for a correlation-aware fixed-sequence SRGP; Theorem 2 gives FWER
control for a procedure that compares the adaptive update sequence with a prespecified hypothetical
update policy. The supplement proves that a fixed adaptive strategy corresponds to a prespecified
SRGP and extends validity to stochastic strategies by conditioning over them. The paper also reports
an eICU model-update application, so the overlap with sequential model replacement is direct.

## Consequence for ShiftLab

This source closes generic claims about (a) repeatedly approving adaptively proposed model updates,
(b) using a binary approval report to limit test-data leakage, (c) alpha recycling over an update
tree, or (d) exploiting correlations among candidate updates. A new controller cannot claim
novelty from adding an e-process/FWER gate to adaptive model selection or from comparing only with
static Bonferroni. Tian–Ramdas online FWER rules and Feng et al.'s adaptive SRGPs are mandatory
statistical baselines under whichever assumptions fit the exact test design.

The contract differs in specific ways. Feng et al. use a fixed IID reusable holdout and a finite
sequence of tests, with a binary approval result; they do not allocate a hard pathwise budget for
new labels, model unknown label delays, optimize acquisition timing, or charge economic deployment
and rollback costs. Their hypotheses measure update quality against a reference model, not whether a
challenger remains economically better in a changing hidden regime. Their results therefore close
the statistical model-update/alpha-recycling component, but not a theorem about query allocation and
reversible economic switching under delayed feedback. This gap remains only a comparison obligation
until a concrete result is established.

Any candidate must compare against adaptive SRGP/model-update baselines when the reusable-holdout
assumptions apply and against sequential online-FWER methods for adaptively arriving hypotheses.
It must then establish a gain that uses the added information structure—costed, delayed observations
and current-regime switching value—rather than merely restating repeated safe model approval. A
promotion-risk guarantee still does not certify benefit after a regime reversal; that requires
post-reversal evidence or a defensible persistence assumption.

## Decision

Reject generic safe sequential model modification as a new algorithmic contribution. G1 remains open
only for a theorem-level acquisition-and-switching result beyond adaptive SRGPs and online FWER
baselines, with matched hard-budget evidence later gated on G2. G2–G5 remain held.

## Provenance

- Official paper: [PMLR article](https://proceedings.mlr.press/v180/feng22a.html),
  [full paper](https://proceedings.mlr.press/v180/feng22a/feng22a.pdf), and
  [supplement](https://proceedings.mlr.press/v180/feng22a/feng22a-supp.pdf).
- Cached paper SHA256: `D4DBF1EC69DBBA48BD5C65F49A41D44541C3C9793A3AA274D6E9D85186C5E719` (1,566,879 bytes).
- Cached supplement SHA256: `416AD57C49478A4F7EAE1FBC282C3D7F692B2452DBB9F3FB8F7C526AD28618D5` (640,604 bytes).
- Selected source-scope and proof-route audit, not an independent reproof.
