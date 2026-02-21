---
status: resolved
trigger: "/v init command (which invokes vibraphone_init_project MCP tool) doesn't work"
created: "2026-02-21T13:20:00Z"
updated: "2026-02-21T22:35:00Z"
resolved_by: 11-05-PLAN.md
---

## Current Focus

hypothesis: (Confirmed - see Resolution)
test: N/A
expecting: N/A
next_action: Report diagnosis to user

## Symptoms

expected: When user runs `/v init`, Claude Code should call the
`vibraphone_init_project` MCP tool with `{"preview": true}` and display results.

actual: User reports "The documentation is there, but the commands don't
actually work."

errors: Unknown - user has not provided specific error message.

reproduction: Run `/v init` in a Claude Code session.

started: Unknown - first report.

## Eliminated

(Empty - investigation in progress)

## Evidence

- timestamp: "2026-02-21T13:21:00Z"
  checked: MCP server registration
  found: All 20 MCP tools properly registered including `init_project`
  implication: MCP server is working correctly

- timestamp: "2026-02-21T13:22:00Z"
  checked: MCP server executable
  found: `vibraphone` command found at `/home/luke/.local/bin/vibraphone`
  implication: MCP server is properly installed

- timestamp: "2026-02-21T13:23:00Z"
  checked: MCP configuration
  found: `.mcp.json` correctly configures vibraphone MCP server
  implication: MCP server should be available to Claude Code

- timestamp: "2026-02-21T13:24:00Z"
  checked: Slash command installation
  found: `~/.claude/commands/v.md` exists (25KB)
  implication: Slash command file is properly installed

- timestamp: "2026-02-21T13:25:00Z"
  checked: Direct MCP tool invocation via stdio
  found: `init_project` tool responds correctly with valid JSON when called
         via MCP protocol
  implication: The MCP server and tool are fully functional

- timestamp: "2026-02-21T13:26:00Z"
  checked: Slash command file format
  found: Frontmatter has `allowed-tools: [mcp__vibraphone]` but this may not
         be the correct format to allow/invoke MCP tools
  implication: The slash command file format may not properly instruct Claude
               to invoke MCP tools

- timestamp: "2026-02-21T13:32:00Z"
  checked: Comparison with working gsd slash commands
  found: Working commands (gsd:debug, gsd:health, gsd:quick) have:
         - `<objective>` section
         - `<process>` section with executable instructions
         - `$ARGUMENTS` parsing and routing
         v.md has NONE of these - it's purely reference documentation
  implication: v.md is missing the executable instructions that Claude Code
               needs to actually perform actions when the slash command is invoked

- timestamp: "2026-02-21T13:34:00Z"
  checked: gsd:health.md structure (working command)
  found: Has `<objective>`, `<execution_context>`, and `<process>` sections
         with specific instructions: "Execute the health workflow..."
  implication: v.md needs similar structure with `<process>` section that
               parses `$ARGUMENTS` and routes to appropriate MCP tool calls

- timestamp: "2026-02-21T13:38:00Z"
  checked: Phase 11 plan (11-01-PLAN.md)
  found: Phase 11 was explicitly about "documentation" - creating reference
         material for v.md. The plan never included making v.md executable.
  implication: This was a design gap - the slash command file was designed
               as reference documentation, not an executable command router.

## Resolution

root_cause: The v.md slash command file is structured as pure reference
documentation, not as an executable command. It lacks:

1. `<objective>` section explaining what to do
2. `<process>` section with instructions to:
   - Parse $ARGUMENTS to extract command name and flags
   - Route to appropriate MCP tool (mcp__vibraphone__init_project, etc.)
   - Handle the tool response

When the user runs `/v init`, Claude Code sees the slash command file but
only finds documentation about what the tools do - not instructions on how
to actually invoke them. Working slash commands (like gsd:debug) have
explicit `<process>` sections that tell Claude exactly what to do.

fix: Restructure v.md to be an executable command router. Two options:

**Option A - Minimal Fix:** Add a `<process>` section that:
1. Parses $ARGUMENTS to get the subcommand (init, list, next, etc.)
2. Contains instructions to call the appropriate MCP tool
3. Handles responses

**Option B - Full Rewrite:** Create separate slash command files for each
command (like gsd does with gsd:debug, gsd:health, etc.):
- ~/.claude/commands/v/init.md
- ~/.claude/commands/v/list.md
- ~/.claude/commands/v/next.md
- etc.

This would require updating the CLI setup-commands to install multiple files.

verification: After fix, running `/v init` should trigger Claude to call
the vibraphone_init_project MCP tool with appropriate parameters.

files_changed: []
suggested_files:
  - src/vibraphone/commands/v.md (primary fix target)

## Resolution Applied

date: "2026-02-21T22:35:00Z"
plan: 11-05-PLAN.md
approach: Option A - Minimal Fix
changes:
  - Added `<process>` section to v.md after frontmatter
  - Implemented $ARGUMENTS parsing for subcommands, flags, positional args
  - Created routing table mapping 18 subcommands to MCP tools (mcp__vibraphone__*)
  - Added preview pattern handling for init, configure-stack, import-plan
  - Added cycle and finish shortcuts
verified: true
verification_notes: "v.md now contains 27 MCP tool references and process section"
