# Spec: MODEL SELECTOR (Okanovic et al., AISTATS 2025)

Retrieved 2026-11-06 by subagent. Status of every claim is tagged: **[READ]** = read directly in the
cited source this session; **[DERIVED]** = my own algebra from read material; **[REPO]** = taken from
existing ShiftLab text, not re-read; **UNVERIFIED** = not read.

## 1. Citation, version, code

- Patrik Okanovic, Andreas Kirsch, Jannes Kasper, Torsten Hoefler, Andreas Krause, Nezihe Merve Gurel,
  "All models are wrong, some are useful: Model Selection with Limited Labels", AISTATS 2025, PMLR v258
  (pp. 2035-2043 per proceedings page snippet, proceedings.mlr.press/v258/okanovic25a.html). Title and
  author list confirmed from the arXiv PDF header (author order there: Okanovic, Kirsch, Kasper, Hoefler,
  Krause, Gurel).
- **Version read:** arXiv 2410.13609v2 (24 Oct 2024), 29 pages, full text via pdftotext
  (`/private/tmp/claude-501/.../scratchpad/msel/ms_paper/ms.pdf`). The PMLR camera-ready PDF was NOT
  fetched: any wording/equation difference between v2 and the PMLR version is UNVERIFIED. Page numbers
  below are the arXiv printed page numbers inferred from pdftotext page markers (approximate +-1 for the
  appendix); section and equation numbers are exact.
- **Official code:** https://github.com/RobustML-Lab/model-selector, default branch `main`, single commit
  `6aa57e5750153bccb04c9e96946b726d14f5d3f1` ("Initial commit", 2024-10-18). Paper footnote 1 gives this URL
  [READ]. I fetched `src/model_selection/methods/model_picker.py`, `src/model_selection/model_selector.py`,
  `src/epsilon_optimization/gridsearch_config.py`, `gridsearch_results.py`, `src/utils/math_utils.py` at
  that SHA into scratchpad (not executed). The commit is HEAD of `main` as of today, so the pin is current.
- **Naming trap [READ]:** the method is registered as `strategy_type = "model_picker"`
  (model_picker.py:18). This is NOT Karimi et al. 2021 Model Picker (a different algorithm; separate repo).
  Result tables must say "Model Selector", never "Model Picker", for this algorithm.

## 2. Native problem and estimand

Sec. 3.1 (p.3) [READ]. Pool-based, batch, offline selection:
- unlabeled pool of n examples with hidden labels y_i; m black-box pretrained classifiers h_j (hard
  predictions only); budget b << n labels; after querying, the remaining n-b examples are classified by the
  chosen model.
- Target ("best model"): h* = argmax_j (1/n) sum_i 1[h_j(x_i)=y_i], i.e. best accuracy over ALL n pool
  labels. A latent variable H with prior over models; goal is argmax_j P(H=h_j | L).
- No null hypothesis, no test, no error-rate guarantee on the selected model's deployment loss. It is a
  best-arm identification / active-learning problem with an immediate noiseless oracle.
- Feedback: oracle returns y_t immediately for any chosen pool example (Alg. 1 lines 6-7). No delay, no
  missing labels, no label or switching cost, no distribution shift (pool is an iid sample, Sec. 4.3.1).

## 3. Exact algorithm

Proxy model, Eq. (1), Sec. 3.1 p.4 [READ]: P(H(x) != y | H = h*) = eps, P(H(x) = y | H = h*) = 1-eps,
eps in [0,1]; labels conditionally independent given H, "flipped with probability eps independently".

Objective, Eq. (2) p.4: choose the label set L of size <= b maximizing I(H; L) (mutual information).
Greedy rule, Eq. (3): x_t = argmax_{x in U_t} I(H; Y | x, L_t).
Entropy form, Eq. (4): x_t = argmin_{x in U_t} E_Y[ H(H | L_t U {(x,Y)}) ]. Footnote 3 (p.4): the expectation
over Y approximates the class posterior "as uniform over the model predictions".
Hypothetical posterior, Eq. (5)-(6) p.5, uniform prior 1/m: P(H=h_j | L_t U {(x,Y=c)}) proportional to
(1-eps)^{h_j,(t,x)} eps^{t - h_j,(t,x)} as printed, where h_j,(t,x) counts correct predictions of h_j on
L_t U {(x,c)}. [DERIVED note] the printed exponent t on the eps factor would equal the number of labels only
if the labelled set has t points, whereas L_t U {(x,c)} has t+1; I did not reconcile this index slip. It is
irrelevant to the code, because the shared eps factor cancels on normalisation; Alg. 1 line 4 and Eq. (7)
are unambiguous.
Posterior update, Eq. (7) p.5: P(H=h_j | L_{t+1}) proportional to P(H=h_j | L_t) (1-eps)^{1[h_j(x_t)=y_t]}
eps^{1[h_j(x_t)!=y_t]}.

