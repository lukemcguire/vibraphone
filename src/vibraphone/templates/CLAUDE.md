# CLAUDE.md — Claude Instructions

This file provides Claude-specific guidance for working with this project.

## Workflow

Read `AGENTS.md` for the complete workflow state machine and available MCP tools.

## Project Context

<!-- Add project-specific context here after initialization -->

## Key Conventions

- Follow the TDD loop: write failing test → implement → run tests → lint → review → commit
- Always use MCP tools for git operations, never raw shell commands
- Each tool response includes `next_steps` — follow them

## Architecture

See `docs/ARCHITECTURE.md` for system diagrams and component relationships.

## Coding Rules

See `docs/CONSTITUTION.md` for language-specific coding conventions.
