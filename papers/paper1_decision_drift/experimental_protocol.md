# Initial protocol

Use the shared four-family iid Gaussian regression benchmark, seeds 11,22,33, n=1200,
train [0,200), calibration [200,350), evaluation [350,1200), change 650, delay 3.
Do not use test labels for hyperparameters. Policies see only arrived labels. Compare methods
on paired streams. Primary metrics: P1 alarm counts, detection delay and expected decision regret;
P2 coverage and width; P3 cumulative squared loss plus explicit adaptation costs.
Report nondetections separately and avoid interpreting post-change alarms in benign controls as
harmful-shift power. Stream bootstrap intervals are descriptive at this small sample size.
Future confirmatory study requires independent threshold-calibration seeds, larger locked test
seed sets, matched budgets and predefined post-change windows. No significance claim yet.
