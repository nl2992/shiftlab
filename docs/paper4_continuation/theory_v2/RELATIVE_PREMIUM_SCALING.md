# Relative premium scaling (descriptive) — wpC2

**Run:** `scripts/paper4_continuation/theory_v2/wpC2_relative_premium.py` (sha256 recorded in the output), started
2026-11-10 20:45 EST, 3 workers, `nice 10`, 2.5 h wall cap; finished 2026-11-11 00:10. 1,808 cells planned:
**1,762 ok, 46 not run** (all at T = 10, B = 6, wall cap). Full exact output (42 MB) kept out of git at
`outputs/paper4_theory_v2/wpC2_relative_premium_v1.json` (sha256 `72bd5906…7e1a73f`); float projection committed as
`results/wpC2_relative_premium_v1_compact.json`. **Descriptive, synthetic; not confirmatory.**

**Statistic.** ρΓ = Γ / (C₀ − V*_IID): the premium per unit of the IID value of information. C₀ = Σ_t P_A(Y_t = 1)
(= T/2 for stationary symmetric chains). Γ from `gamma_cell` certified intervals (midpoint; interval widths ≤ 1e-12).
Families: **F_persist** t ∈ {1/10, 1/4}, e ∈ {(1/100, 99/100), (1/10, 9/10)}, d ∈ {1, 2}, c = k = 0;
**F_anti** t ∈ {3/4, 9/10}, e = (1/10, 9/10), d = 1, c = 0, k ∈ {0, 1/50}; **F_coin** prior 0, t01 = 1/2,
t10 = 1/10, e = (1/10, 3/5), d = 1, c = k = 0. α ∈ {1/20, 1/10, 1/4, 1/2}; T 4–10; B 1–6 with B ≤ T − d.

**Lead verification (exact, `gamma_cell`):** F_anti t = 9/10, T = 7, B = 4, α = 1/20: Γ = 0.126441472, VOI = 0.2013217,
ρΓ = 0.62806; T = 9, B = 6: Γ = 0.289254896, VOI = 0.4044614, ρΓ = 0.71516 (FCG-fast, 82 rows). Both equal the run.

## Max over configurations and α ≤ 1/2 of ρΓ, with [certified Γ > 0 / cells]

