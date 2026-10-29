# IMPLEMENT: build one user-story phase at a time

1. If `checklists/` has incomplete items, settle them with the user first (implement would stop and ask).
2. Pick the next unchecked phase in tasks.md. Dispatch the implementer with a brief per agent-contract.md:
   the feature path, the phase and task ids, and the acceptance scenarios that phase must satisfy.
   One phase per dispatch; run phases one after another (no worktrees, no parallel writers).
3. When the implementer returns:
   - read its report; answer its QUESTIONS in a batched round with the user;
   - a decision that changes the spec, plan or a principle goes through change.md before work continues;
   - confirm the phase's tasks are checked in tasks.md and the gate passed.
4. Repeat until no task is unchecked. The state moves to FINISH.
