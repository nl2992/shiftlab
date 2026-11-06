# Failure Atlas v2: real-data validation

Seed base 2026110398, 10 policy seeds per episode, QSG v1, strong re-ports included. Episode-level paired bootstrap (seeds averaged within episode). Powered: >= 8 episodes. The nine cached streams were exposed to earlier ShiftLab work (B3/B3+) but not to the development of this repair.

## Repaired minus host (episode-level)

| host -> repaired | openml_ldpa (K=32) | airlines (K=50) | criteo (K=50) | rialto (K=16) | bank (K=8) | spam (K=1) | uci_occupancy (K=4) | weather (K=3) | elec2 (K=4) |
|---|---|---|---|---|---|---|---|---|---|
| gated_deployment -> gated_deployment+QCE+front | -80.9 [-107.1,-56.5]* | -1.3 [-4.4,+2.3] | -0.0 [-0.4,+0.3] | -3.3 [-5.0,-1.6]* | -4.0 [-15.3,+2.5] | -138.4 | -66.2 [-203.7,+5.1] | -26.0 [-46.5,+0.0] | +2.0 [-1.8,+6.3] |
| discern_style -> discern_style+QCE+front | -188.8 [-227.3,-151.4]* | -5.0 [-11.0,+0.4] | -1.3 [-2.9,-0.1]* | -122.9 [-141.4,-103.6]* | -4.0 [-15.4,+2.2] | -296.4 | -79.0 [-230.9,-0.6]* | -50.2 [-83.4,+0.0] | +0.0 [-8.7,+8.5] |
| SMCS+retain-incumbent -> SMCS+QCE+front | -6.4 [-10.3,-2.6]* | +0.9 [-0.4,+2.8] | +1.5 [+0.5,+2.7]! | -1.1 [-1.9,-0.3]* | -4.6 [-13.9,+0.0] | -12.5 | -13.4 [-36.0,+0.0] | -2.0 [-9.3,+4.0] | -5.6 [-15.1,-0.1]* |
| xu_acquisition_only -> xu_acquisition_only+QCE+front | -16.7 [-24.5,-8.9]* | +0.8 [-0.5,+2.5] | +0.5 [+0.1,+1.1]! | -0.4 [-1.0,+0.1] | +0.4 [+0.1,+0.8]! | -19.0 | -18.2 [-57.9,+2.9] | -6.1 [-10.0,-1.6]* | +0.2 [-0.0,+0.7] |
| gated_adaptive_range -> gated_adaptive_range+front | -22.2 [-30.3,-14.4]* | +0.2 [-2.3,+3.5] | +0.0 [-0.5,+0.5] | -4.5 [-6.4,-2.7]* | -3.7 [-16.2,+3.4] | -42.8 | -25.0 [-75.6,+0.6] | -14.5 [-24.0,+0.0] | +1.4 [+0.0,+3.7]! |
| discern_design_floor -> discern_design_floor+front | -4.5 [-8.9,-0.4]* | +1.5 [+0.9,+2.2]! | +0.1 [+0.1,+0.1]! | -0.5 [-1.6,+0.2] | +3.5 [+1.8,+5.1]! | -4.9 | -2.1 [-7.0,+0.6] | -2.4 [-4.6,+0.0] | +0.3 [+0.0,+0.6]! |

## QSG and best repaired host vs the strongest published certified method

Strongest published = lowest mean net among gated_deployment, gated_adaptive_range, discern_style, discern_design_floor, xu_acquisition_only, SMCS+retain-incumbent on these episodes (selected on the same data, which favours the comparator).

