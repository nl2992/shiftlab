# Blockers (verified)

| ID | Blocker | Verification | Impact | Workaround |
|---|---|---|---|---|
| BL-1 | ARIS cross-family reviewer backends (Codex MCP / `spawn_agent`, Oracle, Gemini, `claude-review` MCP) are unavailable in this Claude Code session | No `.aris/reviewer.json`; `reviewer-backends.md` line 22 says the Claude-host default is Codex MCP, and no such MCP tools are loaded | Cannot obtain `cross-family accepted` reviews | Fresh-context native subagents recorded as same-family / provisional (ARIS assurance rule) |
| BL-2 | Some publisher pages block automated fetch (AAAI OJS, bot protection) | HTTP 200 with a bot-protection page (2026-11-09) | Heck et al. AAAI 2026 not read | Record as UNRESOLVED; search for an alternative copy |
