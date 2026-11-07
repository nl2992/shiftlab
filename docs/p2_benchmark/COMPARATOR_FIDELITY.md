# P2 comparator fidelity audit (W3, 2026-11-06)

**Purpose:** for every comparator in the P2 panel, state whether it reproduces author code, what
adapter choices it carries, and what remains unchecked. This consolidates
`docs/promising_directions/sota/SOTA_IMPLEMENTATION_VALIDATION.md` (Rounds 1–4), the two port
fixes of 2026-11-05/06, and `docs/sprint2/SOTA_BENCHMARK_AUDIT.md`. No new parity run was
possible here: the pinned author clones are not on this machine, and fetching them needs your
approval.

## Status by comparator

| Panel name | Source method | Author-code parity | Adapter choices that change behaviour | Open item | Name to use in the paper |
|---|---|---|---|---|---|
| `gated_deployment`, `gated_adaptive_range` | Karampatziakis, Mineiro & Ramdas, ICML 2021 (MOPE, §5.3 gated deployment) | **Checked 2026-11-07 (P1):** bet arithmetic matches the author code exactly when the bet matrix is non-singular (no non-singular step differs, max 3e-16; all 189 mismatches of 36,000 steps are singular). Endpoint rule differs (see below) | Shared paced acquisition; quadratic log-wealth lower bound instead of the author's finite-grid exact wealth; per-step `wmax_t = 1/q_t` in the adaptive-range reading. **Two local bugs fixed:** propensity ordering (`c66185c0`) and interval intersection (`81dc4d34`, ported here as `0c52913c`) | Port is conservative: intervals about 1.5× wider than native MOPE; consider an exact-grid endpoint option | "gated deployment (MOPE CS), common-contract port" |
| `discern_style`, `discern_design_floor` | Balachandran, arXiv 2609.17560 (2026, not peer reviewed) | **Not possible:** no author code found (search 2026-11-06). The port's docstring wrongly pointed to `n17s/mope`, the MOPE repository; corrected | Printed-construction port; learned judge routing not used; design floor π_min = .25 in the strong reading. **Local bug fixed:** PrPl-EB penalty missing /4 | Done (P3): no code found, docstring fixed. Remains a printed-construction port | "DISCERN-style certificate (printed construction)" |
| `SMCS+retain-incumbent` | Arnold/Gavrilopoulos et al., sequential MCS (arXiv 2404.18678) | **Yes, cross-language:** the author's R `Simulation1.R` E_adj trajectories match to 4.7e-15 | Importance weighting with λ_s = q_s/2 (the native λ = 1/2 gives negative wealth when q < 1/2); retain-incumbent deployment rule chosen in development; excluded models never re-enter | The time-averaged null variant (Sim3) is blocked by missing R packages | "SMCS inference + retain-incumbent rule" |
| `xu_acquisition_only` | Xu, Karampatziakis & Mineiro, NeurIPS 2024 | **Not possible:** the author code has a syntax error at `Predictor.py:230` (pinned by a test) | Xu acquisition reduces to gated uniform sampling here; certificate is ShiftLab's paired-loss certificate, not Xu's RCPS guarantee | — | "ShiftLab certificate + Xu acquisition (composite)"; not counted as a published certificate |
| `choe_ramdas_eb(+front)` | Choe & Ramdas, *Operations Research* 2024 | **Behavioural check 2026-11-07 (P2):** same verdict as `comparecast.eprocess_expm` on 88–100% of full-feedback streams; ours rejects earlier and slightly more often | PrPl-EB on query-conditional ±1 outcomes. Sprint notes record that a faithful Choe–Ramdas test targets the time-averaged conditional mean over **all** events, which a label budget cannot observe directly | Document as more aggressive than the authors' e-process | "Choe–Ramdas-style e-process (budget adaptation)" |
| `cams_adapter` | Liu et al., NeurIPS 2024 | **Yes, exactly** (posterior to 1e-12, identical query lists) | argmax deployment with incumbent kept on ties; our own contextual policies (author training code not shipped); switch cost charged by us | — | "CAMS with our contextual and constant policies" |
| `model_picker_adapter` | Model Picker | **Yes, exactly** (three stream settings) | Adapter to deployment and switching | — | "Model Picker adapter" |
| `model_selector_causal` | Model Selector | Causal adapter recorded as **not faithful** | Constant across disagreements (proved collapse) | — | Context only |
| `variance_min_ipw` | Variance minimisation | Native matches at rtol 1e-12; the streaming IPW variant is a different estimator | LURE does not transfer to streams | — | "variance-min score with streaming IPW" |
| `online_llm_picker` | Online LLM Picker | No author code located | `eps` unrecoverable from the text (we chose 1e-8); budget front-loads | — | Context only |
| `DM_HAC_monitor` | Sequential DM / Chu–Stinchcombe–White idea | n/a (adaptation) | Newey–West studentised CUSUM on paced disagreement queries; asymptotic size only | — | "DM-HAC monitor (adaptation)" |

