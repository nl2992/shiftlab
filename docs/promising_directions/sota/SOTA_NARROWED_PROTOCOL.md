# Narrowed protocol: does an economic stop beat a certificate stop?

Registered 2026-11-03, **before** any of the three new comparators was implemented and before any
comparison was run. The prior-art check (`SOTA_PRIOR_ART.md`) established that both halves of the
previously proposed paper are pre-empted. This protocol defines what is left, and the condition
under which we stop.

## 1. The narrowed claim

Everything about *disagreement-only acquisition* and *stopping once a decision is settled* is
prior art (Sawade 2012 `active!=`; DISCERN arXiv:2609.17560; Karampatziakis et al. ICML 2021
gated deployment; classically SPRT). We claim none of it.

What is left, and all we will claim:

> **Under a hard label budget, delayed label release and an explicit switching cost, stopping
> acquisition when the *economic* deployment decision can no longer change yields lower net cost
> than stopping when a *statistical certificate* fires.**

The distinction is the trigger:
- **Certificate trigger** (prior art): stop when the evidence is conclusive at level `alpha`.
- **Economic trigger** (ours): stop when no further label could change the deployed action, given
  the switching cost `c_s` and the remaining horizon `T - t`.

These differ exactly when the certificate fires but switching is not worth `c_s`, or when the
certificate has not fired but the decision is already economically determined.

## 2. Comparators that decide it

Three, implemented faithfully, each stopping on a certificate rather than on economics:

1. **DISCERN-style** — disagreement-restricted sampling with an anytime-valid betting confidence
   sequence, stopping when a Safe/Regression verdict fires. The closest prior art to our rule.
2. **Gated deployment** (Karampatziakis, Mineiro & Ramdas, ICML 2021) — deploy when the lower
   confidence sequence crosses 0, discard when the upper does, stop on either.
3. **Sawade 2012** — both the `active!=` degenerate form and, where a calibrated `p(y|x)` is
   available from development data, the instance-dependent form, since Sawade's own hedge is that
   calibration preserves instance information.

All run in the same simulator, on the same streams, with the same budget, delay and costs, and
with acquisition held fixed where the comparison is of stopping rules.

## 3. Pre-registered outcome rule

Primary test, on the two **properly powered** cases only (**rialto**, K=16; **openml_ldpa**,
K=32), at the primary configuration:

- **CONTINUE** if the 95% paired CI of `ours - best_certificate_stop` net cost lies **below 0 on
  at least one** powered case and is not above 0 on the other.
- **STOP** if the interval **straddles 0 on both** powered cases. A tie means the economic trigger
  does not pay for itself, and the programme ends with that recorded.
- **STOP** if we **lose** on either powered case.

The three low-power cases (spam K=1, weather K=3, uci_occupancy K=4) are reported but **cannot
decide** this. Seed-level bootstraps do not establish an episode-level effect, and that rule has
held throughout this programme.

## 4. Mechanism prediction, stated before the run

If the economic trigger helps, the gain must appear in the decomposition as:
- **fewer switches** (certificate fires, switch not worth `c_s`), and/or
- **fewer labels after the decision is economically settled but before the certificate fires**.

It must **not** appear as lower deployment loss, since neither trigger changes which model is
better. If the gain shows up as deployment loss, the result is an artefact and will be
investigated rather than reported.

## 5. What a positive result would and would not support

Would support: a short, precise contribution — in budgeted, delayed, switching-cost deployment,
the stopping trigger should be economic rather than statistical, demonstrated against the
published certificate-triggered alternatives.

Would **not** support: any claim to disagreement-only acquisition, to stopping-once-settled as an
idea, or to the acquisition collapse. All are prior art and will be cited as such.

## 6. Scope corrections carried forward

- The collapse claim holds for **hard predictions only**. Sawade's calibrated `p(y|x)` form
  retains instance information, and we will say so.
- `SOTA_COMPLETION_GATE.json` keeps its original meaning. This protocol does not redefine the
  gate; it defines the condition under which we stop trying to meet it.
