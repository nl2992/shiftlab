# P1: why A5b loses power under persistence, and what was tried

Code is in `scripts/sota_sprint/fam_p.py` (`RenewalEvidence`, `CapMixture`, `UnionEvidence`, `FamP1`, `p1_diag`).
Raw outputs are in `outputs/sprint2/P/p1diag/p1diag.json` and `outputs/sprint2/P/dev_syn/`.
All results here are development evidence.

## 1. Formal diagnosis

The queried sign chain follows "keep w.p. a, else redraw Bernoulli(p)", where a = rho^gap. In hazard form:

* the exit rate from a favourable run is h1 = (1-a)(1-p);
* the exit rate from an unfavourable run is h0 = (1-a)p.

For 0 <= a < 1, the map (p, a) -> (h0, h1) is one-to-one, and the null p <= 1/2 is exactly
h0 <= h1. At the boundary a=1 both exit rates are zero for every p, so p is not identifiable from
the sign chain; the argument and the reported information calculations concern a<1.
For the interior a < 1, the null restriction p <= 1/2 is equivalent to h0 <= h1. Evidence about
that inequality comes from observed transitions and run exits; long persistence makes these
informative transitions rarer at a fixed query budget.

**Fisher information** (per step, p = .6; `fisher_efficiency`):

| a | I(p), rho known | I_eff(p), rho free | ratio |
|---|---|---|---|
| 0 | 4.17 | 4.17 | 1.00 |
| .25 | 2.52 | 2.50 | .99 |
| .5 | 1.41 | 1.39 | .98 |
| .8 | .48 | .46 | .97 |
| .95 | .11 | .11 | .96 |

Not knowing rho costs at most 4% of the information on this grid. The larger loss comes from
persistence itself: at a = .8, I(p) is about 9x smaller than at a = 0, even with rho known. At a
fixed query budget and gap, a test cannot create information absent from the queried chain; more
queries or wider query gaps can offset some of this loss.

**Simulation** (100 queries, 100 reps, seed 2026110790). Every quantity is a mean log e-value in
nats. The "oracle" is the conditional LLR of the true alternative against p = .5 at the true rho.

| p, rho, min gap G | oracle | single-start SUI | absorbed by null sup | alt-mixture misfit | renewal |
|---|---|---|---|---|---|
| .65, .8, G=1 | 2.4 | -2.0 | 1.5 | 2.9 | 1.2 |
| .65, .8, G=7 | 3.7 | 0.9 | 1.4 | 1.4 | 2.6 |
| .65, .8, G=12 | 4.0 | 1.7 | 1.2 | 1.1 | 2.8 |
| .65, .95, G=7 | 1.1 | -3.0 | 1.2 | 2.9 | 0.4 |
| .65, 0, G=1 | 4.5 | 2.4 | 0.8 | 1.2 | 3.2 |

* **Not reproduced: 18.5 of 20.5 oracle nats.** I could not reproduce the sprint-1 figure of 18.5 of
  20.5 oracle nats. With this oracle definition the total available evidence after 100 queries at
  p=.65, rho=.8 is only 2.4–4.0 nats. The composite-null sup absorbs 1.2–1.5 nats of it, and the
  alternative mixture loses another 1.1–2.9.
* **The alternative mixture loses more than the null absorbs.** fam_a._B puts .7 prior mass on
  rho'=0, so a persistent alternative is fitted badly at small gaps.
* **Decorrelating the queries helps both sides.** Moving from G=1 to G=12 raises SUI from -2.0 to +1.7.
* **The budget makes power low regardless of construction.** The oracle only reaches the cycle-1
  threshold log(40)=3.7 at about G>=7, so even a perfect test has modest power at this budget.

## 2. Constructions and their validity status

| construction | null bound | status |
|---|---|---|
| `RenewalEvidence` (conditional run-length) | **proved** for the first-order chain with i.i.d. gaps independent of signs (proof in module docstring: MLR domination of the conditional law of L1 given L1+L0) | brute-force test `test_renewal_bruteforce_null_any_persistence` (rho .0/.8/.98) |
| `UnionEvidence` = SUI or renewal at alpha/2 each | union bound | inherits both |
| A5b with c_corr = .10 / .05 (`P1_A5b_c10/_c05`) | unchanged: SUI conditions on the realised predictable gaps | proved (fam_a) |
| `P1_cap95`: SUI with declared cap rho <= .95 | valid **only** for rho <= .95 | dev: .20 false promotion at rho=.98 |
| `P1_capmix`: max_i w_i SUI_{rho<=c_i} | **INVALID** for the free-rho null | dev: .90 at rho=.95, 1.00 at rho=.98 |

**Why the requested cap mixture is invalid.** A union bound P(any rejects) <= sum_i alpha w_i needs
every component to be valid under the true rho. A component whose cap is below the true rho is not
a supermartingale (`test_capmix_invalid_component_documented`). I also tried combining it with a
preliminary test of {rho > c}, which is valid. It recovers nothing: on persistent data the
composite-null sup sits at high rho, so rejecting {p <= 1/2, rho > c} is as hard as rejecting the
free null.

`RenewalEvidence` needs i.i.d. gaps. `FamP1(discard=False)` therefore uses a single pre-promotion
query regime with a data-independent spacing (G = 7, chosen from the diagnostic above, not from
screen seeds). A bursty-disagreement null (`P_bursty_null_r8`) is included to stress that premise.

## 3. Development screen

Setup: 20 seeds, base 2026110701, 23 regimes (`outputs/sprint2/P/dev_syn`). Values are paired ΔJ
against A5b with 95% CI.

| regime | P1_renew | P1_union | P1_sui_fixedgap (ablation: no renewal) | P1_A5b_c10 |
|---|---|---|---|---|
| F5_dep_better_r8 (targeted) | **-14 [-26,-1]** | -9 [-18,0] | -7 [-16,+2] | +2 |
| S_dep_better_r95 (targeted) | +3 | +3 | +4 | -1 |
| F0_better (iid) | +27 [+13,+42] | +34 | +36 | 0 |
| F9_bursty_better | +47 | +41 | +39 | 0 |
| P_hmm_better / P_piecerho_better | +38 / +39 | +34 / +40 | +32 / +30 | ~0 |
| S_reversal_400 | -31 [-46,-17] | -20 | -17 | 0 |

* **Null promotion.** On the nine other screened null regimes, P1_renew,
  P1_union, P1_sui_fixedgap and P1_A5b_c10 each had 0/20 promotions. These include the
  semi-Markov, order-2, bursty, piecewise-rho and rho=.98 nulls. In the separate out-of-class
  `P_hmm_null` stress, P1_renew, P1_union and P1_sui_fixedgap remained at 0/20, while P1_A5b_c10
  matched A5b at 3/20 (.15); see the P4 discussion. This HMM observation does not test an in-class
  guarantee.
* **Verdict: SCREENED_NEGATIVE as a power repair.**
  * Fixed spacing without a discard verdict buys power on the persistent first-order alternative
    and reversal savings. Most of that comes from the spacing and the missing discard; renewal adds
    about -7 nats-equivalent on F5_r8, with an overlapping CI.
  * It pays +27 to +47 on iid, bursty and hidden-state alternatives.
  * Adaptive spacing (c_corr) changes nothing.
  * For the spaced rho=.8 cases (G=7,12), the remaining oracle-to-SUI gap is 2.8 and 2.3 nats;
    at G=1 it is 4.4 nats, so the gap is not uniformly small. Under this budget and contract,
    persistence destroys much of the available information, while both the composite null and the
    alternative mixture contribute to the remaining gap.
