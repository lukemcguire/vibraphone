# Configuration

Vibraphone is configured via `vibraphone.yaml` in your project root.

## Full Configuration Example

```yaml
worktrees_path: ~/.vibraphone/worktrees/

circuit_breakers:
  tests:
    max_attempts: 3
  lint:
    max_attempts: 3
  format:
    max_attempts: 3
  review:
    max_attempts: 5

review:
  model: openai/gpt-4o-mini

quality_gate:
  commands:
    test: pytest
    lint: ruff check
    format: ruff format
    check: ruff check
    test_component: pytest tests/test_{component}.py
    lint_component: ruff check src/{component}/
```

## Configuration Fields

### worktrees_path

Path where git worktrees are created. Defaults to `~/.vibraphone/worktrees/`.

### circuit_breakers

Circuit breaker configuration for each quality gate tool.

| Field | Default | Description |
|-------|---------|-------------|
| `max_attempts` | 3 | Max failures before escalation. Set to `null` to disable. |

### review

Code review configuration.

| Field | Default | Description |
|-------|---------|-------------|
| `model` | openai/gpt-4o-mini | OpenRouter model for code review |

### quality_gate.commands

Command templates for quality gate tools.

| Field | Default | Description |
|-------|---------|-------------|
| `test` | pytest | Test command |
| `lint` | ruff check | Lint command |
| `format` | ruff format | Format command |
| `check` | ruff check | Pre-commit check command |
| `test_component` | (none) | Per-component test command pattern |
| `lint_component` | (none) | Per-component lint command pattern |

## Components

For multi-component projects, define components in `vibraphone.yaml`:

```yaml
components:
  server:
    language: python
    root: ./server
    test_command: pytest
    lint_command: ruff check
    format_command: ruff format
    coverage_threshold: 80
  frontend:
    language: typescript
    root: ./frontend
    test_command: npm test
    lint_command: eslint src/
    format_command: prettier --write
```

Use `configure_stack` to auto-generate this configuration.