| dataset | K | strongest published | QSG - published | best repaired | repaired - published | best uncertified | never |
|---|---|---|---|---|---|---|---|
| openml_ldpa | 32 | SMCS+retain-incumbent (464.3) | -15.7 [-37.5,-0.6]* | SMCS+QCE+front (457.9) | -6.4 [-10.3,-2.6]* | model_picker_adapter (430.5) | 663.0 |
| airlines | 50 | gated_adaptive_range (781.0) | +0.5 [-2.0,+2.9] | discern_style+QCE+front (781.0) | +0.1 [-2.5,+3.5] | qiu_delayed_movement (788.0) | 776.8 |
| criteo | 50 | SMCS+retain-incumbent (697.3) | +0.7 [-0.1,+1.6] | SMCS+QCE+front (698.8) | +1.5 [+0.5,+2.7]! | ryabchenko_capacity (687.1) | 693.9 |
| rialto | 16 | SMCS+retain-incumbent (89.8) | -3.1 [-3.9,-2.1]* | discern_style+QCE+front (87.1) | -2.7 [-4.0,-1.3]* | online_llm_picker (73.1) | 202.1 |
| bank | 8 | discern_design_floor (423.6) | -0.8 [-13.0,+6.7] | discern_style+QCE+front (420.2) | -3.4 [-14.4,+2.8] | model_selector_causal (425.4) | 419.4 |
| spam | 1 | SMCS+retain-incumbent (243.5) | -25.5 | SMCS+QCE+front (231.0) | -12.5 | online_llm_picker (205.0) | 849.0 |
| uci_occupancy | 4 | SMCS+retain-incumbent (151.0) | -17.9 [-37.5,+0.3] | discern_style+QCE+front (135.6) | -15.4 [-37.1,-1.8]* | model_picker_adapter (131.2) | 481.2 |
| weather | 3 | SMCS+retain-incumbent (466.4) | -3.0 [-8.3,+0.2] | discern_style+QCE+front (462.7) | -3.7 [-8.7,+0.0] | model_selector_causal (440.3) | 504.0 |
| elec2 | 4 | SMCS+retain-incumbent (392.3) | -0.9 [-12.8,+13.1] | SMCS+QCE+front (386.7) | -5.6 [-15.1,-0.1]* | ryabchenko_capacity (392.0) | 389.5 |

## Mean net cost per dataset (episode-averaged)

