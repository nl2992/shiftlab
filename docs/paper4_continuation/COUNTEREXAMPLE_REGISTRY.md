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