## Consequences for P2 claims

1. **Two of the six strict-pool certificate families (gated, DISCERN) have no author-code parity**, and
   both had local bugs that changed results (three fixes in two days). The paper must either complete
   gated-deployment parity against `n17s/mope` or label every gated result as a printed-construction
   port and show sensitivity to the fixes.
2. **The MOPE interval fix did not change the FLQ re-test.** A same-seed replay on the patched code reproduced all 116,600 policy runs row for row ([results](results/FLQ_TWO_TIER_RESULTS.md)). The fix still matters in principle, so any new P2 table must use post-fix code.
3. SMCS, CAMS and Model Picker are the most defensible rows (exact author parity). SMCS now matters
   more, because it blocked front-loading's wins in the re-test.

## Planned parity work (P1 first)

| ID | Task | Needs |
|---|---|---|
| P1 | Gated deployment: compare `MopeCS` bets, bounds and stopping times with native `opebet` on shared synthetic streams (full feedback, then IPW-weighted) | Clone `n17s/mope` at the pinned commit (public GitHub) |
| P2 | Choe–Ramdas: compare the e-process on a full-feedback paired stream with `comparecast` | `pip install comparecast` into the project venv (public PyPI) |
| P3 | DISCERN: confirm whether author code exists; correct the docstring attribution | **Done 2026-11-06:** none found; docstring corrected |

## Parity results (2026-11-07)

**P1, gated deployment vs author MOPE** (`scripts/p2_benchmark/mope_parity.py`; author code
`n17s/mope@a4b8584b`, run with `numba`/`cvxpy` stubbed; [results](results/mope_parity.json)).
36 streams × 1,000 steps (three weight designs × three success rates), α = .05, w_max = 20.

- **Bets:** identical to the author's `solve_quad` whenever the 2×2 bet matrix is non-singular.
  All 189 mismatching steps (of 36,000) occur in early, singular steps, where the author code picks
  among three triangle vertices and our port also considers the origin and the edges. Both choices
  are predictable and inside the bet set, so validity is unaffected.
- **Endpoints:** the author computes exact log wealth on a 1,000-point grid; our port uses the
  paper's quadratic lower bound (closed form). Because each method feeds its own endpoint back into
  the next bet, the trajectories diverge and neither interval always contains the other.
- **Coverage** (300 streams × 500 steps, true value known): our port never excluded the true value
  (0/300); the author code did so in 5/300 streams, within α. Median final width is 1.2–1.6×
  larger for our port (for example .42 vs .30 in the q = .2 IPW design).
- **Consequence:** our gated rows are a valid but **less powerful** version of MOPE. Comparisons in
  which gated deployment loses may overstate how far it trails. Report this, or add an exact-grid
  endpoint option and re-run the gated rows.

**P2, Choe–Ramdas stand-in vs `comparecast` 1.0.0** (`scripts/p2_benchmark/choe_ramdas_behaviour.py`;
[results](results/choe_ramdas_behaviour.json)). `confseq` could not be built (CMake/Ninja, Boost,
pybind11 vs Python 3.12). Its one imported function is stubbed and never called on the default
`eprocess_expm` path. 300 full-feedback streams × 2,000 steps per regime, α = .05:

| Regime | Reject (authors) | Reject (ours) | Verdict agreement | Ours earlier by (median events) |
|---|---:|---:|---:|---:|
| iid null | .000 | .010 | .99 | — |
| Markov null ρ=.8 | .073 | .110 | .95 | 46 |
| alternative p = .55 | .097 | .150 | .91 | 153 |
| alternative p = .60 | .733 | .770 | .88 | 151 |
| alternative p = .70 | 1.000 | 1.000 | 1.00 | 91 |

The stand-in is **more aggressive** than the authors' e-process: earlier rejections, more rejections
under the persistent null. Both are within α on the iid null. Label it as a different (EB-CS)
construction in the paper, not as Choe–Ramdas.
