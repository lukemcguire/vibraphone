# Feature Landscape

**Domain:** MCP Server Package + Python Developer Tool
**Researched:** 2026-02-16
**Confidence:** MEDIUM (based on Python packaging ecosystem knowledge, MCP specification, and developer tool patterns; lack of web access for current MCP ecosystem survey)

## Table Stakes

Features users expect. Missing = product feels incomplete.

| Feature | Why Expected | Complexity | Dependencies | Notes |
|---------|--------------|------------|--------------|-------|
| **Package Installation** | | | | |
| `uv tool install` support | Modern Python tooling standard; isolated environments | Low | Proper pyproject.toml with [project.scripts] | Must work with both `uv` and `pip` |
| `pip install -e .` (editable) | Developer standard for local development | Low | Standard setuptools/hatch config | Critical for contributors |
| Dependency declaration | Python packaging fundamental | Low | None | Runtime deps in [project.dependencies], optional deps in [project.optional-dependencies] |
| Version pinning strategy | Reproducible installs | Medium | Lock file or constraint strategy | Balance compatibility vs security |
| **Server Lifecycle** | | | | |
| Single entry point command | MCP servers run as standalone processes | Low | [project.scripts] in pyproject.toml | `vibraphone` → starts FastMCP server |
| Graceful startup/shutdown | Process management expectation | Medium | Signal handlers (SIGTERM, SIGINT) | Clean resource cleanup |
| Error handling on startup | Users need actionable error messages | Medium | Dependency checks before server start | Fail fast with clear guidance |
| Stdio transport support | MCP standard transport | Low | FastMCP handles this | Required for Claude Desktop integration |
| **Configuration** | | | | |
| Project-level config file | Users expect to configure tool behavior | Low | YAML/TOML/JSON parsing | vibraphone.yaml already designed |
| Config file discovery | Tools should find config automatically | Low | Walk up directory tree from cwd | Standard pattern (like .git discovery) |
| Config validation on load | Prevent cryptic runtime errors | Medium | Pydantic or similar schema validation | Fail fast with clear error messages |
| Sensible defaults | Zero-config for simple cases | Medium | Depends on config schema design | Must work without config for basic usage |
| **MCP Protocol Compliance** | | | | |
| Tool registration | MCP servers expose tools | Low | FastMCP handles this | Already implemented |
| Tool schemas (JSON Schema) | Clients need to understand tool parameters | Low | FastMCP decorators handle this | Already implemented |
| Error responses | MCP error protocol compliance | Low | FastMCP handles this | Standard JSON-RPC error codes |
| Capability negotiation | MCP initialization handshake | Low | FastMCP handles this | Server capabilities declaration |
| **Documentation** | | | | |
| README with quickstart | First thing users see | Low | None | Installation → basic usage → next steps |
| Installation instructions | Users need to know how to install | Low | None | Multiple methods: uv, pip, git |
| Tool reference docs | Users need to know what tools exist | Medium | None | One page per tool with examples |
| Configuration reference | Users need to know config options | Medium | Depends on config finalization | Schema → markdown generation |
| Troubleshooting guide | Users will hit common issues | Medium | Aggregate learnings over time | Prerequisites, permissions, path issues |
| **Quality Assurance** | | | | |
| Unit tests | Developer tool standard | Medium | pytest | Mock external dependencies (br, git) |
| Integration tests | Verify end-to-end flows | High | Real git repos, br binary | Critical for workflow correctness |
| Type hints | Python 3.13 expectation | Low | None | Already in pyproject.toml linting rules |
| Linting in CI | Maintain code quality | Low | Ruff (already configured) | Enforce on PR |
| **Prerequisite Management** | | | | |
| Dependency detection | Tool wraps external binaries (br, bv, git, just, node) | Medium | `check_prerequisites` tool (in scope) | Detect via shutil.which() |
| Clear error messages | Users need to know what's missing and how to fix it | Low | Prerequisite detection | "br not found. Install: cargo install beads_rust" |
| Graceful degradation | Some features optional (bv for triage/plan_parallel) | Medium | Feature flags in code | Core works, advanced features require more deps |
| **Project Scaffolding** | | | | |
| `init_project` command | Users expect setup wizard for new projects | High | `init_project` tool (in scope) | Generate config, docs, Justfile, .mcp.json |
| Template file generation | Scaffold needs templates to render | Medium | Bundle templates in package | AGENTS.md, CLAUDE.md, governance docs |
| Idempotent scaffolding | Re-running should be safe | Medium | Check existing files before overwrite | Merge or skip, don't clobber |
| `.gitignore` updates | Generated files need ignore rules | Low | Append to existing .gitignore | .vibraphone/, worktrees if local |
| **Cross-Platform Support** | | | | |
| Linux support | Primary development platform | Low | Already working (WSL2 in context) | Path handling, shell commands |
| macOS support | Common developer platform | Medium | Path differences, shell differences | Test on macOS |
| Windows support (best-effort) | Some users on Windows | High | Path separators, shell commands, worktree paths | Consider WSL2 as primary Windows path |

## Differentiators

Features that set product apart. Not expected, but valued.

