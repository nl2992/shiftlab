# Check: Model Selector (Okanovic et al., AISTATS 2025) - independent re-read

Checker run 2026-11-06. Verdict tags: CONFIRMED / CORRECTED / UNVERIFIABLE. Sources re-read by me:
PMLR v258 camera-ready PDF (raw.githubusercontent.com/mlresearch/v258/.../okanovic25a.pdf, via the
proceedings page) and arXiv 2410.13609v2; official code `RobustML-Lab/model-selector`, full SHA
`6aa57e5750153bccb04c9e96946b726d14f5d3f1` (resolved with `gh api`; equals `main` HEAD). Downloads were
in fresh scratchpad dirs; nothing downloaded was executed.

## Version differences (PMLR vs arXiv v2)
- Main text (Sec. 3, Eqs. 1-7, Algorithm 1, footnote 3, Sec. 3.3), Table 3, Table 4, Table 5 and the
  Appendix C text on Chen et al. are word-for-word the same in both. CONFIRMED no change to the algorithm.
- **CORRECTED (spec Sec. 4 "Paper prints NO global default" / Sec. 9 "PMLR differences UNVERIFIED")**: the PMLR
  version adds Appendix D.4 "On eps Selection Efficiency" (absent in arXiv v2). It says practitioners can
  use a heuristic range [0.45, 0.49] without grid search, closer to 0.49 under high model disagreement, and
  that the two-phase (coarse then fine) search takes 61 minutes on ImageNet versus 30 hours for baselines.
  So the paper does print a heuristic range (not a single default); 0.46 remains a code-only fallback
  (model_picker.py:13).
- Minor: PMLR carries the AISTATS footer, arXiv carries the footnote with the repo URL. No equation changes.

## Claim-by-claim
1. Citation, authors, PMLR v258: CONFIRMED (proceedings page lists the same six authors, same order).
2. Setting (Sec. 3.1): best model = argmax of accuracy over all n pool labels; latent H; goal
   argmax P(H=h_j|L): CONFIRMED (PMLR Sec. 3.1). No null hypothesis or deployment guarantee: CONFIRMED.
3. Eq. (1) noise model, Eq. (4) argmin expected posterior entropy, Eq. (5)-(7), Algorithm 1: CONFIRMED.
   Eq. (6) exponent: the printed form is (1-eps)^{h_{j,(t,x)}} eps^{t - h_{j,(t,x)}} while the set has t+1
   points; the spec's index-slip note is CONFIRMED (same in PMLR). Algorithm 1 line 4 also uses x_t before it
   is chosen (notation slip); irrelevant to the code.
4. Footnote 3 ("approximate the posterior over the classes as uniform over the model predictions"):
   CONFIRMED text. Code departs: expected entropy averages over ALL `num_classes` with weight 1/num_classes
   (model_picker.py:80-92 region; lines 84, 91-92 verified). The spec's paper-vs-code discrepancy is CONFIRMED.
5. Final rule = highest labeled-set accuracy, not posterior argmax (Alg. 1 line 12): CONFIRMED in paper and in
   model_selector.py:41-43 (uniform random tie-break via `np.random.choice`).
6. Code arithmetic: gamma = (1-eps)/eps (model_picker.py:24), weights multiplied by gamma^{1[match]},
   renormalised, base-2 `scipy.stats.entropy`, uniform prior (:35), random choice among exact minima (:52):
   CONFIRMED.
7. Pool filter / back-fill: CORRECTED line numbers only. In the file at the pinned SHA the disagreement filter
   is model_selector.py:25-31 (spec said 23-29/31), the model-ranking loop 35-43, the back-fill 46-51
   (spec 46-52). Behaviour CONFIRMED, including the edge case that `model_ranking_t[-1]` raises if no
   disagreement example exists (empty `Lt`); not in the spec.
8. eps handling (Sec. 3.3, App. D): noisy oracle from model votes, grid search, choose best eps with no real
   labels: CONFIRMED ("most frequent class" for few classes, sampling for many). Code: `create_noisy_oracle`
   (math_utils.py:192) with measures "vote" (argmax votes), "vote_dist" (sampled), "snorkel" (unimplemented stub,
   comment only): CONFIRMED. Note default measure "vote" is argmax even for many-class tasks, which differs from
   the paper's sentence for large label sets; the config files that choose the measure were not opened:
   UNVERIFIABLE which measure produced ImageNet rows.
9. Grid and metric: gridsearch_config.py:47-48 default `np.arange(0.35, 0.5, 0.01)` already reaches 0.49;
   the 0.49 append (:51-52) applies only when an explicit `epsilon_range` is given and the experiment name
   lacks "finegrained". CORRECTED (the spec implies the append is general). Default metric `success_diff`
   (:57) with threshold 0.9 (:58): CONFIRMED. Metric used for the published Table 4: UNVERIFIABLE. Note
   `success_diff` needs the competitor list, so in the paper it was probably not the metric for the
   noisy-oracle runs; this is inference, not read.
