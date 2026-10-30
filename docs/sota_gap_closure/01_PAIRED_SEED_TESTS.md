# 01 Paired-seed tests
* Same `qseed` => identical query events for arms with equal `q_t` (HG vs `pprm` at equal fraction have identical `labels` per seed) - `test_seed_reproducibility_and_common_random_numbers`.
* Different `qseed` => different label events.
* Identical inputs reproduce `logW` bit-for-bit.
* Arms in each experiment run on the same world objects: world `w` uses `seed0 + 1000 w` for every configuration (`store.run_grid`), so paired differences are computed per seed.
* Q2/Q3 use one stream per world shared by all methods/policies; Q3 policies share the label uniform matrix `U`.
Genuinely different query decisions (growth, variance, CAMS-style) still use the same `U`, so paired comparisons differ only through `q_t`.
