# Round 1 development findings

540 distinct algorithm configurations completed on 8 registered cases (4,320 configuration-case evaluations), 64 paths each. Corrected evaluator version is authoritative for shift-attributable harm. This is exploratory, known-nominal, finite-support simulation; not real-data confirmation or exhaustive published-method superiority.

## Baseline provenance

Active-RCPS fixed-target component matches author code at delay 1 (max logwealth error 1.33e-15). Its delay-5/24, hard-cap, complement-risk monitoring wrapper is a separate adaptation. The full learned query policy and RCPS grid inversion are not reproduced. Other published families remain open in BASELINE_COVERAGE.md.

## Candidate ranking

Ranking uses empirical null rate <=.05, then lower mean shift-attributable harm before alarm. With only 64 null paths, this is a triage filter, NOT evidence that size is controlled at .05. No confirmed finalist is declared.

     id  post_power  harm_to_alarm     labels  worst_null_alarm  guidance  gamma  cap allocation  restart  empirical_screen_eligible
R1_0139    0.997396      20.491953 234.122396          0.031250      0.25   0.90 0.75    uniform     True                       True
R1_0121    0.994792      20.679870 234.122396          0.031250      0.25   0.80 0.75    uniform     True                       True
R1_0247    0.994792      20.804271 234.122396          0.031250      0.50   0.90 0.75    uniform     True                       True
R1_0229    0.997396      21.127292 234.122396          0.046875      0.50   0.80 0.75    uniform     True                       True
R1_0031    0.992188      21.210234 234.122396          0.031250      0.00   0.90 0.75    uniform     True                       True
R1_0157    1.000000      21.235339 234.122396          0.031250      0.25   0.95 0.75    uniform     True                       True
R1_0265    1.000000      21.305938 234.122396          0.015625      0.50   0.95 0.75    uniform     True                       True
R1_0133    1.000000      21.373672 234.122396          0.031250      0.25   0.90 0.50    uniform     True                       True
R1_0013    0.992188      21.483073 234.122396          0.015625      0.00   0.80 0.75    uniform     True                       True
R1_0258    0.989583      21.506693 234.122396          0.000000      0.50   0.95 0.50    uniform    False                       True

## Adapted published component, same streams/query randomness

                  case             kind  delay  alarm_rate  post_power  harm_to_alarm     labels
            00_null_d5             null      5    0.000000    0.000000       0.000000 234.812500
        01_nuisance_d5         nuisance      5    0.000000    0.000000       0.000000 234.640625
          02_abrupt_d5           abrupt      5    1.000000    1.000000      42.210938 232.750000
           03_small_d5            small      5    0.968750    0.968750      44.665625 234.671875
            04_late_d5             late      5    0.656250    0.656250      51.792187 233.187500
       05_recurring_d5        recurring      5    0.984375    0.968750      40.327500 235.390625
06_guidance_failure_d5 guidance_failure      5    1.000000    0.984375      41.012813 235.093750
         07_abrupt_d24           abrupt     24    1.000000    1.000000      53.961563 233.640625

## Common weaknesses and next test

Late onset and small changes are the weakest cells. Allocation changes consume different numbers of labels despite the same hard cap; label/cost efficiency must therefore be compared on a frontier, not raw alarm power alone. A low propensity floor enlarges the safe betting range and reduces attainable bets. Restart mixtures trade early capital for later recovery. Auxiliary-guidance performance must be compared with its matched cost parent across all cases, including broken guidance.

324 intermediate-guidance configurations were compared to their matched cost-only parents. Development mean harm deltas range from -4.709193 to 7.008359; selection uncertainty and repeated testing prohibit a novelty conclusion.

Next: complete faithful PR/PPRM and active query baseline audits; register a bottleneck-targeted second round addressing budget pacing and guidance reliability, with equal-label frontiers. Add realistic calibration and dependence/delay stress. Verify on untouched synthetic seeds and chronological real streams only after protocol freeze. The full user objective remains ACTIVE.
