# PAVE-EF C3 confirmation protocol (frozen before any confirmation run)

Registered 2026-11-08 in the commit that adds this file. Development evidence: `41_PAVE_MATCHED.md`
and `42_PAVE_ON_EF.md`, including amendments 1–2. Prior art: `60_PAVE_NOVELTY.md` (weak
NOVEL-INTEGRATION).

## Frozen method

`pave_ef` (`scripts/methods_recovery/pave_ef.py`, class `PaveEF`): the `episode_front` engine with
PAVE's pending-aware value-of-information acquisition (`PAVE_TUNED`, unchanged since GAVE-R),
active only when d ≥ 2T/(B+2). No parameter is tuned for C3.

## Arms

- `episode_front`: the same engine on its uniform label calendar. This is the **primary
  comparator**; development showed it identical to the matched `ef_dss`.
- `pave_ef`.
- `pave_ef_novoi`: the VoI rollout replaced by a deadline-truncated calendar, as the
  **attribution control** (`pave_ef_matched.NoVoI`).

## Target family and cells (54)

The 9 GAVE-R gate-on Family-3 specifications (`pave_matched.GATE_ON_50`) at:
- **in-family delays** d ∈ {50, 100, 200}, 27 cells, already used in development but with
  fresh seeds;
- **unseen delays** d ∈ {75, 150, 300}, 27 cells, never run.

The runner asserts that every cell satisfies the gate.

## Seeds

- `pave_c3_eval`: 102300000–102399999. Cell i uses 102300000 + 1000·i + k, k < 100.
- `pave_c3_null`: 102400000–102499999.

Both are registered in `configs/seed_registry.yaml` in this commit.

## Primary analysis (two contrasts, Holm-adjusted at familywise .05)

Effects are relative differences of equal-weight cell-mean J/T over all 54 cells. CIs and
p-values come from a paired bootstrap over seeds within cells (10,000 resamples; two-sided
p = 2·min(share of resamples ≥ 0, share ≤ 0)).

- **P1 (effect):** `pave_ef − episode_front` ≤ −2% of `episode_front` J/T (point estimate), with
  Holm-adjusted p < .05.
- **P2 (mechanism):** `pave_ef − pave_ef_novoi` < 0, with Holm-adjusted p < .05.

**Validity guard.** On the d=50 null grid (`pave_ef.null_cells()`, 500 fresh streams per cell),
the false-promotion Clopper-Pearson 95% upper bound of `pave_ef` in the independent-label nulls
(ρ = 0, and f1null) must be ≤ .10. Dependent-label nulls (ρ ≥ .5) are reported only: the engine
makes no validity claim there.

**C3 PASS** = P1 and P2 and the guard. Also reported:
- the in-family vs unseen-delay split;
- per-delay contrasts;
- losing cells;
- labels used, arrival before T and pending inventory.

## Not allowed

No retuning after confirmation results. No change of cells, weights, comparators or rule. A
failure is recorded as a failure.
