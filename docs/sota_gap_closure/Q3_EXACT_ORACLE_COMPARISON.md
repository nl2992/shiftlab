# Exact first-promotion reference on the toy instance (`dive.rpoq_exact`)
The repository's exact solver gives, for the toy binary-contrast instance (horizon 10, delay 2, two contexts), the optimal probability of crossing the promotion threshold under the alternative (power) and under the null (false promotion) for each hard label budget b:

| p_alt | budget | power | null_alarm |
|---|---|---|---|
| (0.8, 0.7) | 0 | 0.0000 | 0.0000 |
| (0.8, 0.7) | 1 | 0.0000 | 0.0000 |
| (0.8, 0.7) | 2 | 0.0007 | 0.0003 |
| (0.8, 0.7) | 3 | 0.0330 | 0.0094 |
| (0.8, 0.7) | 4 | 0.3684 | 0.0625 |
| (0.8, 0.7) | 5 | 0.3686 | 0.0626 |
| (0.8, 0.7) | 6 | 0.3867 | 0.0677 |
| (0.65, 0.6) | 0 | 0.0000 | 0.0000 |
| (0.65, 0.6) | 1 | 0.0000 | 0.0000 |
| (0.65, 0.6) | 2 | 0.0005 | 0.0003 |
| (0.65, 0.6) | 3 | 0.0188 | 0.0094 |
| (0.65, 0.6) | 4 | 0.1673 | 0.0625 |
| (0.65, 0.6) | 5 | 0.1674 | 0.0626 |
| (0.65, 0.6) | 6 | 0.1791 | 0.0677 |

With a promotion gain G, false-promotion loss L and label cost c per label, the exact optimal budget is argmax_b [G power(b) - L null(b) - c b]; policies that always spend the whole budget are suboptimal once c * b exceeds the marginal power gain. The Q3 environment is not tractable for the exact solver (continuous state), so the exact comparison is restricted to this instance; no claim is made that the Q3 policies approach an exact optimum.
