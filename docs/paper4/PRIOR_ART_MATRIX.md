# Paper 4 prior-art matrix

**Date:** 2026-11-09. "Read" means the primary text was read in this session. "Repo audit" means a
primary-source audit recorded earlier in `docs/risk_preserving_approx/`. "Memory" means cited without
re-reading; it is not decisive.

| Source | Read status | Assumptions / information | Objective & guarantee | Pending outcomes adversary-visible? | Learner randomisation | Implies our result? | Classification |
|---|---|---|---|---|---|---|---|
| Krale, Bovy, Galesloot, Simão, Jansen, *On Evaluating Policies for Robust POMDPs*, NeurIPS 2025 ([link](https://proceedings.neurips.cc/paper_files/paper/2025/hash/52c74b3df11d1c1802333d866e844dcf-Abstract-Conference.html)) | Read, pp. 1–9 | ⟨s,a⟩-rectangular, dynamic uncertainty; nature knows states, agent memory, actions | Policy evaluation via the nature MDP; extreme-point best response (Thm 3); RQMDP/RFIB upper bounds; discounted reward; no constraints; no complexity results | Yes (pending labels are state) | Nature sees memory, which is conservative for private coins | Yes, for the risk identity and verifier | **PROVED EQUIVALENT** (verifier); not applicable to the constrained two-law optimisation |
| Andriushchenko, Češka, Macák, Junges, Katoen, JAIR 2025 ([link](https://www.jair.org/index.php/jair/article/view/16593)) | Abstract only | Coloured MDPs; FSC / program sketches; aleatoric uncertainty | Synthesis via abstraction refinement and counterexample generalisation | Not stated | Not stated | No; it is synthesis within a controller family | **UNRESOLVED** (body not read) |
| Heck et al., AAAI 2026 ([link](https://ojs.aaai.org/index.php/AAAI/article/view/40944)) | Blocked by bot protection | — | Robust structurally constrained policy synthesis | — | — | — | **UNRESOLVED** (not retrieved) |
| Bošanský, Kiekintveld, Lisý, Pěchouček, *Exact double-oracle algorithm for zero-sum extensive-form games with imperfect information*, JAIR 2014 | Memory | Sequence-form EFGs | Restricted-game expansion by best responses; exact convergence | Generic EFG | Sequence form | FCG is a one-sided (null-only) instance | **PRIOR ART** for the FCG pattern; equivalence of the scheme assumed, not re-proved this session |
| Mutapcic & Boyd, *Cutting-set methods for robust convex optimization*, 2009 | Memory | Robust constraints with a worst-case oracle | Cutting-set convergence | — | — | FCG is a cutting-set method | **PRIOR ART** (scheme) |
| Cubuktepe et al., AAAI 2021 | Repo audit (`PRIOR_ART_EQUIVALENCE_AUDIT.md`) | Uncertain POMDP; FSC synthesis then exact robust verification | Synthesis + verification | — | FSC | Synthesis/verification split is established | **UNRESOLVED** for a two-law unrestricted bound |
| Khonji, Jasour & Williams, IJCAI 2019 | Repo audit | Single-law chance-constrained POMDP, constant horizon | FPTAS | No (single law) | — | Not for the causal-null family | **UNRESOLVED** (repo) |
| Horák et al., one-sided POSGs | Repo audit | One-sided partial observation | Value recursion, HSVI | — | — | Scalarised representation equivalent | **PROVED EQUIVALENT** (representation, repo) |
| Online POMDP survey; Barenboim & Indelman NeurIPS 2023; hypothesis pruning; RAO* | Repo + audit note | Admissible-bound branch-and-bound | Value-loss pruning | — | — | Yes, for value-sensitive pruning | **PROVED EQUIVALENT** (pruning), see `PAPER4_VALUE_SHIELD_DECISION_V1.md` |
| ShiftLab Candidate B (IID relaxation + exact verification + root repair) | Repo | Same contract | Exact `[L, U]` interval, no speedup | Yes | Yes | FCG with `K = {IID}` is exactly Candidate B | **PROVED EQUIVALENT** at zero cuts |

**Open novelty question for FCG:** is a null-only cutting-set scheme with an exact product-state
separation oracle, applied to a two-law chance-constrained causal game, already published? Neither the
read sources nor the repo audits establish that it is. Absence is not proof. Reading Bošanský et al. and
any constrained-POMDP cutting-plane work is required before any novelty wording beyond "problem-specific
algorithm".
