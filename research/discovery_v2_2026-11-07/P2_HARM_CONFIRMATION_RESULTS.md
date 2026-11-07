# P2 harm-attribution confirmation — results

Protocol: `P2_HARM_CONFIRMATION_REGISTRATION.md`, committed and pushed as 24dd05c6 before any twin stream was built on the three
datasets. Outputs: `outputs/p2_confirm_rates.csv`, `outputs/p2_confirm_verdicts.json`. Run provenance:
`outputs/discovery_v2_p2_confirm/RUN_RECORD.md` (not committed). It records one runner failure and one kill, both handled
without changing the protocol.

Data: tetouan_power (360 episodes), steel_energy (240), seoul_bike (40). All three are UCI chronological streams that no earlier P2
analysis used.

## Frozen verdicts — **CONFIRMED**

| test | registered criterion | result | pass |
|---|---|---|---|
| HC1 (primary) | Δ = H_BSWAP − H_PERM, 95% lower bound > 0 | Δ = **0.00536** [0.00234, 0.00896] | ✓ |
| HC2 (primary) | H_PERM upper bound ≤ 0.005 | H_PERM = 0 (0 harmful promotions in 19,200 certified-port runs); upper bound 0 | ✓ |
| power guard | P_BSWAP ≥ 0.02 | P_BSWAP = 0.0776 [0.0646, 0.0916] | ✓ (powered) |
| HC3 | Δ > 0 on ≥ 2 of 3 datasets | tetouan +0.0082, seoul +0.0042, steel +0.0013 (3/3) | ✓ |
| S1 | ESWAP: every certified upper CI ≤ .0936 | max promote .022; 0 ports above the bound | ✓ |
| S2 | BSWAP: ≥ 3 of 10 ports break | 6 / 10 | ✓ |

Pooled certified-port rates (promote / harmful):

| condition | promote | harmful |
|---|---|---|
| ORIG | .189 | .0021 |
| PERM | .148 | 0 |
| BSWAP | .078 | .0054 |
| ESWAP | .0016 | 0 |

PERM still breaks 8/10 ports, and ORIG breaks 8/10. This replicates the earlier finding that the per-split effect alone drives gates
past the marginal bound, and that this produces no harmful promotion.

## What the confirmation does and does not show

* **Confirmed claim.** On three new real streams under the exchangeable-twin construction, certified-gate promotions driven by the
  split fixed effect were never harmful. Promotions driven by serial dependence alone (100-event block swaps) were harmful at a small
  but nonzero rate, about 0.5% of runs and about 7% of the promotions those runs made. The gates stayed valid under the exact
  per-event null.
* **Magnitude.** The absolute harm is small. The highest cell is SMCS on tetouan, .031 [.017, .048]. For comparison, the uncertified
  selectors (Model Picker, CAMS) are harmful in 24–46% of runs under every condition, including ESWAP.
* **Concentration (post-hoc sensitivity, not registered).**
  * Removing SMCS gives Δ = .0032.
  * Removing tetouan gives Δ = .0017.
  * The harm comes mostly from SMCS on all three datasets and from the Choe–Ramdas and gated ports on tetouan. On steel and seoul,
    only SMCS has nonzero harm.
  * The effect is therefore real in the pooled test, but it is port- and stream-specific, not uniform.
* **Partly mechanical component (stated in the registration).** PERM keeps the episode advantage and makes the stream
  exchangeable, so HC2 largely re-tests validity under an i.i.d. null. HC1 carries the substantive content.
* **Scope.**
  * Results hold for one twin construction, one block length (100), and common-contract ports at HEAD, without the MOPE fixes.
  * seoul_bike contributes only 40 episodes.
  * This is not a claim about native implementations or other dependence structures.

## Consequence for P2

The exploratory harm decomposition in `DISCOVERY_DECISION.md` §1 is now **CONFIRMED** within the stated scope. P2 stays at
**class B**, now with a confirmed, decision-relevant finding:

> Marginal-bound violations by certified gates on persistent streams split into a benign fixed-effect part and a smaller,
> harmful dependence part.

It is not class A yet. Moving up needs:
1. a block-length dose–response check;
2. the MOPE code-fix replay;
3. author-code comparators;
4. the prior-art audit.
