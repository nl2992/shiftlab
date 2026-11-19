# Proof package: arbitrary fixed label budget

## Claim and status

**Status: proved as stated; fresh adversarial same-family review PASS (provisional).** The reviewer found no fatal, critical, major, or minor mathematical issues and matched the proof assumptions to the repository game. This is not cross-family verification or formal proof-assistant verification. See `B_GENERAL_FIXED_PREMIUM_PROOF_AUDIT_2026-11-13.md`. The theorem is now recorded in the theorem registry; the overall publication decision remains open pending the locked novelty and evidence checks.

For any integer $B\ge1$, define
$$
H_B:=6B^3+3B+2,
\qquad
r_0(B):=\frac{1}{16(B+2)H_B}.
$$
In the stationary symmetric anti-persistent HMM, suppose
$$
d=1,\quad c=k=0,\quad \alpha=\frac1{10},\quad
\frac25<g<\frac12,\quad 0<r<r_0(B).
$$
Then, for every integer $T\ge3B$,
$$
\Gamma(T)\ge
\alpha gr\,\frac{3(B+1)}{8(B+2)},
\qquad
\rho_\Gamma(T)\ge\frac{3}{8(B+2)}.
$$

The radius depends on $B$. The theorem does not assert a common positive radius for all unbounded budgets.

## Assumptions and notation

Let $a=\sqrt g$, $\rho=-r$, and let $X_t\in\{-1,1\}$ be a stationary symmetric Markov chain with
$$
\mathbb E[X_{t+1}\mid X_t]=\rho X_t.
$$
Its initial spin is fair, and its transition signs are independent with mean $\rho$. Conditional on the hidden states, queried emission signs $S_t\in\{-1,1\}$ are independent and satisfy
$$
\mathbb P(S_t=s\mid X_t)=\frac{1+a sX_t}{2}.
$$
A zero label corresponds to $s=-1$. The conditional gain of action $1$ over action $0$ is $a\,\mathbb E[X_t\mid\text{released labels}]$.

The proof also requires the following features of the existing model:

1. At most one label is queried per time step, and query decisions are predictable from released labels and the learner's private randomization.
2. A label queried at time $t$ is released before the action at time $t+1$. A query at $t$ cannot inform the action at $t$.
3. Actions do not affect the hidden process or future emissions. Query and switching costs are zero.
4. Private randomization is independent of the hidden process and null-label randomness.
5. Null risk is the probability of ever choosing action $1$, called *promotion* below. A causal-feasible learner has this risk at most $\alpha$ under every admissible causal null.
6. The null class includes IID fair labels and, for each $j\le B$, a null $\nu_j$ that forces queried label $j$ to zero and uses fair labels at every other queried position. In particular, the current query and its ordinal must be public before that label is generated.
7. There is no additional observation carrying hidden-state information beyond the released queried labels.

Write $\operatorname{VOI}_{\rm IID}$ and $\operatorname{VOI}_{\rm causal}$ for the optimized expected gains relative to never promoting, with the respective risk constraints. Thus
$$
\Gamma=\operatorname{VOI}_{\rm IID}-\operatorname{VOI}_{\rm causal},
\qquad
\rho_\Gamma=\frac{\Gamma}{\operatorname{VOI}_{\rm IID}}
$$
when the denominator is positive.

## Dependency map

The theorem follows from:

1. An exact cylinder-density formula and posterior expansion for a fixed realized adaptive-query path.
2. Uniform bounds on the density perturbation and posterior remainder.
3. A Bellman envelope for every adaptive continuation, including a query on the promotion step.
4. The equal-mixture null certificate and a first-promotion leaf decomposition.
5. An explicit IID witness and its finite-horizon gain.
6. The stated arithmetic bounds.

## 1. Spin moments and adaptive-query cylinders

For deterministic ordered times $v_1<\cdots<v_{2q}$,
$$
\mathbb E\!\left[\prod_{\ell=1}^{2q}X_{v_\ell}\right]
=
\rho^{\sum_{\ell=1}^{q}(v_{2\ell}-v_{2\ell-1})},
$$
and every odd spin moment is zero. To see this, write each $X_v$ as the initial spin times the product of transition signs up to $v$. The initial spin kills odd moments. For an even product, transition signs cancel outside the paired intervals; independence gives the displayed power.

