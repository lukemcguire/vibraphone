# ARCHITECTURE.md — Visual Source of Truth

Mermaid diagrams that give the agent a compressed understanding of the system
without reading every file. Diagrams are generated incrementally as the project
grows.

---

## Architecture Overview

<!-- Add system context diagrams here as the project develops -->

---

## When Diagrams Are Created and Updated

| Trigger                     | Action                                                                                |
| --------------------------- | ------------------------------------------------------------------------------------- |
| `gsd:new-project` completes | Agent generates initial system context + data model diagrams                          |
| `import_gsd_plan` runs      | Bridge tool checks if phase introduces new components; flags diagram update needed    |
| `complete_task` runs        | Agent updates diagrams if task changed architecture (enforced by AGENTS.md directive) |
| `request_code_review` runs  | Reviewer checks for missing diagram updates per CONSTITUTION.md rules                 |
