# Null class specifications
| id | null world | what is held fixed | what the e-process null requires | status of the requirement |
|---|---|---|---|---|
| X01 | iid, fixed vs independent random delay | marginal law | outcome-independent delay | holds |
| X02 | outcome-dependent / heavy / burst delay | marginal law | in-order release for outcome-dependent delay | prefix holds; arrived-subset not covered |
| X03 | AR(1) latent logit noise | marginal law of (x, y) | `E[R_t | F_{t-1}] <= r0` | **fails** (conditional risk drifts) |
| X04 | cluster-shared random effects | marginal law | same | **fails** |
| X05 | history-adaptive covariates, calibrated P(loss|x) | stationary marginal risk | same | fails conditionally (adaptive covariate mix) |
| X06 | heterogeneous conditional risk, unchanged marginal risk | marginal risk = r0 | marginal null; predictable bets | holds after repair; legacy cap violates |
| X07 | severe proxy bias / anti-informative proxy | law, outcomes | unbiasedness of IPW (proxy-free) | holds |
| X08 | no shift (G1, G2, G3 K2, G4) | all | iid for G1-G3; G4 is GARCH-dependent | G4 fails conditionally |
| X09 | benign covariate shift, prior shift | label law (cov), cost falls (prior) | no decision-cost harm | Brier risk rises under `prior` shift (predictive harm without decision harm) |
| X10 | transient harm | - | power question | - |
| X11 | multiple recurrent shifts | - | power question | - |
| X12 | very low label availability (0.2%-2%) | marginal law | same as X01 | holds |
| X13 | hard budget exhaustion | marginal law | inactive events after exhaustion | holds |
| X14 | extreme but bounded losses (FN cost, clipped heavy-tailed returns) | bounded range | boundedness | G4 clip: dependence fails; cost: holds |
