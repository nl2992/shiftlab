# Fixed PPI block-e-process mixture weight screen

Development-only screen on 30 matched streams per scenario, n=6400, B=20, four labels per block, reliance cap 0.1, and a nominal 20% label-dollar budget. Each fixed weight mixes the CM-EB block process and the predictable positive betting process. No weight is selected for confirmatory evaluation from these data.

|Scenario|Method|Streams|Detections|False escalations|
|---|---|---:|---:|---:|
|boundary_local_harm|CM-EB block PPI|30|0/30|0/30|
|boundary_local_harm|Eventwise frozen PPI|30|24/30|0/30|
|boundary_local_harm|Eventwise updating PPI|30|26/30|0/30|
|boundary_local_harm|PPI fixed mixture w=0.1|30|17/30|0/30|
|boundary_local_harm|PPI fixed mixture w=0.25|30|14/30|0/30|
|boundary_local_harm|PPI fixed mixture w=0.5|30|9/30|0/30|
|boundary_local_harm|PPI fixed mixture w=0.75|30|0/30|0/30|
|boundary_local_harm|PPI fixed mixture w=0.9|30|0/30|0/30|
|harmful_adaptation|CM-EB block PPI|30|0/30|0/30|
|harmful_adaptation|Eventwise frozen PPI|30|29/30|0/30|
|harmful_adaptation|Eventwise updating PPI|30|29/30|0/30|
|harmful_adaptation|PPI fixed mixture w=0.1|30|18/30|0/30|
|harmful_adaptation|PPI fixed mixture w=0.25|30|13/30|0/30|
|harmful_adaptation|PPI fixed mixture w=0.5|30|10/30|0/30|
|harmful_adaptation|PPI fixed mixture w=0.75|30|1/30|0/30|
|harmful_adaptation|PPI fixed mixture w=0.9|30|0/30|0/30|
|recurring_regimes|CM-EB block PPI|30|0/30|0/30|
|recurring_regimes|Eventwise frozen PPI|30|24/30|0/30|
|recurring_regimes|Eventwise updating PPI|30|24/30|0/30|
|recurring_regimes|PPI fixed mixture w=0.1|30|17/30|0/30|
|recurring_regimes|PPI fixed mixture w=0.25|30|14/30|0/30|
|recurring_regimes|PPI fixed mixture w=0.5|30|10/30|0/30|
|recurring_regimes|PPI fixed mixture w=0.75|30|0/30|0/30|
|recurring_regimes|PPI fixed mixture w=0.9|30|0/30|0/30|
|stationary|CM-EB block PPI|30|0/30|0/30|
|stationary|PPI fixed mixture w=0.1|30|0/30|0/30|
|stationary|PPI fixed mixture w=0.25|30|0/30|0/30|
|stationary|PPI fixed mixture w=0.5|30|0/30|0/30|
|stationary|PPI fixed mixture w=0.75|30|0/30|0/30|
|stationary|PPI fixed mixture w=0.9|30|0/30|0/30|

The best-performing tested weight is exploratory because the same development streams were used for the weight grid. A fresh seed block and null calibration are required before reporting a selected weight's power or error rate.