```
not run (family,T,B): [('F_anti', 10, 6), ('F_coin', 10, 6), ('F_persist', 10, 6)]

== F_persist
max rho [pos/total] T rows x B cols [1, 2, 3, 4, 5, 6]
4 0.0000[0/32] 0.0000[0/32] 0.0000[0/16]       -             -             -      
5 0.0000[0/32] 0.0000[0/32] 0.0000[0/32] 0.0000[0/16]       -             -      
6 0.0000[0/32] 0.0000[0/32] 0.0000[0/32] 0.0000[0/32] 0.0000[0/16]       -      
7 0.0000[0/32] 0.0000[0/32] 0.0000[0/32] 0.0000[0/32] 0.0000[0/32] 0.0025[1/16]
8 0.0000[0/32] 0.0000[0/32] 0.0000[0/32] 0.0000[0/32] 0.0105[3/32] 0.0150[4/32]
9 0.0000[0/32] 0.0000[0/32] 0.0000[0/32] 0.0022[2/32] 0.0155[6/32] 0.0211[11/32]
10 0.0000[0/32] 0.0000[0/32] 0.0000[0/32] 0.0039[2/32] 0.0168[9/32] 0.0291[2/6]
 B=1 max rho 0.0000 at (T,B)=(10, 1) cfg/alpha/Gamma=None; certified-positive 0/224
 B=2 max rho 0.0000 at (T,B)=(10, 2) cfg/alpha/Gamma=None; certified-positive 0/224
 B=3 max rho 0.0000 at (T,B)=(10, 3) cfg/alpha/Gamma=None; certified-positive 0/208
 B=4 max rho 0.0039 at (T,B)=(10, 4) cfg/alpha/Gamma=(1, '1/2', 0.007007); certified-positive 4/176
 B=5 max rho 0.0168 at (T,B)=(10, 5) cfg/alpha/Gamma=(0, '1/2', 0.044119); certified-positive 18/144
 B=6 max rho 0.0291 at (T,B)=(10, 6) cfg/alpha/Gamma=(0, '1/2', 0.079734); certified-positive 18/86

== F_anti
max rho [pos/total] T rows x B cols [1, 2, 3, 4, 5, 6]
4 0.3235[16/16] 0.2453[16/16] 0.5025[16/16]       -             -             -      
5 0.3235[16/16] 0.3964[16/16] 0.3799[16/16] 0.5924[16/16]       -             -      
6 0.3235[16/16] 0.2946[16/16] 0.5187[16/16] 0.5200[16/16] 0.6302[16/16]       -      
7 0.3235[16/16] 0.3405[16/16] 0.4446[16/16] 0.6296[16/16] 0.6397[16/16] 0.6749[16/16]
8 0.3235[16/16] 0.2762[16/16] 0.4714[16/16] 0.5602[16/16] 0.6712[16/16] 0.7058[16/16]
9 0.3235[16/16] 0.2906[16/16] 0.4001[16/16] 0.5897[16/16] 0.6519[16/16] 0.7152[16/16]
10 0.3235[16/16] 0.2421[16/16] 0.4093[16/16] 0.5187[16/16] 0.6416[16/16]       -      
 B=1 max rho 0.3235 at (T,B)=(10, 1) cfg/alpha/Gamma=(9, '1/20', 0.0055); certified-positive 112/112
 B=2 max rho 0.3964 at (T,B)=(5, 2) cfg/alpha/Gamma=(11, '1/4', 0.1408); certified-positive 112/112
 B=3 max rho 0.5187 at (T,B)=(6, 3) cfg/alpha/Gamma=(11, '1/20', 0.060495); certified-positive 112/112
 B=4 max rho 0.6296 at (T,B)=(7, 4) cfg/alpha/Gamma=(11, '1/20', 0.119306); certified-positive 96/96
 B=5 max rho 0.6712 at (T,B)=(8, 5) cfg/alpha/Gamma=(10, '1/20', 0.192789); certified-positive 80/80
 B=6 max rho 0.7152 at (T,B)=(9, 6) cfg/alpha/Gamma=(10, '1/20', 0.289255); certified-positive 48/48

== F_coin
max rho [pos/total] T rows x B cols [1, 2, 3, 4, 5, 6]
4 0.0000[0/4] 0.0509[3/4] 0.0604[3/4]       -             -             -      
5 0.0000[0/4] 0.0543[3/4] 0.0636[4/4] 0.0879[4/4]       -             -      
6 0.0000[0/4] 0.1131[3/4] 0.1039[4/4] 0.1074[4/4] 0.1037[4/4]       -      
7 0.0000[0/4] 0.1336[4/4] 0.1351[4/4] 0.1342[4/4] 0.1294[4/4] 0.1377[4/4]
8 0.0000[0/4] 0.1444[4/4] 0.1464[4/4] 0.1469[4/4] 0.1475[4/4] 0.1527[4/4]
9 0.0000[0/4] 0.1520[4/4] 0.1718[4/4] 0.1694[4/4] 0.1728[4/4] 0.1794[4/4]
10 0.0000[0/4] 0.1578[4/4] 0.1876[4/4] 0.1834[4/4] 0.1900[4/4]       -      
 B=1 max rho 0.0000 at (T,B)=(10, 1) cfg/alpha/Gamma=None; certified-positive 0/28
 B=2 max rho 0.1578 at (T,B)=(10, 2) cfg/alpha/Gamma=(12, '1/10', 0.006018); certified-positive 25/28
 B=3 max rho 0.1876 at (T,B)=(10, 3) cfg/alpha/Gamma=(12, '1/20', 0.003872); certified-positive 27/28
 B=4 max rho 0.1834 at (T,B)=(10, 4) cfg/alpha/Gamma=(12, '1/10', 0.007878); certified-positive 24/24
 B=5 max rho 0.1900 at (T,B)=(10, 5) cfg/alpha/Gamma=(12, '1/20', 0.004284); certified-positive 20/20
 B=6 max rho 0.1794 at (T,B)=(9, 6) cfg/alpha/Gamma=(12, '1/10', 0.007344); certified-positive 12/12
```

## Reading (data only)

- **F_anti:** ρΓ rises with B at every T: max 0.32 (B = 1) → 0.40 → 0.52 → 0.63 → 0.67 → **0.72 (B = 6)**; Γ > 0 is
  certified in every cell. At B ≥ 3 it exceeds the proved B = 1 ceiling ρΓ ≤ 1/2. The largest values occur at the
  smallest α (1/20).
- **F_persist:** Γ = 0 in every cell with B ≤ 3; positive from B = 4 and rising: max ρΓ 0.004 (B = 4), 0.017 (B = 5),
  0.029 (B = 6); 18 of 86 B = 6 cells certified positive. Absolute Γ up to 0.080 (T = 10, B = 6, α = 1/2).
- **F_coin:** ρΓ roughly flat in B from B = 2 (0.16–0.19), increasing mildly in T.

## Locked decision rule (ledger, 2026-11-10 ~20:50, before any output was read)

Condition for one bounded general-B theorem attempt: in F_persist or F_anti, max ρΓ at the largest completed B
≥ 0.05, not below its B = 2 value by more than a factor 2, and certified Γ > 0 in ≥ 3 largest-B cells.
**F_anti meets it** (0.715 at B = 6 vs 0.396 at B = 2; 48/48 positive). F_persist does not (0.029 < 0.05).
**Outcome: launch one bounded general-B theorem attempt on the anti-persistent family.**