Algorithm 1 (p.5) [READ], with the author code mapped [READ, model_picker.py / model_selector.py @6aa57e5]:

```
Require: models M, pool U_0, eps, budget b, oracle
 1  L_0 <- {}                                          # model_picker.py:43 (Lt = [])
 2  for t = 0..b-1:                                    # :44
 3-5   for c in Y: hypothetical posterior (Alg l.4)    # compute_entropies :68-95, loop over classes :80
 6     x_t <- argmin_x E_Y[H(H | L_t U {(x,Y)})]        # Eq.4; :47-52 (random tie-break among exact minima)
 7     y_t <- oracle(x_t)                              # :58 reads oracle[idx]
 8-9   L_{t+1}, U_{t+1}                                # :55,60-63
10     posterior update (Eq. 7)                        # update_posterior :100-107
12 return argmax_j (1/b) sum_{i in L_b} 1[h_j(x_i)=y_i]   # final rule = highest LABELED-SET ACCURACY,
                                                        # NOT posterior argmax. model_selector.py:39-43,
                                                        # uniform random tie-break at :41-42
```

Code arithmetic [READ]: gamma = (1-eps)/eps (model_picker.py:24); weights multiplied by gamma^{1[correct]}
(:84, :103), then renormalised. [DERIVED] this equals Eq. (7) after normalisation because the eps^{1[wrong]}
factor is common to all models that are wrong and (1-eps)/eps is the ratio. Expected entropy uses base-2
`scipy.stats.entropy` averaged with weight 1/num_classes over ALL classes in `classes` (:80, :91-92).
Prior: uniform (:35-36).

Code-only steps not in Algorithm 1 [READ]:
- model_selector.py:23-29 drops pool examples on which all models agree, runs the strategy on the rest with
  budget min(b, #disagreements) (:31), and back-fills any unspent budget with random agreement-region
  examples (:46-52). [DERIVED] Dropping agreement examples is consistent with the argmin: on an agreement
  example every hypothetical label either rewards all models or none, so the posterior is unchanged and
  the expected entropy equals the current entropy (the maximum over candidate examples); it only changes
  which ties occur.
- model_selector.py:35-43 records the selected model after every prefix (`model_ranking_t`).

## 4. Hyperparameters and defaults

- **Single model hyperparameter: eps** [READ Sec. 3.1, 3.3]. Paper prints NO global default; eps is "learned"
  per model collection (Table 3 p.17, Table 4 p.25) and ranges 0.36 (SST-2, MRPC-type) to 0.50 (Drift);
  0.47 for CIFAR10-High/Low, QQP, WNLI; 0.45 PACS/CoLA/ImageNet-Pytorch-type (Table 4 values, noisy vs oracle:
  agree to within about 0.01). eps = 0.5 means gamma = 1, all scores tie, i.e. uniform random sampling
  (Appendix D, Drift) [READ]; the repo test file also asserts this [REPO].
- **Code default eps = 0.46** (model_picker.py:13). This is the code's fallback when a config omits eps; it
  is not a paper-stated default [READ both].
- **How eps is set without labels (Sec. 3.3 p.5-6; Sec. 4.3.1 (p.~8); Appendix D) [READ]:** build a noisy
  oracle from the candidate models' predictions (most-predicted class when few classes; sample from the
  prediction distribution when many classes), treat it as the true oracle, run the whole selection protocol
  for each eps on a grid, pick the eps with the best best-model identification probability. Appendix D.1:
  suitable eps in [0.35, 0.49]; below 0.35 overfits; eps = 0.49 slower on ImageNet collections. The paper's
  rationale: a small eps makes the update factor (1-eps)/eps large (9 at eps = 0.1) and over-weights evidence;
  larger eps regularises. eps is "a proxy for disagreement among competing models".
