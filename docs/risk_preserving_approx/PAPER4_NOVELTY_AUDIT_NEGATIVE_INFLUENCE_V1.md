# ShiftLab Paper 4: source-matched novelty decision and a falsifiable theorem programme

**Dated:** 2026-11-09. **Scope:** full-history causal-null binary labels, known alternative HMM, delayed requests, hard pathwise query budget, first-promotion risk; no repository was modified. **Status:** prior-art decision + independently checked mathematical derivation; *not a completed novel algorithm or paper*.

## 1. Firm novelty decisions

The proposed *value-sensitive safe pruning theorem* is an instance of admissible value-bound branch-and-bound: permanently take a safe action when an admissible lower bound shows continuation offers at most epsilon of gain. The extra observation that removing promotions cannot increase first-promotion risk is a direct pathwise monotonicity argument. It cannot be submitted as a stand-alone new theorem. Key source-level comparisons:

- Online POMDP planning survey: https://pmc.ncbi.nlm.nih.gov/articles/PMC2748358/ (admissible upper/lower action-value bounds and branch-and-bound).
- Barenboim and Indelman, NeurIPS 2023: https://proceedings.neurips.cc/paper_files/paper/2023/hash/fc6bd0eef19459655d5b097af783661d-Abstract-Conference.html (deterministic approximate-to-exact value bounds).
- Barenboim et al., hypothesis pruning with value-loss guarantees: https://cris.technion.ac.il/en/publications/data-association-aware-pomdp-planning-with-hypothesis-pruning-per/ (explicit pruning based on tolerated value loss).
- Andriushchenko et al., JAIR 2025: https://www.jair.org/index.php/jair/article/view/16593 (counterexample-guided finite-state controller synthesis for constrained POMDPs).
- Heck et al., AAAI 2026: https://ojs.aaai.org/index.php/AAAI/article/view/40944 (robust structurally constrained policy synthesis via SAT/probabilistic model checking).
- Krale et al., NeurIPS 2025: https://proceedings.neurips.cc/paper_files/paper/2025/hash/52c74b3df11d1c1802333d866e844dcf-Abstract-Conference.html (robust-POMDP policy evaluation and optimality bounds).
- Burkhardt et al., IJCAI 2026: https://ijcai.org/proceedings/2026/244 (efficient approximate DNF model counting; cannot claim a generic DNF counter is novel).
- ShiftLab prior exact monotonicity boundary: https://github.com/nl2992/shiftlab/blob/main/docs/switching_monotone_promotion_reduction_v1.md .
- ShiftLab prior counterexample: https://github.com/nl2992/shiftlab/blob/main/docs/switching_monotone_class_separation_v1.md .
- ShiftLab prior pruning failure: https://github.com/nl2992/shiftlab/blob/research/risk-preserving-switching-approx-2026-10-29/docs/risk_preserving_approx/RESEARCH_LEDGER.md .

**Therefore:** no main-track novelty from: value-based safe pruning by itself; conventional finite-state-controller synthesis + validation; one-sided-POSG scalarization; a standard full-history best-response Bellman recursion; exact monotone null-to-fair-IID reduction; or approximate counting of monotone DNF promotions alone.

## 2. A more specific quantitative mathematical result to exploit

Let `T` potential binary labels form a complete tape `y in {0,1}^T`. A deterministic, nonanticipating learner policy with pre-fixed query budget and delayed release induces a Boolean event `g(y)=1` iff it ever promotes a challenger. The causal null may choose the conditional probability `p_t` of a queried `Y_t=1` after seeing its own full past and the public learner choice, with `p_t in [0,1/2]`; unqueried labels can be extended to the complete potential tape without changing the learner's decisions.

For a prefix `h`, define `v(h)` as the maximum causal-null probability of eventual promotion conditional on that prefix, and define `f(h)` as the fair-IID-Bernoulli(1/2) conditional probability of promotion. At terminal tapes, `v(y)=f(y)=g(y)`. Backward recursion:

```
v(h) = max{ v(h0), [v(h0)+v(h1)]/2 }
f(h) = [f(h0)+f(h1)]/2.
```

These expressions correctly permit the full-history adversary to choose `p=0` or `p=1/2` separately at every prefix. At an event not queried by the policy, the potential bit does not change `g`, so the two continuation values agree.

