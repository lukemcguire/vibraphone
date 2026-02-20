---
status: resolved
phase: 10-command-infrastructure
source: [10-01-SUMMARY.md, 10-02-SUMMARY.md, 10-03-SUMMARY.md, 10-04-SUMMARY.md, 10-05-SUMMARY.md]
started: 2026-02-20T16:00:00Z
updated: 2026-02-20T18:10:00Z
---

## Current Test

[testing complete]

## Tests

### 1. v.md Bundled in Package
expected: File src/vibraphone/commands/v.md exists with slash command content,
frontmatter (name, description, argument-hint), and MCP Tool Calling Convention
section
result: pass

### 2. setup-commands CLI Available
expected: Running `vibraphone setup-commands --help` shows usage information
for the setup-commands subcommand
result: issue
reported: "not exactly, there's a `vibraphone-cli` command that has this, the `vibraphone` command is for the MCP server"
severity: minor

### 3. setup-commands Installs v.md
expected: Running `vibraphone-cli setup-commands` creates ~/.claude/commands/v.md
with the bundled slash command content. Output shows destination path and
restart reminder.
result: pass

### 4. setup-commands Auto-Creates Directory
expected: If ~/.claude/commands/ directory doesn't exist, setup-commands
creates it automatically (no manual mkdir required)
result: pass

### 5. skill Subcommand Removed
expected: Running `vibraphone-cli skill` returns an error (command not found).
The deprecated skill subcommand no longer exists.
result: pass

### 6. README Has Slash Commands Section
expected: README.md contains a "Slash Commands" section with installation
instructions, command reference table (18 commands), and MCP Tool Calling
Convention guidance.
result: issue
reported: "references `vibraphone` not `vibraphone-cli`; the MCP Tool calling section is too under the hood compared to the scope of the rest of the README"
severity: minor

## Summary

total: 6
passed: 4
issues: 2
pending: 0
skipped: 0

## Gaps

- truth: "Running vibraphone setup-commands --help shows usage information"
  status: resolved
  reason: "User reported: not exactly, there's a `vibraphone-cli` command that has this, the `vibraphone` command is for the MCP server"
  severity: minor
  test: 2
  root_cause: "Documentation was written assuming a single `vibraphone` command would serve both MCP server and CLI purposes, but the implementation evolved to use two separate entry points (`vibraphone` for MCP server, `vibraphone-cli` for CLI) without updating the user-facing documentation accordingly."
  artifacts:
    - path: "README.md"
      line: 57
      issue: "References `vibraphone setup-commands` but should be `vibraphone-cli setup-commands`"
  missing:
    - "Update README.md line 57 to use `vibraphone-cli setup-commands`"
  debug_session: "completed"
  resolved_by: "10-05-PLAN.md"
  resolved_at: "2026-02-20"

- truth: "README Slash Commands section has accurate command names and appropriate scope"
  status: resolved
  reason: "User reported: references `vibraphone` not `vibraphone-cli`; the MCP Tool calling section is too under the hood compared to the scope of the rest of the README"
  severity: minor
  test: 6
  root_cause: "The MCP Tool Calling Convention subsection in README.md contains low-level protocol implementation details (JSON serialization behavior) that are appropriate for the v.md slash command file (where agents need this to call tools correctly) but inappropriate for a project README (where users need high-level usage guidance)."
  artifacts:
    - path: "README.md"
      lines: "85-97"
      issue: "MCP Tool Calling Convention section explains MCP protocol internals and direct tool calling, which is too technical for README audience"
  missing:
    - "Remove lines 85-97 from README.md (the entire MCP Tool Calling Convention subsection)"
    - "v.md already contains this content, making the README section redundant"
  debug_session: "completed"
  resolved_by: "10-05-PLAN.md"
  resolved_at: "2026-02-20"
