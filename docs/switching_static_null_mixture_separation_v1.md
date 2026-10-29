# Causal-null risk is not a mixture of fixed null kernels

**Date:** 2026-10-28. **Status:** exact two-label separation; supports the information contract, not a new algorithm.

## Contract and proposition

Request two binary common-outcome labels at events 1 and 2, with deterministic release delay 2; decide after both labels arrive. The hard query budget is B=2. Under the global null, at each event the conditional success probability may be any value in `[0,1/2]` chosen using the full event-time past. Let the terminal promotion event be `E={Y1 != Y2}`.

The worst causal-null promotion risk is `3/4`. In contrast, under any fixed nonadaptive product kernel with `Y1~Ber(q1)` and `Y2~Ber(q2)`, where `q1,q2∈[0,1/2]`, `P(E)=q1+q2-2q1q2≤1/2`. Any mixture over such fixed kernels also has risk at most `1/2`, since its risk is the average of the component risks. Hence the risk gap is exactly `1/4`; for any `alpha∈(1/2,3/4)`, fixed-kernel mixture calibration accepts this promotion rule while the causal conditional-null contract rejects it.

**Proof.** Write `p1=P(Y1=1)`, `p20=P(Y2=1|Y1=0)`, and `p21=P(Y2=1|Y1=1)`. Then

`P(E)=(1-p1)p20+p1(1-p21)`.

Over `[0,1/2]^3`, this is maximized at `(p1,p20,p21)=(1/2,1/2,0)`, with value `3/4`. For a fixed product kernel, the event probability is `q1+q2-2q1q2`; its maximum on `[0,1/2]^2` is `1/2`. Convex mixtures cannot increase the maximum of a linear event probability. The exact endpoint enumeration is in `scripts/check_switching_static_null_mixture_separation.py`; results and script hash are in `outputs/switching_static_null_mixture_separation_v1/results.json`.

## Consequence

The causal adversary can exploit event-time history even when the learner cannot yet observe a pending label. A Bayesian mixture over stationary IID nulls or over fixed time-varying independent null kernels is not a valid substitute for the declared conditional null. This gives a sharper comparator boundary than an IID-only calibration counterexample. Full-history state augmentation can represent the adaptive null, but the exact safe planning state must retain its history dependence; the gap does not itself establish that a compact risk statistic is impossible.

The event is nonmonotone in the labels, so this does not contradict the monotone-event theorem reducing causal risk to IID risk. It also does not prove any algorithmic or complexity lower bound. The source-level audits of robust POMDPs and partially observed games remain relevant: a useful method must preserve causal risk while compressing or approximating the full history game, and prove its economic performance against that oracle.

## Decision

Reject fixed-kernel mixture calibration as the risk model for nonmonotone promotion events. Preserve the causal conditional-null contract. This separation is a feasibility/comparator result only; no efficacy evaluation follows.
