# Observation control, switching cost, and change detection: prior-art boundary

**Date:** 2026-10-28. This is a focused source read, not an exhaustive novelty search or a claim that the remaining combination is novel.

## Primary source

Tze Siong Lau and Wee Peng Tay, “Asymptotically Optimal Sampling Policy for Quickest Change Detection with Observation-Switching Cost,” IEEE Transactions on Signal Processing 69 (2021), preprint [arXiv:1912.11693](https://arxiv.org/abs/1912.11693). The primary preprint PDF and extracted text are cached under `outputs/switching_source_audit_v1/lau_tay_observation_switching_cost.*`; provenance is recorded in `switching_source_manifest_v7.json`.

## What it already does

The paper jointly chooses a sampling-action policy and a GLR-CuSum stopping time. It assumes known pre/post-change distributions and action-conditional observation laws, imposes an average run length to false alarm (ARL) constraint and a long-run average observation-switching-cost (AOSC) constraint, and minimizes Lorden worst-case average detection delay. For finite-window open-loop sampling policies, it derives asymptotic ARL–WADD performance, optimizes the sampling policy through a quadratic program, and proves that a window-size-one policy suffices for the asymptotically optimal open-loop design. It also proposes a two-threshold stopping procedure with observation-dependent sampling and feasibility guarantees for the ARL/AOSC constraints.

The paper motivates the setting with sensor processing/communication latency (including an example of 300–400 ms before observations are processed), but that is not a delayed-label filtration in its theorem: the sampling policy's observation history is used as available, and the formal model does not queue requested outcomes for release after a fixed delay. Its decision is a one-time irreversible stopping declaration. Its false-alarm criterion is ARL, not a finite-horizon probability of ever making a false 0-to-1 deployment under a composite conditional null. Its cost constraint is long-run average switching among sensing actions, not a pathwise total query cap plus economic switching between deployed models.

## Consequence for the research claim

This prior work closes a second broad framing: “jointly optimize information acquisition and switching costs subject to false alarms” is already an established problem family. The result is scoped and asymptotic, but a new paper cannot claim the broad combination as novel merely by replacing ARL with alpha, making decisions reversible, or adding a delay buffer. The ICML 2026 paid-observation result separately closes the generic hard-budget acquisition-plus-action-switching-regret premise.

The only plausible remaining target from the current charter is a specific finite-sample separation for *repeated reversible deployment* under (i) fixed or known delayed label release, (ii) a pathwise cap on paired model-comparison queries including pending requests, (iii) an anytime global false-promotion guarantee under the declared conditional null, and (iv) a dynamic economic comparator with explicit switch charges. This list is a problem boundary, not evidence of novelty. Before designing a controller, the next derivation must show why known QCD sampling-control reductions, paid-observation switching algorithms, delayed Hedge/online-learning reductions, and standard constrained sequential design do not already imply the claimed theorem. If the only result is the conjunction of those existing guarantees under compatible assumptions, stop the novelty claim and revise the research hypothesis.
