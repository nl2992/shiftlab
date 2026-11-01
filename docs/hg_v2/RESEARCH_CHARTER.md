# Research charter (sprint v2) — branch `research/hg-decision-aware-betting-v2`, from `1299c1c`

This sprint has its own acceptance criteria and does **not** rewrite the legacy exit condition ("verified wins over known benchmarks on synthetic and real data"), which stays recorded as **unmet** (`docs/sota_synthetic_search/16_*`, `docs/hg_validation/*`). Historical failures are preserved.

**Two objectives, never conflated.** A: control a predictive (Brier) risk null. B: control a decision-cost null. A Brier e-process with a cost gate is an *Objective-A* guarantee with an empirically decision-aware filter; it carries **no** no-decision-harm guarantee.

**Compute budget:** planning ceiling 12 CPU-hours for the first pass; development searches here are minutes each.
**Data discipline:** G1/G2/G3 confirmation pools are exposed (descriptive only). Development uses fresh seed blocks 40000+ (dev worlds) and 41000 (G3 development stream). Confirmation will use new generator families (G4–G6) and seed blocks ≥ 50000, frozen first.
**Pre-registered development metrics:** harm power, benign-world false alarm, null false alarm at the theory threshold (1/α, α = .05); G3-development power and false alarm; then a threshold-swept benign-FA frontier for the top candidates, calibrated on development data only.
**Development selection (H1):** a candidate is carried forward if, at **both** label rates, (i) harm power ≥ HG_unifcap + 0.03 on the dev worlds, or (ii) it dominates ONS at a matched benign-FA cap ≤ .05 by ≥ 0.03, and null FA ≤ .07. Special-case winners are retained and labelled.
**Contracts:** H1 (gated ONS) — Objective-A validity under H0-A with fixed known delay (bet and gate depend on resolved labels only); decision-awareness is empirical. H2 — Objective B contract needs a cost null; H3 — dependence-aware, contract stated per variant.
