# Synthetic validation

Checks use actual stored observations. Oracle radii describe the DGP, not fitted-model residuals. Monte Carlo deviations are diagnostic, not guaranteed test power.
Each bullet names one immutable stored version and its generation configuration. Versions are not independent replicates.

- Scenario-wide oracle quantile validation: 43/43 scenarios pass exact CDF and replicated coverage gates (36 regression laws; remaining scenarios are classification tasks without residual interval radii). Evidence: `scenario_quantile_validation.json`; processing commit `dd5aa3bfa27d5feecc5b0a57856ef92c1adcc480`.

- `ar1@2054a117aa59dbdb3af4 (n=5000, d=4, seed=42, severity=1.0, pattern=abrupt)`: mean residual=0.00780, iid descriptive SE=0.00423, oracle 90% radius coverage=0.9006; temporal cases require dependence-aware SE.
  Lag-1 autocorrelation=0.5920; configured rho=0.6.
- `ar1@8a9348a9fe075dd2559f (n=5000, d=4, seed=42, severity=1.0, pattern=abrupt)`: mean residual=0.00780, iid descriptive SE=0.00423, oracle 90% radius coverage=0.9006; temporal cases require dependence-aware SE.
  Lag-1 autocorrelation=0.5920; configured rho=0.6.
- `ar1@a303a4edf08d63bc4335 (n=5000, d=4, seed=42, severity=1.0, pattern=abrupt)`: mean residual=0.00780, iid descriptive SE=0.00423, oracle 90% radius coverage=0.9006; temporal cases require dependence-aware SE.
  Lag-1 autocorrelation=0.5920; configured rho=0.6.
- `ar1@e09dfc3a0f11f85226a4 (n=5000, d=4, seed=42, severity=1.0, pattern=abrupt)`: mean residual=0.00780, iid descriptive SE=0.00423, oracle 90% radius coverage=0.9006; temporal cases require dependence-aware SE.
  Lag-1 autocorrelation=0.5920; configured rho=0.6.
