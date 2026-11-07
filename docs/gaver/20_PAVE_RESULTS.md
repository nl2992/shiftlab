# GAVE-R WP2: PAVE (pending-aware value-of-label governor) results

Date 2026-11-06, branch `research/gave-r-2026-11-06`, base `main@7354480a`. Development/screening
only: no confirmation seeds, no claim beyond the cells listed. Code commit `a7116a16 (code), results in the commit after it (9912008e)`.

## Verdict (read this first)

**PAVE as specified fails screening. Stop rule: partially triggered, with one narrow positive.**

* Overall PAVE is worse than the frozen DSS: mean cost/round over 31 cells 0.4419 (reserve on) or
  0.4195 (no reserve) vs DSS 0.3874-0.3886, uniform 0.4203-0.4230, undecided-only 0.3785-0.3815.
* Mandatory regression cell 1, `f3_rho0_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1`: PAVE is
  **16-19% worse than DSS and 33-46% worse than the strongest in-repo comparator** (`episode_front`),
  CI excluding 0. Not repaired.
* Mandatory regression cell 2, `on0.6_L1_strong_harmful_d50_b0.05_s0.1` (where DSS is exactly
  uniform): PAVE improves by 4.9% (reserve on, CI excl. 0) and by **8.2%** (no reserve, fresh
  seeds, CI excl. 0) over uniform/DSS, and 1.5% (CI incl. 0) / **6.0%** (CI excl. 0) over
  `episode_front`, the strongest comparator there.
* The benefit is confined to the long-delay (d=50) cells. There PAVE beats uniform with the same
  evidence engine (mean +3.4%, 5 of 9 cells better, 1 worse) and undecided-only (+10.4%, 7/9
  better, 0 worse). At d=1 and d=10 it is worse than DSS in every cell where the difference is
  resolved (0 better, 13 worse of 22).
* Null: for rho <= 0.8 (B/T in {0.05, 0.1}, d in {1, 10}) PAVE's Clopper-Pearson 95% upper bound on false promotion is <= 0.0283 in all cells (reserve on, n = 210-500 streams per cell) and <= 0.0586 (reserve off, n = 120-140), versus DSS up to 0.269 at rho = 0.8. At rho = 0.95 (reported, not required) PAVE is not safe (UCB 0.119-0.453; DSS 0.65-0.79). The low PAVE FP largely reflects that it promotes less often, not a safety mechanism.
* Screening criteria (00_PLAN): (i) null FP UCB <= 0.1: **met** at rho <= 0.8 in the tested cells, but with fewer than the planned 500 streams in 12 of 16 cells; (ii) at least a small gain
  over the strongest in-repo comparator in target cells: **met in one of two** (d=50 cell yes, F3
  cell no, large loss); (iii) not materially worse in neighbours: **not met** (see tables; 13 of
  the 22 d<=10 cells are worse than DSS with CI excluding 0 in the reserve-off arm, none better).
  Overall: **fail**; an acquisition governor of this form is not a candidate for integration (WP5).
* Stop rule ("no attributable benefit over uniform with the same evidence"): there is an
  attributable benefit over uniform only in the d>=50 regime, where the DSS delay switch already
  falls back to uniform. Outside that regime PAVE is, on average, no better than uniform (d=1:
  -1.3%, d=10: -1.8% mean relative gain vs uniform on fresh seeds). I therefore record: PAVE does
  not earn its place as a general governor; a narrow d>=50 variant remains of exploratory interest.

Honest caveats: the model is a hand-built heuristic with two tuned scalars; the design went through
three development iterations (below), so the d=50 signal is a selected result on dev seeds, with
one fresh-seed replication of the no-reserve arm. The reserve-off variant was chosen *after*
seeing the ablation (post-hoc), then evaluated on fresh seeds (`eval2`).

## What was built

