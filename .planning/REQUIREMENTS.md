# Requirements: Vibraphone v0.1.1

**Defined:** 2026-02-18
**Core Value:** Agents invoke vibraphone tools reliably via /v commands — no more
serialization guessing.

## v1 Requirements

### Slash Commands

- [x] **SLASH-01**: User can invoke core workflow tools via /v commands (list, next,
  start, test, lint, format, review, commit, merge, cleanup, complete, recover, status,
  health)
- [x] **SLASH-02**: User can invoke dict-heavy tools via /v commands (init,
  configure-stack, import-plan) with proper parameter handling
- [x] **SLASH-03**: Stringification bug is investigated, root cause identified, and fixed
  or documented
- [x] **SLASH-04**: Documentation includes /v command usage (README update, SKILL.md
  disposition)
- [x] **SLASH-05**: User can run `vibraphone setup-commands` to install /v commands to
  ~/.claude/commands/v/
- [x] **SLASH-06**: Existing artifacts (skills/v/, vibraphone-cli) are cleaned up or
  repurposed with clear migration path

## Out of Scope

| Feature | Reason |
|---------|--------|
| PyPI publishing | Git/local install sufficient for now |
| Full CLI interface | MCP server remains primary interface |
| Commands for all 18 tools | Focus on workflow + dict-heavy; others can be added later |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SLASH-01 | Phase 10 | Complete |
| SLASH-02 | Phase 10 | Complete |
| SLASH-03 | Phase 10 | Complete |
| SLASH-04 | Phase 10 | Complete |
| SLASH-05 | Phase 10 | Complete |
| SLASH-06 | Phase 10 | Complete |

**Coverage:**

- v1 requirements: 6 total
- Mapped to phases: 6
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-18*
*Last updated: 2026-02-19 after plan 10-04 completion*
