# Exact first-promotion reference on the toy instance (`dive.rpoq_exact`)
The repository's exact solver gives, for the toy binary-contrast instance (horizon 10, delay 2, two contexts), the optimal probability of crossing the promotion threshold under the alternative (power) and under the null (false promotion) for each hard label budget b:

(exact table pending: `outputs/gap_closure/e11_exact_voi.csv`)

With a promotion gain G, false-promotion loss L and label cost c per label, the exact optimal budget is argmax_b [G power(b) - L null(b) - c b]; policies that always spend the whole budget are suboptimal once c * b exceeds the marginal power gain. The Q3 environment is not tractable for the exact solver (continuous state), so the exact comparison is restricted to this instance; no claim is made that the Q3 policies approach an exact optimum.
