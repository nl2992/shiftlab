# Status note: CAMS (Contextual Active Model Selection, Liu et al., NeurIPS 2024)

Retrieved 2026-11-06 by subagent. This is NOT a re-derivation of CAMS. It records what the repository has
already verified and what I re-checked today. Tags: **[REPO]** repo's own claim, not re-verified by me;
**[CHECKED]** I confirmed it this session; **UNVERIFIED** not checked.

## 1. Citation, version, code

- Liu et al., "Contextual Active Model Selection", NeurIPS 2024. Repo's audit row cites it that way
  (docs/sprint2/SOTA_BENCHMARK_AUDIT.md l.24) [REPO]. Author list, equations and the paper PDF were NOT read
  today: **UNVERIFIED** here. CAMS-MAX is cited to Appendix G.7 of the NeurIPS PDF
  (proceedings.neurips.org/paper_files/paper/2024/file/5966e7c5c017d8449d215faeb1db4173-Paper-Conference.pdf)
  [REPO, audit l.28-33]; not re-opened.
- Official code: `xuefeng-cs/Contextual-Active-Model-Selection`. The port pins commit
  `6cbcc62fa289983d10c77637e4bd49f13c2248ed` (cams.py docstring l.3-5) [REPO]. **[CHECKED]** via `gh api`:
  that SHA exists upstream (committed 2025-01-19T00:56:37Z) and is the current HEAD of `main` (repo last
  pushed 2025-01-19T01:19:01Z), so the pin is not stale. The clone itself is gitignored under
  `vendor_sota/cams` and is absent from this worktree.

## 2. Native problem (as recorded by the port, not re-derived)

Stream-based, label-on-demand model selection among pretrained models with contextual policy advice; label of
round t is available before round t+1; no deployment switching cost (cams.py docstring l.8-12). Prediction
action is sampling I_t ~ w_t (l.12-13). [REPO]

## 3-4. Algorithm and defaults (port structure only)

Two author variants ported, kept separate: `CAMS` = `CAMS_identity` (weights w_t = Q^T E_t) and `CAMS-MAX` =
`CAMS_test` (w_t = E_t[argmax Q]; author comment at CAMS_test.py:8 labels it CAMS-MAX) (cams.py l.26-31)
[REPO]. Core functions in the port, each claimed line-for-line from author code with source line ranges in
comments: `normalise_advice` l.62, `smooth_advice` l.76, `policy_posterior` l.89, `learning_rate` l.107,
`weighted_entropy_query` l.115, `query_probability` l.138, `loss_increment` l.166, `_CAMSCore` l.177. Not ported,
recorded as BLOCKED in the docstring (l.34-45): author policy training (advice matrices shipped precomputed;
`policy_list.txt` names MLP checkpoints not shipped), random-policy generator, task7 context-free branch and
task9 scaling constants. Hyperparameter defaults were not re-read by me (UNVERIFIED today).

## 5. Guarantee

Not re-read (UNVERIFIED today). The repo audit does not attribute any anytime-valid guarantee to the
deployment adapters.

## 6. Mapping to ShiftLab contract

[REPO] SOTA_BENCHMARK_AUDIT.md l.24: "CAMS/CAMS-MAX constant-policy deployment adapters": context-free
constant policies (advice matrix = one-hot per model, `constant_policy_advice` l.281), argmax-incumbent
deployment, hard cap, delayed updates, switching costs. D2 is a ShiftLab hybrid, not published CAMS. CAMS has no
native switching cost, so the c_s charge, argmax deployment (author samples I_t ~ w_t), delay handling via
frozen-at-issue-time E and q (cams.py l.381-392), and budget cap (author keeps drawing after exhaustion,
ignores them; port keeps the draw but suppresses the request, l.333-345) are all adapter choices.
- **Achievable tier:** T1 for `CAMSNative` under delay=1 and switch_cost=0 with the author's advice matrices
  or constant policies; **T3** for `CAMSDeploymentAdapter` (and `cams_max_adapter`) on the common contract.
- Using the repo's own KNN-correctness contextual policy yields "CAMS with our policies", never CAMS (l.34-39).

## 7. Existing ShiftLab code and verified status

- Port: scripts/promising_directions/sota/competitors/cams.py (458 lines): `CAMSNative` l.333,
  `CAMSDeploymentAdapter` l.381. Registered `cams_adapter`, `cams_max_adapter` (scripts/sota_sprint/bench.py:66-67,78),
  host `cams` in scripts/sota_sprint/fam_d.py:151-153.
- **Verified by the repo [REPO]:** audit sentence at SOTA_BENCHMARK_AUDIT.md l.65 reports "numerical source
  reproduction for CAMS, Model Picker and SMCS". Supporting test: tests/promising_directions/test_sota_cams.py
  (10 test functions). `test_port_matches_author_code_numerically` (l.269-329) runs author `CAMS_identity.py` /
  `CAMS_test.py` from `vendor_sota/cams` on the shipped VERTEBRAL data and asserts weights equal to atol=1e-12,
  identical request and hidden-label sequences. It is `skipif` when `vendor_sota/` is absent
  (l.269), as it is in this worktree, so **I could not and did not re-run it** (pass state UNVERIFIED by me).
  Other CAMS checks in the repo: CAMS_MAX_VALIDATION.md/.json (matched comparison vs CAMS) and the WP1 replay
  [REPO, audit l.37-52], plus tests/test_hard_budget_delayed_cams.py.
- **Repo-stated limits [REPO]:** evaluation uses only constant policies, not the paper's contextual policy
  sets or datasets; "Call entries CAMS/CAMS-MAX constant-policy deployment adapters"; not a reproduction of the
  full experimental system.
- **Re-checked by me [CHECKED]:** pinned SHA exists and equals upstream HEAD; the line numbers quoted above in
  cams.py (docstring pin, class and function positions) match the file. Not re-checked: any equation, any
  author-code line, any default.

**Current honest tier:** `CAMSNative` T1 (repo-verified via numerical parity test, vendor absent so unconfirmed
here); `cams_adapter`/`cams_max_adapter` T3. In context-free two-model streams CAMS reduces to a weighted-entropy
query rule over two constant policies; the audit's naming ("constant-policy deployment adapter") is the correct
label. Whether the contextual advantage of CAMS is exercised at all in the benchmark: no (constant policies).

## 8. Reproduction tests

Available [REPO]: test_port_matches_author_code_numerically (needs vendor_sota/cams; VERTEBRAL data). Paper
numbers were not collected today (UNVERIFIED).

## 9. Open questions

- Re-run the parity test with a fresh clone of the pinned SHA (needs a download into a clean dir; not done).
- Check CAMS paper theorem statements and hyperparameter defaults against the port if the programme wants
  the full template (this note intentionally stops short).
