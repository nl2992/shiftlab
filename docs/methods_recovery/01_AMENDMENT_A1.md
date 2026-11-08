# Gap-Mix+ prereg Amendment A1 (2026-11-08): Arm-5 pacing for neighbour families

**Defect.** The registered tuning stage selected Arm-5 fixed pacing only for the six target
(B/T, d) families. The alt evaluation also includes neighbouring-control cells with d = 50 and
B/T = .5, whose families had no frozen Arm-5 config. The alt run therefore crashed
(`KeyError: 'b0.05_d50'`) after writing a partial set of rows. The null stage completed.

**Fix.** Arm 5 for the five missing families (b0.05_d50, b0.1_d50, b0.25_d50, b0.5_d1,
b0.5_d10) is selected by the registered rule (§4: best of the 32-config grid, per family,
equal-weight cell mean J/T) on **tuning seeds only**: block 101306000–101309999, inside the
registered tuning block and unused by stage `tune`, with 8 seeds per cell. Output:
`configs/methods_recovery/gapmix_plus_frozen_nb.json` (+ sha256). The original frozen config
and its hash are unchanged. Arm 4 is unchanged.

**Integrity.**
- The partial alt rows were not inspected or analysed before this amendment.
- No eval outcome informs the neighbour selection.
- The alt stage then resumes. The runner skips rows already written, and those rows came
  from the unchanged frozen configs.