| Feature | Value Proposition | Complexity | Dependencies | Notes |
|---------|-------------------|------------|--------------|-------|
| **Workflow Enforcement** | | | | |
| Quality gate circuit breakers | **Core differentiator**: Can't commit bad code | Medium | Existing implementation | Tests must pass before commit allowed |
| Worktree isolation | **Core differentiator**: Tasks isolated, main stays clean | Medium | Git worktree support | Prevents context bleeding between tasks |
| LLM-powered code review | **Core differentiator**: AI enforces CONSTITUTION | High | LLM API access, prompt templates | Governance-aware review before merge |
| Session recovery | **Core differentiator**: Resume after crash/disconnect | High | Session state persistence | Check for stale sessions on startup |
| **Developer Experience** | | | | |
| Auto-recovery on startup | Detects incomplete sessions without user action | Medium | vibraphone.yaml presence check | "You have task X in worktree Y. Resume?" |
| Smart config defaults | Minimal config needed for common cases | Medium | Config schema design | Worktree default `~/.vibraphone/worktrees/` |
| Rich error context | Errors include next steps, not just failure | Medium | Error message design | "Test failed: 3 failures in test_foo.py. Run `just test` to see details." |
| Health check tool | Self-diagnostic for troubleshooting | Low | Existing `health_check` tool | Check br, config, session state, worktree status |
| **Integration Depth** | | | | |
| GSD planning bridge | Import GSD plans into task system | Medium | `import_gsd_plan` tool (existing) | npx @lukemcguire/get-shit-done wrapper |
| Justfile recipe generation | Integrate with existing task runners | Low | `init_project` generates recipes | test, lint, format recipes |
| Git worktree-aware tools | All tools understand worktree context | High | Worktree path tracking in session | `start_task` creates, tools operate in it, `cleanup_task` removes |
| **Governance as Code** | | | | |
| CONSTITUTION.md enforcement | Code review checks against project rules | High | LLM review with CONSTITUTION context | Not just lint rules — architectural principles |
| Architecture diagram generation | Living architecture docs | Medium | Mermaid templates in ARCHITECTURE.md | Scaffold template, user maintains |
| Decision log (ADR) scaffolding | Capture design decisions over time | Low | DECISIONS.md template | Markdown template with ADR format |
| Glossary scaffolding | Domain language documentation | Low | GLOSSARY.md template | Reduces ambiguity in agent conversations |
| **Testing Discipline** | | | | |
| TDD loop enforcement | Test → Code → Review → Commit | Medium | Circuit breaker integration | Can't merge without passing tests |
| Test runner integration | Run tests in context, block on failure | Low | Existing `run_tests` tool | Shell out to pytest/just test |
| Coverage awareness (future) | Track test coverage trends | High | coverage.py integration | Out of scope for v1, but natural extension |

## Anti-Features

Features to explicitly NOT build.

| Anti-Feature | Why Avoid | What to Do Instead | Notes |
|--------------|-----------|-------------------|-------|
| **Distribution Complexity** | | | |
| PyPI publishing (v1) | Premature optimization; no users yet | Install from git URL or local path | Add PyPI when usage validates need |
| Multiple distribution formats | Complexity without proven need | Python package only | No Docker image, no binary, no snap/brew |
| Plugin system | YAGNI; adds API surface to maintain | Built-in tools only | Extensibility via config, not plugins |
| **Interface Expansion** | | | |
| Standalone CLI (beyond server) | Duplicate functionality; maintenance burden | MCP tools only | Single `vibraphone` entry point starts server |
| Web UI | Out of scope; MCP is the interface | Agent interaction via tools | Users interact through Claude/coding agents |
| REST API | MCP already provides RPC interface | stdio MCP transport | Don't add second interface |
| **Configuration Complexity** | | | |
| User-level config (`~/.config/vibraphone/`) | Project-level sufficient for v1; adds complexity | vibraphone.yaml in project only | Defer until multi-project patterns emerge |
| Environment variable config | YAML config is explicit and auditable | vibraphone.yaml only | Exception: runtime secrets (API keys) |
| Config format proliferation | Multiple formats = maintenance burden | YAML only | Not TOML, not JSON, not INI |
| **Feature Creep** | | | |
| Task estimation/tracking | beads_rust already handles this | Delegate to br | Don't reimplement beads features |
| CI/CD integration | Out of scope; focus on local workflow | Local quality gate only | CI can call vibraphone tools, but not vibraphone's job |
| Issue tracker integration | Out of scope; beads is task system | Use br for tasks | GitHub issues ≠ vibraphone tasks |
| Multi-agent orchestration (v1) | bv not reliably available; defer | Stub `triage`, `plan_parallel` | Keep placeholders, don't implement |
| Language polyglot support | Python projects only for v1 | Python-specific tooling | Justfile is polyglot, but vibraphone assumes Python |

## Feature Dependencies

