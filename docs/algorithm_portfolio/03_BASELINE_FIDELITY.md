# Baseline fidelity

| Baseline | Implementation | Fidelity status | Used in |
|---|---|---|---|
| Wald LCB payback (two-model) | `qsg_methods_search/hurdles.py` | Our construction (reference baseline), tuned over λ{.8–.97} × γ{.1–.3} | next-method screens |
| K-model Wald | `multimodel_bcr/policies.py` (IPW-consistent pairwise evidence) | Our construction, tuned | BCR |
| Gong–Zhang-style (`gongT_w100_m10`) | `failure_atlas_v2_flq/r6_policies.py` + tuning | **Adapter**, not a reproduction (docstring: source guarantees do not transfer) | EQSDp C3, C4 primary comparator |
| Qiu-style delayed movement | same | **Adapter**: blocked fixed-share Hedge on IW differences | EQSDp C3, C4 secondary |
| Regol-style UPF T3 | `qsg_methods_search/upf_style_switch_timing.py` (ported, 13 tests) | **Adapter** of UPF to reversible budgeted switching | comparator panel |
| Model Picker | `promising_directions/sota/competitors/model_picker.py` | Line-referenced port of the authors' code; deployment adapter marked `# ADAPTER` | BCR B3/B4 |
| Model Selector | `.../model_selector.py` | Causal adapter; pool rule not representable in this simulator, so not used | — |
| Markov-LR evidence, Gap-Mix, DSS, PAVE, `episode_front`, gap-10 thinning | `src/shiftlab/gaver/`, Atlas cycle scripts | In-repo constructions (GAVE-R); Gap-Mix validity empirical at ρ̄=.8 | Tracks B/C |

Rule for every table: adapters are named "-style" or "adapter". Gains over them are not claims
about the native published algorithms.