- Code for the grid search [READ]: grid `np.arange(0.35, 0.5, 0.01)` when no `epsilon_range` given
  (gridsearch_config.py ~l.47-48), or the user range, with 0.49 appended unless the experiment name contains
  `finegrained` (~l.51-52). Metrics in gridsearch_results.py: `fastest` (first smoothed t with success > 0.9,
  kernel 5; :24-48), `success_diff` (:51-73, needs competitor list), `success_avg` (mean success over the
  budget; :76-93). Default metric in code is `success_diff` (gridsearch_config.py ~l.57), default threshold
  0.9 (~l.58). Noisy oracle: `create_noisy_oracle(... measure="vote")` (math_utils.py:192; docstring lists
  "vote", "vote_dist", "snorkel").
- Experimental protocol [READ Sec. 4.3.1, Table 3, App. B]: eps learned over 1,000 realizations; pool sizes
  1,000 for most collections (65 WNLI, 250 RTE, 350 MRPC, 5,000 QQP) as reported in the fetched summary of
  Table 3; I did not re-read Table 3 cell by cell (UNVERIFIED for individual sizes).
- **UNVERIFIED:** which grid metric (`fastest`, `success_avg`, `success_diff`) produced the published
  Table 4 values. The existing ShiftLab port also flags this as BLOCKED [REPO].

## 5. Guarantee

Paper has NO theorem of its own. the related-work discussion in Appendix C (arXiv p.19, [READ]) says the greedy
mutual-information policy's "provable near-optimality guarantees" from Chen et al. 2015 (binary symmetric
channel) "generally apply" to this setting, and in Sec. 3.1 they concede that a single eps "is a major
simplification" of Chen et al.'s model. Assumptions behind the borrowed guarantee: noiseless-oracle
queries of an iid pool, labels conditionally independent given H with a single flip rate eps, uniform prior,
hard black-box predictions. Not covered: any shift between pool and deployment, delayed or missing or
selectively sampled feedback, query or switching costs, a deployment-loss or no-regret guarantee, validity
under misspecification of eps (the paper itself shows noisy labels cannot pick the best model reliably:
Appendix D.3, Table 5 accuracy gaps up to 15.93% RTE, 13.78% Drift [READ via summary]). Do not call any
Model Selector run "certified".

## 6. Mapping to ShiftLab's deployment contract

Contract: two frozen models, paired per-round loss, B=200 of T=2000, c_q=0.05, c_s=5, delayed labels
(scripts/sota_sprint/bench.py:3,25; src/shiftlab/contract/interface_v2.py:35-80).
- Pool-based retrospective querying is the core of Alg. 1 line 6 (argmin over ALL unlabeled pool examples).
  The simulator can label only the event currently processed, so the faithful algorithm cannot run on the
  stream; it can run (a) as a native offline experiment on a fixed pool, or (b) in a block-pool experiment
  where the pool is a block of already-arrived events whose labels may be bought later (requires a simulator
  change or an out-of-simulator evaluation). With m=2 models, [DERIVED] expected posterior entropy is the same
  for every disagreement example (any number of classes, any posterior, any eps), so the acquisition reduces
  to uniform sampling of the disagreement region; the ShiftLab test
  `test_two_model_expected_entropy_is_instance_blind` asserts the same [REPO, not re-run by me].
- **Achievable tier:** T1 for the native pool procedure on its own pool/oracle setting (author code exists and
  is pinned). **T3 at most** for the deployment contract (record gate + pacing + delayed-release posterior +
  switch-aware deployment). It can never be called the authors' algorithm there.
- Deviations required under T3 (all would be listed in any result table): query gate replaces global argmin;
  pacing cap; pending-label semantics; deployment tie-break incumbent-sticky instead of uniform random;
  hard budget cap; switch charge; eps fixed (0.46) or chosen on development streams; final rule applied
  online rather than after b labels; Eq. (7) update delayed until release.

## 7. Existing ShiftLab code

