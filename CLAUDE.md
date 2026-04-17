# CLAUDE.md

Guidance for AI assistants (Claude Code and similar) working in this repository.

## Repository Status

This repository is in its **initial state** — no source code has been committed yet. A real analysis of structure, tooling, and conventions is not possible until code lands. The sections below are scaffolding to be filled in as the project takes shape.

When you (the assistant) add or change meaningful structure, **update this file in the same change** so it stays accurate.

## Project Overview

_TBD — describe what this project does, who it's for, and the high-level architecture once code exists._

## Repository Structure

_TBD — document top-level directories and their purpose as they're created._

Current layout:

```
.
└── CLAUDE.md
```

## Development Commands

_TBD — fill in once tooling is chosen. Typical entries:_

- **Install dependencies:** _e.g. `npm install`, `pip install -e .`, `cargo build`_
- **Run locally:** _TBD_
- **Build:** _TBD_
- **Test:** _TBD_
- **Lint / format:** _TBD_
- **Type-check:** _TBD_

## Coding Conventions

_TBD — document style rules, naming patterns, module layout, error-handling expectations, and any project-specific idioms as they emerge._

## Git Workflow

- Primary development branch for Claude-authored changes: `claude/add-claude-documentation-Iqz5u`.
- Create feature branches off the main branch (to be defined).
- Keep commits focused and descriptive.
- Do **not** open pull requests automatically — wait for an explicit request from the user.
- Do **not** skip hooks (`--no-verify`) or force-push without explicit instruction.

## Notes for AI Assistants

- Prefer editing existing files over creating new ones.
- Do not invent conventions that aren't grounded in committed code.
- When the codebase grows, replace the `TBD` sections above with real, verified information rather than speculation.
- If you're unsure whether a convention applies, ask the user rather than guessing.
