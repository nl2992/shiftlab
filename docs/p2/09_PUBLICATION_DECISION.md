# P2-NAD publication decision (2026-11-10)

## Verdict

**The current result is not a competitive ICML/NeurIPS/ICLR main-track algorithmic paper.** Per
the brief, no fallback venue is recommended. Below are what exists, what is missing, and the
direction with the highest expected value.

## What the programme produced

- **A new controller family (NAD / NAD-2S).** It has a stated validity proof for a declared
  dependence class. It is about 3% cheaper than the dependence-robust state of the art on
  synthetic alternatives (registered H1/H3a; small effect). It keeps level α in class and passes
  Tier B.
- **A quantitative account of the price of robustness.** This is an information-rate bound
  for the per-step class. It explains why every marginal-null-valid method costs ~10% more than
  V1 certificates on persistent alternatives.
- **Two benchmark corrections.**
  - An author-faithful MOPE endpoint. The repo's earlier MOPE comparisons understated it by
    3–6%.
  - A 7,440-episode real-twin validity map. Every V1 certificate, including author-faithful MOPE,
    promotes at 11–22% on exact real marginal nulls.
- **A frozen, registered confirmation** with honest failures (H2, H3, H6, H7).

## Why it is not main-track ready

1. **No cost win against the strongest comparator.** Author-endpoint MOPE and the V1 front-loaders
   are cheaper everywhere. NAD's advantage holds only inside the robust class, and on real data
   it vanishes (H2/H3 ties).
2. **The motivating harm is not visible on real data.** Invalid promotions on real twins are
   economically harmless or beneficial (C7). A skeptical reviewer will ask why anyone should pay
   for marginal-null validity. The answer currently rests on synthetic ρ = .95 nulls.
3. **The theory is elementary and relaxed.** Validity is testing-by-betting plus Ville. The rate
   bound holds for the per-step relaxation only. A lower bound for the stationary class, which UI
   can beat, is missing.
4. **Novelty is integrative.** The envelope bet existed internally (QSG-env8), A5b already spaced
   queries, and universal inference is known. The new parts are the restart-safe conditioning, the
   sign-independent two-stream design, and the robustness value. These are modest.

## What would be needed (for this line)

- Real streams with **strong, economically harmful** serial dependence. That means a dataset where
  V1 promotions measurably cost money. Without it, the robustness story is synthetic.
- A stationary-class lower bound matched by an algorithm. That would turn C8 into a tight
  characterisation.
- An external review of P1–P5.

## Highest-expected-value next direction

The repeated finding across P1 and P2 is that **per-stream information is the binding
constraint**:
- free labels are worth ≤ 5 units;
- tweaks to the evidence process move cost by ≤ 3%;
- real dependence is weak.

The one lever no programme has tested is **pooling across streams**. A team that runs many
concurrent incumbent/challenger decisions (C4 has 27 sources and 2,097 episodes) can share an
effect-size prior. It can use compound or e-BH-style decisions to control the fleet-level false
promotion rate. That would replace the per-stream α, and the gains could be large. This
direction:
- is information-theoretically different from everything screened so far;
- has natural top-venue theory (compound decisions, e-value FDR under dependence);
- has data available locally.

Recommendation: scope a "fleet-level certified promotion" pilot on C4 before any further
single-stream method search.

## Reproduction

The confirmation was run detached with `scripts/p2/run_confirm.sh` from the frozen worktree. The
analysis is `PYTHONIOENCODING=utf-8 python scripts/p2/analyze_confirm.py outputs/p2/confirm` with
the env from `scripts/p2/env.sh`. Development commands are in `04_DEVELOPMENT_RESULTS.md`.

## Addendum 2026-11-10: fleet-level pilot

The recommended direction was piloted (`fleet/PILOT_REPORT.md`) and is a **NO-GO**:
- Pooled betting priors change cost by ≤ 0.2% (synthetic) and +0.04% (27 real sources).
- e-LOND online FDR costs 0.8–2.3%, because any fleet error guarantee is at least as strict as a
  per-decision α.

The remaining lever with the highest expected value is a new information source, for example
earlier or cheaper feedback. Another statistical test on the same information is not it.