```
Package Installation
  └─> Server Lifecycle
        └─> MCP Protocol Compliance
              └─> Tool Registration
                    ├─> Configuration (tools need config)
                    ├─> Prerequisite Management (tools need br/git/etc)
                    ├─> Workflow Enforcement (core tools)
                    └─> Project Scaffolding (init_project tool)

Configuration
  ├─> Config File Discovery
  ├─> Config Validation
  └─> Sensible Defaults

Prerequisite Management
  └─> Graceful Degradation (when optional deps missing)

Project Scaffolding
  ├─> Template File Generation
  ├─> Idempotent Scaffolding
  └─> .gitignore Updates

Workflow Enforcement
  ├─> Quality Gate Circuit Breakers
  │     └─> Test Runner Integration
  ├─> Worktree Isolation
  │     └─> Git Worktree-Aware Tools
  ├─> LLM-Powered Code Review
  │     └─> Governance as Code (CONSTITUTION.md)
  └─> Session Recovery
        └─> Auto-Recovery on Startup

GSD Planning Bridge
  └─> Prerequisite Management (needs node/npx)

Governance as Code
  ├─> Project Scaffolding (generates templates)
  └─> LLM-Powered Code Review (consumes CONSTITUTION.md)
```

## MVP Recommendation

### Phase 1: Package Foundation
Prioritize table stakes to make the package installable and usable:

1. **Package Installation** - uv/pip install works
2. **Server Lifecycle** - `vibraphone` command starts server
3. **MCP Protocol Compliance** - Server responds to MCP clients
4. **Configuration** - vibraphone.yaml discovery and loading
5. **Documentation** - README with installation and quickstart

**Defer:** Cross-platform testing (Linux first), advanced error handling

### Phase 2: Core Workflow
Migrate existing tools to enable the workflow differentiators:

1. **Prerequisite Management** - `check_prerequisites` tool
2. **Workflow Enforcement** - Migrate existing tools (beads, worktree, quality gate)
3. **Project Scaffolding** - `init_project` tool
4. **Quality Assurance** - Unit tests for migrated tools

**Defer:** Integration tests (manual verification first), session recovery (known bug)

### Phase 3: Polish
Add differentiators that improve DX:

1. **Session Recovery** - Auto-recovery on startup (fix known bug)
2. **Integration Depth** - GSD bridge, Justfile generation (via init_project)
3. **Governance as Code** - CONSTITUTION enforcement in code review
4. **Developer Experience** - Rich error messages, health check
5. **Quality Assurance** - Integration tests
6. **Documentation** - Tool reference, config reference, troubleshooting

**Defer:** Coverage awareness (future), multi-agent orchestration (requires bv)

### Rationale for Ordering

**Phase 1 → Phase 2:** Can't test workflow without package being installable.

**Phase 2 → Phase 3:** Core workflow must work before polish matters. Session recovery is valuable but not blocking for initial usage.

**GSD bridge in Phase 3:** Vibraphone works standalone; GSD integration is bonus.

**Documentation incremental:** Basic docs in Phase 1 (installation), comprehensive docs in Phase 3 (after features stable).

## Complexity Assessment

| Feature Category | Overall Complexity | Risk Areas |
|------------------|-------------------|------------|
| Package Installation | LOW | Standard Python packaging patterns |
| Server Lifecycle | LOW | FastMCP handles heavy lifting |
| MCP Protocol Compliance | LOW | FastMCP abstracts protocol details |
| Configuration | MEDIUM | Schema validation, discovery logic |
| Prerequisite Management | MEDIUM | Cross-platform binary detection |
| Project Scaffolding | MEDIUM-HIGH | Template rendering, idempotency, file merging |
| Workflow Enforcement | HIGH | Git worktree complexity, session state management |
| LLM-Powered Code Review | HIGH | Prompt engineering, LLM API reliability, CONSTITUTION parsing |
| Session Recovery | HIGH | State persistence, crash detection, recovery flow (known bug) |
| Integration Depth | MEDIUM | External tool wrapping (br, git, just, npx) |
| Quality Assurance | MEDIUM-HIGH | Integration tests need real git repos and br |
| Cross-Platform Support | MEDIUM-HIGH | Path handling, shell differences, worktree behavior varies |

## Sources

**Note:** Research conducted without web access due to tool restrictions. Findings based on:

- Python packaging ecosystem knowledge (PEP 517/518/621, setuptools, hatchling, uv, pip)
- MCP specification understanding (stdio transport, JSON-RPC, tool schemas, capability negotiation)
- Python developer tool patterns (pytest, ruff, mypy, pre-commit, tox)
- Project context documents (migration-plan.md, PROJECT.md, pyproject.toml)
- Developer tool packaging experience (CLI tools, LSP servers, framework integrations)

**Confidence Level:** MEDIUM
- **HIGH confidence:** Python packaging table stakes, MCP protocol basics, developer tool expectations
- **MEDIUM confidence:** MCP ecosystem patterns (no web access to survey current MCP servers)
- **LOW confidence:** Current MCP server landscape (unable to verify what other MCP servers include)

**Recommended Validation:**
- Survey existing MCP servers (GitHub search, MCP registry if exists) to identify common patterns
- Review FastMCP documentation for latest best practices
- Check uv documentation for `uv tool install` requirements and conventions
- Test cross-platform behavior early (macOS, Windows/WSL2) to avoid late surprises
