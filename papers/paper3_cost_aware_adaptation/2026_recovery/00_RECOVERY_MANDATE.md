# Paper 3 recovery mandate (2026-11-10)

Branch `research/paper3-recovery-2026-11-10`, worktree `ICML/shiftlab-paper3-recovery-2026-11-10`.
Rooted at the Paper 3 head `20464a26`. All earlier work is preserved unchanged, both on that branch
and in `../2026_programme/`.

## Source of the F1–F3 definitions (blocker, recorded)
The user's message refers to an "original recovery prompt" defining F1–F3. That text is not in
this session, in any branch, or on disk: a search of the repository and the project transcripts
found only the 2026-11-10 user message. F1–F3 below are reconstructed from that message, which is
quoted where possible. If the original prompt is supplied, `10_CHECKLIST.md` must be re-mapped
against it.

## Workstreams (from the user's 2026-11-10 message)
- **F1:** joint information acquisition, evidence weighting and economically actionable
  certification. Benchmark against standard empirical-Bernstein methods. Preserve the sparse-label
  results (B3 M2: about 28 vs 137 labels on synthetic data). Claim no novelty without an
  attributable mechanism. The B3 diagnosis is accepted: the binding term is the drift slack
  v·(d+(h−1)/2). Evidence weighting (discounting by age) trades that bias against variance, and
  this is the F1 lever to test.
- **F2:** certificate-aware acquisition, i.e. acquisition rules that target certificate growth per
  label and per unit cost. The failed A0–A5 planners do not reject all acquisition rules.
- **F3 (mandatory):** reversible, risk-budgeted intervention. The decision and safety formulation
  differs from future-payback certification. Interventions may be rolled back, and the guarantee
  bounds realised, identifiable harm (for example cumulative excess loss of the intervention
  relative to the incumbent, plus switching fees) by a risk budget R with probability ≥ 1−α,
  anytime. It does not forecast future payback.

## Evaluation protocol
- Development: the exposed c4 streams. EVEN episodes are used for all choices; ODD episodes are a
  single selection check. Synthetic validity is checked first, on the payback null classes and on
  the core 24-regime simulator (`src/shiftlab/paper3/simulation.py`).
- Fresh data: a new real batch that no programme has opened. It is built, hashed and sealed before
  any F-method is frozen (owner: data agent; `05_FRESH_DATA_INVENTORY.md`). Confirmation is
  registered in `06_CONFIRMATION_REGISTRATION.md` before opening and is opened once.
- Comparators (strongest relevant, not only B2):
  - Wald+cutoff (Paper 1 reference)
  - B0a/B0w/B0b, B2, B3
  - standard empirical-Bernstein confidence sequences: Waudby-Smith & Ramdas PrPl-EB and hedged
    betting, and Howard et al. stitched EB
  - CUSUM / e-process gate with rollback
  - a conservative-bandit-style budget rule
  - a Drift2Act/RAR-style rollback adapter where applicable
  Each is labelled NATIVE / DOCUMENTED_ADAPTER / IN_HOUSE. Tuning budgets are equal and logged.
- Effects are graded on the user's scale. A narrower scoped contribution is acceptable when its
  mechanism, comparators and scope are clear. No universal-dominance requirement applies.

## File ownership (only the PI session commits)
| Owner | Files |
|---|---|
| Audit | `01_*.md`, `references_recovery.bib` |
| Data | `05_FRESH_DATA_*`, `scripts/paper3/recovery/data/`, data under `../shift-research-starter/data/p3_fresh/` |
| F1 | `src/shiftlab/paper3/recovery/f1/`, `scripts/paper3/recovery/f1/`, `tests/paper3/recovery/f1/`, `F1_*.md` |
| F2 | same pattern under `f2/`, plus `F2_*.md` |
| F3 | same pattern under `f3/`, plus `F3_*.md` |

Ledgers go to `ledger/<owner>.jsonl`. Outputs go to `outputs/paper3/recovery/<owner>/`, which is
gitignored; summaries are copied to `results/`.
