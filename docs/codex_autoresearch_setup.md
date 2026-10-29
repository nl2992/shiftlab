# Independent Codex research setup

Branch: `research/risk-preserving-switching-approx-2026-10-29`, based on
`ec42a2da9fdf59a6cf26970fb19aa9d5fb8973cc` from fetched origin/main.
Checkout: `shiftlab-risk-approx-2026-10-29`, beside the other isolated checkouts.
The governing mission is `risk_preserving_approx/RESEARCH_BRIEF.md`; the original
`research/codex-autoresearch` setup branch remains preserved separately.

## Installed toolkit

Project-local skills live in `.agents/skills/` and are available on the next turn
when working from this checkout. They are not installed in the user's global
Codex configuration. Source revisions and installed skill paths are pinned in
`docs/agent_skills.lock.json`; licenses are in `docs/skill-licenses/`.

- DietrichGebert/ponytail: all six core/review/maintenance skills.
- HKUSTDial/Supervisor-Skills: all twelve research and writing skills.
- wanshuiyin/Auto-claude-code-research-in-sleep (ARIS): 87 Codex skills,
  with shared references and upstream tools/templates under `.aris/upstream/`.

ARIS's helper manifest `.aris/installed-skills-codex.txt` points to this checkout's
`.aris/upstream` absolute path. It is machine-local and ignored. After relocating,
regenerate its one tab-separated line: `repo_root<TAB><absolute .aris/upstream path>`.
PowerShell sessions can instead set `$env:ARIS_REPO` to that absolute path.
ARIS shell examples assume Bash; translate them to PowerShell or use a configured
Bash environment. Python helpers are installed source, not a verified runtime
for every optional provider. External reviewer/API/server credentials have not
been configured or exercised. Same-family reviews remain provisional.

## Starting research

Work from this checkout. Read AGENTS.md, `docs/research_charter.md`, and
`docs/budgeted_switching_research_goals.md`; preserve the current G1 scope and
existing confirmation restrictions. Read each selected SKILL.md before executing
it. Suggested sequence: HKUST idea-evaluator, focused ARIS novelty-check,
experiment-plan, a bounded registered CPU smoke run, then research-review.
Use `.aris/runs/` for local run state and a unique Codex output directory.
Create an independent environment here with `uv sync` when research begins;
large datasets and ignored artifacts have not been copied from the main checkout.

This commit sets up the toolkit only. No experiment, autonomous research loop,
recurring automation, remote job, or external notification has been launched.
The mission and initial research plan are now recorded in `risk_preserving_approx/`.
Keep initial checks bounded; register each new experiment before execution.
