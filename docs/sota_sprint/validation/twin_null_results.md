# P2 known-null real streams (exchangeable twins): results

Protocol: [../p2_known_null_protocol.md](../p2_known_null_protocol.md) (registered 36d9796 before any build). 20 splits x K episodes x 3 policy seeds per dataset; promotion = fraction of runs that ever promote on a known-null stream; 95% CI = cluster bootstrap over splits. Bold = point > .0936 with lower bound > .05.

| dataset | median rho-hat | disagreement | mean realised adv [CI] (K0) |
|---|---|---|---|
| appliances | 0.6000000000000001 | 0.128 | +0.0077 [-0.0049,+0.0193] |
| beijing_pm25 | 0.7000000000000001 | 0.082 | -0.0012 [-0.0031,+0.0009] |
| bike_hour | 0.5 | 0.054 | -0.0014 [-0.0047,+0.0017] |
| household_power | 0.7000000000000001 | 0.044 | +0.0006 [-0.0007,+0.0020] |
| metro | 0.9 | 0.008 | +0.0003 [-0.0002,+0.0007] |

| policy | appliances | beijing_pm25 | bike_hour | household_power | metro |
|---|---|---|---|---|---|
| gated_deployment | **0.244** [0.164,0.325]; harm -0.0 | 0.092 [0.062,0.124]; harm +7.3 | 0.089 [0.042,0.142]; harm +3.7 | **0.102** [0.066,0.143]; harm +3.1 | 0.006 [0.000,0.016]; harm +0.8 |
| discern_style | 0.006 [0.000,0.017]; harm +8.5 | 0.000 [0.000,0.000]; harm +7.7 | 0.000 [0.000,0.000]; harm +5.3 | 0.000 [0.000,0.000]; harm +4.4 | 0.000 [0.000,0.000]; harm +0.8 |
| gated_adaptive_range | **0.314** [0.219,0.408]; harm -4.6 | **0.099** [0.069,0.131]; harm +7.3 | 0.089 [0.042,0.142]; harm +3.7 | **0.102** [0.066,0.143]; harm +3.1 | 0.006 [0.000,0.016]; harm +0.8 |
| gated_adaptive_range+front | **0.400** [0.292,0.508]; harm -6.1 | **0.118** [0.082,0.157]; harm +6.6 | 0.100 [0.042,0.158]; harm +3.1 | **0.110** [0.075,0.152]; harm +2.9 | 0.006 [0.000,0.016]; harm +0.8 |
| discern_design_floor | **0.197** [0.108,0.294]; harm +0.6 | 0.021 [0.006,0.039]; harm +7.3 | 0.019 [0.000,0.044]; harm +5.2 | 0.018 [0.005,0.033]; harm +4.3 | 0.000 [0.000,0.000]; harm +0.8 |
| SMCS+retain-incumbent | **0.428** [0.339,0.511]; harm -1.1 | **0.219** [0.177,0.273]; harm +8.8 | **0.158** [0.092,0.222]; harm +4.1 | **0.189** [0.149,0.229]; harm +3.2 | 0.037 [0.015,0.069]; harm +0.9 |
| xu_acquisition_only | **0.375** [0.275,0.478]; harm -4.5 | **0.175** [0.137,0.214]; harm +7.4 | **0.153** [0.089,0.219]; harm +3.8 | **0.133** [0.097,0.173]; harm +3.5 | 0.013 [0.003,0.025]; harm +0.8 |
| choe_ramdas_eb | **0.336** [0.242,0.428]; harm -6.0 | **0.123** [0.090,0.155]; harm +6.7 | 0.097 [0.042,0.156]; harm +2.9 | **0.113** [0.078,0.151]; harm +2.8 | 0.009 [0.000,0.019]; harm +0.8 |
| choe_ramdas_eb+front | **0.358** [0.267,0.450]; harm -6.3 | **0.132** [0.096,0.168]; harm +6.7 | 0.108 [0.050,0.175]; harm +3.3 | **0.115** [0.080,0.152]; harm +2.8 | 0.009 [0.000,0.019]; harm +0.8 |
| gated_deployment+QCE | **0.372** [0.275,0.464]; harm -6.2 | **0.119** [0.082,0.158]; harm +6.7 | 0.092 [0.042,0.150]; harm +3.1 | **0.119** [0.083,0.160]; harm +3.1 | 0.006 [0.000,0.016]; harm +0.8 |
| gated_deployment+QCE+front | **0.408** [0.300,0.508]; harm -5.9 | **0.129** [0.089,0.171]; harm +6.3 | 0.092 [0.042,0.150]; harm +2.9 | **0.122** [0.085,0.165]; harm +3.0 | 0.006 [0.000,0.016]; harm +0.8 |
| A5b | 0.042 [0.008,0.083]; harm +3.2 | 0.007 [0.000,0.018]; harm +4.9 | 0.058 [0.017,0.100]; harm +4.3 | 0.035 [0.015,0.057]; harm +3.3 | 0.000 [0.000,0.000]; harm +0.8 |
| A1b | 0.075 [0.033,0.117]; harm +7.1 | 0.014 [0.004,0.029]; harm +8.3 | 0.083 [0.042,0.133]; harm +5.0 | 0.033 [0.013,0.053]; harm +4.2 | 0.000 [0.000,0.000]; harm +0.8 |
| rmm:gated_deployment+RMM | **0.597** [0.481,0.706]; harm -5.5 | **0.273** [0.214,0.331]; harm +7.8 | **0.142** [0.083,0.208]; harm +3.6 | **0.137** [0.098,0.180]; harm +3.4 | 0.006 [0.000,0.016]; harm +0.8 |
| rmm:discern_style+RMM | **0.586** [0.475,0.692]; harm -5.4 | **0.274** [0.218,0.330]; harm +7.9 | **0.139** [0.078,0.206]; harm +3.6 | **0.138** [0.100,0.180]; harm +3.4 | 0.006 [0.000,0.016]; harm +0.8 |
| rmm:SMCS+retain-incumbent+RMM | **0.625** [0.514,0.722]; harm -6.0 | **0.360** [0.300,0.421]; harm +8.5 | **0.186** [0.114,0.258]; harm +3.9 | **0.190** [0.148,0.232]; harm +3.0 | 0.016 [0.006,0.028]; harm +0.8 |
| rmm:gated_adaptive_range+RMM | **0.586** [0.472,0.694]; harm -5.3 | **0.277** [0.226,0.329]; harm +7.7 | **0.142** [0.083,0.208]; harm +3.5 | **0.139** [0.100,0.183]; harm +3.4 | 0.006 [0.000,0.016]; harm +0.8 |
| D1 | **0.486** [0.372,0.589]; harm -12.4 | **0.274** [0.231,0.321]; harm +3.9 | **0.192** [0.125,0.258]; harm +1.2 | **0.166** [0.130,0.203]; harm +1.4 | 0.025 [0.009,0.044]; harm +0.5 |
| D2 | **0.556** [0.450,0.658]; harm -7.2 | **0.274** [0.224,0.331]; harm +4.8 | **0.181** [0.114,0.242]; harm +2.1 | **0.180** [0.143,0.217]; harm +1.8 | 0.030 [0.014,0.048]; harm +0.7 |
| QSG | **0.625** [0.517,0.728]; harm -8.3 | **0.331** [0.273,0.396]; harm +8.9 | **0.217** [0.142,0.283]; harm +4.1 | **0.198** [0.158,0.238]; harm +3.1 | 0.037 [0.016,0.062]; harm +0.9 |
| model_picker_adapter | **0.908** [0.867,0.944]; harm -4.8 | **0.886** [0.861,0.910]; harm +18.6 | **0.869** [0.822,0.911]; harm +12.3 | **0.860** [0.838,0.882]; harm +11.4 | **0.720** [0.673,0.766]; harm +5.7 |
| cams_adapter | **0.925** [0.889,0.958]; harm -0.0 | **0.918** [0.902,0.933]; harm +25.7 | **0.906** [0.858,0.945]; harm +17.7 | **0.866** [0.838,0.893]; harm +15.3 | **0.820** [0.777,0.856]; harm +8.9 |

**K1 (>= 5/9 powered certified ports break the bound on a rho-hat >= .5 dataset): PASS** (9/9): gated_adaptive_range: ['appliances', 'beijing_pm25', 'household_power']; gated_adaptive_range+front: ['appliances', 'beijing_pm25', 'household_power']; discern_design_floor: ['appliances']; SMCS+retain-incumbent: ['appliances', 'beijing_pm25', 'bike_hour', 'household_power']; xu_acquisition_only: ['appliances', 'beijing_pm25', 'bike_hour', 'household_power']; choe_ramdas_eb: ['appliances', 'beijing_pm25', 'household_power']; choe_ramdas_eb+front: ['appliances', 'beijing_pm25', 'household_power']; gated_deployment+QCE: ['appliances', 'beijing_pm25', 'household_power']; gated_deployment+QCE+front: ['appliances', 'beijing_pm25', 'household_power']
**K2 (A5b bootstrap upper bound <= .0936 on every dataset): FAIL** {'appliances': True, 'beijing_pm25': True, 'bike_hour': False, 'household_power': True, 'metro': True}
