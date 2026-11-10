# Engineering completion audit (theory_v2, Work Package E)

Audited 2026-11-10 on branch `research/paper4-causal-premium-theory-2026-11-10` at `bfd86eea`, working tree clean
on entry. Nothing was committed or edited except this file. Scratch scripts are under the session scratchpad and
are not part of the repo (see "Commands").

## E1. Root-mixture correctness

### E1.1 Correct realisation formula

Root lottery: draw a private coin `B ~ Bernoulli(q)` at time 0, independent of labels and hidden state. If `B = 1`
play behavioural policy `pi` throughout, otherwise play the deterministic safe plan `sigma` ("never promote",
choice `(0,0)` everywhere). Perfect recall holds (the learner information is its own action history plus released
labels), so Kuhn's theorem gives a behavioural realisation. For learner information `I` and choice `a`:

    beta(I,a) = [q rho_pi(I) pi(I,a) + (1-q) rho_sigma(I) sigma(I,a)] / [q rho_pi(I) + (1-q) rho_sigma(I)]

where `rho_p(I)` is plan `p`'s own-action reach probability, the product of `p`'s action probabilities along the
history in `I`. Label probabilities appear identically in both branches and cancel. The weight of a branch is
therefore its prior weight times `rho`, not its prior weight times the 0/1 indicator "history is consistent with
the plan". The two agree only when every `rho` is 0 or 1, i.e. for deterministic plans. This is the old helper's
defect: for a stochastic `pi` it drops `rho_pi(I)`.

Risk: realisation-space mixing is linear, so `Risk(beta) = q Risk(pi) + (1-q) Risk(sigma)`. The causal-null risk is a
maximum over null strategies of a linear function and `Risk(sigma, y) = 0` for every null strategy `y`, so
`max_y [q R(pi,y)] = q max_y R(pi,y)`. Hence `Risk(beta) = q Risk(pi)` exactly. Taking `q = min(1, alpha / Risk(pi))`
(and `q = 1` when `Risk(pi) = 0`) gives `Risk(beta) <= alpha`, with equality when `Risk(pi) > alpha`. If `sigma` had
positive null risk, only the inequality would hold; the helper's `safe_choice` argument does not make that case
valid, and the docstring does not warn about it (see E1.5).

### E1.2 Implementation check: `src/shiftlab/dive/root_mixture.py::mix_root_lottery`

The code implements exactly that formula, with `fractions.Fraction` throughout (no floats). `reach` is computed by
recursion along the history with memoisation keyed on `(plan, game.information)`. Choices come from
`game.choices`, so the query budget is preserved.

| Case | Behaviour | Evidence |
|---|---|---|
| `q = 1` | returns `policy` itself (identity) | code; test; my check |
| `q = 0` | returns the safe plan; risk 0, metrics equal never-promote | my check |
| `q` outside `[0,1]` | `ValueError` | test; my check |
| risk already `<= alpha` | caller sets `q = 1`; helper returns raw | caller formula `min(1, alpha/risk)` |
| risk 0 | caller sets `q = 1` via `if risk else F(1)`; helper never divides | all callers use that guard |
| `alpha = 0`, risk `> 0` | `q = 0` gives safe plan, risk 0 | my check (`q = 0`) |
| `alpha = 0`, risk 0 | `q = 1`, raw returned | caller formula |
| neither plan reaches `I` (`total == 0`) | falls back to raw `policy` | `test_unreachable_information_falls_back_to_raw` |
| `pi` stochastic at every information set | exact | 36 random cases below |
| mixture of a mixture | composes: `mix(mix(pi,1/2),2/3)` and `mix(pi,1/3)` have equal exact risk and metrics | my check (12 compositions) |
| float `q` | accepted and converted exactly (`F(0.5) = 1/2`) | my check; undocumented |

My independent check (cells C2 and C3, 6 random fully stochastic behavioural policies each, `q` in {1/3, 2/7, 9/10},
36 cases): exact `null_risk(mix) == q * null_risk(pi)` and exact expected metrics `== q * metrics(pi) + (1-q) * metrics(never)`
in all 36. 0 failures.

### E1.3 Regression test against the old logic

- `git log --follow` shows `root_mixture.py` and `tests/test_root_mixture.py` each have one commit, `a09683f9`. That
  commit only adds the guard to `eprocess_gated_planner.mix_with_never_promote` and does not alter the old mixture body
  (the diff is pure addition plus the keyword flag).
