# Project template

A starting point for any project built with Claude Code and GitHub Spec Kit. It holds the tooling only:
no product, no specs. Every decision ends up in exactly one Spec Kit file, and hooks keep the workflow on
track, so there is no decision log to keep up to date.

## What is in it
| Path | What it is |
|---|---|
| `CLAUDE.md` | A short router: the current workflow state and which instruction file to read |
| `.claude/instructions/` | One fixed instruction file per state, plus the contract every agent follows |
| `.claude/agents/` | implementer, reviewer, ui-checker (Claude in Chrome), researcher |
| `.claude/hooks/flow.py` | Works out the state; blocks edits to fixed files, agent commits and broken rules |
| `.claude/immutable.sha256` | Hashes of the fixed files above |
| `.claude/skills/` | Spec Kit commands (`/speckit-*`) and react-doctor, as their installers ship them |
| `.specify/` | Spec Kit 1.2.2, unmodified |
| `specs/` | The product: one folder per feature, created by Spec Kit (not present until the first feature) |
| `scripts/gate.ps1` | The project's quality checks; the only tooling file a project edits |

## Prerequisites
Git (with Git Bash on Windows, which Claude Code uses for hooks), Python 3.11+, PowerShell 7 (`pwsh`),
Node 20+, [uv](https://docs.astral.sh/uv/) and Claude Code. Then, once per machine:

```
uv tool install specify-cli
uv tool install pre-commit
```

Optional, used by the agents:
- **Claude in Chrome** (ui-checker): install the extension, then run `/chrome` in Claude Code.
- **MCP servers** (researcher): Context7, GitHub and Hugging Face, connected in Claude Code (`/mcp`).

## Start a new project
1. Copy this folder (without `.git`) to the new project and run `git init`.
2. Open Claude Code in the project. It starts in the SETUP state and walks you through:
   the constitution (`/speckit-constitution`), the gate commands in `scripts/gate.ps1`, and `pre-commit install`.
3. Describe what you want to build. The first feature, the foundation, asks about users and goals, the
   screen map, naming and what is out of scope. Each later feature asks for its user stories, then Spec Kit
   takes over: specify, clarify, plan, tasks, implement.

## How the workflow runs
The state is computed from Spec Kit's own files each time; nothing stores it.

```
SETUP -> IDLE -> (intake questions, /speckit-specify) -> CLARIFY -> PLAN -> TASKS -> IMPLEMENT -> FINISH -> IDLE
         any state: a change to existing behaviour -> CHANGE -> back to IMPLEMENT or FINISH
```
The first feature, `000-foundation`, holds what every feature shares: users and goals, the screen map,
the glossary and naming conventions, and what is out of scope. It goes through clarify only and has no
stories, plan or tasks; each story lives in the one feature spec that builds it.

- Product decisions are edited into the feature spec in place; principles into the constitution.
  Git history is the archive.
- Only the main session asks you questions. Agents return their questions in their report.
- Claude commits only after showing the change and getting your yes; agents never commit.

Check the state yourself: `python -I .claude/hooks/flow.py state`.
List everything that names a term before changing it: `python -I .claude/hooks/flow.py refs "<term>"`.

## Changing a fixed file
Files listed in `.claude/immutable.sha256` are blocked for Claude. To change one on purpose, edit it
yourself, then record the new hashes in your own terminal: `python -I .claude/hooks/flow.py rehash`.

The edit guard is a first line only: a shell command can still slip past it (for example through a glob).
The Stop hook and pre-commit re-check every hash, so such an edit is caught before the turn ends or a commit.

Turn off any plugin that brings its own planning or development process (for example one that plans,
dispatches agents or creates worktrees), so Spec Kit is the only process: `/plugin` in Claude Code.

## Upgrading Spec Kit
```
uv tool upgrade specify-cli
specify integration upgrade claude
```
Spec Kit's files are not hash-locked, so no rehash is needed. Check the release notes for renamed commands
and update the instruction files if any changed.

## Known issue
On Windows, Spec Kit's PowerShell scripts can garble the emoji in Spec Kit's own templates (development
documents only, never the app) and print broken JSON. The commands still work around it. Spec Kit also
ships Python scripts (`specify init ... --script py`), which may avoid this; not yet tried.

## Tests for the tooling
`python -m unittest discover -s .claude/hooks/tests`
