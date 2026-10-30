# Development grid results (v2; development seeds only, nothing here is confirmation)

## H1: decision-gated ONS (17 configs × 2 label rates; `outputs/hg_v2/h1_dev_search.csv`, `h1_frontier_dev.csv`)
Fresh development seeds (dev worlds 40000+, G3 development stream 41000). Gate and ONS bet depend on resolved labels only, so the Objective-A (Brier) guarantee under H0-A with fixed delay is inherited; decision-awareness is empirical.

**Theory-threshold table (selected rows; harm power / benign FA / null FA / G3-dev power):**
| labels | arm | dev power | benign FA | null FA | G3-dev power |
|---|---|---|---|---|---|
| 10% | HG_unifcap | .579 | .032 | .010 | .229 |
| 10% | ONS | .681 | .090 | .025 | .338 |
| 10% | gated ONS hard w200 | .651 | .058 | .020 | .294 |
| 10% | gated ONS unc k2 | .642 | .052 | .010 | .271 |
| 10% | gated ONS soft a2 b0 | .643 | .049 | .005 | .265 |
| 20% | HG_unifcap | .849 | .097 | .005 | .510 |
| 20% | ONS | .838 | .143 | .030 | .517 |
| 20% | gated ONS hard w200 | .841 | .102 | .010 | .492 |
Gated ONS sits between HG and ONS: it recovers most of ONS's power with false alarms roughly halfway to HG's.

**Matched benign-FA frontier (thresholds swept; empirical operating points, forfeit the theory guarantee).** Best harm power with benign FA ≤ cap, null FA ≤ .07:
| labels | cap | HG_unifcap | ONS | disc_only | gONS hard200 | gONS soft2 | gONS unc2 | gONS multi |
|---|---|---|---|---|---|---|---|---|
| 10% | .02 | .464 | – | .352 | .481 | .453 | .461 | **.506** |
| 10% | .05 | .579 | .503 | .528 | .602 | **.643** | .603 | .608 |
| 10% | .08 | .688 | .641 | .642 | .651 | .685 | **.692** | .647 |
| 20% | .05 | .744 | – | – | **.777** | .735 | .738 | .762 |
| 20% | .08 | .812 | .751 | .737 | **.819** | .794 | .798 | .793 |

**Reading against the pre-registered selection rule (charter).** Rule (ii) — beat ONS at matched benign FA ≤ .05 by ≥ .03: **met** by all gated variants (10%: +.10 to +.14 at cap .05; at 20% ONS cannot reach the cap). Rule (i) — beat HG_unifcap by ≥ .03 in power at the theory threshold at both rates: met at 10% (+.05 to +.07), **not** at 20% (≤ −.01). Against HG at matched FA the gains are small and mixed (+.003 to +.064). So gated ONS is a modest, development-level improvement on ONS and approximately ties HG, not a clear advance over HG. Carried forward to the next stage: hard w200, soft a2 b0, unc k2, multi (30/200). No confirmation claim.

## H2: Brier-guided bets for a decision-cost-null e-process (`outputs/hg_v2/h2_dev_search.csv`)
Tested object: the cost increment (null: conditional decision cost ≤ nominal), uniform-cap bound 5/6, bets from resolved labels only. Roles here are decision-harm roles, so "benign FA" is a false alarm with respect to decision harm. Dev power / benign FA / null FA / G3-dev power:
| labels | arm | dev power | benign FA | null FA | G3-dev power |
|---|---|---|---|---|---|
| 10% | cost e-process (parent, `pp_cost_tight`) | .153 | .011 | .010 | .077 |
| 10% | cost + discounted Kelly | .268 | .017 | .015 | .096 |
| 10% | H2a cost-only ONS | .335 | .032 | .025 | .156 |
| 10% | H2b Brier-guided ONS | .407 | .032 | .015 | .192 |
| 10% | **H2c Brier-guided discounted Kelly (γ=.995)** | **.424** | .019 | .015 | .179 |
| 20% | cost parent | .354 | .019 | .015 | .133 |
| 20% | cost + discounted Kelly | .511 | .029 | .015 | .223 |
| 20% | H2a | .523 | .046 | .030 | .235 |
| 20% | H2b | .577 | .039 | .030 | .298 |
| 20% | **H2c (γ=.995)** | **.673** | .026 | .015 | .312 |
(Brier references: HG .579 / .849, ONS .681 / .838, but those test the Brier null and pay .03–.14 benign-world false alarms.)

**Reading.** Letting the Brier history choose the bet size for cost evidence raises the cost-valid monitor's power from .153 to .424 (10%) and from .354 to .673 (20%) at false alarms ≤ .03: +0.27 and +0.32 over the cost parent, +0.16 over cost-only discounted Kelly, and +0.09/+0.15 over cost-only ONS. This is the first candidate with a guarantee about the *decision-cost* null that is competitive in power. It still trails Brier-evidence methods on raw power (the information limit the charter warned about); the question for confirmation is whether the decision-harm false-alarm advantage (≤ .03 vs .03–.14) is worth that gap. Development evidence only.

## H3a: ONS against a predictable conditional baseline (`outputs/hg_v2/h3_dev_search.json`)
Null false alarm under AR(1) covariates (ρ = .98, 10% / 20% labels): parent .083 / .167, HG .090 / .280, ONS .217 / .333; baseline-ONS (γ_b = .995, .99) .047–.053 / .163–.167. Dev power (10% / 20%): parent .473 / .708, HG .579 / .849, baseline-ONS .156–.290 / .424–.562.
**Reading: a trade-off, not a fix.** The adaptive baseline brings strong-dependence false alarms back to or below the parent's level at 10% labels and to the parent's level at 20% labels (still ≈ .16, above α), but it gives up roughly half of the power. Detecting change *relative to the recent past* absorbs slow drift by construction. No dependence-robust method with useful power has been found; H3b (blocks) and H3c (HMM regime-aware) are not implemented.