Fix the learner's private seed and a realized decision-tree cylinder with $m\le B$ released signs $s_1,\ldots,s_m$ at increasing query times
$$
u_1<\cdots<u_m.
$$
Although the schedule is adaptive, these times are fixed on this cylinder: each query decision is determined by the earlier released signs. For a subset $J=\{j_1<\cdots<j_k\}$, set $s_J=\prod_{j\in J}s_j$. Its alternative probability is
$$
2^{-m}D_m,
$$
where
$$
D_m
=
\sum_{\substack{J\subseteq[m]\\ |J|\ {\rm even}}}
a^{|J|}s_J
\rho^{\sum_{\ell=1}^{|J|/2}
(u_{j_{2\ell}}-u_{j_{2\ell-1}})}.
\tag{1}
$$
The empty subset contributes $1$. This follows by expanding
$$
\mathbb E\prod_{i=1}^{m}(1+a s_iX_{u_i})
$$
and applying the spin moments. The cylinder event imposes no additional hidden-state observation: its adaptive decisions are already fixed by its sign prefix.

This is a formula for a **fixed realized cylinder**, not an assertion that the same moment identity holds unconditionally at arbitrary adaptive stopping times.

For $n\ge u_m+1$, the posterior action gain after that cylinder, with no additional released labels, is
$$
w_n=
\frac{1}{D_m}
\sum_{\substack{J\subseteq[m]\\ |J|\ {\rm odd}}}
a^{|J|+1}s_J
\rho^{
\sum_{\ell=1}^{(|J|-1)/2}
(u_{j_{2\ell}}-u_{j_{2\ell-1}})
+n-u_{j_{|J|}}}.
\tag{2}
$$
It follows from the same expansion after multiplying by $aX_n$. Since $a<1$, all emission likelihood factors are strictly positive, and hence $D_m>0$.

## 2. Uniform density and posterior bounds

Put $x=B^2r$. Since $H_B\ge6B^3$,
$$
B^2r
<
\frac{B^2}{16(B+2)H_B}
\le\frac{1}{96B(B+2)}
\le\frac1{288}.
$$
In particular $x<1/2$ and $r<1/2$.

Every paired gap in an even subset has length at least one. Using $g=a^2<1$, (1) gives
$$
|D_m-1|
\le
\delta_B(r):=
\sum_{q=1}^{\lfloor B/2\rfloor}
\binom{B}{2q}r^q.
$$
For each $q$, $\binom{B}{2q}\le B^{2q}$. Thus
$$
\delta_B(r)
\le\sum_{q\ge1}(B^2r)^q
=\frac{x}{1-x}
\le2B^2r.
\tag{3}
$$
Consequently $D_m\le1+\delta_B(r)$. The sharper proposed density bound with $(g_+r)^q$ also follows whenever $g\le g_+$.

For $m\ge1$, isolate the latest singleton $J=\{m\}$ in (2). Its unnormalized contribution is
$$
g s_m\rho^{n-u_m}.
$$
Each older singleton has $n-u_i\ge2$. For an odd subset of size $2q+1$, its $q$ internal paired gaps contribute at least $q$ powers of $r$, and $n-u_{j_{2q+1}}\ge1$. Summing absolute values from $n=u_m+1$ to infinity, dividing by $gr$, and again using $g\le1$ gives the uniform remainder
$$
P_B(r):=
\frac{(B-1)r+
\displaystyle\sum_{q=1}^{\lfloor(B-1)/2\rfloor}
\binom{B}{2q+1}r^q}
{1-r}.
\tag{4}
$$
The corresponding sharper expression with $(g_+r)^q$ is valid when $g\le g_+$.

To bound (4), use $1/(1-r)\le2$, $\binom{B}{2q+1}\le B^{2q+1}$, and $x<1/2$:
$$
\begin{aligned}
P_B(r)
&\le 2\left[(B-1)r+B\sum_{q\ge1}x^q\right]\\
&\le 2Br+2B\frac{x}{1-x}\\
&\le 2Br+4B^3r.
\end{aligned}
\tag{5}
$$
This includes $B=1$, where the actual remainder is zero.