| policy                        |   airlines |   bank |   criteo |   elec2 |   openml_ldpa |   rialto |   spam |   uci_occupancy |   weather |
|:------------------------------|-----------:|-------:|---------:|--------:|--------------:|---------:|-------:|----------------:|----------:|
| CONTROL_never_switch          |      776.8 |  419.4 |    693.9 |   389.5 |         663   |    202.1 |  849   |           481.2 |     504   |
| P7s_settled                   |      780.4 |  427.5 |    699   |   396.8 |         480.1 |     98.3 |  247.4 |           178.1 |     473.6 |
| QSG                           |      781.4 |  422.8 |    698   |   391.4 |         448.5 |     86.7 |  218   |           133.1 |     463.4 |
| QSG-env8                      |      785.5 |  428.1 |    699.2 |   400   |         495.2 |     88.6 |  348   |           161   |     481.6 |
| QSG-env95                     |      786.4 |  428.1 |    699.7 |   395.5 |         640.1 |    109.7 |  859   |           486.7 |     485.9 |
| QSG-no_front                  |      781.3 |  428.1 |    697.6 |   389.6 |         458.6 |     88.7 |  248.7 |           146.4 |     467.6 |
| QSG-no_monitor                |      778.8 |  419.9 |    697.2 |   395.3 |         455.8 |     79.6 |  209.2 |           133.8 |     457.7 |
| QSG-no_rollback               |      782.1 |  422.8 |    698   |   399.3 |         442.2 |     86.7 |  218   |           133.1 |     463.4 |
| QSG-no_started                |      781.6 |  422.9 |    698.1 |   400.8 |         454.6 |     85.9 |  218   |           136.8 |     462.7 |
| QSG-r25                       |      781.4 |  422.8 |    698   |   391.4 |         450.6 |     86.7 |  218   |           133.1 |     463.4 |
| SMCS+QCE                      |      781.7 |  428.1 |    698.5 |   392.2 |         466.9 |     91   |  249.6 |           153.4 |     471.1 |
| SMCS+QCE+front                |      782.4 |  423   |    698.8 |   386.7 |         457.9 |     88.7 |  231   |           137.6 |     464.4 |
| SMCS+front_only               |      781.9 |  423.1 |    696.3 |   403.6 |         459   |     87.6 |  231   |           137.3 |     461   |
| SMCS+retain-incumbent         |      781.5 |  427.6 |    697.3 |   392.3 |         464.3 |     89.8 |  243.5 |           151   |     466.4 |
| cams_adapter                  |      792.6 |  438.4 |    694.4 |   398.4 |         434.2 |     74.9 |  211.2 |           133.4 |     449   |
| discern+front_only            |      786.5 |  428.1 |    700.5 |   395.5 |         672.9 |    210.3 |  859   |           486.7 |     513.2 |
| discern_design_floor          |      782.7 |  423.6 |    700.4 |   395.2 |         496.7 |    135.4 |  287.2 |           151.6 |     498.4 |
| discern_design_floor+front    |      784.2 |  427.1 |    700.5 |   395.5 |         492.3 |    134.8 |  282.3 |           149.4 |     496   |
| discern_style                 |      786   |  424.2 |    700.4 |   395.2 |         649.1 |    210   |  530   |           214.6 |     512.9 |
| discern_style+QCE             |      779.4 |  423.3 |    698.6 |   393.8 |         475.2 |     89.4 |  261   |           163.7 |     472   |
| discern_style+QCE+front       |      781   |  420.2 |    699.1 |   395.2 |         460.3 |     87.1 |  233.6 |           135.6 |     462.7 |
| economic_replacement          |      788   |  427.6 |    683.5 |   391.3 |         448.6 |     94.5 |  243   |           160.9 |     449   |
| gated+front_only              |      781.1 |  420.4 |    699.1 |   396.6 |         461.1 |     90.9 |  233.6 |           137.1 |     468.8 |
| gated_adaptive_range          |      781   |  424.1 |    699.1 |   395.3 |         483.3 |     95.4 |  276.4 |           162.1 |     483.3 |
| gated_adaptive_range+front    |      781.1 |  420.4 |    699.1 |   396.6 |         461.1 |     90.9 |  233.6 |           137.1 |     468.8 |
| gated_deployment              |      782.4 |  424.4 |    699   |   394.4 |         539.4 |     94.9 |  372   |           204.8 |     495.9 |
| gated_deployment+QCE          |      779.9 |  424   |    699   |   395.6 |         481.3 |     94.6 |  273.5 |           170.6 |     476.4 |
| gated_deployment+QCE+front    |      781.2 |  420.4 |    699   |   396.4 |         458.6 |     91.7 |  233.6 |           138.6 |     469.9 |
| gong_zhang_paid_obs           |      790.1 |  435.3 |    687.7 |   401.3 |         442.7 |     81.1 |  221   |           139.5 |     442.9 |
| model_picker_adapter          |      789.3 |  435   |    691.1 |   396.9 |         430.5 |     74.3 |  205.3 |           131.2 |     445.3 |
| model_selector_causal         |      791.1 |  425.4 |    688.1 |   410.5 |         435   |     77.9 |  210   |           135.8 |     440.3 |
| online_llm_picker             |      795.2 |  437.1 |    695.8 |   401   |         432.3 |     73.1 |  205   |           134.8 |     453.7 |
| qiu_delayed_movement          |      788   |  439.5 |    690   |   404   |         450.9 |     84.8 |  222.5 |           145.4 |     445.7 |
| ryabchenko_capacity           |      809   |  532.1 |    687.1 |   392   |         475.9 |    102.1 |  266.8 |           151.8 |     460.1 |
| variance_min_ipw              |      800.6 |  435.5 |    693.7 |   409.3 |         434.1 |     79.3 |  221.7 |           141.3 |     443.3 |
| xu+front_only                 |      782   |  428.1 |    698.8 |   395   |         472.1 |     99   |  241   |           163   |     462.9 |
| xu_acquisition_only           |      781.2 |  427.7 |    698.3 |   394.8 |         488.8 |     99.4 |  260   |           181.2 |     469.1 |
| xu_acquisition_only+QCE       |      781.4 |  427.7 |    698.5 |   394.4 |         496.5 |     99.3 |  280.1 |           190   |     467.5 |
| xu_acquisition_only+QCE+front |      782   |  428.1 |    698.8 |   395   |         472.1 |     99   |  241   |           163   |     462.9 |