- I extracted the pre-fix module (`git show a09683f9^:src/shiftlab/dive/eprocess_gated_planner.py`) and ran it on C2
  FCG iteration 6 (robust risk 13/100, `q = 10/13`). It returns exact risk **280952/2779205 (about 0.101) > 1/10**,
  the same value the test asserts via `_allow_stochastic=True`. So the test exercises the genuine old logic, not a
  re-implementation. The new helper returns exactly 1/10.
- On random stochastic policies the pre-fix helper misses the target badly (C2: 3719715/5916064 vs target
  4045/14784; C3: 313556222291/447254438400 vs 10196887/36220800), confirming the defect is a wrong lottery in
  general. It violates `alpha` only on some cases (the ledger already notes this).
- The test file has 11 collected tests (not 9 as the audit states), all passing. It also checks that the guard
  raises `ValueError`, deterministic old == new on reachable information, budget never exceeded, and agreement of
  cost, risk and every reachable behaviour with the independent sequence-form implementation
  `paper4.frontier_cuts.mix_root_never_promote` on C2 and C3 (iterations 0 and 6/7).
- Lint: `ruff` reports 2 `RUF059` (unused unpacked variables `raw`, `q`) in `tests/test_root_mixture.py` lines 110
  and 149. Cosmetic; not fixed.

### E1.4 Callers

Every reference to the helper or to any older root-mixing code in `src/` and `scripts/`:

| Caller | Mixing path | Classification |
|---|---|---|
| `src/shiftlab/paper4/frontier_cuts.py:313` and `frontier_cuts_fast.py:87` (`_repair`) | own sequence-form `mix_root_never_promote` (exact for stochastic) | CORRECT; independently cross-checked against `mix_root_lottery` |
| `scripts/paper4_continuation/theory_C/gamma_lib.py:89`, `theory_B/b3_distill.py:37` (wrapper), `src/shiftlab/paper4_continuation/ablation.py:349` (via `_repair`) | `mix_root_never_promote` | CORRECT |
| `scripts/research_risk_approx/{run_eprocess_gated_planner,run_eprocess_threshold8_screen,compare_t7_strong_calendar,compare_t8_strong_calendar,compare_t8_b4_calendars,compare_t8_delay2_calendars}.py` | `mix_with_never_promote` on `EProcessGatedPlanner.solve_gated()` policy | DETERMINISTIC-ONLY (safe); guarded since `a09683f9`. Verified: gate planner at T=8, B=3, d=1 for thresholds 4 and 8 is not stochastic at any pre-promotion information (guard returns `None`); activations 2/5 and 4/5, mixed risk 1/10 |
| `scripts/research_risk_approx/run_candidate_g_scalarized_dp_screen.py` | `mix_with_never_promote` (guarded) and its own local `root_mixture(game, first, second, weight)`, a copy of the OLD consistent-plan weighting with no guard | Inputs are `one_hot` DP policies only (deterministic by construction), so the local copy is exact. It is an UNGUARDED function that would be wrong for stochastic inputs. Result rows are filtered on exact `robust_risk <= alpha` with `robust_risk == game.null_risk`, so a wrong lottery would have been caught or discarded. Classification: deterministic-only (safe) but latent hazard; recommend replacing with a two-policy generalisation |
| `scripts/research_risk_approx/iid_relaxation_{certified_pipeline,t8_grid,t10_stress}.py` | `mix_with_never_promote` on an LP-recovered policy (can be stochastic) | GUARDED: would now raise `ValueError` if raw risk `> alpha` and the policy randomises pre-promotion. Saved activation for the LP candidate is 1 in every cell (see E1.5). Not yet migrated to `mix_root_lottery`; any rerun on a cell with raw risk `> alpha` would stop with an error. This is a loud failure, not a silent one |
| `tests/test_eprocess_gated_planner.py` | `mix_with_never_promote` on gate policy | deterministic, passes |
| Many scripts/src files (not counted) that write `activation * raw + (1-activation) * safe` (e.g. `causal_switching_game.py:382-405`, `compare_*`, `generate_*`, `verify_*`) | value-level scalar bound; no behavioural policy is constructed | SAFE by linearity of realisation-space mixing (E1.1); not a code path through either helper |

No unguarded stochastic path that was actually exercised with `0 < activation < 1` was found.

### E1.5 Historical results possibly affected

