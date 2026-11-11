# Counterexample registry

| ID | Refutes | Exact witness | Verified by |
|---|---|---|---|
| CE-1 | Marginal-average randomised risk certificate | 2-branch coin example: true 3/4 vs certificate 1/2 | `tests/paper4/test_counterexample_library.py::test_E` |
| CE-2 | Posterior-only compression | Alias example (full-history value 128/125 vs posterior-only 14/25) | test A |
| CE-3 | Monotone restriction is cost-free | Monotone best value 0 vs unrestricted 19/200 | test D |
| CE-4 | Rare-history pruning is safe | Alternative mass 1/200; risk 1/2 vs 0 | test K |
| CE-5 | IID relaxation is tight | C2/C3/C6: Gamma = 0.0417 / 0.0118 / 0.0116 (`L0` vs `V*`) | `docs/paper4/experiments/results/fcg_dev_v1.json` |
| CE-6 | "TP2 transition + MLR emissions ⇒ Γ = 0" | T=4, B=2, d=2, t01=2/5, t10=1/20, emissions (1/10,3/5), prior 0, c=k=0, α=1/10: Γ = 657/5000000; IID optimum promotes iff (Y1,Y2)=(0,1); violates (M) | WP C agent; lead re-computed with FCG + reference (`scratchpad/verify_c.py`) |
| CE-7 | "Γ is T-invariant in general" | C2 family (B=2, tr 9/10, em 1/10): Γ = 0.032567, 0.029459, 0.028712 at T=8,9,10 | WP C agent (`theory_C/` JSON) |
| CE-8 | "TP2 + MLR ⇒ Γ = 0" already at B = 1 | T=5,B=1,d=2,t01=1/2,t10=0, em (3/20,3/5), prior 0, c=k=0, α=1/10: Γ = 39/32000 | WP G reviewer; lead re-computed (`scratchpad/verify_g.py`) |
| CE-9 | Original Theorem C3 formula | e=1/4,k=1/10,c=0,α=1/10, T=4,6: true Γ = 0.005 vs claimed 0.0075 | WP G reviewer; lead re-computed |
| CE-10 | "TP2 + MLR ⇒ Γ = 0" at B ≥ 2 (smallest) | T=3,B=2,d=1,t01=1/2,t10=1/10, em (1/10,3/5), prior 0, c=k=0, α=1/10: Γ = 9/50000 | WP C agent; lead re-computed (`scratchpad/verify_c2.py`) |
| CE-11 | Symmetric persistent ⇒ Γ = 0 without a stationary start | T=6,B=3,d=1,t=1/4, em (1/10,9/10), prior 0, α=1/10: Γ = 0.00216; same cell with prior 1/2: Γ = 0 (lead control) | WP C agent; lead re-computed with control |
| CE-12 | "Symmetric stationary persistent ⇒ Γ = 0" (Z2) and "TP2 + M_marg ⇒ Γ = 0" (U-M), for every α | T=5,B=4,d=1,t01=t10=1/10, em (1/100,99/100), prior 1/2, c=k=0, α=25/32: Γ ≈ 0.0020925 (certified); Γ = 0 at every other α tested in [1/20, 7/8] | theory_v2 WP-B agent (`wpB_ce_record_v1.json`); lead re-computed with `gamma_cell` |
| CE-13 | C3′ formula at T = 2 | e=1/4,k=1/10,c=0,α=1/10,T=2: Γ = 3/400 vs C3′ 1/200 (correct: α((g−k)/2−c) at T=2) | theory_v2 WP-A auditor; lead re-computed |
| CE-14 | "Symmetric stationary persistent and α ≤ 1/2 ⇒ Γ = 0" (Z2≤½) | T=8,B=4,d=2,t01=t10=1/4, em (1/1000,999/1000), prior 1/2, c=k=0: Γ ≈ 1.2846e-4 at α=5/16, 3.21e-5 at α=1/2 (certified); smallest α with Γ>0 seen 21/128 (T∈{9,10}, B∈{6,7}) | theory_v2 WP-B (`wpB2_record_v1.json`); lead re-computed with `gamma_cell` |
| CE-15 | "Even delay d ⇒ Γ = 0" beyond B = 1 (true at B = 1, SP1) | T=4,B=2,d=2,t01=t10=3/4,e=(1/10,9/10),prior 1/2,c=k=0,α=1/10: Γ(1)=0, Γ(2)=1/500 | theory_v2 WP-C; lead re-computed |
| CE-16 | "Switching cost lowers Γ" | t=3/5,e=1/10,d=1,T=60,c=0,B=1: Γ/α 0.05333 (k=0) → 0.054 (k=1/50) | theory_v2 WP-C (closed form, SP1) |
| CE-17 | "Γ monotone in B" (stochastic anti-persistent) | T=4,d=1,t=3/5,e=1/10,c=0,k=1/50: Γ(1)=0.0054 > Γ(2)=0.00412 < Γ(3) | theory_v2 WP-C |
| CE-18 | SP1-D "g ≤ 2k ⇒ Γ = 0" at T = d+1 | T=2,d=1,t=1,e=1/10,c=0,k=2/5,α=1/10: Γ = 3/250 | theory_v2 SP1 reviewer; lead re-computed |
| CE-19 | "Γ decreases in d for k > 0" at fixed small T | T=8,t=99/100,e=1/4,c=1/100,k=1/10,α=1/4: Γ ≈ 0.0054 (d=5) < 0.0121 (d=7) | theory_v2 SP1 reviewer (closed form + exact DP) |