Files: `scripts/promising_directions/sota/competitors/model_selector.py` (classes `ModelSelectorNative`
l.134, `ModelSelectorCausalAdapter` l.292 (`request_labels` l.354, gate test l.372, `observe` l.378), `run_block_pool_experiment`); registered as
`model_selector_causal` in `scripts/failure_atlas_v2/suite.py:72`, `scripts/failure_atlas_v2_flq/suite.py:72`
(`ModelSelectorCausalAdapter(2, 2, r("model_selector"))`), `scripts/sota_sprint/fam_d.py:53,154-155` (host
`ms` for DeployGate D6), listed in `bench.py:66,79`, `bench2.py:50` (null-tested: "none"), `fam_t.py:403`.
Tests: `tests/promising_directions/test_sota_model_selector.py` incl. `test_native_reproduces_author_outputs_exactly`
(l.414) comparing to the vendored author code; `vendor_sota/` is gitignored and absent in this worktree, so
those author-parity tests are skipped here (I did not run them; their pass status is UNVERIFIED by me).

What matches [READ both sides]: SHA 6aa57e57 matches my pin; eps default 0.46 (module l.65; author
model_picker.py:13); gamma formula (:24); update (:97-107); entropy loop (:68-95) including 1/num_classes
weighting; final rule = highest labeled accuracy with random ties (author model_selector.py:39-43); filter
and back-fill (:23-29, :46-52); grid 0.35-0.49 step .01 and extra 0.49; noisy `vote` oracle; the module
docstring correctly notes the `model_picker` registry name and the two-model degeneracy.

Discrepancies / risks:
1. Adapter deploys but does not implement Alg. 1 line 6: the "record gate" (adapter `request_labels`) asks
   for the current event iff its expected entropy is the minimum of a 50-event window. With m=2 all scores tie
   so the gate always fires (test name `test_adapter_gate_never_rejects_in_two_model_setting` [REPO]); the
   policy is then "label every disagreement, paced". Honest label: pacing rule plus Model-Selector posterior,
   not Model Selector acquisition.
2. Paper footnote 3 ("uniform over model predictions") vs code uniform over all `num_classes`; identical for
   2 classes and 2 models (the contract), may differ when a class is predicted by no model. Not reconcilable
   from the paper text alone; the port copies the code (`hypothetical_entropies`, module l.90-110), which is the right choice for
   T1 parity but is a paper-vs-code discrepancy to cite.
3. Adapter final rule: ties go to the incumbent then lowest index (adapter predict), published rule breaks
   ties uniformly (author :41-42). Declared ADAPTER in the source.
4. `select_epsilon` picks `success_avg` or `fastest`; the metric behind the published eps values is not
   known (see Sec. 4). The ShiftLab default 0.46 is the code fallback, not a paper-stated or tuned value.
5. Adapter ignores the paper's eps-tuning entirely in the benchmark (fixed 0.46); no stream-side
   noisy-oracle tuning is performed.

**Current honest tier:** `ModelSelectorNative` = T1-claimed (line-by-line port with parity tests against the
pinned author code, UNVERIFIED by me because vendor_sota is absent). `model_selector_causal` = **T3**,
and in the two-model contract it is effectively "paced disagreement sampling + labeled-accuracy deployment".
Result tables should read "Model Selector causal record-gate adapter (T3)", never "Model Selector".

## 8. Reproduction tests available

From the paper [READ]: Table 4 eps values (noisy vs oracle) per collection; Table 3 best eps. These need the
authors' prediction collections (`resources/datasets/*`, listed in the repo; model-prediction `.npy` data not
fetched). Exact identities usable without data: (a) Eq. (7) posterior update by hand (3 models, known
agreements); (b) eps = 0.5 gives gamma = 1 and identical scores for all examples (uniform random sampling);
(c) final rule returns argmax of labeled-set accuracy, not of posterior; (d) the `fastest`/`success_avg`
formulas on a toy success curve. All four are already covered by tests named above [REPO]. A true numerical
reproduction of the paper's identification-probability curves was not attempted by anyone I can verify.

## 9. Open questions / UNVERIFIED

- PMLR version differences vs arXiv v2 (UNVERIFIED).
- Exact Eq. (6) exponent index convention (see Sec. 3); Alg. 1 and Eq. (7) used instead.
- Table 3 per-collection pool sizes and Table 4 metric (UNVERIFIED beyond the summary I read).
- Whether the shipped grid-search configs use metric "all" (the existing port says so [REPO]); I did not open
  the config JSONs.
- Appendix D.3 / Table 5 numbers read via a summarising fetch of the HTML, not from the PDF text.
- Whether any later erratum exists. Not searched.
