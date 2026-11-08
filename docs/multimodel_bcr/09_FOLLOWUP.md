# BCR follow-up (corrective directive, Task 1): frontier and contextual specialists

**Main comparator.** A development-selected deployable policy: the in-sample best of K-Wald with
disagreement acquisition and K-Wald with Model-Picker acquisition, tuned on the same grid as
every other family. The post-hoc envelope is kept only as a diagnostic (03).

## 1. Label price × budget grid

c_q ∈ {.02, .05, .1, .2} × B ∈ {100, 200, 400}; 10 environments; 20 fresh development seeds
(base 2026111401). Matched grid for every family: λ{.9,.95} × γ{.05,.1}; BCR and the new rule add
z_u{.5,1.5} × ρ_mon{.1,.3}.

**New acquisition rule `emp` (economic Model Picker).** Model Picker's posterior-disagreement
query probability, computed only over the economically plausible set {deployed} ∪ {challengers
whose optimistic payback covers c_s}. Outside that set it monitors at ρ_mon × the full-set MP
probability, which keeps q > 0 so the IPW evidence stays consistent. Code:
`scripts/multimodel_bcr/policies.py` (`acq="emp"`), `frontier.py`, `analyze_frontier.py`.
Output: [frontier_analysis.txt](frontier_analysis.txt).

| pool (seed-paired mean over cells) | emp − principal comparator | recovery-regret Δ |
|---|---|---|
| c_q ≥ .1 (6 cells) | **−2.97 [−5.72, −0.21]**, p = .036 (≈0.5% of cost) | −1.8 |
| c_q ≤ .05 (6 cells) | +0.16 [−3.28, +3.60] | +6.5 |
| all 12 cells | −1.40 [−4.25, +1.45] | +2.4 |

- BCR (decision-relevant acquisition) gets worse as labels get dearer: +12.5 and +19.4 at
  c_q = .2, B = 200/400, because it spends labels freely.
- `emp` uses 59–83 labels against Model-Picker acquisition's ~96.
- Reading: `emp` has a small, label-price-dependent edge that is borderline in development.
  It was selected from 16 configs against 8 for the comparators, so the edge is optimistic.
  At about 0.5% of cost it is *negligible* on the fair-evaluation scale.

## 2. Contextual specialists (routing contract)

New runner `scripts/multimodel_bcr/ctx.py`.
- **Contract.** Context x ∈ {0,1} is observed; the deployment is a routing table; c_s is charged
  per table update; same budget, delay and paid labels.
- **Environments.** C1 static specialists, C2 drifting mix, C3 specialists appearing at t=800,
  C4 a context-blind winner, C5 null.
- **Seeds.** 20 fresh seeds (base 2026111501).
- **Genuine contextual baselines.** Per-context Wald (`cw`), and per-context Model Picker
  acquisition with Wald deployment (`cmp`, the tabular analogue of contextual active selection;
  the CAMS author code cannot be run because its trained advice policies are not shipped).

| family (best config) | net | labels | table updates | regret |
|---|---|---|---|---|
| context-blind K-Wald | 583.9 | 198 | 1.68 | 132.8 |
| contextual Wald (principal comparator) | 500.2 | 197 | 2.85 | 48.7 |
| contextual MP + Wald | 514.5 | 26 | 1.99 | 61.9 |
| contextual BCR | 497.0 | 97 | 2.58 | 46.5 |
| contextual economic MP | 511.6 | 26 | 2.07 | 60.4 |

- Contextual BCR − contextual Wald: −3.16 [−9.70, +3.37] (not significant, half the labels).
- Contextual economic MP: +11.4 [+0.5, +22.3] (worse).
- Context-blind: +83.7 (much worse).

## Verdict: **BCR CLOSED (negative)**

There is no novel, attributable net-cost advantage over fairly tuned deployable baselines.
- Specialist structure is captured by standard per-context Wald.
- BCR's acquisition saves labels but does not lower cost significantly.
- The one positive lead, `emp` at high label prices, is about 0.5%, borderline, and
  selection-favoured.

Kept findings:
- a label-efficiency frontier (MP-style acquisition reaches near-equal cost with 50–90% fewer
  labels);
- contextual routing is essential when specialists exist;
- decision-relevant acquisition is harmful when labels are expensive.
