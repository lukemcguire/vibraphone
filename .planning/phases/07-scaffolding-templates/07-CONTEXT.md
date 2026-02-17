# Phase 7: Scaffolding & Templates - Context

**Gathered:** 2026-02-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Agent scaffolds vibraphone into any project via init_project MCP tool. Generates vibraphone.yaml config, governance docs (.planning/vibraphone/), and validates prerequisites. Templates bundled in Python wheel via importlib.resources. Creating worktrees and running tasks are separate phases.

</domain>

<decisions>
## Implementation Decisions

### Conflict Handling
- Prompt per file via agent — tool returns conflict info, agent conveys to user, user decides
- Binary options only: Yes/No per file (no "skip all" or "yes to all")
- Always show diff before asking to overwrite
- Non-conflicting files write immediately while waiting for conflict resolution
- No rollback needed — each file decision is independent

### Init Experience
- Progress steps show results: `Checking prerequisites... ✓ br, ✓ bv`
- Celebratory success message: ASCII art + congratulations + docs link
- Fail fast on errors: stop immediately, show clear error, suggest fix
- Plain text output (human-readable, no JSON structure needed for agent parsing)

### Prerequisites Reporting
- Platform-aware install commands: macOS (brew), Linux (apt/brew), Windows (scoop)
- Core dependencies only: br, bv, git (essential for vibraphone to function)
- Output in both formats: structured list `{tool, installed, install_command}` + ready-to-run shell script
- Auto-check on init_project call (warns if missing), also available on demand via check_prerequisites tool

### Template Variables
- Full scan auto-detection: git remote URL, directory name, language, test framework, CI platform from existing files
- Partial prompts fallback: only prompt for values that couldn't be detected
- Review first: show all detected values, let user edit before writing files
- Essentials only: project name, worktrees_path, stack config (author, repo URL, CI prefs inferred)

### Claude's Discretion
- Exact ASCII art design for celebratory message
- Progress step phrasing/wording
- Which files constitute "governance docs" (follow existing template structure)
- Error message tone and detail level

</decisions>

<specifics>
## Specific Ideas

- Experience should feel like `create-next-app` — progress feedback, celebratory finish
- Conflict handling should feel safe: user always sees what would change before confirming
- Platform detection should "just work" without user needing to specify OS

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 07-scaffolding-templates*
*Context gathered: 2026-02-17*