The infinite positive-part tail of the latest singleton equals
$$
G_0=\frac{gr}{1-r^2}
\quad\text{if its label is zero},\qquad
G_1=\frac{gr^2}{1-r^2}
\quad\text{if its label is one}.
\tag{6}
$$
A finite horizon or a promotion later than $u_m+1$ can only shorten these tails.

## 3. Bellman envelope, including a same-step query

For a current hidden-spin mean $x$, the posterior after observing query sign $s$ is
$$
\psi_s(x)=\frac{x+as}{1+asx},
\qquad
\mathbb P(S=s\mid x)=\frac{1+asx}{2}.
$$
Direct calculation yields
$$
\mathbb E[\psi_S(x)]=x,\qquad
\mathbb E|\psi_S(x)|=\max(|x|,a).
$$
Using $z^+=(z+|z|)/2$, for any $j\ge1$,
$$
\mathbb E[(a\rho^j\psi_S(x))^+]-(a\rho^jx)^+
=\frac{gr^j}{2}\left(1-\frac{|x|}{a}\right)^+.
\tag{7}
$$

At time $t$, after all earlier labels have released and before a possible query at $t$, define the no-more-query potential
$$
F_t(x)=\sum_{j=0}^{T-t}(a\rho^jx)^+,
\qquad F_{T+1}=0.
$$
Let $W_{t,b}(x)$ be the maximal expected future gain with $b$ queries available. We prove, by backward induction simultaneously over $t$ and $b$, that
$$
W_{t,b}(x)\le F_t(x)+b v_1,
\qquad
v_1:=\frac{gr}{2(1-r)}.
\tag{8}
$$

The result is immediate at $T+1$. At time $t$, the current action contributes at most $(ax)^+$. If no query is made, the next mean is $\rho x$, and induction bounds the continuation by $F_{t+1}(\rho x)+bv_1$. If a query is made, its label releases at $t+1$, so the next mean is $\rho\psi_S(x)$. Induction bounds the continuation by
$$
\mathbb E F_{t+1}(\rho\psi_S(x))+(b-1)v_1.
$$
By (7), the expected potential increase over $F_{t+1}(\rho x)$ is at most
$$
\sum_{j=1}^{T-t}\frac{gr^j}{2}\le v_1.
$$
Both branches therefore satisfy (8), since
$$
(ax)^++F_{t+1}(\rho x)=F_t(x).
$$

The query branch includes a query made on the first-promotion step: its label is unavailable to that step's action and consumes one of the remaining query slots. Because action choices do not affect observations and switching costs are zero, the envelope also allows arbitrary rollback and later re-promotion.

## 4. First-promotion continuation bounds

Consider a first-promotion leaf with $m\ge1$ released labels, latest label $y$, and $n=B-m$ possible remaining queries, including any same-step query. Combining (2), (5), (6), and (8), its conditional continuation value $V(h)$ satisfies
$$
\frac{D_m V(h)}{gr}
\le
\frac{G_y}{gr}+P_B(r)
+\frac{(1+\delta_B(r))n}{2(1-r)}.
\tag{9}
$$
Multiplication by $D_m$ is deliberate: it removes the posterior denominator before the density upper bound is used.

For $r<1/2$,
$$
\frac{G_0}{gr}-1=\frac{r^2}{1-r^2}\le2r,
\qquad
\frac{G_1}{gr}=\frac{r}{1-r^2}\le2r.
$$
Also,
$$
\begin{aligned}
\frac{n}{2}\left(\frac{1+\delta_B}{1-r}-1\right)
&=\frac{n(\delta_B+r)}{2(1-r)}\\
&\le B(\delta_B+r)\\
&\le 2B^3r+Br.
\end{aligned}
$$
Using (5), the total correction in (9) is at most
$$
2r+(2Br+4B^3r)+(2B^3r+Br)
=H_Br.
$$
Thus
$$
\frac{D_m V(h)}{gr}
\le \mathbf 1_{\{y=0\}}+\frac n2+H_Br.
\tag{10}
$$

