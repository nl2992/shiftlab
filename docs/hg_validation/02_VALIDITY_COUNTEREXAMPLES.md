# 02. Counterexample and repair (exact finite-support; `outputs/hg_validation/02_EXACT_NULL_TESTS.json`)

Two equiprobable contexts, risks (0.6, 0.2) so the marginal risk equals r0 = 0.4 exactly, q = 0.1, bet ceiling λ0 = 1 (any predictable value is allowed by the theorem).
| proxy | cap | exact E[λ(Z)X] per step | λ by context | MC P(sup E ≥ 20), 400 steps, 4000 paths |
|---|---|---|---|---|
| anti-informative (0.05, 0.35) | context-dependent (HG as implemented) | **+0.0447** | (0.588, 0.141) | **0.0675 > α=0.05** |
| anti-informative | uniform support bound | 0 | 0.189 / 0.189 | 0.035 |
| calibrated (0.6, 0.2) | context-dependent | −0.0141 | (0.086, 0.227) | 0.0045 |
| calibrated | uniform | n/a | | toy proxy 0.6 exceeds the Brier support bound 0.25, so this cell is not a valid check |

**Conclusion.** With a context-dependent cap the product has positive exact drift under the marginal null, i.e. it is **not** a supermartingale, and a crossing probability above α occurs. A calibrated proxy makes the violation conservative (cap is small where the increment is positive), which explains why the observed null false alarm is ≤ .03 in all synthetic runs; an anti-informative or misspecified proxy can break the guarantee. The counterexample uses the idealised λ0 = 1; the plug-in bet is tiny under a stationary null, so the practical inflation is small, but the *guarantee* does not hold.

**Repair (verified):** cap with the a-priori support bound (proxy ≤ 1/4 for Brier, ≤ 5/6 for decision cost) so λ_t depends on resolved labels only. Exact drift is 0 and the MC crossing is 0.035. Power cost on the 19-world dev pool (200 seeds):
| labels | arm | harm power | benign FA | null FA |
|---|---|---|---|---|
| 10% | pprm_tight / unifcap | .485 / .502 | .042 / .046 | .015 / .015 |
| 10% | HG / HG_unifcap | .591 / .603 | .035 / .038 | .030 / .030 |
| 20% | pprm_tight / unifcap | .730 / .746 | .096 / .101 | .010 / .010 |
| 20% | HG / HG_unifcap | .834 / .839 | .102 / .104 | .025 / .025 |
The repaired bound costs no power on these worlds (slightly more). **Open:** BD's context-dependent q needs q_min in the bound; the repaired variant is not yet re-run on held-out data.
