# Delayed history-predictable propensity and latency grid

- Streams per scenario/configuration/arm: 30
- Total stream-arm rows: 4320
- Horizon: 2400; label cap: 480; root seed: 27404027
- Stream generation device: cuda; sequential monitor replay: CPU NumPy.
- All cells are development diagnostics. The small null cells do not calibrate the false-escalation rate.
- The registered iid DGP and fixed outcome-independent delays support only the assumptions in `docs/delayed_history_predictable_bound_protocol.md`.
- No research figure was generated because PaperBanana is unavailable in the active environment.

## Full grid summary

| scenario                       |   feedback_delay |   q_min | bound_mode   |   streams |   false_escalations |   detection_rate |   onset_reach_rate |   mean_labels |   mean_processed |   mean_event_delay |   mean_wall_delay |
|:-------------------------------|-----------------:|--------:|:-------------|----------:|--------------------:|-----------------:|-------------------:|--------------:|-----------------:|-------------------:|------------------:|
| high_cost_local_harm_d0.04     |                1 |  0.0500 | fixed        |        30 |                   0 |           0.0000 |             1.0000 |      276.8667 |        2400.0000 |           nan      |          nan      |
| high_cost_local_harm_d0.04     |                1 |  0.0500 | predictable  |        30 |                   2 |           0.0000 |             0.9333 |      144.4667 |        2248.9667 |           nan      |          nan      |
| high_cost_local_harm_d0.04     |                1 |  0.1000 | fixed        |        30 |                   0 |           0.0000 |             1.0000 |      347.5000 |        2381.5667 |           nan      |          nan      |
| high_cost_local_harm_d0.04     |                1 |  0.1000 | predictable  |        30 |                   2 |           0.0000 |             0.9333 |      257.1667 |        2249.4333 |           nan      |          nan      |
| high_cost_local_harm_d0.04     |                1 |  0.1500 | fixed        |        30 |                   0 |           0.0000 |             1.0000 |      425.5333 |        2300.4333 |           nan      |          nan      |
| high_cost_local_harm_d0.04     |                1 |  0.1500 | predictable  |        30 |                   2 |           0.0000 |             0.9333 |      362.0000 |        2248.7667 |           nan      |          nan      |
| high_cost_local_harm_d0.04     |                3 |  0.0500 | fixed        |        30 |                   0 |           0.0000 |             1.0000 |      281.0667 |        2400.0000 |           nan      |          nan      |
| high_cost_local_harm_d0.04     |                3 |  0.0500 | predictable  |        30 |                   2 |           0.0000 |             0.9333 |      155.6667 |        2249.5333 |           nan      |          nan      |
| high_cost_local_harm_d0.04     |                3 |  0.1000 | fixed        |        30 |                   0 |           0.0000 |             1.0000 |      346.0333 |        2381.1667 |           nan      |          nan      |
| high_cost_local_harm_d0.04     |                3 |  0.1000 | predictable  |        30 |                   2 |           0.0000 |             0.9333 |      255.2000 |        2249.6333 |           nan      |          nan      |
| high_cost_local_harm_d0.04     |                3 |  0.1500 | fixed        |        30 |                   0 |           0.0000 |             1.0000 |      417.5667 |        2280.2333 |           nan      |          nan      |
| high_cost_local_harm_d0.04     |                3 |  0.1500 | predictable  |        30 |                   2 |           0.0000 |             0.9333 |      362.3667 |        2249.0667 |           nan      |          nan      |
| high_cost_local_harm_d0.04     |               12 |  0.0500 | fixed        |        30 |                   0 |           0.0000 |             1.0000 |      305.4000 |        2400.0000 |           nan      |          nan      |
| high_cost_local_harm_d0.04     |               12 |  0.0500 | predictable  |        30 |                   2 |           0.0000 |             0.9333 |      153.0667 |        2253.0333 |           nan      |          nan      |
| high_cost_local_harm_d0.04     |               12 |  0.1000 | fixed        |        30 |                   0 |           0.0000 |             1.0000 |      351.1667 |        2383.8000 |           nan      |          nan      |
| high_cost_local_harm_d0.04     |               12 |  0.1000 | predictable  |        30 |                   2 |           0.0000 |             0.9333 |      271.2000 |        2250.6667 |           nan      |          nan      |
| high_cost_local_harm_d0.04     |               12 |  0.1500 | fixed        |        30 |                   0 |           0.0000 |             1.0000 |      425.3333 |        2286.7333 |           nan      |          nan      |
| high_cost_local_harm_d0.04     |               12 |  0.1500 | predictable  |        30 |                   2 |           0.0000 |             0.9333 |      376.1333 |        2230.0333 |           nan      |          nan      |
| high_cost_local_harm_d0.04     |               24 |  0.0500 | fixed        |        30 |                   0 |           0.0000 |             1.0000 |      279.7667 |        2400.0000 |           nan      |          nan      |
| high_cost_local_harm_d0.04     |               24 |  0.0500 | predictable  |        30 |                   3 |           0.0000 |             0.9000 |      159.4333 |        2182.3000 |           nan      |          nan      |
| high_cost_local_harm_d0.04     |               24 |  0.1000 | fixed        |        30 |                   0 |           0.0000 |             1.0000 |      360.2667 |        2377.7000 |           nan      |          nan      |
| high_cost_local_harm_d0.04     |               24 |  0.1000 | predictable  |        30 |                   2 |           0.0000 |             0.9333 |      272.9333 |        2258.6333 |           nan      |          nan      |
| high_cost_local_harm_d0.04     |               24 |  0.1500 | fixed        |        30 |                   0 |           0.0000 |             1.0000 |      422.2333 |        2288.2667 |           nan      |          nan      |
| high_cost_local_harm_d0.04     |               24 |  0.1500 | predictable  |        30 |                   2 |           0.0000 |             0.9333 |      375.5333 |        2229.7000 |           nan      |          nan      |
| high_cost_local_harm_d0.20     |                1 |  0.0500 | fixed        |        30 |                   0 |           0.0000 |             1.0000 |      338.9333 |        2400.0000 |           nan      |          nan      |
| high_cost_local_harm_d0.20     |                1 |  0.0500 | predictable  |        30 |                   1 |           0.0000 |             0.9667 |      191.0667 |        2348.6000 |           nan      |          nan      |
| high_cost_local_harm_d0.20     |                1 |  0.1000 | fixed        |        30 |                   1 |           0.0333 |             0.9667 |      370.8333 |        2308.9000 |           919.0000 |          920.0000 |
| high_cost_local_harm_d0.20     |                1 |  0.1000 | predictable  |        30 |                   0 |           0.0000 |             1.0000 |      313.1000 |        2390.1667 |           nan      |          nan      |
| high_cost_local_harm_d0.20     |                1 |  0.1500 | fixed        |        30 |                   0 |           0.0333 |             1.0000 |      436.0667 |        2256.3333 |           541.0000 |          542.0000 |
| high_cost_local_harm_d0.20     |                1 |  0.1500 | predictable  |        30 |                   0 |           0.0000 |             1.0000 |      409.9667 |        2361.1333 |           nan      |          nan      |
| high_cost_local_harm_d0.20     |                3 |  0.0500 | fixed        |        30 |                   0 |           0.0000 |             1.0000 |      345.1667 |        2400.0000 |           nan      |          nan      |
| high_cost_local_harm_d0.20     |                3 |  0.0500 | predictable  |        30 |                   1 |           0.0000 |             0.9667 |      202.0000 |        2347.9667 |           nan      |          nan      |
| high_cost_local_harm_d0.20     |                3 |  0.1000 | fixed        |        30 |                   1 |           0.0333 |             0.9667 |      371.8667 |        2315.1667 |           919.0000 |          922.0000 |
| high_cost_local_harm_d0.20     |                3 |  0.1000 | predictable  |        30 |                   1 |           0.0333 |             0.9667 |      311.0000 |        2329.9667 |           712.0000 |          715.0000 |
| high_cost_local_harm_d0.20     |                3 |  0.1500 | fixed        |        30 |                   1 |           0.0000 |             0.9667 |      428.6667 |        2239.4000 |           nan      |          nan      |
| high_cost_local_harm_d0.20     |                3 |  0.1500 | predictable  |        30 |                   0 |           0.0000 |             1.0000 |      410.0333 |        2355.9000 |           nan      |          nan      |
| high_cost_local_harm_d0.20     |               12 |  0.0500 | fixed        |        30 |                   0 |           0.0000 |             1.0000 |      326.2667 |        2400.0000 |           nan      |          nan      |
| high_cost_local_harm_d0.20     |               12 |  0.0500 | predictable  |        30 |                   0 |           0.0333 |             1.0000 |      200.7333 |        2375.2667 |           446.0000 |          458.0000 |
| high_cost_local_harm_d0.20     |               12 |  0.1000 | fixed        |        30 |                   0 |           0.1000 |             1.0000 |      382.2000 |        2333.9000 |           800.3333 |          812.3333 |
| high_cost_local_harm_d0.20     |               12 |  0.1000 | predictable  |        30 |                   0 |           0.0333 |             1.0000 |      319.9333 |        2367.1333 |           681.0000 |          693.0000 |
| high_cost_local_harm_d0.20     |               12 |  0.1500 | fixed        |        30 |                   0 |           0.0667 |             1.0000 |      439.0000 |        2279.9333 |           548.0000 |          560.0000 |
| high_cost_local_harm_d0.20     |               12 |  0.1500 | predictable  |        30 |                   0 |           0.0000 |             1.0000 |      409.7667 |        2366.7000 |           nan      |          nan      |
| high_cost_local_harm_d0.20     |               24 |  0.0500 | fixed        |        30 |                   0 |           0.0000 |             1.0000 |      327.2000 |        2400.0000 |           nan      |          nan      |
| high_cost_local_harm_d0.20     |               24 |  0.0500 | predictable  |        30 |                   1 |           0.0333 |             0.9667 |      220.2000 |        2343.7333 |           895.0000 |          919.0000 |
| high_cost_local_harm_d0.20     |               24 |  0.1000 | fixed        |        30 |                   0 |           0.0333 |             1.0000 |      380.3333 |        2345.4000 |           105.0000 |          129.0000 |
| high_cost_local_harm_d0.20     |               24 |  0.1000 | predictable  |        30 |                   0 |           0.0333 |             1.0000 |      326.2333 |        2373.7667 |           670.0000 |          694.0000 |
| high_cost_local_harm_d0.20     |               24 |  0.1500 | fixed        |        30 |                   0 |           0.0667 |             1.0000 |      439.9333 |        2263.4000 |           493.5000 |          517.5000 |
| high_cost_local_harm_d0.20     |               24 |  0.1500 | predictable  |        30 |                   0 |           0.0000 |             1.0000 |      417.8667 |        2333.3667 |           nan      |          nan      |
| high_cost_local_harm_d0.40     |                1 |  0.0500 | fixed        |        30 |                   0 |           0.0333 |             1.0000 |      333.7333 |        2397.0667 |          1111.0000 |         1112.0000 |
| high_cost_local_harm_d0.40     |                1 |  0.0500 | predictable  |        30 |                   1 |           0.0667 |             0.9667 |      198.8000 |        2304.0667 |           910.5000 |          911.5000 |
| high_cost_local_harm_d0.40     |                1 |  0.1000 | fixed        |        30 |                   0 |           0.1000 |             1.0000 |      390.5667 |        2328.4333 |           760.3333 |          761.3333 |
| high_cost_local_harm_d0.40     |                1 |  0.1000 | predictable  |        30 |                   1 |           0.0667 |             0.9667 |      310.0667 |        2294.0667 |           858.5000 |          859.5000 |
| high_cost_local_harm_d0.40     |                1 |  0.1500 | fixed        |        30 |                   0 |           0.0333 |             1.0000 |      439.5333 |        2225.9333 |            34.0000 |           35.0000 |
| high_cost_local_harm_d0.40     |                1 |  0.1500 | predictable  |        30 |                   1 |           0.1000 |             0.9667 |      401.0333 |        2272.3000 |           983.0000 |          984.0000 |
| high_cost_local_harm_d0.40     |                3 |  0.0500 | fixed        |        30 |                   0 |           0.0333 |             1.0000 |      336.2000 |        2396.9667 |          1106.0000 |         1109.0000 |
| high_cost_local_harm_d0.40     |                3 |  0.0500 | predictable  |        30 |                   1 |           0.0667 |             0.9667 |      195.0667 |        2306.2000 |           941.0000 |          944.0000 |
| high_cost_local_harm_d0.40     |                3 |  0.1000 | fixed        |        30 |                   0 |           0.0667 |             1.0000 |      382.3000 |        2335.6333 |           565.5000 |          568.5000 |
| high_cost_local_harm_d0.40     |                3 |  0.1000 | predictable  |        30 |                   1 |           0.0667 |             0.9667 |      307.7667 |        2292.9000 |           745.5000 |          748.5000 |
| high_cost_local_harm_d0.40     |                3 |  0.1500 | fixed        |        30 |                   0 |           0.1000 |             1.0000 |      441.2333 |        2189.6333 |           534.3333 |          537.3333 |
| high_cost_local_harm_d0.40     |                3 |  0.1500 | predictable  |        30 |                   1 |           0.1333 |             0.9667 |      400.9000 |        2266.3667 |           941.7500 |          944.7500 |
| high_cost_local_harm_d0.40     |               12 |  0.0500 | fixed        |        30 |                   0 |           0.0000 |             1.0000 |      347.2000 |        2400.0000 |           nan      |          nan      |
| high_cost_local_harm_d0.40     |               12 |  0.0500 | predictable  |        30 |                   2 |           0.1000 |             0.9333 |      201.1667 |        2243.9667 |           935.0000 |          947.0000 |
| high_cost_local_harm_d0.40     |               12 |  0.1000 | fixed        |        30 |                   0 |           0.0000 |             1.0000 |      381.2667 |        2366.3333 |           nan      |          nan      |
| high_cost_local_harm_d0.40     |               12 |  0.1000 | predictable  |        30 |                   1 |           0.0667 |             0.9667 |      304.0333 |        2287.6667 |           748.0000 |          760.0000 |
| high_cost_local_harm_d0.40     |               12 |  0.1500 | fixed        |        30 |                   0 |           0.0667 |             1.0000 |      449.7667 |        2212.0000 |           785.0000 |          797.0000 |
| high_cost_local_harm_d0.40     |               12 |  0.1500 | predictable  |        30 |                   2 |           0.0667 |             0.9333 |      398.6000 |        2215.2000 |           828.0000 |          840.0000 |
| high_cost_local_harm_d0.40     |               24 |  0.0500 | fixed        |        30 |                   0 |           0.0000 |             1.0000 |      334.8333 |        2400.0000 |           nan      |          nan      |
| high_cost_local_harm_d0.40     |               24 |  0.0500 | predictable  |        30 |                   1 |           0.0333 |             0.9667 |      191.2000 |        2317.6667 |           989.0000 |         1013.0000 |
| high_cost_local_harm_d0.40     |               24 |  0.1000 | fixed        |        30 |                   0 |           0.0333 |             1.0000 |      391.5000 |        2365.4000 |           841.0000 |          865.0000 |
| high_cost_local_harm_d0.40     |               24 |  0.1000 | predictable  |        30 |                   1 |           0.0667 |             0.9667 |      305.8333 |        2297.3333 |           778.0000 |          802.0000 |
| high_cost_local_harm_d0.40     |               24 |  0.1500 | fixed        |        30 |                   0 |           0.0667 |             1.0000 |      446.3333 |        2225.0000 |           889.0000 |          913.0000 |
| high_cost_local_harm_d0.40     |               24 |  0.1500 | predictable  |        30 |                   1 |           0.0667 |             0.9667 |      408.6000 |        2288.8333 |          1009.5000 |         1033.5000 |
| high_cost_local_harm_d0.60     |                1 |  0.0500 | fixed        |        30 |                   0 |           0.1000 |             1.0000 |      372.1333 |        2356.3000 |           762.0000 |          763.0000 |
| high_cost_local_harm_d0.60     |                1 |  0.0500 | predictable  |        30 |                   0 |           0.3667 |             1.0000 |      218.0000 |        2217.4667 |           701.1818 |          702.1818 |
| high_cost_local_harm_d0.60     |                1 |  0.1000 | fixed        |        30 |                   0 |           0.3000 |             1.0000 |      392.1333 |        2237.0333 |           705.8889 |          706.8889 |
| high_cost_local_harm_d0.60     |                1 |  0.1000 | predictable  |        30 |                   1 |           0.3667 |             0.9667 |      311.7000 |        2125.1000 |           656.5455 |          657.5455 |
| high_cost_local_harm_d0.60     |                1 |  0.1500 | fixed        |        30 |                   0 |           0.2667 |             1.0000 |      445.9333 |        2125.6000 |           714.1250 |          715.1250 |
| high_cost_local_harm_d0.60     |                1 |  0.1500 | predictable  |        30 |                   1 |           0.3000 |             0.9667 |      399.7333 |        2136.0000 |           673.3333 |          674.3333 |
| high_cost_local_harm_d0.60     |                3 |  0.0500 | fixed        |        30 |                   0 |           0.1667 |             1.0000 |      373.1667 |        2346.8667 |           878.2000 |          881.2000 |
| high_cost_local_harm_d0.60     |                3 |  0.0500 | predictable  |        30 |                   0 |           0.3333 |             1.0000 |      208.8333 |        2209.9667 |           626.9000 |          629.9000 |
| high_cost_local_harm_d0.60     |                3 |  0.1000 | fixed        |        30 |                   0 |           0.3000 |             1.0000 |      392.9333 |        2222.9333 |           671.0000 |          674.0000 |
| high_cost_local_harm_d0.60     |                3 |  0.1000 | predictable  |        30 |                   0 |           0.3000 |             1.0000 |      325.9333 |        2238.4667 |           658.7778 |          661.5556 |
| high_cost_local_harm_d0.60     |                3 |  0.1500 | fixed        |        30 |                   0 |           0.2667 |             1.0000 |      442.4667 |        2129.7000 |           629.2500 |          632.2500 |
| high_cost_local_harm_d0.60     |                3 |  0.1500 | predictable  |        30 |                   1 |           0.3000 |             0.9667 |      400.7333 |        2140.7667 |           655.8889 |          658.8889 |
| high_cost_local_harm_d0.60     |               12 |  0.0500 | fixed        |        30 |                   0 |           0.1333 |             1.0000 |      376.5000 |        2367.4667 |           944.0000 |          956.0000 |
| high_cost_local_harm_d0.60     |               12 |  0.0500 | predictable  |        30 |                   0 |           0.3000 |             1.0000 |      223.5667 |        2242.3667 |           662.6667 |          674.5556 |
| high_cost_local_harm_d0.60     |               12 |  0.1000 | fixed        |        30 |                   0 |           0.3000 |             1.0000 |      390.8000 |        2221.5667 |           658.8889 |          670.8889 |
| high_cost_local_harm_d0.60     |               12 |  0.1000 | predictable  |        30 |                   1 |           0.2667 |             0.9667 |      323.1000 |        2211.5667 |           655.1250 |          667.1250 |
| high_cost_local_harm_d0.60     |               12 |  0.1500 | fixed        |        30 |                   0 |           0.2000 |             1.0000 |      448.0000 |        2152.0667 |           662.8333 |          674.8333 |
| high_cost_local_harm_d0.60     |               12 |  0.1500 | predictable  |        30 |                   0 |           0.3000 |             1.0000 |      413.3667 |        2197.3333 |           647.8889 |          659.8889 |
| high_cost_local_harm_d0.60     |               24 |  0.0500 | fixed        |        30 |                   0 |           0.1667 |             1.0000 |      373.0000 |        2364.2333 |           961.4000 |          985.4000 |
| high_cost_local_harm_d0.60     |               24 |  0.0500 | predictable  |        30 |                   0 |           0.2667 |             1.0000 |      233.4000 |        2290.9333 |           767.1250 |          791.0000 |
| high_cost_local_harm_d0.60     |               24 |  0.1000 | fixed        |        30 |                   0 |           0.2667 |             1.0000 |      385.7667 |        2234.8000 |           632.1250 |          655.5000 |
| high_cost_local_harm_d0.60     |               24 |  0.1000 | predictable  |        30 |                   0 |           0.3000 |             1.0000 |      326.2000 |        2229.7333 |           610.1111 |          634.1111 |
| high_cost_local_harm_d0.60     |               24 |  0.1500 | fixed        |        30 |                   1 |           0.2667 |             0.9667 |      442.4000 |        2139.6667 |           727.1250 |          751.1250 |
| high_cost_local_harm_d0.60     |               24 |  0.1500 | predictable  |        30 |                   0 |           0.3333 |             1.0000 |      415.7000 |        2192.3333 |           704.3000 |          728.1000 |
| mixed_sign_exact_marginal_null |                1 |  0.0500 | fixed        |        30 |                   0 |           0.0000 |             0.0000 |      278.5333 |        2400.0000 |           nan      |          nan      |
| mixed_sign_exact_marginal_null |                1 |  0.0500 | predictable  |        30 |                   1 |           0.0000 |             0.0000 |      151.4667 |        2334.6667 |           nan      |          nan      |
| mixed_sign_exact_marginal_null |                1 |  0.1000 | fixed        |        30 |                   0 |           0.0000 |             0.0000 |      352.3333 |        2355.3000 |           nan      |          nan      |
| mixed_sign_exact_marginal_null |                1 |  0.1000 | predictable  |        30 |                   0 |           0.0000 |             0.0000 |      275.5000 |        2400.0000 |           nan      |          nan      |
| mixed_sign_exact_marginal_null |                1 |  0.1500 | fixed        |        30 |                   0 |           0.0000 |             0.0000 |      422.7667 |        2277.8667 |           nan      |          nan      |
| mixed_sign_exact_marginal_null |                1 |  0.1500 | predictable  |        30 |                   0 |           0.0000 |             0.0000 |      393.3333 |        2400.0000 |           nan      |          nan      |
| mixed_sign_exact_marginal_null |                3 |  0.0500 | fixed        |        30 |                   0 |           0.0000 |             0.0000 |      282.1333 |        2400.0000 |           nan      |          nan      |
| mixed_sign_exact_marginal_null |                3 |  0.0500 | predictable  |        30 |                   0 |           0.0000 |             0.0000 |      167.1667 |        2400.0000 |           nan      |          nan      |
| mixed_sign_exact_marginal_null |                3 |  0.1000 | fixed        |        30 |                   0 |           0.0000 |             0.0000 |      352.9333 |        2376.2667 |           nan      |          nan      |
| mixed_sign_exact_marginal_null |                3 |  0.1000 | predictable  |        30 |                   0 |           0.0000 |             0.0000 |      276.5667 |        2400.0000 |           nan      |          nan      |
| mixed_sign_exact_marginal_null |                3 |  0.1500 | fixed        |        30 |                   0 |           0.0000 |             0.0000 |      423.8667 |        2280.4667 |           nan      |          nan      |
| mixed_sign_exact_marginal_null |                3 |  0.1500 | predictable  |        30 |                   0 |           0.0000 |             0.0000 |      400.9000 |        2385.5333 |           nan      |          nan      |
| mixed_sign_exact_marginal_null |               12 |  0.0500 | fixed        |        30 |                   0 |           0.0000 |             0.0000 |      281.0000 |        2400.0000 |           nan      |          nan      |
| mixed_sign_exact_marginal_null |               12 |  0.0500 | predictable  |        30 |                   0 |           0.0000 |             0.0000 |      168.7667 |        2400.0000 |           nan      |          nan      |
| mixed_sign_exact_marginal_null |               12 |  0.1000 | fixed        |        30 |                   0 |           0.0000 |             0.0000 |      341.9667 |        2381.3000 |           nan      |          nan      |
| mixed_sign_exact_marginal_null |               12 |  0.1000 | predictable  |        30 |                   1 |           0.0000 |             0.0000 |      271.3667 |        2322.5667 |           nan      |          nan      |
| mixed_sign_exact_marginal_null |               12 |  0.1500 | fixed        |        30 |                   0 |           0.0000 |             0.0000 |      420.2000 |        2280.6000 |           nan      |          nan      |
| mixed_sign_exact_marginal_null |               12 |  0.1500 | predictable  |        30 |                   1 |           0.0000 |             0.0000 |      377.7333 |        2322.6667 |           nan      |          nan      |
| mixed_sign_exact_marginal_null |               24 |  0.0500 | fixed        |        30 |                   0 |           0.0000 |             0.0000 |      279.0000 |        2400.0000 |           nan      |          nan      |
| mixed_sign_exact_marginal_null |               24 |  0.0500 | predictable  |        30 |                   1 |           0.0000 |             0.0000 |      164.1000 |        2326.0667 |           nan      |          nan      |
| mixed_sign_exact_marginal_null |               24 |  0.1000 | fixed        |        30 |                   0 |           0.0000 |             0.0000 |      347.2000 |        2381.3000 |           nan      |          nan      |
| mixed_sign_exact_marginal_null |               24 |  0.1000 | predictable  |        30 |                   1 |           0.0000 |             0.0000 |      274.1000 |        2326.1000 |           nan      |          nan      |
| mixed_sign_exact_marginal_null |               24 |  0.1500 | fixed        |        30 |                   0 |           0.0000 |             0.0000 |      425.1000 |        2306.4000 |           nan      |          nan      |
| mixed_sign_exact_marginal_null |               24 |  0.1500 | predictable  |        30 |                   0 |           0.0000 |             0.0000 |      395.1667 |        2400.0000 |           nan      |          nan      |
| strict_negative_control        |                1 |  0.0500 | fixed        |        30 |                   0 |           0.0000 |             0.0000 |      299.2667 |        2400.0000 |           nan      |          nan      |
| strict_negative_control        |                1 |  0.0500 | predictable  |        30 |                   0 |           0.0000 |             0.0000 |      172.3000 |        2400.0000 |           nan      |          nan      |
| strict_negative_control        |                1 |  0.1000 | fixed        |        30 |                   0 |           0.0000 |             0.0000 |      352.9000 |        2377.6667 |           nan      |          nan      |
| strict_negative_control        |                1 |  0.1000 | predictable  |        30 |                   1 |           0.0000 |             0.0000 |      285.1000 |        2315.7333 |           nan      |          nan      |
| strict_negative_control        |                1 |  0.1500 | fixed        |        30 |                   0 |           0.0000 |             0.0000 |      431.4667 |        2306.5667 |           nan      |          nan      |
| strict_negative_control        |                1 |  0.1500 | predictable  |        30 |                   1 |           0.0000 |             0.0000 |      381.4667 |        2292.8667 |           nan      |          nan      |
| strict_negative_control        |                3 |  0.0500 | fixed        |        30 |                   0 |           0.0000 |             0.0000 |      307.1000 |        2400.0000 |           nan      |          nan      |
| strict_negative_control        |                3 |  0.0500 | predictable  |        30 |                   0 |           0.0000 |             0.0000 |      169.8000 |        2400.0000 |           nan      |          nan      |
| strict_negative_control        |                3 |  0.1000 | fixed        |        30 |                   0 |           0.0000 |             0.0000 |      346.9333 |        2383.5667 |           nan      |          nan      |
| strict_negative_control        |                3 |  0.1000 | predictable  |        30 |                   0 |           0.0000 |             0.0000 |      291.6000 |        2399.4333 |           nan      |          nan      |
| strict_negative_control        |                3 |  0.1500 | fixed        |        30 |                   0 |           0.0000 |             0.0000 |      432.4333 |        2307.1333 |           nan      |          nan      |
| strict_negative_control        |                3 |  0.1500 | predictable  |        30 |                   0 |           0.0000 |             0.0000 |      395.6000 |        2390.1000 |           nan      |          nan      |
| strict_negative_control        |               12 |  0.0500 | fixed        |        30 |                   0 |           0.0000 |             0.0000 |      304.4333 |        2400.0000 |           nan      |          nan      |
| strict_negative_control        |               12 |  0.0500 | predictable  |        30 |                   0 |           0.0000 |             0.0000 |      161.3667 |        2400.0000 |           nan      |          nan      |
| strict_negative_control        |               12 |  0.1000 | fixed        |        30 |                   0 |           0.0000 |             0.0000 |      369.3333 |        2378.5000 |           nan      |          nan      |
| strict_negative_control        |               12 |  0.1000 | predictable  |        30 |                   0 |           0.0000 |             0.0000 |      290.5000 |        2399.1333 |           nan      |          nan      |
| strict_negative_control        |               12 |  0.1500 | fixed        |        30 |                   0 |           0.0000 |             0.0000 |      442.0667 |        2302.4333 |           nan      |          nan      |
| strict_negative_control        |               12 |  0.1500 | predictable  |        30 |                   0 |           0.0000 |             0.0000 |      398.2333 |        2384.3000 |           nan      |          nan      |
| strict_negative_control        |               24 |  0.0500 | fixed        |        30 |                   0 |           0.0000 |             0.0000 |      296.7333 |        2400.0000 |           nan      |          nan      |
| strict_negative_control        |               24 |  0.0500 | predictable  |        30 |                   0 |           0.0000 |             0.0000 |      181.7333 |        2400.0000 |           nan      |          nan      |
| strict_negative_control        |               24 |  0.1000 | fixed        |        30 |                   0 |           0.0000 |             0.0000 |      368.4333 |        2384.5333 |           nan      |          nan      |
| strict_negative_control        |               24 |  0.1000 | predictable  |        30 |                   0 |           0.0000 |             0.0000 |      296.6333 |        2400.0000 |           nan      |          nan      |
| strict_negative_control        |               24 |  0.1500 | fixed        |        30 |                   0 |           0.0000 |             0.0000 |      443.4667 |        2307.1667 |           nan      |          nan      |
| strict_negative_control        |               24 |  0.1500 | predictable  |        30 |                   0 |           0.0000 |             0.0000 |      402.0000 |        2365.0000 |           nan      |          nan      |

