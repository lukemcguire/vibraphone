# Roadmap: Vibraphone

## Milestones

- **v0.1.0 Initial Release** -- Phases 1-9 (shipped 2026-02-17)
- **v0.1.1 Slash Commands** -- Phases 10-12 (in progress)

## Phases

<details>
<summary>v0.1.0 Initial Release (Phases 1-9) -- SHIPPED 2026-02-17</summary>

- [x] Phase 1: Package Foundation (3/3 plans) -- completed 2026-02-16
- [x] Phase 2: Configuration & Core Utilities (3/3 plans) -- completed 2026-02-16
- [x] Phase 3: Task Management Tools (5/5 plans) -- completed 2026-02-16
- [x] Phase 4: Worktree & Session Tools (4/4 plans) -- completed 2026-02-17
- [x] Phase 5: Quality Gate Tools (5/5 plans) -- completed 2026-02-17
- [x] Phase 6: Bridge & Stack Tools (4/4 plans) -- completed 2026-02-17
- [x] Phase 7: Scaffolding & Templates (5/5 plans) -- completed 2026-02-17
- [x] Phase 8: Quality Gate Worktree Integration (1/1 plan) -- completed 2026-02-17
- [x] Phase 9: Testing & Documentation (5/5 plans) -- completed 2026-02-17

**Delivered:** 18 MCP tools, 4,388 LOC Python, 413 tests, complete documentation

</details>

<details>
<summary>v0.1.1 Slash Commands (Phases 10-12) -- IN PROGRESS</summary>

- [x] Phase 10: Command Infrastructure (4/4 plans) -- completed 2026-02-19

  **Goal:** Establish /v slash command installation mechanism with CLI command and
  bundled v.md file.

  **Plans:**
  - [x] 10-01-PLAN.md -- Create commands/ package with v.md slash command file
  - [x] 10-02-PLAN.md -- Add setup-commands CLI subcommand with unit tests
  - [x] 10-03-PLAN.md -- Clean up obsolete skill-based implementation
  - [x] 10-04-PLAN.md -- Add /v command documentation to README.md (gap closure)
- [ ] Phase 11: Command Documentation (0/4 plans) -- in progress

  **Goal:** Document all /v slash commands in v.md with correct MCP tool calling
  convention. Covers core workflow commands (list, next, start, test, lint,
  format, review, commit, merge, cleanup, complete, recover, status, health)
  and dict-heavy commands (init, configure-stack, import-plan).

  **Requirements:** SLASH-01, SLASH-02, SLASH-04

  **Plans:**
  - [ ] 11-01-PLAN.md -- Document structure + Quick Reference + dict-heavy commands
  - [ ] 11-02-PLAN.md -- Start Work + Run Quality commands with full coverage
  - [ ] 11-03-PLAN.md -- Commit & Merge + Session Management + Troubleshooting
  - [ ] 11-04-PLAN.md -- Final verification checkpoint
- [ ] Phase 12: Tool Hardening (0/8 plans) -- pending

**Goal:** Agents invoke vibraphone tools reliably via /v commands -- no more
serialization guessing.

**Requirements:**
- SLASH-01: Add /v commands for core workflow tools
- SLASH-02: Add /v commands for dict-heavy tools
- SLASH-03: Investigate stringification bug -- root cause and fix
- SLASH-04: Documentation update for /v commands
- SLASH-05: `vibraphone setup-commands` CLI to install slash commands
- SLASH-06: Clean up existing artifacts (skills/v/, vibraphone-cli)

</details>

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Package Foundation | v0.1.0 | 3/3 | Complete | 2026-02-16 |
| 2. Configuration & Core Utilities | v0.1.0 | 3/3 | Complete | 2026-02-16 |
| 3. Task Management Tools | v0.1.0 | 5/5 | Complete | 2026-02-16 |
| 4. Worktree & Session Tools | v0.1.0 | 4/4 | Complete | 2026-02-17 |
| 5. Quality Gate Tools | v0.1.0 | 5/5 | Complete | 2026-02-17 |
| 6. Bridge & Stack Tools | v0.1.0 | 4/4 | Complete | 2026-02-17 |
| 7. Scaffolding & Templates | v0.1.0 | 5/5 | Complete | 2026-02-17 |
| 8. Quality Gate Worktree Integration | v0.1.0 | 1/1 | Complete | 2026-02-17 |
| 9. Testing & Documentation | v0.1.0 | 5/5 | Complete | 2026-02-17 |
| 10. Command Infrastructure | v0.1.1 | Complete | 2026-02-19 | 2026-02-19 |
| 11. Command Documentation | v0.1.1 | 0/4 | In Progress | -- |
| 12. Tool Hardening | v0.1.1 | 0/8 | Pending | -- |

---

*Full phase details archived in `.planning/milestones/v0.1.0-ROADMAP.md`*
*v0.1.1 research: `.planning/research/SUMMARY.md`*
