# Literature review for Paper 3 (F3 shield), 2026-11-19

All entries below were checked against arXiv / publisher / DBLP pages on 2026-11-19.

## Existing citations re-verified
- hu2026prudent (Prudent-Banker, arXiv:2605.23351, May 2026): conservative adversarial bandits with delays; expected pseudo-regret, no switching fee, rollback or label budget. Our closest competitor in theory.
- lamaakal2026drift2act (Drift2Act, arXiv:2603.08578, ICLR 2026 CAO workshop): drift controller with window-risk certificate.
- lindon2026design (arXiv:2603.25971, v2 May 2026): design-based anytime-valid CS with delayed outcomes.
- digalakis2025challenger (arXiv:2512.18390, v2 Jul 2026): when to switch to a challenger; regret vs foresight oracle.

## Added to the related-work section
| Work | Why relevant | How we differ |
|---|---|---|
| Moradipari et al., NeurIPS 2020, stage-wise conservative linear bandits | per-round baseline constraint | multiplicative reward constraint, immediate feedback |
| Laroche et al., ICML 2019, SPIBB | fall back to baseline where data are scarce | offline certificate, no live rollback |
| Sawarni et al., arXiv:2510.19672, policy learning with abstention | defer to safe default where policies disagree | offline, regret target |
| Zhou, Li, Zhu, arXiv:2610.10393 (Oct 2026), safe meta-policy design | budget on expected number of regressing updates | expectation over updates, offline planning; not pathwise |
| Sadeghian et al., arXiv:2611.02251 (Nov 2026), Retrain/Alert/Rollback | operational rollback framework under drift | empirical only, no harm bound |
| Ramdas, Grünwald, Vovk, Shafer, Stat. Sci. 2023 | survey of anytime-valid inference | background |

## Considered, not added
- Conservative dueling bandits (arXiv:2610.36708): preference feedback, no delays.
- E-SHIFT (arXiv:2510.03839), sequential paired-sample monitoring (arXiv:2611.22886), Who Drifted (arXiv:2606.15474): anytime-valid monitoring/alarms; covered by the existing Podkopaev & Ramdas citation. Could be added if a reviewer asks for more monitoring work.
- Evidence sufficiency under delayed ground truth (arXiv:2604.15740): governance/proxy monitoring, cs.CY.

## Novelty check
No work found that bounds pathwise cumulative harm of a reversible promotion, with switching fees, under delayed, sampled and missing labels, or that proves the rollback and in-transit reserves are necessary. The positioning in the paper still holds. The nearest threats are Prudent-Banker (theory) and Safe Meta-Policy Design (budgeted updates); both are now distinguished explicitly.

## Dataset citations added
UCI DOIs for metro (10.24432/C5X60B), beijing_pm25 (C5JS49), bike (C5W894), appliances (C5VC8G), household power (C58K54), bank (C5K306); OpenML (Vanschoren et al. 2014); elec2 (Harries 1999); criteo (Diemert et al., AdKDD 2017); rialto (Losing et al., ICDM 2016); spam (Katakis et al., KAIS 2010); weather (Elwell & Polikar, IEEE TNN 2011).
