# Gap-Mix+ (evidence-adaptive querying): preregistration, C3 development stage

Branch `research/methods-recovery-2026-11-07`, cut from `main@9f62583a` on 2026-11-07. Registered BEFORE any Gap-Mix+
run. Sources: user directive "Methods-Paper Recovery" (2026-11-07); GAVE-R development results in `docs/gaver/` (90_SUMMARY,
10, 20, 50); `docs/failure_atlas_next_method_proposal_v1.md`; `docs/failure_atlas_v2_flq/results/REPORT.md`;
`scripts/failure_atlas_v2_flq/qsg.py`. All GAVE-R numbers are development evidence, not confirmation.

## 1. Hypothesis (mechanistic)

GAVE-R was sub-additive: joint was 2.8% worse than PAVE alone (gate-on), with interaction -0.0064 [-.0106, -.0026] (50).
Our hypothesis is that PAVE's value-of-label rollout models evidence growth with the iid DSS statistic, not with Gap-Mix's
evidence. Under Markov dependence, labels close in time carry redundant information. Gap-Mix's exact-gap likelihood
P^{g} therefore gains less per label at short gaps and needs more labels before promoting. A governor that is blind to
this spends budget where Gap-Mix's evidence grows slowly.

**Gap-Mix+** chooses whether to query at t from (E_t, Δ_t, B_t, T−t, P_t, d), where:
- E_t is Gap-Mix's current log-evidence and its distance to the promotion threshold;
- Δ_t is the gap since the last query;
- B_t is the remaining budget;
- P_t is the pending labels;
- d is the delay.

The aim is to buy the label that most improves the *eventual promotion decision under Gap-Mix*: expected Gap-Mix
log-wealth gain per label at gap Δ under the alternative plug-in, compared with what remains needed and with the
remaining budget, horizon and pending pipeline. Start rule-based (at most 3 free parameters); add complexity only if
it improves results.

Validity requirement: query times are F_{t-1}-predictable (the decision uses only released data), so Gap-Mix's exact-gap
null martingale argument applies under the declared rho_bar = 0.8. This is checked empirically on the null grid; it is
not assumed.

## 2. Arms (paired: identical streams, seeds, budget B, costs)

| Arm | Evidence | Acquisition |
|---|---|---|
| 1 | Valid Markov-LR (existing) | existing DSS-shell acquisition |
| 2 | Gap-Mix `exact0.8_s4` | existing DSS-shell acquisition |
| 3 | Gap-Mix | PAVE (the failed GAVE-R coupling; delay-gated form where GAVE-R used it) |
| 4 | Gap-Mix | **Gap-Mix+ evidence-adaptive querying** |
| 5 | Gap-Mix | simple tuned fixed pacing (best constant gap or spacing per cell family) |
| 4a | Gap-Mix | ablation: Arm 4 with the evidence terms (E_t and the threshold distance) frozen to their prior values, keeping Δ, B, T−t, P, d |

Extra comparators, reported but not arms:
- QSG-envelope evidence (`qsg.py`) with existing acquisition;
- gap-10 thinning;
- `episode_front`;
- uniform.

The comparator for C3 is the strongest valid one among Arms 1, 2, 3 and 5 and the extra comparators, chosen per cell
family by lowest mean J on the eval seeds.

## 3. Operating family (target) and controls

- **Target:** moderate dependence rho in {0.5, 0.8} (declared rho_bar = 0.8); budget-constrained B/T in
  {0.05, 0.1, 0.25}; delay d in {1, 10}; early and late sustained improvements. Use the GAVE-R harness cells (01_HARNESS_MAP)
  restricted to this family.
- **Neighbouring controls:**
  - rho = 0 (iid);
  - d = 50 (PAVE's niche);
  - B/T = 0.5 (budget not binding).
  Arm 4 must not be materially worse there: no more than a *small* loss, with the paired CI upper bound within 3%.
- **Null grid** for validity:
  - rho in {0, 0.5, 0.8};
  - all B/T and d above;
  - 500 streams per cell.
  False-promotion Clopper-Pearson 95% upper bound must be at most 0.1 for Arms 2-5 and 4a. Out of scope, reported only:
  rho = 0.95.

## 4. Tuning / evaluation split

- **Tuning seeds:** a fresh block, registered in `configs/seed_registry.yaml` as development/tuning. Tune Arm 4's θ
  (at most 3 params, at most 30 configurations) and Arm 5's pacing (equal or larger grid: at least 30 configurations) on
  these only. Fairness rule: Arm 5 gets at least as many tuning configurations as Arm 4.
- **Eval seeds:** a second fresh block, 60 seeds per alternative cell. No tuning after any eval result is seen; a change
  requires an amendment and a fresh eval block.

## 5. C3 decision rule (pass/fail; registered)

PASS requires all of the following. Effects are relative reductions in mean J/T, with paired bootstrap 95% CI.

1. **Effect:** Arm 4 vs the strongest valid comparator (§2), pooled over the target family, is at least *meaningful*:
   at least 3%, with the CI excluding 0.
2. **Attribution:** Arm 4 vs Arm 4a, pooled target, has a CI excluding 0 in favour of Arm 4. The evidence-dependent
   part must matter.
3. **Specific beats:**
   - Arm 4 beats Arm 2 and Arm 5, each with the CI excluding 0, pooled target.
   - Arm 4 beats Arm 3, pooled target and in the gate-on (d >= 2T/(B+2)) subset.
4. **Validity:** null UCB at most 0.1 on the whole rho <= 0.8 null grid.
5. **Neighbourhood:** no neighbouring-control family worse than *small* (as defined in §3).

If 1-4 hold but 5 fails, the result is "PASS-narrow", reported with the failing neighbour.

FAIL means: record negative, and go to PAVE-Delay+ (directive priority 2) under its own preregistration. A PASS is
development evidence only. The confirmation stage (fresh harness families, then C4 with at least 8 real datasets)
comes after freezing.

## 6. Reporting

Report per-cell and pooled J/T, detection rate, delay, labels used, pending-label inventory, false promotion, and the
interaction I = (J_00 − J_11) − [(J_00 − J_10) + (J_00 − J_01)] for evidence {Markov-LR, Gap-Mix} × acquisition
{existing, Gap-Mix+}. Record every run, including crashes and negatives.
