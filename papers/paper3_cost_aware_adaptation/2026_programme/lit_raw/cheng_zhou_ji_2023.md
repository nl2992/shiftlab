# Cheng, Zhou, Ji, Understanding the Role of Feedback in Online Learning with Switching Costs
ICML 2023, PMLR 202:5521-5543. https://proceedings.mlr.press/v202/cheng23f.html ; PDF downloaded and text-extracted 2026-11-09.
Access: abstract page read; PDF extracted but theorem/assumption detail relies on the repo's primary-text audit docs/switching_cheng_audit_v1.md (SHA recorded); not re-read line by line.
Facts: oblivious adversary, K actions, unit switching cost; minimax regret T^(2/3) (bandit), sqrt(T) (full info); total observation budget B gives about T sqrt(K/B) (soft-Theta); batched mirror descent plus shrinking dartboard. Regret is against the best FIXED action.
Not covered: delay queue, dynamic comparator, time-uniform risk constraint, query price.
