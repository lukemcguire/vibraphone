# Vibraphone

Vibraphone is an MCP server that enforces quality gates for AI coding agents.

## Why Vibraphone?

AI coding agents are powerful but unsafe. They skip tests, ignore lint failures, and commit without review. Vibraphone enforces quality gates through tooling - not prompting.

## Features

- **Quality Gates**: Tests, lint, format, and LLM-powered code review before any commit
- **Worktree Isolation**: Each task gets its own git worktree
- **Session Recovery**: Resume interrupted work
- **Circuit Breakers**: Automatic escalation on repeated failures

## Quick Links

- [Installation & Quickstart](https://github.com/lukemcguire/vibraphone#quickstart)
- [Configuration](configuration.md)
- [Tool Reference](tools/task-tools.md)
- [Architecture](architecture.md)