### Proposition A: exact causal-risk surcharge identity

Define the negative directional continuation influence

`I_minus(h) = [v(h0)-v(h1)]_+`.

Then

`R_causal(g) - R_IID(g) = sum_{t=1}^T 2^{-t} sum_{h in {0,1}^{t-1}} I_minus(h)`.

**Proof:** At each prefix, `v(h)=(v(h0)+v(h1))/2 + I_minus(h)/2`; subtract the fair recursion and repeatedly expand the resulting difference under fair-prefix averaging. All terminal differences vanish. This is an exact Bellman algebra identity, not yet a standalone novelty claim.

**Interpretation:** the entire price of the adaptive null, versus fair IID calibration, is supported on branch inversions where a negative result makes promotion more likely under the worst remaining null response. This suggests an *inversion-frontier* rather than a generic full response-tree certificate.

### Proposition B: upper-closure guarantee for a pure plan

For the promotion set `A={y:g(y)=1}`, let its upward hull be `A_up={x: exists y in A with y<=x coordinatewise}`. Then

`R_IID(A) <= R_causal(A) <= P_IID(A_up)`, hence

`R_causal(A) - R_IID(A) <= P_IID(A_up\A)`.

**Proof:** `p_t<=1/2` permits common-uniform coupling with iid fair bits `Z_t` such that `Y_t<=Z_t` pathwise, even if `p_t` adapts to prior outcomes and public actions. The increasing event `A_up` dominates `A`; under the common coupling `1_A(Y)<=1_{A_up}(Y)<=1_{A_up}(Z)`. IID fair is an admissible null, giving the lower bound.

This is a quantitative extension of the repository's already-proved exact monotonicity boundary, but it follows directly from standard stochastic domination. It should be described as an *input certificate*, not claimed novel on its own.

### Proposition C: safety repair and unrestricted-oracle cost certificate

Assume an IID-relaxed optimizer produces policy `pi` with `R_IID(pi)<=alpha` and `C_alt(pi)<=V_IID+eps_opt`, where `V_IID<=V_full` since fair IID is a member of the unrestricted causal-null family. For each **pure plan in the support**, obtain a valid upper-hull or refined risk certificate and average these upper bounds with the fixed ex-ante mixture weights, yielding `r_bar>=R_causal(pi)`. Let `pi_0` be a never-promote policy, with cost `C_0`, and `q=min(1,alpha/r_bar)` (take `q=1` if `r_bar=0`). Root-mix `pi` with probability `q` and `pi_0` otherwise. Then

`R_causal(pi_repaired)<=alpha`, and

`0 <= C_alt(pi_repaired)-V_full <= eps_opt+(1-q)*(C_0-C_alt(pi))`.

**Proof:** The risk of the independent root mixture is at most `q*r_bar`, since the safe arm has zero first-promotion risk; cost is linear in the root lottery. Since `V_full>=V_IID` and the IID policy has suboptimality at most `eps_opt`, subtract the lower bound to obtain the claim.

**Caveats:** (a) the resulting bound can be vacuous if the hull is too conservative; (b) `eps_opt` must be certified against the unrestricted *IID-relaxed* optimization, not merely the best finite controller; (c) externally verifying a policy's empirical false-promotion frequency does not substitute for `r_bar`.

**Critical randomization counterexample:** Do NOT construct a risk certificate from only the *marginal randomized promotion map* `E_U[g_U(y)]` when the null can observe public query actions. Suppose the learner flips a fair private root coin `U`. Under U=0 it queries at both events 1 and 2 and promotes after receiving Y2 iff Y2=0. Under U=1 it queries only at event 2 and promotes after receiving Y2 iff Y2=1. The null observes whether event 1 was queried, and can set `p_2=0` on the first branch and `p_2=1/2` on the second. True robust risk is `(1 + 1/2)/2 = 3/4`, whereas the marginal promotion function is constant `1/2` on every complete label tape. Its monotone hull is also `1/2`. Therefore its supposed `1/2` certificate is INVALID. Per-pure-plan bounds averaged over the ex-ante root coin remain safe. This distinction matters in a game where public actions leak learner randomness.

## 3. Exhaustive arithmetic check

The accompanying script `shiftlab_paper4_risk_tax_check.py` enumerated all Boolean first-promotion events for T=1,2,3 (4+16+256 events). All passed the exact surcharge identity and the monotone-hull upper bound.