- `docs/risk_preserving_approx/iid_relaxation_certified_pipeline_v1.json`: all `activation` values are `1`.
- `iid_relaxation_t8_grid_v1.json`: the LP candidate `repair_activation` is `1` in every cell. The only non-1
  activations are the e-process gate baselines (`gate_4` = 2/5, `gate_8` = 4/5), which are deterministic gate
  policies (re-derived above). **This corrects the earlier audit sentence "all equal 1": the LP candidates all equal
  1; the gate baselines do not, and are safe for the reason above.**
- `iid_relaxation_t10_stress_v1.json`: the single activation field is `1`.
- `docs/paper4/` and `docs/paper4_continuation/` results use the sequence-form `mix_root_never_promote`
  (correct) or value-level bounds. The only appearances of `mix_with_never_promote` under `docs/paper4*` are prose
  describing the hazard. The defect was first observed in the Paper 4 session, not in a saved result.
- Candidate G result `candidate_g_scalarized_dp_screen_v1.json` includes one `root_mix_lambda_4_8` row; inputs are
  deterministic and the risk was verified exactly in-script.
- The old-helper scripts above assert exact repaired risk `<= alpha` after mixing (and in some, metrics equal to the
  branch mixture), so a risk-violating realisation could not have been saved silently.

Conclusion: no saved historical result was produced by the old helper on a stochastic policy with `0 < activation < 1`.
Nothing needs rerunning. The one residual would be a rerun of the three LP scripts on a cell where the IID-relaxed
optimum exceeds `alpha` under causal risk; they must first be switched to `mix_root_lottery`.

### E1.6 Gaps and recommended follow-ups (not done here)

1. Switch the three LP scripts to `mix_root_lottery` (they will otherwise raise). Re-running would change the
   executed-source hashes recorded in their JSONs, so do it only with a new versioned output.
2. Replace the unguarded local `root_mixture` in the candidate G script with a guarded two-policy helper, or add a
   deterministic assertion to it.
3. Add to `tests/test_root_mixture.py`: random stochastic policies (36-case property check above), composition,
   `q = 0` (risk 0 and metrics equal never-promote), and an explicit check that `q` is an exact rational. These checks
   were run ad hoc only.
4. Document in the `mix_root_lottery` docstring that exactness of `Risk = q Risk(pi)` needs the safe plan to have zero
   null risk, and that a float `q` is converted exactly.

## E2. A3 campaign status

- `pgrep -f ablation_campaign`: no process running (checked at the start and again before finishing).
- Output `/Users/nigelli/Desktop/ICML/Shift-lab/.claude/worktrees/failure-atlas-v2-sota-195428/docs/paper4_continuation/results/a3_campaign_v1.json`
  **exists**: 107,558 bytes, modified 2026-11-10 04:10. I confirmed existence and size only. I did not read, validate or
  copy it, so its contents, completeness (25 vs fewer completed runs) and any failures are unchecked.
- It is not present in this branch (`docs/paper4_continuation/results/` here holds only `a4_feasibility_v1.json`), and
  `ENGINEERING_AUDIT.md` still has no A3 result or A5 section.

## E3. Note

FCG retained as certified reference oracle, not a contribution. Its exactness (`L <= V* <= U`) is proved and
reproduced (A1), but the scheme is prior art and the publication decision is NO-GO.

## E4. Ledger reconciliation (corrections to make; no files edited)

Git evidence: `git log --oneline` on the branch (HEAD `bfd86eea`), and file listings under
`docs/paper4_continuation/`, `scripts/paper4_continuation/`, `src/shiftlab/paper4_continuation/`.

### TASK_LEDGER.md

1. First row names branch `research/paper4-antitone-frontier-2026-11-09 @ 8e9366a7`. Work since `b1215242` is on
   `research/paper4-causal-premium-theory-2026-11-10`; add a branch-change row. The ledger lacks rows for `a7a1673f`
   (theory_v2 master plan and ledger) and `bfd86eea` (usage-limit interruption).
2. Row "A2, A3/A4, B, C, E | Launched to subagents ... IN PROGRESS" is stale: all of those are COMPLETE in later rows.
   Mark SUPERSEDED.
3. The "Branch @ commit" column is `—` for every row after A1. Fill from git: meta/D1/D2 `b3e74c25`; A2 `a09683f9`;
   A3 harness and A4 `9c803de8`; literature `e7964dd8`; WP C `bf5a3c7d`; idea-eval C `870553e4`; WP B `ded27a0d`;
   lint note `76b9f744`; WP G `d30b3af0`; WP C follow-up `075a963d`; D3/D4 `ddd957c2`; WP E survivors `510aad8d`;
   H `b1215242`. Row A1 cites `affd5077`.