For a leaf with $m=0$, the hidden mean is zero before any query. Equation (8) gives
$$
\frac{V(h)}{gr}
\le\frac{B}{2(1-r)}
\le\frac B2+Br.
\tag{11}
$$
This covers a same-step query because it is included among the $B$ available slots. The inequalities also cover $B=1$.

## 5. Null mixture, leaf summation, and private randomization

Let
$$
Q=\frac{\mathrm{IID}+\nu_1+\cdots+\nu_B}{B+1}.
$$
For a fixed cylinder of $m$ released labels containing $z$ zeros,
$$
Q(h)=2^{-m}\frac{B+1-m+2z}{B+1}.
\tag{12}
$$
Indeed, for $j>m$, $\nu_j$ assigns the fair-cylinder mass. For $j\le m$, it assigns twice that mass if label $j$ is zero, and zero otherwise. Marginalizing an unreleased same-step label contributes no extra factor. Equations (1) and (12) give
$$
\frac{\mathbb P_A(h)}{Q(h)}
=\frac{(B+1)D_m}{B+1-m+2z}.
\tag{13}
$$

Fix a private seed. First-promotion leaves are disjoint. Before first promotion, gain is zero; conditional gain on leaf $h$ is at most $V(h)$. Therefore
$$
\operatorname{gain}(\text{seed})
\le
\sum_h\mathbb P_A(h)V(h)
\le R_Q(\text{seed})\,
\max_h\frac{\mathbb P_A(h)V(h)}{Q(h)}.
\tag{14}
$$
The last maximum is over possible first-promotion leaves; non-promotion contributes zero.

For $m\ge1$, put $n=B-m$. If the latest label is zero, then $z\ge1$, and the leading term from (10) and (13) is bounded by
$$
\frac{B+1}{n+3}\left(1+\frac n2\right)
=
\frac{(B+1)(n+2)}{2(n+3)}
\le
\frac{(B+1)^2}{2(B+2)}
=:C_B,
\tag{15}
$$
because $0\le n\le B-1$. If the latest label is one, then $z\ge0$, and its leading term is at most
$$
\frac{B+1}{n+1}\frac n2
\le\frac{B^2-1}{2B}
\le C_B.
\tag{16}
$$
The likelihood prefactor multiplying the $H_Br$ remainder is at most $B+1$. For $m=0$, (11) gives leading term $B/2\le C_B$, and its remainder $Br$ is also at most $(B+1)H_Br$. Therefore
$$
\max_h\frac{\mathbb P_A(h)V(h)}{Q(h)}
\le gr\,[C_B+(B+1)H_Br].
\tag{17}
$$

The IID version uses the cylinder ratio $D_m$. From (10)-(11), its maximum is at most
$$
gr\,[I_B+H_Br],\qquad I_B:=\frac{B+1}{2}.
\tag{18}
$$

Integrate (14) and its IID analogue over the independent private seed. **No conditional feasibility given the seed is assumed.** The unconditioned $Q$-risk is the average of the risks under its admissible components, so it is at most $\alpha$ for a causal-feasible learner. The unconditioned IID risk is at most $\alpha$ for an IID-feasible learner. Taking suprema gives
$$
\operatorname{VOI}_{\rm causal}
\le \alpha gr[C_B+(B+1)H_Br],
\qquad
\operatorname{VOI}_{\rm IID}
\le \alpha gr[I_B+H_Br].
\tag{19}
$$

## 6. IID witness and truncation

For $B\ge2$, query at time $1$, promote at time $2$ exactly when the first label is zero, and otherwise never promote. On the promotion branch, make the remaining queries at
$$
5,8,\ldots,3B-1,
$$
and choose the action with positive current posterior gain. The IID promotion risk is $1/2$. The alternative promotion probability is also $1/2$, by stationarity and symmetry.

Conditional on the first label being zero, the action gain at time $2$ is $gr$. At the query at time $5$, the prior spin mean has magnitude $ar^4$. Equation (7), with $j=1$, gives an incremental expected positive-part gain at time $6$ of
$$
\frac{gr}{2}(1-r^4).
$$