10. Table 3 best eps and pool sizes (WNLI 65, RTE 250, MRPC 350, QQP 5,000, others 1,000, EmoContext 1,000,
    SST-2 750, CoLA 800, MNLI 1,000): CONFIRMED against PMLR Table 3 cell by cell for the spec's cited rows.
11. **Table 4 values**: CORRECTED/COMPLETED. PMLR Table 4 (noisy / oracle eps): CIFAR10-High .47/.47,
    CIFAR10-Low .47/.47, EmoContext .47/.46, PACS .45/.45, Drift .50/.50, ImageNet .45/.46, ImageNet Pytorch
    .45/.46, ImageNetV2 T-I .46/.45, T-0.7 .45/.45, M-F .48/.47, MRPC .37/.36, CoLA .45/.45, QNLI .44/.45,
    QQP .47/.47, SST-2 .36/.36, WNLI .47/.47, MNLI .43/.44, RTE .39/.39. Spec's range statements (.36 to .50,
    agreement within 0.01) CONFIRMED, but its "0.36 (SST-2, MRPC-type)" is slightly loose (MRPC is .37 noisy,
    .36 oracle). Table 3 "best eps across 1,000 realizations" equals the Table 4 noisy column.
12. Drift eps = 0.5 means random sampling (gamma = 1): CONFIRMED (App. D.1 statement and algebra).
13. Table 5 gaps (RTE 15.93%, Drift 13.78%): CONFIRMED against the PMLR table (read from PDF text, not a
    summary, resolving the spec's UNVERIFIED on this point).
14. Guarantee: CONFIRMED the paper has no theorem. Appendix C says the borrowed near-optimality guarantees
    "generally apply" and, otherwise, eps rises toward 0.5 so random sampling is the right baseline.
    This is a heuristic, not a proved guarantee; the spec's "do not call it certified" stands.
15. **Two-model record-gate degeneracy**: CONFIRMED analytically and numerically with a refinement.
    For m = 2 and a disagreement example (predictions a != b), the hypothetical posteriors are
    (gamma p0, p1), (p0, gamma p1) and, for any other label, the unchanged posterior, so the expected entropy
    is (H_a + H_b + (C-2) H_0)/C, identical for every disagreement example and every pair (a, b), any posterior,
    any eps. REFINEMENT (new, material): this is exact only in exact arithmetic. I ran
    `hypothetical_entropies` from the ShiftLab port on all ordered disagreeing pairs with random posteriors
    and eps in [0.35, 0.49]: C = 2 gave 0/300 trials with unequal entropies; C = 3 gave 125/300, C = 4 gave
    186/300, C = 10 gave 259/300 trials where scores differ by ~1e-16 because the per-class sum is accumulated
    in a different order for different pairs. The adapter gate `ent[-1] != np.min(ent)`
    (model_selector.py, `request_labels`) therefore can reject an event on floating-point noise when
    C >= 3, so the claim "the gate always fires with two models" holds exactly only for two classes (the
    ShiftLab contract). It also means the adapter's choice is not even the Model Selector argmin with random
    tie-break. The author algorithm on a pool with m = 2 reduces to uniform random sampling among
    disagreement examples (random tie-break among exact minima), CONFIRMED. For C = 2 the in-code pool
    filter already removes agreement examples; the entropy at an agreement example equals H(p) and is not
    comparable (it can be larger or smaller than the disagreement value), which is why the filter matters.
16. Native tier T1 and adapter tier T3, naming ("Model Selector causal record-gate adapter (T3)", not Model
    Picker): CONFIRMED. `model_selector_causal` registration at scripts/failure_atlas_v2/suite.py:72 and
    :45 label verified.
17. Parity test status: see "Vendor availability" below. UNVERIFIABLE here.

## Vendor availability
`/Users/nigelli/Desktop/ICML/Shift-lab/vendor_sota` in the main checkout contains only `.gitignore`
(14 bytes); no `model_selector/` or `cams/` clone. The tests hardcode `ROOT / "vendor_sota/..."`
(test_sota_model_selector.py:41-42; test_sota_cams.py:35) with no environment-variable or path override, so
they cannot be pointed at another location without editing files. Neither pytest nor the vendor data is
available in the repo venvs I tried (both `.venv`s lack pytest). Parity tests were NOT run. The author code
at the pin is now in the scratchpad (`.../scratchpad/check_msel/ms_code/`) if the lead wants a clean clone
into `vendor_sota/` for step 4.

## Verdict
Spec is accurate on the algorithm, hyperparameters, tier and code mapping; corrections are the PMLR D.4
heuristic range, the grid-0.49 detail, author line numbers, and the float-noise caveat on the degeneracy claim.

**ACCEPT WITH CORRECTIONS**
