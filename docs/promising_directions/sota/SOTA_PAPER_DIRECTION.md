# Rethinking the paper: what we actually have

Written 2026-11-03, after all six mandatory competitors were implemented and five verified
against their author code. This is a research-direction assessment, not a result.

## The three assets, honestly weighed

**1. The five-way collapse.** Five published acquisition methods provably reduce to
disagreement-gated sampling in a two-frozen-model binary task, established five independent ways,
four of them verified against author implementations. The variance-minimisation case is exact
(`score = 1[disagree]`, surrogate cancels); the Model Selector case is proved for any number of
classes, any posterior, any epsilon.

**2. Settled-decision acquisition (P7s).** A strict efficiency gain on the certified baseline:
20-67% fewer labels with *bitwise identical* deployment behaviour on four of five real cases.
Small in net cost (0.2-3.8%), mechanically transparent, and it satisfies an exact scaling law that
a fitted effect would not.

**3. The comparison infrastructure.** A common simulator with hidden labels, frozen propensities,
hard budgets and delayed release, plus faithful ports of six published methods with every
adapter deviation and every irreproducibility recorded.

## The problem with the original framing

The brief's gate — beat every mandatory competitor on net cost — is now in tension with what we
learned while building it. If we win, the collapse means we won against methods whose instance
selection was inert in this regime. We would have to disclose that, and the disclosure
substantially deflates the claim. "We beat the state of the art in active model selection" would
be true in letter and misleading in substance.

That is not a reason to hide the collapse. It is a reason to stop pretending the horse race is
the interesting part.

## The recommended framing

**The collapse explains why a simple economic rule can compete with sophisticated acquisition.**
The two assets are not separate papers; one is the mechanism for the other.

> In two-frozen-model binary deployment, instance-level acquisition has nothing to work with: the
> single bit of pre-label information is consumed by the disagreement gate every method applies.
> What remains available is *when to stop paying* — and that is where the gains are.

Under this framing P7s stops being "a 2% improvement on P3b" and becomes the constructive half of
a structural claim: having shown instance selection is vacuous here, we show what is not vacuous,
and the exact `c_q` scaling law becomes direct evidence that the gain is purely economic.

## This makes the comparison better, not unnecessary

The collapse yields **falsifiable predictions**, so the experiments the brief demands become a
test rather than a horse race:

- **H1.** All five collapsed methods perform within noise of matched-rate disagreement sampling.
- **H2.** Net-cost differences among them are explained by query-*rate* schedules and stopping
  behaviour, not by which instances they pick.
- **H3.** Our advantage decomposes entirely into the `c_q N_q` term, as it already does against
  P3b.

If H1 fails, the collapse does not bite in practice and we report that — which would be a real
finding against our own thesis. **The SOTA gate work is not wasted under this framing; it is
promoted from supporting evidence to the test of the central claim.**

## Risks, stated plainly

1. **"Obvious in hindsight."** The strongest mitigation is that five independent research groups
   built machinery that is inert here, and the fact was neither stated nor measured by any of
   them. Verified-against-author-code derivations make it a finding, not an observation.
2. **Narrow setting.** It holds for two models with binary labels and hard predictions. We must
   state the boundary precisely, including where it *stops*: variance minimisation discriminates
   at K>=3, Model Selector at >=3 models. The counter-argument is that incumbent-versus-challenger
   is exactly two models, which is the common production case.
3. **Prior art is not yet cleared.** Two targeted searches found no statement of this result, and
   the nearest work (CODA, Kay et al., ICCV 2025) argues the *opposite* direction: that methods
   wrongly ignore agreement structure, with a premise requiring many models and categories.
   **That is not a sufficient novelty check.** Before any claim is drafted, a full prior-art
   search is required, and the result may be that someone has said this in a footnote.
4. **The positive contribution is modest.** P7s remains a small effect. Under the new framing it
   does not have to carry the paper, but it must not be oversold either.

## Recommendation

Pivot to the structural result, keep P7s as the constructive half, and **run the full comparison
as a test of H1-H3**. Keep `SOTA_COMPLETION_GATE.json` as it is: the gate is about net cost and it
is not met. This document does not change that status, and reframing the paper is not a substitute
for running the experiments.

**Required before drafting**: a proper prior-art search on the collapse claim. If it is known, the
paper reverts to the efficiency result and the collapse becomes a well-evidenced section rather
than the contribution.