Concrete T=3 example `A={010,101}`:

- IID fair risk: `2/8 = 0.25`.
- Exact causal-null risk: `0.5`.
- Monotone-hull risk: `5/8 = 0.625`.
- Exact nonmonotonicity surcharge: `0.25`.

The hull is conservative by `0.125`, which supplies a toy separating a coarse certificate from a refined adversarial-risk calculation.

Out of the 256 three-bit events, the hull bound is exact in 248. This is a finite enumerative observation, not an empirical generalization.

## 4. What might constitute a new paper

**Research hypothesis: inversion-frontier risk certification and optimization.** Instead of enumerating every history-adaptive causal-null response, compile each candidate learner controller or promotion policy into a succinct symbolic decision structure. Compute conservative bounds on the negative directional continuation influences at *unresolved branch inversions*, and refine only the proof obligations that materially affect `r_bar`. Couple that verifier to an IID-relaxed economic optimizer and a global lower-bound certificate.

The new result would have to establish all of:

1. Sound full-history causal risk for delayed adaptive querying (including opponent visibility of pending labels and public actions).
2. A quantitative approximation bound relative to the unrestricted robust two-law optimum—not the best compressed controller.
3. A new, proved **output-sensitive** resource bound in terms of a pre-defined inversion-frontier or certificate complexity that avoids materializing the entire causal-response history tree; all costs of discovering that frontier must count.
4. An actual end-to-end speed or memory win over ShiftLab's exact first-promotion decomposition and source-matched robust-POMDP evaluation/CEGAR baselines.
5. No reliance on a uniform-polynomial claim in horizon or budget: IID-relaxed POMDP optimization itself can remain hard. Write complexity relative to an explicit IID-oracle cost unless a separately proved tractable subfamily is specified.

Why the proposed *algorithm* could have novelty: the strong prior methods solve generic robust POMDPs or synthesize compact policies but do not, in the audited abstracts/source passages, supply this specific **negative-influence certificate + unrestricted-oracle economic gap** with a verified frontier-size advantage under the full causal-null contract. This is a candidate technical gap only; absence of an identical statement is not proof of publication originality.

## 5. Immediate priority tests and hard exits

**G1 (novelty):** formal source-matched reduction to Krale et al. NeurIPS 2025 robust-POMDP policy evaluation, JAIR 2025 oracle-guided synthesis, AAAI 2026 constrained/robust SAT model checking, POMDP branch-and-bound and symbolic model checking. If the inversion-frontier method is their Bellman evaluator plus pruning, CLOSE THE IDEA.

**G2 (proof):** write a proposed theorem with explicit controller representation, admissible interval bounds, hidden pending-outcome treatment, root-randomization visibility, certificate complexity parameter, and exact error propagation. Prove it on T<=3 and exhibit counterexamples to unsound state merging and marginalization.

**G3 (algorithmic screen):** implement a pure verification prototype first; compare costs with a full adversarial risk evaluator on exact T=5/6 cases and T=8, B=3. Do not optimize controller parameters while the verifier remains exponential. Run a deliberately nonmonotone reversal case as well as a monotone event.

**G4 (unrestricted-oracle bound):** connect a mathematically valid IID-relaxation *global* lower bound, and report `U-L` for repaired policies; if the gap cannot be materially reduced, the claimed approximate optimality is vacuous.

**G5 (new confirmation):** only after proof/novelty/synthetic passes, freeze new instances and compare independently to strong methods. Source-matched CPU resources, same null, same query cap and delay, exact risk and independent policy evaluation are mandatory.

### Proposed research decision

- **Original value-sensitive pruning:** NO-GO as a standalone theorem; known branch-and-bound principle.
- **Pure monotone risk identity:** ALREADY PROVED IN SHIFT LAB; not new.
- **Exact negative-influence surcharge identity and root repair:** mathematically justified, but routine Bellman/coupling ingredients; useful as certificates, not yet main-track novelty.
- **Inversion-frontier optimizer with certified global cost/risk bounds and a new end-to-end resource theorem:** CONDITIONAL GO, theory-first. The missing theorem is the resource/representation result, not the risk algebra.

The current work does *not* establish any new winning optimizer. This is the honest next claim to try to prove, rather than another unqualified novelty assertion.