For each subsequent query, the previous query was three steps earlier. Its prior mean has magnitude at most $r^3<a$, since $r<1/2$ and $a>\sqrt{2/5}>1/2$. At the time-5 query its prior mean also has magnitude below $a$. Hence the identity $\mathbb E|\psi_S(x)|=a$, valid when $|x|<a$, implies that each subsequent query has
$$
\mathbb E\!\left[\frac{|x|}{a}\,\middle|\,Y_1=0\right]=r^3.
$$
Equation (7) gives an incremental expected gain $gr(1-r^3)/2$ at its release time.

These release times are distinct, and each increment is no larger than the full nonnegative positive-part action value at that time. They therefore add to the time-2 gain without double counting. The last query is at $3B-1$ and releases at $3B$, so $T\ge3B$ includes every counted action. If $\zeta_T$ is this pure plan's alternative gain divided by its IID risk, then its two branch probabilities $1/2$ cancel and
$$
\frac{\zeta_T}{gr}
\ge
\frac{B+1}{2}
-\frac{r^4+(B-2)r^3}{2}.
\tag{20}
$$
For $B=1$, use only the first query and promotion at time $2$; then
$$
\frac{\zeta_T}{gr}\ge1=I_1.
\tag{21}
$$
Mixing the witness with never promoting, with witness probability $2\alpha$, makes its IID risk exactly $\alpha$. Thus
$$
\operatorname{VOI}_{\rm IID}\ge\alpha\zeta_T.
\tag{22}
$$

## 7. Constants and final division

For $B\ge2$, since $0<r<1$,
$$
\frac{r^4+(B-2)r^3}{2}
\le \frac{(B-1)r}{2}
<
\frac{B-1}{32(B+2)H_B}
\le\frac{B+1}{16(B+2)}.
\tag{23}
$$
For $B=1$, the witness remainder in (21) is zero. The causal-certificate remainder obeys
$$
(B+1)H_Br<\frac{B+1}{16(B+2)}.
\tag{24}
$$
Since
$$
I_B-C_B
=\frac{B+1}{2(B+2)},
$$
equations (19), (22), (23), and (24) yield
$$
\Gamma
\ge\alpha gr
\left[
\frac{B+1}{2(B+2)}
-\frac{2(B+1)}{16(B+2)}
\right]
=
\alpha gr\,\frac{3(B+1)}{8(B+2)}.
\tag{25}
$$
In particular the witness makes $\operatorname{VOI}_{\rm IID}>0$. Moreover,
$$
I_B+H_Br
<
\frac{B+1}{2}+\frac1{16(B+2)}
\le B+1.
$$
Dividing the positive lower bound (25) by the IID upper bound in (19) gives
$$
\rho_\Gamma
=\frac{\Gamma}{\operatorname{VOI}_{\rm IID}}
\ge\frac{3}{8(B+2)}.
$$
This completes the candidate argument. $\square$

## Simultaneous finite-budget corollary

For $B\ge1$, $H_B\le11B^3$ and $B+2\le3B$, hence
$$
r_0(B)\ge\frac1{528B^4}.
$$
For $0<r<1/1056$, define
$$
\bar B(r)=\left\lfloor(1056r)^{-1/4}\right\rfloor\ge1.
$$
Then every $1\le B\le\bar B(r)$ has $r<r_0(B)$. Consequently, for every $T\ge3\bar B(r)$,
$$
\rho_\Gamma(T,B,\alpha)\ge\frac{3}{8(\bar B(r)+2)}.
$$
This supplies an explicit finite budget range on an open parameter region; it does not establish an independent empirical definition of label scarcity.

## Remaining review obligations

- Independently review the new arbitrary-budget proof, especially the interpretation of predictable query actions and the admissibility of the $\nu_j$ nulls.
- Confirm that the exact model's filtration and payoff conventions match the assumptions above.
- Apply the other locked GO criteria separately, including the required S-2 review, numerical consistency, and novelty assessment. This proof alone does not establish the overall publication decision.
