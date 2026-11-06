# P2 related work and benchmark comparison (W2, 2026-11-06)

**Method:** web searches on 2026-11-06. Bibliographic facts (authors, venue, year, scope) were
checked against publisher, proceedings or arXiv pages, listed under Sources. Rows marked † were
read beyond the abstract by a fetch agent. Its claims about later sections are model-extracted
summaries and should be re-read before citation. This is a first verified pass, not an exhaustive
survey. One targeted gap search found no benchmark that combines all of P2's elements; that is
weak evidence of absence, not proof.

## Closest prior work

**Fernández-Barrios et al., arXiv:2609.04388 (Sept 2026), "Candidate Comparability Before Promotion"†**
is the closest. It runs a common-harness comparison of nine update policies for network intrusion
detection, with a conditional-on-past null, an e-process commit rule, delayed-label arms and a fixed
class-balanced label probe. Differences from P2: its probes are random rather than actively queried;
it has no real-data known-null streams (its exchangeable re-draw is synthetic); it has no marginal-null
or serial-dependence analysis; and it does not price labels or switches ("labels are counted, not
priced", per the extracted summary). P2 must cite it and state these differences explicitly.

**Dutta, arXiv:2607.28577 (July 2026), "Forward-Gated Model Replacement in Crypto Markets"†** runs
shadow evaluation on delayed labels with a fixed paired-NLL promotion threshold, and handles
temporal dependence with a block bootstrap. It compares only its own policies, gives no sequential
guarantee, sets no label budget and models no economic cost.

## Benchmark comparison (Table 1 draft)

| Work | Task | Multiple methods, common contract | Anytime-valid methods evaluated | Label budget / active queries | Delayed labels | Temporal dependence / conditional vs marginal null | Known nulls from real data | All-in economic cost |
|---|---|---|---|---|---|---|---|---|
| WILDS (Koh et al., ICML 2021) | OOD robustness, 10 datasets | Yes | No | No | No | No | No | No |
| Wild-Time (Yao et al., NeurIPS D&B 2022) | Temporal shift, 5 datasets | Yes (13 methods) | No | No | No | Temporal shift, not serial dependence | No | No |
| TableShift (Gardner et al., NeurIPS D&B 2023) | Tabular shift, 15 tasks | Yes | No | No | No | No | No | No |
| Failing Loudly (Rabanser et al., NeurIPS 2019) | Shift detection | Yes | No | No | No | No | No | No |
| Label Delay in OCL (Csaba et al., NeurIPS 2024) | Continual learning | Yes | No | No | **Yes** | No | No | Compute only |
| Fernández-Barrios et al. (arXiv 2609.04388, 2026)† | Promotion in intrusion detection | **Yes (9)** | Partly (one e-process variant) | Fixed probe, not active | **Yes** | Conditional null; no serial or marginal analysis | Synthetic only | No |
| Dutta (arXiv 2607.28577, 2026)† | Model replacement in crypto | Own policies only | No | No | **Yes** | Block bootstrap | No | No |
| **P2 (proposed)** | Incumbent–challenger promotion | **Yes (~25)** | **Yes** | **Hard budget, active** | **Yes, swept** | **Both nulls, dependence classes** | **Exchangeable twins** | **Yes: loss + labels + switches** |

## Method sources (comparators and framing)

| Reference | Role in P2 | Verified facts |
|---|---|---|
| Giacomini & White, *Econometrica* 74(6):1545–1578, 2006 | Conditional vs unconditional predictive ability | Proposes tests of both; the conditional nests the unconditional |
| Henzi & Ziegel, *Biometrika* 109(3):647–663, 2022 (correction 109(4)) | Anytime-valid forecast comparison | E-values valid without data-generating assumptions; the authors note lower power |
| Choe & Ramdas, *Operations Research* 72(4):1368–1387, 2024 | Sequential forecaster comparison (comparator `choe_ramdas_eb`) | Confidence sequences and e-processes for a weak "on average" null; Python package `comparecast` |
| Karampatziakis, Mineiro & Ramdas, ICML 2021, PMLR 139:5301–5310 | Gated deployment (comparators `gated_deployment`, `gated_adaptive_range`) | Off-policy CS with a gated-deployment application |
| Podkopaev & Ramdas, ICLR 2022 | Harmful-shift monitoring with delayed labels | Sequential risk tracking via confidence sequences |
| Amoukou et al., NeurIPS 2024 | Label-free harmful-shift detection | Extends Podkopaev–Ramdas with a learned error proxy |
| Xu, Karampatziakis & Mineiro, NeurIPS 2024 | Active, budgeted labelling (`xu_acquisition_only` uses its acquisition) | Expected-proportion label budget; optimal label policy characterised |
| Zrnic & Candès, ICML 2024 (PMLR 235) | Active inference under a label budget | Model-guided labelling with valid CIs |
| Liu, Xia, Stevens & Chen, NeurIPS 2024 (CAMS) | Uncertified active model selection (`cams_adapter`) | Context-aware selection plus active querying; code public |
| Arnold/Gavrilopoulos et al., "Sequential model confidence sets", arXiv 2404.18678 (JRSSB per one aggregator; author order varies across versions) | `SMCS+retain-incumbent` | E-process-based, time-uniform, non-asymptotic MCS |
| Balachandran, arXiv 2609.17560 (2026), DISCERN | `discern_style`, `discern_design_floor` | Zero-label tier plus disagreement-only audited tier with an anytime-valid CS; single author, not peer reviewed |

## Implications for the P2 claim

1. The **gap statement must narrow.** Evaluating promotion policies on a common harness with delayed
   labels is not new (2609.04388). The new part is the combination of real-data known nulls,
   conditional-vs-marginal scoring under dependence, an active hard label budget, and all-in economic
   cost. The headline finding (F8: the validity gate reorders the leaderboard) depends on that combination.
2. Add 2609.04388's ATC/DoC/ADWIN-style label-free policies as context baselines if it is cheap. At
   minimum, discuss why they target a different question.
3. Before submission, rerun the gap search for anything dated after 2026-11-06, and do a manual pass
   on the DISCERN, CAMS and Xu related-work sections.

## Sources

- [Choe & Ramdas, IDEAS/RePEc](https://ideas.repec.org/a/inm/oropre/v72y2024i4p1368-1387.html); [arXiv 2110.00115](https://arxiv.org/abs/2110.00115v6)
- [Henzi & Ziegel, BORIS](https://boris.unibe.ch/166789); [correction](https://boris.unibe.ch/180818/)
- [Podkopaev & Ramdas, arXiv 2110.06177](https://arxiv.org/abs/2110.06177v3); [ICLR poster](https://iclr.cc/virtual/2022/poster/6896)
- [Karampatziakis et al., ICML 2021](https://icml.cc/virtual/2021/spotlight/10472); [mlanthology](https://mlanthology.org/icml/2021/karampatziakis2021icml-offpolicy)
- [Wild-Time, NeurIPS D&B](https://papers.neurips.cc/paper_files/paper/2022/hash/43119db5d59f07cc08fca7ba6820179a-Abstract-Datasets_and_Benchmarks.html)
- [TableShift, arXiv 2312.07577](https://arxiv.org/abs/2312.07577)
- [WILDS, arXiv 2012.07421](https://arxiv.org/abs/2012.07421)
- [Failing Loudly, NeurIPS 2019](https://proceedings.neurips.cc/paper/2019/hash/846c260d715e5b854ffad5f70a516c88-Abstract.html)
- [Label Delay in OCL, NeurIPS 2024](https://neurips.cc/virtual/2024/poster/93776)
- [Amoukou et al., NeurIPS 2024](https://proceedings.neurips.cc/paper_files/paper/2024/hash/e9721921b799b6ea98d37f9e77f1a7fe-Abstract.html)
- [Giacomini & White, Econometric Society](https://econometricsociety.org/publications/econometrica/2006/11/01/tests-conditional-predictive-ability)
- [Sequential model confidence sets, arXiv 2404.18678](https://arxiv.org/abs/2404.18678v2)
- [Xu et al., NeurIPS 2024](https://proceedings.neurips.cc/paper_files/paper/2024/hash/6eb05d8bc6bd7bb6868c64b5802125bd-Abstract.html)
- [CAMS, NeurIPS 2024](https://papers.neurips.cc/paper_files/paper/2024/hash/5966e7c5c017d8449d215faeb1db4173-Abstract-Conference.html)
- [Zrnic & Candès, arXiv 2403.03208](https://arxiv.org/abs/2403.03208)
- [DISCERN, arXiv 2609.17560](https://arxiv.org/pdf/2609.17560)
- [Dutta, arXiv 2607.28577](https://arxiv.org/abs/2607.28577)
- [Fernández-Barrios et al., arXiv 2609.04388](https://arxiv.org/abs/2609.04388)
