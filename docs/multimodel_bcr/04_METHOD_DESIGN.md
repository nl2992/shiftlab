# BCR prototype design (as tested)

Deployment is the shared K-Wald rule (01_BASELINES.md).

- **Economic challenger set.** P = {j ≠ i : (m_ij + z_u·se_ij)·r_R·(T−t) > c_s}: the challengers
  whose optimistic remaining-horizon payback covers the switching cost.
- **Decision-relevant acquisition.**
  - An event is relevant if the models in {i} ∪ P do not all agree.
  - Relevant events are budget-paced over the estimated number of remaining relevant events.
  - Other R events are queried at ρ_mon × the base rate (floor .02). This keeps q > 0, so the
    IPW evidence stays consistent.
  - The first 20 labels use disagreement pacing.
- **Grid.** λ{.85,.9,.95} × γ{.05,.1,.15,.25} × z_u{.5,1.5} × ρ_mon{.1,.3}.

Candidates A–E (directive §9) were not developed because the gate failed. Candidate B
(ranking-sensitive acquisition) is effectively already tested as B4: Model Picker's
posterior-weighted disagreement probability is a ranking-sensitive query rule, and it ties B2.
