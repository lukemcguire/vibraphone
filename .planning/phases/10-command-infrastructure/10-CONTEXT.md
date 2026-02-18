# Phase 10: Command Infrastructure - Context

**Gathered:** 2026-02-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Establish the `/v` slash command installation mechanism. Create the CLI command
that installs slash commands to the correct location, set up the bundled command
file, and remove obsolete skill-based implementation. Documentation of commands
happens in Phase 11.

</domain>

<decisions>
## Implementation Decisions

### Installation UX

- Minimal output on success: single line with destination path
- Always show restart reminder: "Restart Claude Code for commands to take
  effect"
- Silent overwrite if v.md already exists (no confirmation needed)
- No version info in output (keep it minimal)

### Migration Handling

- No migration code needed - this is a one-time personal cleanup
- Old `~/.claude/skills/v/` directory: user will manually delete
- Old `vibraphone skill install` CLI: remove entirely, no compatibility alias
- No README or placeholder in skills directory

### Error Handling

- Auto-create `~/.claude/commands/` if missing (no error)
- Permission errors: clear error message with path and suggestion
- Missing bundled v.md: clear error indicating corrupt install
- Exit codes: simple (0 = success, 1 = any failure)

### Verification Approach

- No CLI verify flag needed
- setup-commands verifies by checking file exists and is non-empty
- No manual verification steps suggested to user
- Unit tests for: CLI command, file copy, error cases

### Claude's Discretion

- Exact wording of error messages
- Exact wording of success message
- Test file organization

</decisions>

<specifics>
## Specific Ideas

- Keep the CLI experience minimal and reliable - it's infrastructure, not a
  feature users interact with often
- The goal is "just works" - users run it once and forget about it

</specifics>

<deferred>
## Deferred Ideas

None - discussion stayed within phase scope.

</deferred>

---

*Phase: 10-command-infrastructure*
*Context gathered: 2026-02-18*