- `concept@06c1bbaacd7907d26efb (n=1000, d=2, seed=42, severity=1.5, pattern=variable_dwell)`: mean residual=-0.00997, iid descriptive SE=0.00939, oracle 90% radius coverage=0.891; temporal cases require dependence-aware SE.
- `concept@14bac6a6d278d14fc81f (n=1000, d=2, seed=42, severity=2.0, pattern=temporary)`: mean residual=-0.00997, iid descriptive SE=0.00939, oracle 90% radius coverage=0.891; temporal cases require dependence-aware SE.
- `concept@6416ea19fc2c8cebc56f (n=5000, d=4, seed=42, severity=1.0, pattern=abrupt)`: mean residual=0.00780, iid descriptive SE=0.00423, oracle 90% radius coverage=0.9006; temporal cases require dependence-aware SE.
- `concept@661211c36e1bd0ca1f6c (n=1000, d=2, seed=42, severity=2.0, pattern=oblivious_adversarial)`: mean residual=-0.00997, iid descriptive SE=0.00939, oracle 90% radius coverage=0.891; temporal cases require dependence-aware SE.
- `concept@719dbe4f2a23fd4d3c90 (n=1000, d=2, seed=42, severity=2.0, pattern=oblivious_adversarial)`: mean residual=-0.00997, iid descriptive SE=0.00939, oracle 90% radius coverage=0.891; temporal cases require dependence-aware SE.
- `concept@816c0d57d83b07c35c56 (n=5000, d=4, seed=42, severity=1.0, pattern=abrupt)`: mean residual=0.00780, iid descriptive SE=0.00423, oracle 90% radius coverage=0.9006; temporal cases require dependence-aware SE.
- `concept@9e54140b081e7e572f2a (n=5000, d=4, seed=42, severity=1.0, pattern=abrupt)`: mean residual=0.00780, iid descriptive SE=0.00423, oracle 90% radius coverage=0.9006; temporal cases require dependence-aware SE.
- `concept@aa70da4f86492b9f8084 (n=5000, d=4, seed=42, severity=1.0, pattern=abrupt)`: mean residual=0.00780, iid descriptive SE=0.00423, oracle 90% radius coverage=0.9006; temporal cases require dependence-aware SE.
- `concept@abcec6c0ebc1c0209130 (n=1000, d=2, seed=42, severity=2.0, pattern=oblivious_adversarial)`: mean residual=-0.00997, iid descriptive SE=0.00939, oracle 90% radius coverage=0.891; temporal cases require dependence-aware SE.
- `concept@aeef64a4714351e4f47e (n=1000, d=2, seed=42, severity=2.0, pattern=abrupt)`: mean residual=-0.00997, iid descriptive SE=0.00939, oracle 90% radius coverage=0.891; temporal cases require dependence-aware SE.
- `concept@cb2b4341f8101f96ff95 (n=1000, d=2, seed=42, severity=1.5, pattern=recurring)`: mean residual=-0.00997, iid descriptive SE=0.00939, oracle 90% radius coverage=0.891; temporal cases require dependence-aware SE.
- `concept@e2461ffd1a6145cc5dd8 (n=1000, d=2, seed=42, severity=0.5, pattern=multiple)`: mean residual=-0.00997, iid descriptive SE=0.00939, oracle 90% radius coverage=0.891; temporal cases require dependence-aware SE.
- `concept@e9fbb8e14cecd7a037cc (n=1000, d=2, seed=42, severity=3.0, pattern=abrupt)`: mean residual=-0.00997, iid descriptive SE=0.00939, oracle 90% radius coverage=0.891; temporal cases require dependence-aware SE.
- `concept@ec3bdf1a271e675be5a8 (n=1000, d=2, seed=42, severity=2.0, pattern=linear)`: mean residual=-0.00997, iid descriptive SE=0.00939, oracle 90% radius coverage=0.891; temporal cases require dependence-aware SE.
- `feedback_change@7dc0f057b17388b0952b (n=5000, d=4, seed=42, severity=1.0, pattern=recurring)`: mean residual=0.00780, iid descriptive SE=0.00423, oracle 90% radius coverage=0.9006; temporal cases require dependence-aware SE.
- `heavy_tailed@1699ba0fe0307ba7bc81 (n=5000, d=4, seed=42, severity=1.0, pattern=abrupt)`: mean residual=0.00634, iid descriptive SE=0.00424, oracle 90% radius coverage=0.8996; temporal cases require dependence-aware SE.
- `heavy_tailed@a79bff28e49b3694aa38 (n=5000, d=4, seed=42, severity=1.0, pattern=abrupt)`: mean residual=0.00634, iid descriptive SE=0.00424, oracle 90% radius coverage=0.8996; temporal cases require dependence-aware SE.
- `heavy_tailed@cd57bce8c0d99669b557 (n=5000, d=4, seed=42, severity=1.0, pattern=abrupt)`: mean residual=0.00634, iid descriptive SE=0.00424, oracle 90% radius coverage=0.8996; temporal cases require dependence-aware SE.
- `heavy_tailed@f1122899d44646c9fcfe (n=5000, d=4, seed=42, severity=1.0, pattern=abrupt)`: mean residual=0.00634, iid descriptive SE=0.00424, oracle 90% radius coverage=0.8996; temporal cases require dependence-aware SE.
- `hidden_cost@317e25bbc10d4e6843dd (n=5000, d=4, seed=42, severity=1.0, pattern=abrupt)`: mean residual=0.00780, iid descriptive SE=0.00423, oracle 90% radius coverage=0.9006; temporal cases require dependence-aware SE.
- `hidden_cost@35660b3cb557d4700abe (n=5000, d=4, seed=42, severity=1.0, pattern=abrupt)`: mean residual=0.00780, iid descriptive SE=0.00423, oracle 90% radius coverage=0.9006; temporal cases require dependence-aware SE.
- `hidden_cost@3d8c473169d966eeafb1 (n=5000, d=4, seed=42, severity=1.0, pattern=abrupt)`: mean residual=0.00780, iid descriptive SE=0.00423, oracle 90% radius coverage=0.9006; temporal cases require dependence-aware SE.
- `hidden_cost@418980a5fc11aebb9f98 (n=5000, d=4, seed=42, severity=1.0, pattern=abrupt)`: mean residual=0.00780, iid descriptive SE=0.00423, oracle 90% radius coverage=0.9006; temporal cases require dependence-aware SE.
- `iid_regression@2ec3afaae147c5e67b5c (n=20000, d=64, seed=42, severity=1.0, pattern=abrupt)`: mean residual=-0.00186, iid descriptive SE=0.00210, oracle 90% radius coverage=0.9032; temporal cases require dependence-aware SE.
- `iid_regression@6172f78b8ffa9e08f94c (n=5000, d=4, seed=42, severity=1.0, pattern=abrupt)`: mean residual=0.00780, iid descriptive SE=0.00423, oracle 90% radius coverage=0.9006; temporal cases require dependence-aware SE.
- `iid_regression@69e08181d6ac7d071f67 (n=5000, d=4, seed=42, severity=1.0, pattern=abrupt)`: mean residual=0.00780, iid descriptive SE=0.00423, oracle 90% radius coverage=0.9006; temporal cases require dependence-aware SE.
- `iid_regression@749d51b44e3a8a8068a5 (n=5000, d=4, seed=42, severity=1.0, pattern=abrupt)`: mean residual=0.00780, iid descriptive SE=0.00423, oracle 90% radius coverage=0.9006; temporal cases require dependence-aware SE.
- `iid_regression@ec1804e2f447a6af06b9 (n=5000, d=4, seed=42, severity=1.0, pattern=abrupt)`: mean residual=0.00780, iid descriptive SE=0.00423, oracle 90% radius coverage=0.9006; temporal cases require dependence-aware SE.
- `iid_regression@f2651e700ab64a957f07 (n=20000, d=64, seed=42, severity=1.0, pattern=abrupt)`: mean residual=-0.00186, iid descriptive SE=0.00210, oracle 90% radius coverage=0.9032; temporal cases require dependence-aware SE.
- `irrelevant@0776b20e3a343bd75dda (n=5000, d=4, seed=42, severity=1.0, pattern=abrupt)`: mean residual=0.00780, iid descriptive SE=0.00423, oracle 90% radius coverage=0.9006; temporal cases require dependence-aware SE.
- `irrelevant@6214dd25d33709869d63 (n=5000, d=4, seed=42, severity=1.0, pattern=abrupt)`: mean residual=0.00780, iid descriptive SE=0.00423, oracle 90% radius coverage=0.9006; temporal cases require dependence-aware SE.
- `irrelevant@8d58c220c4b53d25104e (n=5000, d=4, seed=42, severity=1.0, pattern=abrupt)`: mean residual=0.00780, iid descriptive SE=0.00423, oracle 90% radius coverage=0.9006; temporal cases require dependence-aware SE.
- `irrelevant@92f0fb941cf3793f3461 (n=5000, d=4, seed=42, severity=1.0, pattern=abrupt)`: mean residual=0.00780, iid descriptive SE=0.00423, oracle 90% radius coverage=0.9006; temporal cases require dependence-aware SE.
- `prior_shift@05dec821b91a162740bb (n=5000, d=4, seed=42, severity=1.0, pattern=abrupt)`: mean residual=-0.00071, iid descriptive SE=0.00454, oracle 90% radius coverage=None; temporal cases require dependence-aware SE.
- `prior_shift@1e9125458315feb8c23f (n=5000, d=4, seed=42, severity=1.0, pattern=abrupt)`: mean residual=-0.00071, iid descriptive SE=0.00454, oracle 90% radius coverage=None; temporal cases require dependence-aware SE.
- `prior_shift@291c4501c2352c682e2f (n=5000, d=4, seed=42, severity=1.0, pattern=abrupt)`: mean residual=-0.00071, iid descriptive SE=0.00454, oracle 90% radius coverage=None; temporal cases require dependence-aware SE.
- `prior_shift@abbff93d3272b88b7a04 (n=5000, d=4, seed=42, severity=1.0, pattern=abrupt)`: mean residual=-0.00071, iid descriptive SE=0.00454, oracle 90% radius coverage=None; temporal cases require dependence-aware SE.
- `target_variance@0b907947193c744fd05c (n=1000, d=2, seed=42, severity=2.0, pattern=abrupt)`: mean residual=-0.01528, iid descriptive SE=0.02110, oracle 90% radius coverage=0.891; temporal cases require dependence-aware SE.
- `target_variance@1b4799bc4d7f91e90331 (n=5000, d=4, seed=42, severity=1.0, pattern=abrupt)`: mean residual=0.01441, iid descriptive SE=0.00670, oracle 90% radius coverage=0.9006; temporal cases require dependence-aware SE.
- `target_variance@3868905063fc0161a3ae (n=5000, d=4, seed=42, severity=1.0, pattern=abrupt)`: mean residual=0.01441, iid descriptive SE=0.00670, oracle 90% radius coverage=0.9006; temporal cases require dependence-aware SE.
- `target_variance@5979e73e31d1c605cc2d (n=5000, d=4, seed=42, severity=1.0, pattern=abrupt)`: mean residual=0.01441, iid descriptive SE=0.00670, oracle 90% radius coverage=0.9006; temporal cases require dependence-aware SE.
- `target_variance@ff65712a55b8b96f10ba (n=5000, d=4, seed=42, severity=1.0, pattern=abrupt)`: mean residual=0.01441, iid descriptive SE=0.00670, oracle 90% radius coverage=0.9006; temporal cases require dependence-aware SE.
