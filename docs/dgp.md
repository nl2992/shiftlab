# Synthetic specification

For t=0,...,n-1, draw independent X_t ~ N(0,I_4) and epsilon_t ~ N(0,1).
Use Y_t = beta_t^T X_t + sigma_t epsilon_t. Initially beta=(1,-0.9,0,0), sigma=0.3.
For t >= tau, benign shift adds strength s to X[3], concept replaces beta[0] by 1-s,
and variance replaces sigma by 0.3(1+s). No-shift changes nothing. Families are exclusive.
The actual beta, sigma, family and tau are saved with each run; null tau is null.
Random draws are shared across controls for paired comparisons. There is no temporal dependence.
A Bernoulli(1-missing) observation mask determines whether labels arrive at t+delay.
Prediction always precedes the delivery phase. Offline evaluation scores even missing labels.
