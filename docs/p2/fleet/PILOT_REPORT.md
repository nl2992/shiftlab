# Fleet-level certified promotion: pilot report (2026-11-10)

**Verdict: NO-GO** for the two fleet levers tested. Neither reduces cost, and the reason is
structural, not a tuning gap.

Code: `scripts/p2/fleet.py`, `scripts/p2/fleet_summary.py`. Prior art: `_lit_fleet.md` (model-assisted search,
not exhaustive). Runs: `outputs/p2/fleet_s1` (synthetic) and `outputs/p2/fleet_c4` (real). Neither is in Git.

## Design

A fleet is an ordered sequence of promotion episodes on QSG's skeleton. Two arms were tested.

**`eb` (pooled bets).** The betting prior over the challenger edge is a kernel posterior of earlier
episodes' estimated edges. It is fixed at episode start, so validity is unchanged.

**`lond` (online FDR).** e-LOND: episode k promotes at α_k = α·γ_k·(R_{k−1}+1). The episode e-value
is Σ_c 2^{−c} E^{(c)} stopped at its crossing. FDR ≤ α holds under arbitrary dependence. Episodes are
sequential, so the stopped-e-BH and asynchronous-testing caveats in `_lit_fleet.md` do not arise.

## Results

### Synthetic fleets

Setting: 30 fleets × 60 episodes; edge p ∈ {.55,…,.8}; iid; seed base 2026111001. J and its delta
are per episode; the delta is vs `base` with a fleet-clustered 95% CI.

| π0 (null share) | eb ΔJ | lond ΔJ | FDR base / eb / lond |
|---|---|---|---|
| .2 | −0.66 [−1.03, −0.29] (−0.2%) | +8.41 [+7.72, +9.09] | .005 / .003 / .000 |
| .5 | −0.03 [−0.30, +0.24] | +6.61 [+6.11, +7.14] | .020 / .011 / .002 |
| .8 | +0.36 [+0.20, +0.52] | +3.16 [+2.60, +3.73] | .083 / .063 / .011 |

### Real C4 fleets

Setting: 27 sources, episodes in chronological order, 2,097 episodes. These sources were already
opened in the P2-NAD confirmation, so this is development evidence.

| Arm | Source-equal ΔJ vs base | Wins |
|---|---|---|
| eb | +0.18 (+0.04%) | 14/27 |
| lond | +3.51 (+0.81%) | 3/27 |

## Why it fails (mechanism)

1. **A prior buys only a log factor.** A uniform prior over 10 grid points costs at most log 10 ≈
   2.3 nats of the ~3.7 nats needed. Certification time is set by label delay (100 events) and
   per-label information (KL ≈ .02–.1). It is not set by prior regret. The ceiling for prior
   knowledge inside a valid certificate is therefore small. That matches the ≤ 0.2% observed.
2. **Fleet error control can only be stricter.**
   - e-BH rejects when e ≥ K/(αR), which is at least 1/α since R ≤ K.
   - LOND-type spending gives α_k < α until R is large.
   - Any FDR guarantee is therefore at least as strict as an independent α per decision. A fleet
     guarantee is a stronger statement, not a cheaper one.
3. **Within-source "fleets" are really one long deployment.** In C4 the incumbent and challenger
   are the same frozen models in every episode of a source. The benchmark's per-episode reset to
   the incumbent is an artefact.
   - A real deployment would carry the decision and the e-process across windows.
   - Every method would gain from that.
   - It is a benchmark-framing correction, not a method contribution.

## Implications

- Cross-stream pooling of the betting prior is not a viable route to a main-track method under
  this contract.
- The finding sharpens the overall picture. Per-decision cost is limited by delay and per-label
  information, not by statistical machinery. The large remaining gaps (V1 vs robust certificates,
  ~10%) are paid for by validity, and on real data that validity is economically cheap to give up
  (P2-NAD C7).
- The one concrete lever left is outside certificate design: **feedback delay and its timing**.
  Methods could exploit cheaper or earlier proxy feedback, but SAES found proxies weak on the
  current streams. They could also change the contract itself: carry-over deployment across
  windows, or shorter delays at a price. Delay was the dominant cost driver in every
  decomposition. A main-track contribution would most plausibly come from a new information
  source, not a new test.