4. Evidence for A1 is `scratchpad/a1_recheck.py`, which is not in the repo (session scratch). Mark as non-reproducible
   from the repository, or commit the script. `theory_C/fu_*.json` is a glob (files exist; fine).
5. A2 row says "historical activations all 1"; correct to "all LP-candidate activations 1; e-process gate baselines
   2/5 and 4/5 are deterministic" (E1.5). A2 test count "9" should be 11 (E1.3); the "12 tests pass incl. root
   mixture" in the A3 harness row is also off.
6. A3 timing campaign row is absent. Add: campaign finished (process gone); output exists only in the other worktree
   (E2); not yet imported or analysed.
7. "WP E" is used for two different things (literature, novelty audit of survivors) and, in theory_v2, for this
   Engineering work package. Rename to avoid collision.
8. The `D3, D4` row says D4 "pending-asymmetry value test queued after A3". The campaign is finished, so this is now
   unblocked; status should say READY, not queued behind a running campaign.

### NEXT_ACTION.md

1. Item 1 "A3 timing campaign is running" is stale: not running; output exists in `failure-atlas-v2-sota-195428`
   (not under this branch's `results/`, so the file path cited does not exist here).
2. Item 2 (D4 test after campaign): CPU is quiet; now actionable.
3. Item 3 (WP E source-grounded comparison) is DONE (`510aad8d`, `NOVELTY_AUDIT_SURVIVORS.md`). Remove.
4. Item 4: tech-paper-template is DONE (`b1215242`, `PAPER_SKELETON_CHECK.md`); WP G proof review of WP C is DONE
   (`d30b3af0`). The "final fresh-context adversarial review" and `pre-submission-reviewer` are not done.
5. Does not mention the theory_v2 plan (`theory_v2/MASTER_PLAN.md`) or this engineering work package.
6. Item 5: `FINAL_DECISION.md` still says NOT STARTED (consistent).

### THEOREM_REGISTRY.md

1. "D-1..D-4: NOT STARTED" is stale: D1 and D2 are COMPLETE WITH NEGATIVE RESULT, D3 is closed (prior art), D4 is in
   progress (`FALLBACK_SCREENS.md`).
2. Row `C-1`: "proof review pending (WP G)" is stale (done, `d30b3af0`; reviewed corrections are in `C-1 (review)`).
   Same for `C-2` "proof review pending". Row `C-1` also quotes "1,200 symmetric persistent cells" for Lemma U while
   `C-5` and the theory doc give 12,060 cells; update or cross-reference.
3. Duplicate IDs: two rows labelled `C-1` and two labelled `C-2` (one is the review correction). Give the review rows
   distinct IDs.
4. ID offset: registry `C-3` = theory-doc target C4 (upper bound), registry `C-4` = theory-doc target C5 (adaptivity
   gap), registry `C-5` = Lemma U. The TASK_LEDGER and commit `bf5a3c7d` call "C4/C5 NO-GO", which matches the
   theory doc, not the registry's `C-4`/`C-5`. Align the numbering.
5. Missing entries for proved or recorded results in the theory doc follow-up: Lemma P (F2, "any model", PROVED),
   Lemma H (horizon monotonicity), F5 necessity results, and the "Gamma characterisation" that
   `NOVELTY_AUDIT_SURVIVORS.md` ranks as the best survivor.
6. `P4-1`, `P4-2` cite `docs/paper4/theory/01`, which is a prefix only (the file is `01_structural_theorem_audit.md`); give the full
   path.
7. `C-2` states "odd T: Γ = 0" and the Theorem C3 closed form; the review row corrects it to
   `α·min{(g−k)/2−c, g−2k}`. Fold the correction into the main row so the registry reads consistently.

### Other files found stale while reconciling

- `RESULTS_LEDGER.md` has a single row (prior results carried forward). It has no rows for the A4 feasibility JSON,
  the `theory_B/results/*` and `theory_C/*` outputs, the A3 campaign output, or this audit.
- `EXPERIMENT_MANIFEST.md` stops at WP B/C. Missing: WP G, C follow-up, D3/D4, WP E survivors, H, theory_v2, and
  the A3 campaign.
- `ENGINEERING_AUDIT.md`: no A3 result/A5 section; "Seven callers ... one-hot" is correct in count (7 deterministic
  scripts + 3 LP scripts) but see the activation correction above; test count "9" should be 11 and
  "passes (37)" matches the collected 37 for `test_root_mixture + tests/paper4 + test_eprocess_gated_planner`.
- `theory_v2/results/` exists and is empty.

## Test results

All run on a quiet CPU (no campaign process), serially, default plugins.

| Command | Result |
|---|---|
| `uv run --no-sync python -m pytest -q tests/paper4 tests/paper4_continuation` | **26 passed** in 15.6 s (25 in `tests/paper4`, 1 in `tests/paper4_continuation`) |
| `uv run --no-sync python -m pytest -q tests/test_root_mixture.py tests/test_eprocess_gated_planner.py tests/test_causal_switching_game.py tests/test_causal_switching_game_reversal.py` | **24 passed** in 6.3 s (11 root-mixture + 1 gated planner + 12 causal game) |
| `uv run --no-sync python -m ruff check src/shiftlab/dive/root_mixture.py tests/test_root_mixture.py src/shiftlab/dive/eprocess_gated_planner.py` | 2 `RUF059` findings in the test file (cosmetic) |

Ad hoc checks (scratch, not in repo): `e1_check.py` (pre-fix helper reproduction, 36 random stochastic cases,
composition, edges) and `e1_gate.py` (gate planner determinism at T=8, B=3, d=1, thresholds 4 and 8), both run with
`uv run --no-sync python`. Scratchpad:
`/private/tmp/claude-501/-Users-nigelli-Desktop-ICML-Shift-lab--claude-worktrees-shiftlab-methods-strategy-dba13e/06bf436b-d27c-42d6-9116-89f769a07352/scratchpad/`.

## Not checked

- The contents of `a3_campaign_v1.json` and whether the A3 decision rules pass.
- Cells other than C2, C3 and the T=8 gate configuration; the three LP scripts were not rerun.
- Float vs exact agreement in the numeric LP stage, which is outside this audit.

## E2 addendum (lead, 2026-11-10): A3 campaign summary, read-only

Source: `a3_campaign_v1.json` in worktree `failure-atlas-v2-sota-195428` (written 04:10 EST by the other session's
`ablation_campaign.py --reps 5`; campaign `git_head` = `b1215242`, macOS-15.5 arm64, 10 cores). The official A3/A5
write-up belongs to that session (its `NEXT_ACTION.md` item 1); this is an independent read of the raw records.
All 75 runs returned code 0 and status ok; exact final costs agree across R0/R1/R2/F0 in every cell.

| Cell | R0 cached ref | R1 +caching | R2 +num. repr. | I0 learner-only | F0 FCG | FCG cuts |
|---|---|---|---|---|---|---|
| C6 | 6.85 [6.28, 10.75] | 6.42 | 6.66 | 6.10 | 7.23 [7.02, 11.48] | 21 |
| S1 | 64.68 [62.87, 83.44] | 38.33 | 38.01 | 38.00 | 38.06 | 0 |
| T10D1 | 16.70 [16.28, 17.14] | 14.78 | 15.17 | 15.16 | 20.64 [20.23, 37.10] | 33 |

Median wall seconds [min, max] over 5 fresh-process repetitions; peak RSS 197–251 MiB in every cell.
- **Where the time goes:** learner-tree construction (belief updates) dominates every method (e.g. S1 R0: 59.2 of
  59.8 s; T10D1 F0: 9.6 of 15.4 s in-process). LP, cut generation (`cut_rows_float` ≤ 0.24 s) and exact
  certification (≤ 0.54 s) are small.
- **Paired F0/R0 ratios:** C6 1.02–1.17; T10D1 1.20–2.17; S1 0.46–0.63. The S1 gain is matched by R1 (0.46–0.61),
  so it is caching, not FCG.
- **Protocol criteria:** "F0 or I0 faster than R0 in every pair" — I0 holds on C6 and S1 but not T10D1 (rep 0:
  1.20); F0 fails on C6 and T10D1. "Attributable to cut generation (F beats R2 on a cut cell)" — **fails** on both
  cut cells (C6 7.23 vs 6.66; T10D1 20.64 vs 15.17).
- I0's final cost differs from V* by design (iteration-0 relaxation plus repair), so I0 is not a substitute solver.
- **Caveat:** this session's five agents were launched at 03:48 while the campaign ran (03:41–04:10); they stopped
  on a usage limit within minutes, but may have added light CPU load to some repetition-0/1 runs.
- **Verdict (E3 confirmed):** no runtime advantage attributable to FCG's cut generation; FCG is retained as the
  certified reference oracle only.
