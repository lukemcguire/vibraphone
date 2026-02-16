# Phase 2: Configuration & Core Utilities - Context

**Gathered:** 2026-02-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Configuration discovery, loading, and validation infrastructure. The server finds vibraphone.yaml by walking up directories, validates it with helpful errors, and applies defaults when missing. Users don't interact with this directly, but it determines how smoothly things work when configuration problems occur.

</domain>

<decisions>
## Implementation Decisions

### Error Message Depth
- Validation errors show: field name + problem + suggestion (e.g., "worktrees_path: must be a string, got 123. Did you mean to quote the path?")
- YAML syntax errors expose parser detail (line number, parse error from library)
- Server fails fast with exit(1) on invalid config at startup
- Multiple problems reported together, not just first error
- Config file exists but unreadable (permissions, encoding) → fail with error
- Output to stderr only (no log file for v1)
- Warnings allowed for non-fatal issues, server can still start
- Warning vs error threshold at Claude's discretion

### Discovery Edge Cases
- First vibraphone.yaml wins, stop searching immediately
- Search boundary: stop at .git directory (project root)
- If no .git found, fallback to $HOME as boundary
- Discovery happens once at startup, result is cached
- Symlink handling at Claude's discretion (will follow symlinks by default)

### Unknown Field Handling
- Unknown fields in config → warn but continue
- Near-miss typo detection: warn with suggestion for fields that look like typos of known names

### Claude's Discretion
- Which scenarios warrant warnings vs errors
- Symlink handling approach (default: follow symlinks)
- Exact typo detection algorithm (Levenshtein distance threshold)

</decisions>

<specifics>
## Specific Ideas

- No specific references — this is infrastructure plumbing
- Key principle: errors should help users fix problems quickly, not just say "something is wrong"

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 02-configuration-core-utilities*
*Context gathered: 2026-02-16*
