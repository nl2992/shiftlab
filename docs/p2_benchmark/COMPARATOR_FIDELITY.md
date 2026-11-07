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
| `gated_deployment`, `gated_adaptive_range` | Karampatziakis, Mineiro & Ramdas, ICML 2021 (MOPE, §5.3 gated deployment) | **Not checked.** Author repo `n17s/mope@a4b8584b` is pinned but not compared | Shared paced acquisition; quadratic log-wealth lower bound instead of the author's finite-grid exact wealth; per-step `wmax_t = 1/q_t` in the adaptive-range reading. **Two local bugs fixed:** propensity ordering (`c66185c0`) and interval intersection (`81dc4d34`, ported here as `0c52913c`) | Native parity on bet updates, bound direction and coverage, not only endpoints (P1) | "gated deployment (MOPE CS), common-contract port" |
| `discern_style`, `discern_design_floor` | Balachandran, arXiv 2609.17560 (2026, not peer reviewed) | **Not possible:** no author code found (search 2026-11-06). The port's docstring wrongly pointed to `n17s/mope`, the MOPE repository; corrected | Printed-construction port; learned judge routing not used; design floor π_min = .25 in the strong reading. **Local bug fixed:** PrPl-EB penalty missing /4 | Done (P3): no code found, docstring fixed. Remains a printed-construction port | "DISCERN-style certificate (printed construction)" |
| `SMCS+retain-incumbent` | Arnold/Gavrilopoulos et al., sequential MCS (arXiv 2404.18678) | **Yes, cross-language:** the author's R `Simulation1.R` E_adj trajectories match to 4.7e-15 | Importance weighting with λ_s = q_s/2 (the native λ = 1/2 gives negative wealth when q < 1/2); retain-incumbent deployment rule chosen in development; excluded models never re-enter | The time-averaged null variant (Sim3) is blocked by missing R packages | "SMCS inference + retain-incumbent rule" |
| `xu_acquisition_only` | Xu, Karampatziakis & Mineiro, NeurIPS 2024 | **Not possible:** the author code has a syntax error at `Predictor.py:230` (pinned by a test) | Xu acquisition reduces to gated uniform sampling here; certificate is ShiftLab's paired-loss certificate, not Xu's RCPS guarantee | — | "ShiftLab certificate + Xu acquisition (composite)"; not counted as a published certificate |
| `choe_ramdas_eb(+front)` | Choe & Ramdas, *Operations Research* 2024 | **Not checked.** The authors' `comparecast` package exists on PyPI | PrPl-EB on query-conditional ±1 outcomes. Sprint notes record that a faithful Choe–Ramdas test targets the time-averaged conditional mean over **all** events, which a label budget cannot observe directly | Parity on a full-feedback stream vs `comparecast`; document the budget adaptation (P2) | "Choe–Ramdas-style e-process (budget adaptation)" |
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
