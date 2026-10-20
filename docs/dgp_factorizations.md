# Distribution factorizations of the implemented target-shift family

Write `w` for the evaluator's regime weight, `s=severity*w`, `f(X)=X0-.9*X1`,
and `sigma=noise`. The statements below concern the true data-generating distribution,
not a fitted model. All regime annotations are evaluator-only. A change in the target
marginal does not by itself identify pure label shift.

| Registered mechanism | Generative factorization | P(X) | P(Y\|X) | P(X\|Y) | Target marginal |
|---|---|---|---|---|---|
| `prior_shift` | `Y~Bernoulli(expit(s))`; `X0\|Y~N(2Y-1,1)`; other features independent standard normal | Changes as mixture weights change | Changes; posterior log odds `2*X0+s` | Fixed | Class prior changes from 1/2 |
| `imbalance` | Same class-conditional law; prior `expit(log(.1/.9)+s)` | Changes | Changes; posterior log odds `2*X0+logit(prior)` | Fixed | Class prior changes from .1 |
| `label_corruption` | Fixed Gaussian X; observed probability `r+(1-2r)*expit(X0+X1²-1)`, `r=min(.45,s/5)` | Fixed | Changes through symmetric corruption | Generally changes for the observed label | Can change; not held fixed by construction |
| `target_level` | Fixed Gaussian X; `Y=f(X)+s+sigma*Z`, independent standard-normal Z | Fixed | Mean changes | Generally changes | Location changes; not pure regression label shift |
| `target_variance` | Fixed Gaussian X; `Y=f(X)+sigma*(1+s)*Z` | Fixed | Residual variance changes; mean fixed | Generally changes | Variance `1.81+sigma²*(1+s)²`; this is not a scale change of the entire Y variable |
| `tail_frequency` | Fixed Gaussian X; noise is `N(0,sigma²)` with probability `1-r` and `N(0,64*sigma²)` with probability `r=.01+.1*tanh(severity)*w` | Fixed | Tail mixture changes; mean fixed | Generally changes | Variance `1.81+sigma²*(1+63*r)`; rare extremes become more frequent |

These equalities assume the documented independent Gaussian features and noise, before
optional feedback censoring. Missing labels alter the observed feedback process; they
do not redefine the latent target distribution. At zero severity all six mechanisms
retain their specified baseline, which need not equal the IID Gaussian-regression control.

## Pure covariate mechanisms

`mean`, `feature_variance`, `covariance_rotation`, `correlation`, `mixture_weights`,
`new_component`, `feature_tail`, `feature_skew` and `irrelevant` alter X and then apply
the same response law `Y=f(X)+sigma*Z` with independent standard-normal Z. For `irrelevant`
at dimension two the response law is `Y=X0+sigma*Z` in both regimes, so X1 is actually
irrelevant. The heavy-tail and skew transforms use independent replacement response
noise after transforming a feature. Thus their `P(Y|X)` remains fixed even though the
feature transformation itself uses a random draw. The marginal Y distribution may
change when relevant features change; it is unchanged under a shift confined to the
independent nuisance coordinate.

The covariance-rotation baseline has first-two-feature covariance `diag(1,4)`, not
identity. Mixture-weight shift starts from an equal-weight two-component feature mixture;
zero severity preserves that mixture rather than replacing it with a single Gaussian.
These baseline distinctions matter when estimating null false alarms.

`tests/data/test_covariate_properties.py` checks each pure-covariate mechanism's stated
conditional mean directly against its generated oracle and checks regime-specific moments
against analytic targets for mean, variance, rotated covariance, correlation, mixture weights,
new-component probability, tails and skew. These are independent property checks; the generic
oracle-risk test alone is not used as evidence that the covariate mechanism is correct.

`tests/data/test_target_shift_properties.py` and
`data/reports/target_shift_validation.json` independently check the prior-shift class prior and
class-conditional feature means, symmetric label-corruption posterior, target-level conditional
mean, target-variance residual variance, and tail-frequency mixture variance across five seeds.
All reported checks pass their prespecified analytic tolerances. Replicate summaries remain
descriptive.
