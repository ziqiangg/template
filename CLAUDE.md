# Router

Rules live in the files this table points to. Do not add rules here.
The current state is printed at session start (`STATE=...`). If it is missing, run
`python -I .claude/hooks/flow.py state`.

| State | Meaning | Read |
|---|---|---|
| SETUP | constitution or gate not set up yet | `.claude/instructions/setup.md` |
| IDLE | nothing in progress | new work → `intake.md`; change to existing behaviour → `change.md` |
| INTAKE | feature folder without a spec (an interrupted specify) | `.claude/instructions/intake.md` |
| CLARIFY | spec written, no plan yet | `.claude/instructions/clarify.md` |
| PLAN | plan written, checklist not yet approved | `.claude/instructions/plan.md` |
| TASKS | plan and checklist approved, no tasks yet | `.claude/instructions/tasks.md` |
| IMPLEMENT | unchecked tasks | `.claude/instructions/implement.md` |
| FINISH | all tasks done, changes not committed | `.claude/instructions/finish.md` |
| any | the request changes an existing spec, plan or principle | `.claude/instructions/change.md` |

The state follows the active feature (`.specify/feature.json`). An `unfinished:` line names other features
with open tasks; ask the user before switching to one.

Always:
- One home per fact: product behaviour in `specs/<feature>/`, principles in
  `.specify/memory/constitution.md`, gate commands in `scripts/gate.ps1`. Edit in place; git history is the archive.
- Only this session asks the user: batched rounds, each question explains the mechanism and gives options,
  a recommendation and the cost of each. Inside a Spec Kit command that asks its own questions, follow its flow.
- Brief subagents per `.claude/instructions/agent-contract.md`.
- Replies of 250 words or less; trim command output; every outside fact carries its URL.
- Stage, commit or push only after showing what changed and getting the user's yes.
- Files listed in `.claude/immutable.sha256` are fixed. Propose a change; a person edits and runs rehash.
