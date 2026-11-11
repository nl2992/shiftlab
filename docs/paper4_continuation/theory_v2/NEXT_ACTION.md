# theory_v2 — next action

**State (2026-11-11):** programme complete; publication decision **main-track NO-GO (existing results too narrow)**,
see `PUBLICATION_DECISION.md`. No manuscript work.

Only these would reopen a main-track route. Each needs the user's approval and a new locked protocol:
1. **Non-vanishing relative premium for t < 1.** A proof that Γ/(C₀ − V*_IID) stays ≥ c > 0 as T and B grow in
   a stochastic anti-persistent or persistent family. At t = 1 it provably vanishes (Thm A/V, unreviewed), so this
   is expected to fail; attempt it only with a new mechanism in hand.
2. **Lemma S+** (static alternative, c > 0, B ≥ 2 ⇒ Γ = 0). Proving it extends S0 but stays inside known machinery;
   on its own it would not change the decision.

Housekeeping if the branch is kept:
- Independent review of Thm A, Thm V and Lemma A (`GENERAL_B_PREMIUM.md`).
- Carry-over from the earlier phase: D4 pending-asymmetry value test (`FALLBACK_SCREENS.md`), unblocked.
- The full exact scaling output is at `outputs/paper4_theory_v2/wpC2_relative_premium_v1.json` (gitignored, local
  only).
- Do not merge this branch into `main` automatically.

## Superseded 2026-11-11
Item 1's "expected to fail" for t < 1 is withdrawn: the committed data show a T-flat relative premium in mixing
anti-persistent chains. The live plan is `SALVAGE_PLAN.md`; the decision is reopened.