`src/shiftlab/gaver/pave.py`: `PaveMethod(PaveParams)` subclasses the unchanged
`atlas_components.ComposedMethod` built from the frozen DSS spec (`5b5c77b635e5`; test asserts the
spec id) and overrides only `_query` (precedent: `FallbackGapDiagnostic`). Evidence engine,
promotion rule, rollback monitor, `Method.step` budget clamp are untouched. The delay switch is
disabled inside PAVE so the governor owns the request rule in every cell.

* **State** (all from `F_t`): released-label evidence (e-process log-wealth, alarm, recent-window
  benefit `ben`), number of released labels, pending count and event rounds (ages), remaining horizon
  and budget, deployment state, promotion round, rollback reserve (`ceil(0.2 B)`, optional).
* **Working model** (no truth fields): Normal belief on benefit `mu`, variance drifting by `q` per
  round and cut by each arriving label (Kalman); per-round opportunity loss
  `sqrt(V) L(|m-theta|/sqrt(V))` against the switch / keep threshold `h +- s/R`; pre-promotion loss is
  scaled by e-process reachability. The module docstring has the details.
* **Governor**: rollouts for the next request now, `+g`, `+2g` (g = current calendar gap
  `ceil(H/B_rem)`), each followed by a calendar of gap `g` or a burst gap `g//4`; value = minus
  summed loss minus `c` per label. Request iff `V_0 - max(V_1, V_2) > kappa (V_0 - V_none)/K_0`,
  pending capacity allows, and the DSS spend-pace cap `ceil(0.1 B) + floor(2Bt/T)` holds (inherited
  unchanged; so PAVE decides *when within DSS's pace*, it is not an unconstrained spender).
* **Pending capacity (2.2)**: `ceil(d * B_rem / H_rem)` (3 for d=50, B=50) instead of fixed 2.
* **Tuned on dev streams only**: `kappa = 0.1`, `q = 0.03` (grid kappa {0.02, 0.1, 0.3} x q {0.01,
  0.03}, 20 seeds from 101080010 on 7 cells; lowest mean cost). Frozen constants `n0 = 2`,
  `inc = 0.1`, `reserve_frac = 0.2`.
* **Validity**: not claimed. The request is a deterministic function of released information and
  config, the evidence object is unchanged, so the DSS validity status carries over *as an
  assumption* (the engine's conditional-mean null, adaptive sampling). The null table below is the
  only validity evidence collected here.

Tests (`tests/test_gaver_pave.py`, 9 pass): pathwise budget `queries <= B`; every released label
arrives exactly `d` rounds after its request (no unreleased label used); evidence/decision label
lists contain released labels only; `pending == requested - released`; pending-capacity formula;
reserve withheld before promotion and released after; spec id equals the frozen DSS id. Ruff clean.

## Development trail (negative results kept)

| Iteration | Change | Dev result (7 cells, 20 seeds; mean cost/round) |
|---|---|---|
| v0 | stationary posterior + EVSI, reachability cumulative | unusable: 2-4 queries, never promoted (informal 10-seed check, not logged) |
| v1 | stationary EVSI, scalar reachability | still never promoted; kappa irrelevant (`tune_v1_discarded/`, best 0.444 vs DSS 0.353) |
| v2 | drifting belief + regret rollouts + DSS pace cap | best 0.4196 (`tune_v2_noburst/`; DSS 0.3530, uniform 0.4122) |
| v3 | adds burst follow-up spacing `g//4` | best 0.4214 (`tune/`), config used for all results here |

The stationary belief is the structural problem: after a few unfavourable labels it declares the
state decided and stops querying, so it cannot anticipate an onset; adding drift fixed the freezing
but not the lack of burst structure (a detection needs a dense run of favourable labels, which the
myopic value does not encode).

## Results

All costs are cost/round = loss + c N_q + s N_s over T = 1000. Paired over seeds (same stream for
every method), 95% CI from a paired bootstrap of the per-seed difference (4000 resamples). Relative
gain = reduction of mean cost relative to the reference mean (positive = PAVE better), graded
substantial >= 10%, meaningful 3-10% with CI excl. 0, small 1-3%, negligible < 1%.
`undecided_only` is the straddle candidate `b1a17927d9ad` (the acquisition DSS extends).
The regression cell `on0.6_L1_strong_harmful_d50_b0.05_s0.1` has DSS == uniform exactly.

Seeds (stream seed shared across methods): tuning 101080010-101080029; `eval` and `ablate`
101090000-101090059; `eval2` 101110000-101110059; null 101100000-101100499 (cell-dependent, see n column). Seeds
101080000-101080009 (WP0 smoke) unused. 31 cells = 16 cycle-7 primary cells + `fa.neighbours` of the
two regression cells (de-duplicated). Neighbours of the other primary cells were not run.

### Regression cells: PAVE-full (reserve on)

| cell | ref | n | ref cost | PAVE cost | diff [95% CI] | rel gain | grade |
|---|---|---|---|---|---|---|---|
| f3_rho0_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1 | dss | 60 | 0.3786 | 0.4396 | +0.0610 [+0.0415, +0.0805] | -16.1% | worse (CI excl. 0) |
| f3_rho0_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1 | uniform | 60 | 0.3638 | 0.4396 | +0.0758 [+0.0482, +0.1035] | -20.8% | worse (CI excl. 0) |
| f3_rho0_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1 | undecided_only | 60 | 0.3368 | 0.4396 | +0.1028 [+0.0850, +0.1204] | -30.5% | worse (CI excl. 0) |
| f3_rho0_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1 | episode_front | 60 | 0.3313 | 0.4396 | +0.1083 [+0.0809, +0.1341] | -32.7% | worse (CI excl. 0) |
| on0.6_L1_strong_harmful_d50_b0.05_s0.1 | dss | 60 | 0.4014 | 0.3818 | -0.0196 [-0.0364, -0.0046] | +4.9% | meaningful |
| on0.6_L1_strong_harmful_d50_b0.05_s0.1 | uniform | 60 | 0.4014 | 0.3818 | -0.0196 [-0.0364, -0.0046] | +4.9% | meaningful |
| on0.6_L1_strong_harmful_d50_b0.05_s0.1 | undecided_only | 60 | 0.4224 | 0.3818 | -0.0406 [-0.0559, -0.0266] | +9.6% | meaningful |
| on0.6_L1_strong_harmful_d50_b0.05_s0.1 | episode_front | 60 | 0.3876 | 0.3818 | -0.0058 [-0.0235, +0.0103] | +1.5% | small |

### Grade counts over all 31 cells: PAVE-full (reserve on)

| ref | meaningful | negligible | small | substantial | worse (CI excl. 0) | worse (CI incl. 0) |
|---|---|---|---|---|---|---|
| dss | 2 | 6 | 0 | 0 | 22 | 1 |
| episode_front | 0 | 2 | 2 | 0 | 23 | 4 |
| undecided_only | 4 | 2 | 2 | 2 | 21 | 0 |
| uniform | 1 | 6 | 4 | 0 | 13 | 7 |

Mean cost/round over cells (PAVE-full (reserve on)):

| method | cost |
|---|---|
| undecided_only | 0.3785 |
| dss | 0.3874 |
| episode_front | 0.4003 |
| uniform | 0.423 |
| pave:p1d1r1:k0.1:q0.03 | 0.4419 |
| markov_lr_gate | 0.4891 |

### Regression cells: PAVE no-reserve (fresh seeds)

| cell | ref | n | ref cost | PAVE cost | diff [95% CI] | rel gain | grade |
|---|---|---|---|---|---|---|---|
| f3_rho0_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1 | dss | 60 | 0.3984 | 0.4733 | +0.0750 [+0.0507, +0.0996] | -18.8% | worse (CI excl. 0) |
| f3_rho0_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1 | uniform | 60 | 0.3738 | 0.4733 | +0.0996 [+0.0699, +0.1298] | -26.6% | worse (CI excl. 0) |
| f3_rho0_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1 | undecided_only | 60 | 0.3408 | 0.4733 | +0.1325 [+0.1096, +0.1558] | -38.9% | worse (CI excl. 0) |
| f3_rho0_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1 | episode_front | 60 | 0.3240 | 0.4733 | +0.1494 [+0.1222, +0.1771] | -46.1% | worse (CI excl. 0) |
| on0.6_L1_strong_harmful_d50_b0.05_s0.1 | dss | 60 | 0.3980 | 0.3653 | -0.0327 [-0.0462, -0.0194] | +8.2% | meaningful |
| on0.6_L1_strong_harmful_d50_b0.05_s0.1 | uniform | 60 | 0.3980 | 0.3653 | -0.0327 [-0.0462, -0.0194] | +8.2% | meaningful |
| on0.6_L1_strong_harmful_d50_b0.05_s0.1 | undecided_only | 60 | 0.4126 | 0.3653 | -0.0473 [-0.0590, -0.0363] | +11.5% | substantial |
| on0.6_L1_strong_harmful_d50_b0.05_s0.1 | episode_front | 60 | 0.3886 | 0.3653 | -0.0233 [-0.0377, -0.0088] | +6.0% | meaningful |

### Grade counts over all 31 cells: PAVE no-reserve (fresh seeds)

| ref | meaningful | negligible | small | substantial | worse (CI excl. 0) | worse (CI incl. 0) |
|---|---|---|---|---|---|---|
| dss | 5 | 2 | 3 | 0 | 14 | 7 |
| episode_front | 8 | 2 | 1 | 4 | 15 | 1 |
| undecided_only | 1 | 3 | 2 | 6 | 19 | 0 |
| uniform | 5 | 4 | 1 | 8 | 11 | 2 |

Mean cost/round over cells (PAVE no-reserve (fresh seeds)):

| method | cost |
|---|---|
| undecided_only | 0.3815 |
| dss | 0.3886 |
| episode_front | 0.3946 |
| pave:p1d1r0:k0.1:q0.03 | 0.4195 |
| uniform | 0.4203 |

### Factorial ablation (pending, deadline, reserve; 7 cells x 60 seeds)

| arm | mean cost | minus uniform [95% CI] | full minus arm [95% CI] |
|---|---|---|---|
| dss | 0.3495 | -0.0542 [-0.0617, -0.0469] | +0.0635 [+0.0558, +0.0711] |
| p0d0r0 | 0.3863 | -0.0175 [-0.0261, -0.0088] | +0.0268 [+0.0188, +0.0349] |
| p0d0r1 | 0.4199 | +0.0161 [+0.0078, +0.0243] | -0.0069 [-0.0148, +0.0009] |
| p0d1r0 | 0.3815 | -0.0223 [-0.0317, -0.0128] | +0.0315 [+0.0225, +0.0407] |
| p0d1r1 | 0.4317 | +0.0280 [+0.0214, +0.0346] | -0.0187 [-0.0237, -0.0140] |
| p1d0r0 | 0.3867 | -0.0171 [-0.0257, -0.0085] | +0.0263 [+0.0179, +0.0347] |
| p1d0r1 | 0.4179 | +0.0141 [+0.0060, +0.0218] | -0.0049 [-0.0131, +0.0030] |
| p1d1r0 | 0.3682 | -0.0356 [-0.0442, -0.0268] | +0.0448 [+0.0368, +0.0526] |
| p1d1r1 | 0.4130 | +0.0093 [+0.0019, +0.0167] | - |
| uniform | 0.4038 | +0.0000 [+0.0000, +0.0000] | +0.0093 [+0.0019, +0.0167] |

### Null false promotion (null)

| cell | method | n | k | FP rate | CP 95% UCB |
|---|---|---|---|---|---|
| f3_rho0.5_on0.3_L0.6_strong_harmful_d10_b0.05_s0.1_NULL | dss | 230 | 2 | 0.0087 | 0.0271 |
| f3_rho0.5_on0.3_L0.6_strong_harmful_d10_b0.05_s0.1_NULL | pave p1d1r1:k0.1:q0.03 | 230 | 2 | 0.0087 | 0.0271 |
| f3_rho0.5_on0.3_L0.6_strong_harmful_d10_b0.05_s0.1_NULL | uniform | 230 | 0 | 0.0 | 0.0129 |
| f3_rho0.5_on0.3_L0.6_strong_harmful_d10_b0.1_s0.1_NULL | dss | 230 | 4 | 0.0174 | 0.0394 |
| f3_rho0.5_on0.3_L0.6_strong_harmful_d10_b0.1_s0.1_NULL | pave p1d1r1:k0.1:q0.03 | 230 | 1 | 0.0043 | 0.0205 |
| f3_rho0.5_on0.3_L0.6_strong_harmful_d10_b0.1_s0.1_NULL | uniform | 230 | 2 | 0.0087 | 0.0271 |
| f3_rho0.5_on0.3_L0.6_strong_harmful_d1_b0.05_s0.1_NULL | dss | 480 | 7 | 0.0146 | 0.0272 |
| f3_rho0.5_on0.3_L0.6_strong_harmful_d1_b0.05_s0.1_NULL | pave p1d1r1:k0.1:q0.03 | 480 | 3 | 0.0062 | 0.0161 |
| f3_rho0.5_on0.3_L0.6_strong_harmful_d1_b0.05_s0.1_NULL | uniform | 480 | 2 | 0.0042 | 0.0131 |
| f3_rho0.5_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1_NULL | dss | 230 | 3 | 0.013 | 0.0334 |
| f3_rho0.5_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1_NULL | pave p1d1r1:k0.1:q0.03 | 230 | 2 | 0.0087 | 0.0271 |
| f3_rho0.5_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1_NULL | uniform | 230 | 3 | 0.013 | 0.0334 |
| f3_rho0.8_on0.3_L0.6_strong_harmful_d10_b0.05_s0.1_NULL | dss | 230 | 14 | 0.0609 | 0.0935 |
| f3_rho0.8_on0.3_L0.6_strong_harmful_d10_b0.05_s0.1_NULL | pave p1d1r1:k0.1:q0.03 | 230 | 2 | 0.0087 | 0.0271 |
| f3_rho0.8_on0.3_L0.6_strong_harmful_d10_b0.05_s0.1_NULL | uniform | 230 | 2 | 0.0087 | 0.0271 |
| f3_rho0.8_on0.3_L0.6_strong_harmful_d10_b0.1_s0.1_NULL | dss | 220 | 18 | 0.0818 | 0.1189 |
| f3_rho0.8_on0.3_L0.6_strong_harmful_d10_b0.1_s0.1_NULL | pave p1d1r1:k0.1:q0.03 | 220 | 2 | 0.0091 | 0.0283 |
| f3_rho0.8_on0.3_L0.6_strong_harmful_d10_b0.1_s0.1_NULL | uniform | 220 | 7 | 0.0318 | 0.0589 |
| f3_rho0.8_on0.3_L0.6_strong_harmful_d1_b0.05_s0.1_NULL | dss | 220 | 13 | 0.0591 | 0.0923 |
| f3_rho0.8_on0.3_L0.6_strong_harmful_d1_b0.05_s0.1_NULL | pave p1d1r1:k0.1:q0.03 | 220 | 1 | 0.0045 | 0.0214 |
| f3_rho0.8_on0.3_L0.6_strong_harmful_d1_b0.05_s0.1_NULL | uniform | 220 | 0 | 0.0 | 0.0135 |
| f3_rho0.8_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1_NULL | dss | 220 | 48 | 0.2182 | 0.269 |
| f3_rho0.8_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1_NULL | pave p1d1r1:k0.1:q0.03 | 220 | 2 | 0.0091 | 0.0283 |
| f3_rho0.8_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1_NULL | uniform | 220 | 6 | 0.0273 | 0.0531 |
| f3_rho0.95_on0.3_L0.6_strong_harmful_d10_b0.05_s0.1_NULL | dss | 230 | 101 | 0.4391 | 0.4955 |
| f3_rho0.95_on0.3_L0.6_strong_harmful_d10_b0.05_s0.1_NULL | pave p1d1r1:k0.1:q0.03 | 230 | 30 | 0.1304 | 0.1727 |
| f3_rho0.95_on0.3_L0.6_strong_harmful_d10_b0.05_s0.1_NULL | uniform | 230 | 19 | 0.0826 | 0.1189 |
| f3_rho0.95_on0.3_L0.6_strong_harmful_d10_b0.1_s0.1_NULL | dss | 220 | 145 | 0.6591 | 0.7121 |
| f3_rho0.95_on0.3_L0.6_strong_harmful_d10_b0.1_s0.1_NULL | pave p1d1r1:k0.1:q0.03 | 220 | 87 | 0.3955 | 0.4528 |
| f3_rho0.95_on0.3_L0.6_strong_harmful_d10_b0.1_s0.1_NULL | uniform | 220 | 125 | 0.5682 | 0.6244 |
| f3_rho0.95_on0.3_L0.6_strong_harmful_d1_b0.05_s0.1_NULL | dss | 210 | 124 | 0.5905 | 0.6474 |
| f3_rho0.95_on0.3_L0.6_strong_harmful_d1_b0.05_s0.1_NULL | pave p1d1r1:k0.1:q0.03 | 210 | 17 | 0.081 | 0.119 |
| f3_rho0.95_on0.3_L0.6_strong_harmful_d1_b0.05_s0.1_NULL | uniform | 210 | 21 | 0.1 | 0.1408 |
| f3_rho0.95_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1_NULL | dss | 210 | 155 | 0.7381 | 0.7876 |
| f3_rho0.95_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1_NULL | pave p1d1r1:k0.1:q0.03 | 210 | 66 | 0.3143 | 0.3711 |
| f3_rho0.95_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1_NULL | uniform | 210 | 103 | 0.4905 | 0.5494 |
| f3_rho0_on0.3_L0.6_strong_harmful_d10_b0.05_s0.1_NULL | dss | 500 | 3 | 0.006 | 0.0154 |
| f3_rho0_on0.3_L0.6_strong_harmful_d10_b0.05_s0.1_NULL | pave p1d1r1:k0.1:q0.03 | 500 | 1 | 0.002 | 0.0095 |
| f3_rho0_on0.3_L0.6_strong_harmful_d10_b0.05_s0.1_NULL | uniform | 500 | 3 | 0.006 | 0.0154 |
| f3_rho0_on0.3_L0.6_strong_harmful_d10_b0.1_s0.1_NULL | dss | 500 | 1 | 0.002 | 0.0095 |
| f3_rho0_on0.3_L0.6_strong_harmful_d10_b0.1_s0.1_NULL | pave p1d1r1:k0.1:q0.03 | 500 | 4 | 0.008 | 0.0182 |
| f3_rho0_on0.3_L0.6_strong_harmful_d10_b0.1_s0.1_NULL | uniform | 500 | 7 | 0.014 | 0.0261 |
| f3_rho0_on0.3_L0.6_strong_harmful_d1_b0.05_s0.1_NULL | dss | 500 | 3 | 0.006 | 0.0154 |
| f3_rho0_on0.3_L0.6_strong_harmful_d1_b0.05_s0.1_NULL | pave p1d1r1:k0.1:q0.03 | 500 | 2 | 0.004 | 0.0125 |
| f3_rho0_on0.3_L0.6_strong_harmful_d1_b0.05_s0.1_NULL | uniform | 500 | 2 | 0.004 | 0.0125 |
| f3_rho0_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1_NULL | dss | 500 | 5 | 0.01 | 0.0209 |
| f3_rho0_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1_NULL | pave p1d1r1:k0.1:q0.03 | 500 | 4 | 0.008 | 0.0182 |
| f3_rho0_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1_NULL | uniform | 500 | 4 | 0.008 | 0.0182 |

### Null false promotion (null2)

| cell | method | n | k | FP rate | CP 95% UCB |
|---|---|---|---|---|---|
| f3_rho0.5_on0.3_L0.6_strong_harmful_d10_b0.05_s0.1_NULL | pave p1d1r0:k0.1:q0.03 | 140 | 1 | 0.0071 | 0.0334 |
| f3_rho0.5_on0.3_L0.6_strong_harmful_d10_b0.1_s0.1_NULL | pave p1d1r0:k0.1:q0.03 | 130 | 1 | 0.0077 | 0.036 |
| f3_rho0.5_on0.3_L0.6_strong_harmful_d1_b0.05_s0.1_NULL | pave p1d1r0:k0.1:q0.03 | 140 | 1 | 0.0071 | 0.0334 |
| f3_rho0.5_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1_NULL | pave p1d1r0:k0.1:q0.03 | 130 | 1 | 0.0077 | 0.036 |
| f3_rho0.8_on0.3_L0.6_strong_harmful_d10_b0.05_s0.1_NULL | pave p1d1r0:k0.1:q0.03 | 130 | 0 | 0.0 | 0.0228 |
| f3_rho0.8_on0.3_L0.6_strong_harmful_d10_b0.1_s0.1_NULL | pave p1d1r0:k0.1:q0.03 | 120 | 1 | 0.0083 | 0.0389 |
| f3_rho0.8_on0.3_L0.6_strong_harmful_d1_b0.05_s0.1_NULL | pave p1d1r0:k0.1:q0.03 | 130 | 0 | 0.0 | 0.0228 |
| f3_rho0.8_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1_NULL | pave p1d1r0:k0.1:q0.03 | 130 | 3 | 0.0231 | 0.0586 |
| f3_rho0.95_on0.3_L0.6_strong_harmful_d10_b0.05_s0.1_NULL | pave p1d1r0:k0.1:q0.03 | 130 | 29 | 0.2231 | 0.2915 |
| f3_rho0.95_on0.3_L0.6_strong_harmful_d10_b0.1_s0.1_NULL | pave p1d1r0:k0.1:q0.03 | 120 | 56 | 0.4667 | 0.5457 |
| f3_rho0.95_on0.3_L0.6_strong_harmful_d1_b0.05_s0.1_NULL | pave p1d1r0:k0.1:q0.03 | 130 | 22 | 0.1692 | 0.2328 |
| f3_rho0.95_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1_NULL | pave p1d1r0:k0.1:q0.03 | 120 | 37 | 0.3083 | 0.3849 |
| f3_rho0_on0.3_L0.6_strong_harmful_d10_b0.05_s0.1_NULL | pave p1d1r0:k0.1:q0.03 | 140 | 0 | 0.0 | 0.0212 |
| f3_rho0_on0.3_L0.6_strong_harmful_d10_b0.1_s0.1_NULL | pave p1d1r0:k0.1:q0.03 | 130 | 0 | 0.0 | 0.0228 |
| f3_rho0_on0.3_L0.6_strong_harmful_d1_b0.05_s0.1_NULL | pave p1d1r0:k0.1:q0.03 | 140 | 1 | 0.0071 | 0.0334 |
| f3_rho0_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1_NULL | pave p1d1r0:k0.1:q0.03 | 130 | 2 | 0.0154 | 0.0476 |


Per-cell CSVs: `outputs/gaver/wp2/table_r1.csv` (reserve on), `table_r0.csv` (no reserve);
raw rows `outputs/gaver/wp2/{tune,eval,eval2,ablate,null,null2}/rows.csv` (gitignored `outputs/`).

## Reading of the factorial ablation

Pending-aware state + deadline value (both on) improve PAVE relative to both off by -0.018
[-0.025, -0.011] cost/round (reserve off); each alone is worth about -0.013 to -0.019 on top of the
other. The rollback reserve **hurts** by +0.034 [+0.026, +0.041] when everything else is off; in this
simulator the reserved 20% of budget mostly goes unused before promotion. The best PAVE arm is
`p1d1r0` (-0.036 [-0.044, -0.027] vs uniform on those 7 cells), still worse than DSS (-0.054). Note
the 7 cells are mostly d=1/10; PAVE's niche (d=50) has only 1 cell in the ablation, so the
component attribution for the niche is thin.

## Other branches searched (planner note)

Searched `main` and the research/origin branches (`git for-each-ref`, `git grep`) for an
uncertainty/ASI-style acquisition baseline or paid-observation controller. `main` has
`scripts/benchmark_asi_paired_cost.py` and `src/shiftlab/dive/active_inference.py`, but that is
active statistical inference for estimating a paired mean cost with sampling propensities (torch,
prediction-powered mean), not a request-timing controller for a switching policy; I did not port it.
Other branches only matched on generic "value of information" strings
(`data_efficient_prescreen.py`, `failure_atlas_v2/*`); not read in depth. No paid-observation
switching controller was found, so the in-repo comparators are the registered Atlas ones (DSS,
uniform, undecided-only, `episode_front`, Markov-LR). An external ASI-style or Banerjee-Veeravalli
baseline remains unimplemented.

## Limitations

* One governor family; value model is heuristic and hand-built; two scalars tuned on 7 cells.
* Reserve-off selection is post-hoc (replicated on fresh seeds for the eval, not for the null
  unless the `null2` table is present).
* Null cells: only B/T <= 0.1 of the 32 Atlas dependence-null configs (120-500 streams per cell
  rather than the full 500 where stated); rho = 0.95 reported, not required; B/T in {0.25, 0.5} not
  run.
* Bootstrap CIs are per cell over 60 seeds; no multiplicity correction (screening only).
* Does not compare to source-faithful external schedulers (Banerjee-Veeravalli etc.).

## Commands

```bash
cd "C:/Users/nigel/OneDrive/桌面/ICML/shiftlab-gave-r-2026-11-06"
export PYTHONPATH="$PWD/src:$PWD/scripts" PYTHONIOENCODING=utf-8 OMP_NUM_THREADS=1
PY="C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/.venv/Scripts/python.exe"
# one-time: copy outputs/failure_atlas_v1_cycle5/family3 and outputs/failure_atlas_v1_cycle7/tuning
# from the main checkout (read-only) so f3_failure_ids() resolves.
$PY scripts/gaver/run_pave_eval.py --stage tune   --workers 14
$PY scripts/gaver/run_pave_eval.py --stage eval   --workers 14 --kappa 0.1 --q 0.03
$PY scripts/gaver/run_pave_eval.py --stage ablate --workers 14 --kappa 0.1 --q 0.03
$PY scripts/gaver/run_pave_eval.py --stage eval2  --workers 10 --kappa 0.1 --q 0.03
$PY scripts/gaver/run_pave_eval.py --stage null   --workers 12 --kappa 0.1 --q 0.03
$PY scripts/gaver/run_pave_eval.py --stage null2  --workers 10 --kappa 0.1 --q 0.03
$PY scripts/gaver/make_pave_tables.py        # writes outputs/gaver/wp2/tables.md
$PY -m pytest tests/test_gaver_pave.py -q && $PY -m ruff check src/shiftlab/gaver/pave.py scripts/gaver tests/test_gaver_pave.py
```

The runner is resumable (rows appended per job; completed (cell, seed, method) triples skipped).
Stages `tune`/`eval`/`ablate`/`eval2` ran under the final `pave.py` except two cosmetic ruff edits
(dict literal, `next(...)`) and removal of an unused function after the runs started; `null`/`null2`
were restarted once (job order changed to seed-chunk-major so partial runs have equal n per cell;
completed jobs were kept).

## Continue / pivot / stop

Stop PAVE as a general governor. Pivot only if the d>=50 niche matters: a long-delay-only
variant (pending-aware, deadline-aware, no reserve) is the surviving fragment, worth +6-8% over
uniform and `episode_front` in one regression cell family, to be re-tested with fresh seeds and
the full null grid before any claim. Do not promote to WP5 integration in the current form.
