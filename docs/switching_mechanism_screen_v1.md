# Mechanism pre-screen: economical lifetime of delayed evidence

2026-10-28. Analytical development only. No empirical runs or new algorithm nomination.
This tests whether the initially suggested sample-age confidence gate is enough for G2. It is not.

## A valid elementary construction

Assume independent bounded paired scores Z_s in [-1,1] with deterministic means mu_s and
known |mu_(s+1)-mu_s|<=v. No covariate selection in this slice. At an observed-history stopping
time r, commit to n consecutive queries r,...,r+n-1, where n is chosen before seeing this batch's
outcomes. Outcomes arrive with fixed delay d. Charge n against the hard budget when issuing
queries (or reserve the whole batch at commitment); do not issue beyond the horizon/budget.
The last label arrives at t0=r+n-1+d. Use only completed batches in this calculation.

For batch b, assign deterministic alpha_b>0 with sum_b alpha_b<=alpha. Conditional on the
history at commitment, Hoeffding gives, with failure probability at most alpha_b,

    abs(mean(Z_batch)-mean(mu_batch)) <= e_b,
    e_b = sqrt(2 log(2/alpha_b)/n).

The random start and history-dependent n do not spoil this conditional bound: all future
outcomes are independent and n is fixed at commitment. Union over batches then controls all
batch deviations. This proof does not cover outcome-dependent within-batch stopping or selecting
a favorable subset after labels arrive. A different confidence construction would be needed.

For any t>=t0 and h>=1 with t+h-1<=T, the simultaneous event implies

    sum_(j=0)^(h-1) mu_(t+j)
      >= h*(mean(Z_batch)-e_b-v*(t-r-(n-1)/2)) - v*h*(h-1)/2.

Consequently, declare a switch economically certified for that h only if this expression is
greater than k. Even adaptively choosing t,h and batch b is valid on the same simultaneous
event: the extrapolation is deterministic and holds for every admissible future time. This
certifies a *specified hold-for-h action*, before query costs or subsequent reversal charges.
It does not certify an unrestricted controller that might reverse early. The objective must
account for future query costs separately; sunk queries are not recovered by the certificate.

## Exact sample-size penalty for this construction

At t=t0, divide the lower bound by h. Excluding the empirical score and the future-horizon
penalty, the statistical/age penalty is

    p(n)=sqrt(C/n)+v*(d+(n-1)/2),  C=2 log(2/alpha_b).

For v>0, its continuous positive-n minimizer is n_star=(C/v^2)^(1/3): differentiate to obtain
p'(n)=-(sqrt(C)/2)*n^(-3/2)+v/2, with p''(n)>0. Integer minimization over a fixed feasible
range needs only the clipped floor/ceiling of n_star. For v=0 use the largest feasible n.
This formula assumes alpha_b is fixed while comparing n; changing error allocation with n
requires redoing the optimization. Longer batches can worsen the gate even with more labels.

Delay alone contributes v*d. With H=T-t0+1, the *most optimistic possible* batch score is 1.
If for every feasible n and h<=H,

    h*(1-p(n)) - v*h*(h-1)/2 <= k,

then **this certificate family** cannot certify a switch even on an all-positive batch. This is
a family-specific feasibility obstruction, not an information-theoretic impossibility result.
For fixed a=1-p(n), maximize g(h)=h*a-v*h*(h-1)/2 over integer h in [1,H] by checking the
clipped neighboring integers of h_star=a/v+1/2 (v>0). For v=0 the maximum is at a boundary.

The sample-age and future-envelope penalties explain why simply gathering more delayed labels
may not rescue a costed decision. But their composition is elementary and overlaps established
drift correction and switching economics; it fails the substantive-insight gate by itself.

## Acquisition mechanism still required

A candidate worth deriving must choose *whether and when* to initiate or enlarge evidence
acquisition while accounting for pending labels, hard remaining budget, and the chance that
evidence expires before a profitable action. The batch gate above only optimizes an uncertainty
penalty, not decision regret. In particular, choosing n_star ignores the observed decision margin,
query cost and value of reserving labels for reversal. Do not name it as the new algorithm.

**Decision:** reject the elementary age-corrected gate as a standalone contribution. Keep it as
a theoretically explicit comparator/supporting primitive. Continue to a coupled acquisition
derivation only after checking direct delayed-switching and constrained sequential-design work.
No claims about empirical benefit or optimality of an acquisition policy follow from this screen.

Deterministic numerical sanity check: 336 sample-count and horizon-optimizer cases agreed with
exhaustive enumeration (sample caps through 512, horizons through 100, including v=0 and negative
effective margins). Record: `outputs/switching_source_audit_v1/algebra_checks.json`. All seven
cached PDF hashes matched their manifest. These checks neither replace the derivations above
nor constitute empirical method validation.