## Paired harm differences

| scenario                   |   feedback_delay |   q_min | metric                                  |   predictable_minus_fixed_mean |
|:---------------------------|-----------------:|--------:|:----------------------------------------|-------------------------------:|
| high_cost_local_harm_d0.04 |                1 |  0.0500 | post_onset_detection                    |                         0.0000 |
| high_cost_local_harm_d0.04 |                1 |  0.0500 | labels_queried                          |                      -132.4000 |
| high_cost_local_harm_d0.04 |                1 |  0.0500 | evaluator_cumulative_expected_harm_cost |                        -3.2000 |
| high_cost_local_harm_d0.04 |                1 |  0.1000 | post_onset_detection                    |                         0.0000 |
| high_cost_local_harm_d0.04 |                1 |  0.1000 | labels_queried                          |                       -90.3333 |
| high_cost_local_harm_d0.04 |                1 |  0.1000 | evaluator_cumulative_expected_harm_cost |                        -3.2000 |
| high_cost_local_harm_d0.04 |                1 |  0.1500 | post_onset_detection                    |                         0.0000 |
| high_cost_local_harm_d0.04 |                1 |  0.1500 | labels_queried                          |                       -63.5333 |
| high_cost_local_harm_d0.04 |                1 |  0.1500 | evaluator_cumulative_expected_harm_cost |                        -3.2000 |
| high_cost_local_harm_d0.04 |                3 |  0.0500 | post_onset_detection                    |                         0.0000 |
| high_cost_local_harm_d0.04 |                3 |  0.0500 | labels_queried                          |                      -125.4000 |
| high_cost_local_harm_d0.04 |                3 |  0.0500 | evaluator_cumulative_expected_harm_cost |                        -3.2000 |
| high_cost_local_harm_d0.04 |                3 |  0.1000 | post_onset_detection                    |                         0.0000 |
| high_cost_local_harm_d0.04 |                3 |  0.1000 | labels_queried                          |                       -90.8333 |
| high_cost_local_harm_d0.04 |                3 |  0.1000 | evaluator_cumulative_expected_harm_cost |                        -3.2000 |
| high_cost_local_harm_d0.04 |                3 |  0.1500 | post_onset_detection                    |                         0.0000 |
| high_cost_local_harm_d0.04 |                3 |  0.1500 | labels_queried                          |                       -55.2000 |
| high_cost_local_harm_d0.04 |                3 |  0.1500 | evaluator_cumulative_expected_harm_cost |                        -3.2000 |
| high_cost_local_harm_d0.04 |               12 |  0.0500 | post_onset_detection                    |                         0.0000 |
| high_cost_local_harm_d0.04 |               12 |  0.0500 | labels_queried                          |                      -152.3333 |
| high_cost_local_harm_d0.04 |               12 |  0.0500 | evaluator_cumulative_expected_harm_cost |                        -3.2000 |
| high_cost_local_harm_d0.04 |               12 |  0.1000 | post_onset_detection                    |                         0.0000 |
| high_cost_local_harm_d0.04 |               12 |  0.1000 | labels_queried                          |                       -79.9667 |
| high_cost_local_harm_d0.04 |               12 |  0.1000 | evaluator_cumulative_expected_harm_cost |                        -3.2000 |
| high_cost_local_harm_d0.04 |               12 |  0.1500 | post_onset_detection                    |                         0.0000 |
| high_cost_local_harm_d0.04 |               12 |  0.1500 | labels_queried                          |                       -49.2000 |
| high_cost_local_harm_d0.04 |               12 |  0.1500 | evaluator_cumulative_expected_harm_cost |                        -3.2000 |
| high_cost_local_harm_d0.04 |               24 |  0.0500 | post_onset_detection                    |                         0.0000 |
| high_cost_local_harm_d0.04 |               24 |  0.0500 | labels_queried                          |                      -120.3333 |
| high_cost_local_harm_d0.04 |               24 |  0.0500 | evaluator_cumulative_expected_harm_cost |                        -4.8000 |
| high_cost_local_harm_d0.04 |               24 |  0.1000 | post_onset_detection                    |                         0.0000 |
| high_cost_local_harm_d0.04 |               24 |  0.1000 | labels_queried                          |                       -87.3333 |
| high_cost_local_harm_d0.04 |               24 |  0.1000 | evaluator_cumulative_expected_harm_cost |                        -3.2000 |
| high_cost_local_harm_d0.04 |               24 |  0.1500 | post_onset_detection                    |                         0.0000 |
| high_cost_local_harm_d0.04 |               24 |  0.1500 | labels_queried                          |                       -46.7000 |
| high_cost_local_harm_d0.04 |               24 |  0.1500 | evaluator_cumulative_expected_harm_cost |                        -3.2000 |
| high_cost_local_harm_d0.20 |                1 |  0.0500 | post_onset_detection                    |                         0.0000 |
| high_cost_local_harm_d0.20 |                1 |  0.0500 | labels_queried                          |                      -147.8667 |
| high_cost_local_harm_d0.20 |                1 |  0.0500 | evaluator_cumulative_expected_harm_cost |                        -8.0000 |
| high_cost_local_harm_d0.20 |                1 |  0.1000 | post_onset_detection                    |                        -0.0333 |
| high_cost_local_harm_d0.20 |                1 |  0.1000 | labels_queried                          |                       -57.7333 |
| high_cost_local_harm_d0.20 |                1 |  0.1000 | evaluator_cumulative_expected_harm_cost |                         9.8667 |
| high_cost_local_harm_d0.20 |                1 |  0.1500 | post_onset_detection                    |                        -0.0333 |
| high_cost_local_harm_d0.20 |                1 |  0.1500 | labels_queried                          |                       -26.1000 |
| high_cost_local_harm_d0.20 |                1 |  0.1500 | evaluator_cumulative_expected_harm_cost |                         4.3867 |
| high_cost_local_harm_d0.20 |                3 |  0.0500 | post_onset_detection                    |                         0.0000 |
| high_cost_local_harm_d0.20 |                3 |  0.0500 | labels_queried                          |                      -143.1667 |
| high_cost_local_harm_d0.20 |                3 |  0.0500 | evaluator_cumulative_expected_harm_cost |                        -8.0000 |
| high_cost_local_harm_d0.20 |                3 |  0.1000 | post_onset_detection                    |                         0.0000 |
| high_cost_local_harm_d0.20 |                3 |  0.1000 | labels_queried                          |                       -60.8667 |
| high_cost_local_harm_d0.20 |                3 |  0.1000 | evaluator_cumulative_expected_harm_cost |                        -1.3800 |
| high_cost_local_harm_d0.20 |                3 |  0.1500 | post_onset_detection                    |                         0.0000 |
| high_cost_local_harm_d0.20 |                3 |  0.1500 | labels_queried                          |                       -18.6333 |
| high_cost_local_harm_d0.20 |                3 |  0.1500 | evaluator_cumulative_expected_harm_cost |                         8.0000 |
| high_cost_local_harm_d0.20 |               12 |  0.0500 | post_onset_detection                    |                         0.0333 |
| high_cost_local_harm_d0.20 |               12 |  0.0500 | labels_queried                          |                      -125.5333 |
| high_cost_local_harm_d0.20 |               12 |  0.0500 | evaluator_cumulative_expected_harm_cost |                        -5.0200 |
| high_cost_local_harm_d0.20 |               12 |  0.1000 | post_onset_detection                    |                        -0.0667 |
| high_cost_local_harm_d0.20 |               12 |  0.1000 | labels_queried                          |                       -62.2667 |
| high_cost_local_harm_d0.20 |               12 |  0.1000 | evaluator_cumulative_expected_harm_cost |                         4.5200 |
| high_cost_local_harm_d0.20 |               12 |  0.1500 | post_onset_detection                    |                        -0.0667 |
| high_cost_local_harm_d0.20 |               12 |  0.1500 | labels_queried                          |                       -29.2333 |
| high_cost_local_harm_d0.20 |               12 |  0.1500 | evaluator_cumulative_expected_harm_cost |                         8.6800 |
| high_cost_local_harm_d0.20 |               24 |  0.0500 | post_onset_detection                    |                         0.0333 |
| high_cost_local_harm_d0.20 |               24 |  0.0500 | labels_queried                          |                      -107.0000 |
| high_cost_local_harm_d0.20 |               24 |  0.0500 | evaluator_cumulative_expected_harm_cost |                       -10.0267 |
| high_cost_local_harm_d0.20 |               24 |  0.1000 | post_onset_detection                    |                         0.0000 |
| high_cost_local_harm_d0.20 |               24 |  0.1000 | labels_queried                          |                       -54.1000 |
| high_cost_local_harm_d0.20 |               24 |  0.1000 | evaluator_cumulative_expected_harm_cost |                         3.7667 |
| high_cost_local_harm_d0.20 |               24 |  0.1500 | post_onset_detection                    |                        -0.0667 |
| high_cost_local_harm_d0.20 |               24 |  0.1500 | labels_queried                          |                       -22.0667 |
| high_cost_local_harm_d0.20 |               24 |  0.1500 | evaluator_cumulative_expected_harm_cost |                         9.4067 |
| high_cost_local_harm_d0.40 |                1 |  0.0500 | post_onset_detection                    |                         0.0333 |
| high_cost_local_harm_d0.40 |                1 |  0.0500 | labels_queried                          |                      -134.9333 |
| high_cost_local_harm_d0.40 |                1 |  0.0500 | evaluator_cumulative_expected_harm_cost |                       -22.5200 |
| high_cost_local_harm_d0.40 |                1 |  0.1000 | post_onset_detection                    |                        -0.0333 |
| high_cost_local_harm_d0.40 |                1 |  0.1000 | labels_queried                          |                       -80.5000 |
| high_cost_local_harm_d0.40 |                1 |  0.1000 | evaluator_cumulative_expected_harm_cost |                        -7.5333 |
| high_cost_local_harm_d0.40 |                1 |  0.1500 | post_onset_detection                    |                         0.0667 |
| high_cost_local_harm_d0.40 |                1 |  0.1500 | labels_queried                          |                       -38.5000 |
| high_cost_local_harm_d0.40 |                1 |  0.1500 | evaluator_cumulative_expected_harm_cost |                        -9.1067 |
| high_cost_local_harm_d0.40 |                3 |  0.0500 | post_onset_detection                    |                         0.0333 |
| high_cost_local_harm_d0.40 |                3 |  0.0500 | labels_queried                          |                      -141.1333 |
| high_cost_local_harm_d0.40 |                3 |  0.0500 | evaluator_cumulative_expected_harm_cost |                       -21.6400 |
| high_cost_local_harm_d0.40 |                3 |  0.1000 | post_onset_detection                    |                         0.0000 |
| high_cost_local_harm_d0.40 |                3 |  0.1000 | labels_queried                          |                       -74.5333 |
| high_cost_local_harm_d0.40 |                3 |  0.1000 | evaluator_cumulative_expected_harm_cost |                       -11.2000 |
| high_cost_local_harm_d0.40 |                3 |  0.1500 | post_onset_detection                    |                         0.0333 |
| high_cost_local_harm_d0.40 |                3 |  0.1500 | labels_queried                          |                       -40.3333 |
| high_cost_local_harm_d0.40 |                3 |  0.1500 | evaluator_cumulative_expected_harm_cost |                        -3.1333 |
| high_cost_local_harm_d0.40 |               12 |  0.0500 | post_onset_detection                    |                         0.1000 |
| high_cost_local_harm_d0.40 |               12 |  0.0500 | labels_queried                          |                      -146.0333 |
| high_cost_local_harm_d0.40 |               12 |  0.0500 | evaluator_cumulative_expected_harm_cost |                       -42.5600 |
| high_cost_local_harm_d0.40 |               12 |  0.1000 | post_onset_detection                    |                         0.0667 |
| high_cost_local_harm_d0.40 |               12 |  0.1000 | labels_queried                          |                       -77.2333 |
| high_cost_local_harm_d0.40 |               12 |  0.1000 | evaluator_cumulative_expected_harm_cost |                       -28.0267 |
| high_cost_local_harm_d0.40 |               12 |  0.1500 | post_onset_detection                    |                         0.0000 |
| high_cost_local_harm_d0.40 |               12 |  0.1500 | labels_queried                          |                       -51.1667 |
| high_cost_local_harm_d0.40 |               12 |  0.1500 | evaluator_cumulative_expected_harm_cost |                       -30.8533 |
| high_cost_local_harm_d0.40 |               24 |  0.0500 | post_onset_detection                    |                         0.0333 |
| high_cost_local_harm_d0.40 |               24 |  0.0500 | labels_queried                          |                      -143.6333 |
| high_cost_local_harm_d0.40 |               24 |  0.0500 | evaluator_cumulative_expected_harm_cost |                       -18.8000 |
| high_cost_local_harm_d0.40 |               24 |  0.1000 | post_onset_detection                    |                         0.0333 |
| high_cost_local_harm_d0.40 |               24 |  0.1000 | labels_queried                          |                       -85.6667 |
| high_cost_local_harm_d0.40 |               24 |  0.1000 | evaluator_cumulative_expected_harm_cost |                       -22.4533 |
| high_cost_local_harm_d0.40 |               24 |  0.1500 | post_onset_detection                    |                         0.0000 |
| high_cost_local_harm_d0.40 |               24 |  0.1500 | labels_queried                          |                       -37.7333 |
| high_cost_local_harm_d0.40 |               24 |  0.1500 | evaluator_cumulative_expected_harm_cost |                       -12.7867 |
| high_cost_local_harm_d0.60 |                1 |  0.0500 | post_onset_detection                    |                         0.2667 |
| high_cost_local_harm_d0.60 |                1 |  0.0500 | labels_queried                          |                      -154.1333 |
| high_cost_local_harm_d0.60 |                1 |  0.0500 | evaluator_cumulative_expected_harm_cost |                       -83.3000 |
| high_cost_local_harm_d0.60 |                1 |  0.1000 | post_onset_detection                    |                         0.0667 |
| high_cost_local_harm_d0.60 |                1 |  0.1000 | labels_queried                          |                       -80.4333 |
| high_cost_local_harm_d0.60 |                1 |  0.1000 | evaluator_cumulative_expected_harm_cost |                       -54.5800 |
| high_cost_local_harm_d0.60 |                1 |  0.1500 | post_onset_detection                    |                         0.0333 |
| high_cost_local_harm_d0.60 |                1 |  0.1500 | labels_queried                          |                       -46.2000 |
| high_cost_local_harm_d0.60 |                1 |  0.1500 | evaluator_cumulative_expected_harm_cost |                       -41.0400 |
| high_cost_local_harm_d0.60 |                3 |  0.0500 | post_onset_detection                    |                         0.1667 |
| high_cost_local_harm_d0.60 |                3 |  0.0500 | labels_queried                          |                      -164.3333 |
| high_cost_local_harm_d0.60 |                3 |  0.0500 | evaluator_cumulative_expected_harm_cost |                       -82.3400 |
| high_cost_local_harm_d0.60 |                3 |  0.1000 | post_onset_detection                    |                         0.0000 |
| high_cost_local_harm_d0.60 |                3 |  0.1000 | labels_queried                          |                       -67.0000 |
| high_cost_local_harm_d0.60 |                3 |  0.1000 | evaluator_cumulative_expected_harm_cost |                        -2.2000 |
| high_cost_local_harm_d0.60 |                3 |  0.1500 | post_onset_detection                    |                         0.0333 |
| high_cost_local_harm_d0.60 |                3 |  0.1500 | labels_queried                          |                       -41.7333 |
| high_cost_local_harm_d0.60 |                3 |  0.1500 | evaluator_cumulative_expected_harm_cost |                       -30.6000 |
| high_cost_local_harm_d0.60 |               12 |  0.0500 | post_onset_detection                    |                         0.1667 |
| high_cost_local_harm_d0.60 |               12 |  0.0500 | labels_queried                          |                      -152.9333 |
| high_cost_local_harm_d0.60 |               12 |  0.0500 | evaluator_cumulative_expected_harm_cost |                       -76.1400 |
| high_cost_local_harm_d0.60 |               12 |  0.1000 | post_onset_detection                    |                        -0.0333 |
| high_cost_local_harm_d0.60 |               12 |  0.1000 | labels_queried                          |                       -67.7000 |
| high_cost_local_harm_d0.60 |               12 |  0.1000 | evaluator_cumulative_expected_harm_cost |                       -13.8000 |
| high_cost_local_harm_d0.60 |               12 |  0.1500 | post_onset_detection                    |                         0.1000 |
| high_cost_local_harm_d0.60 |               12 |  0.1500 | labels_queried                          |                       -34.6333 |
| high_cost_local_harm_d0.60 |               12 |  0.1500 | evaluator_cumulative_expected_harm_cost |                       -34.8600 |
| high_cost_local_harm_d0.60 |               24 |  0.0500 | post_onset_detection                    |                         0.1000 |
| high_cost_local_harm_d0.60 |               24 |  0.0500 | labels_queried                          |                      -139.6000 |
| high_cost_local_harm_d0.60 |               24 |  0.0500 | evaluator_cumulative_expected_harm_cost |                       -45.3400 |
| high_cost_local_harm_d0.60 |               24 |  0.1000 | post_onset_detection                    |                         0.0333 |
| high_cost_local_harm_d0.60 |               24 |  0.1000 | labels_queried                          |                       -59.5667 |
| high_cost_local_harm_d0.60 |               24 |  0.1000 | evaluator_cumulative_expected_harm_cost |                       -15.3000 |
| high_cost_local_harm_d0.60 |               24 |  0.1500 | post_onset_detection                    |                         0.0667 |
| high_cost_local_harm_d0.60 |               24 |  0.1500 | labels_queried                          |                       -26.7000 |
| high_cost_local_harm_d0.60 |               24 |  0.1500 | evaluator_cumulative_expected_harm_cost |                         0.5600 |
