# IMPLEMENT: build one user-story phase at a time

0. Before the first phase (no task in tasks.md ticked yet), run `/speckit-analyze`. It is read-only: show
   its report in the reply, never save it to a file. Fix every CRITICAL and HIGH finding at its source
   (spec, plan or tasks) and run it again; ask the user about any finding that needs a decision.
1. Every item in `checklists/` must be ticked by the user's approval (plan.md step 5); otherwise settle
   them with the user first, because `/speckit-implement` stops on unticked items.
2. Pick the next unchecked phase in tasks.md. Dispatch the implementer with a brief per agent-contract.md:
   the feature path, the phase and task ids, the acceptance scenarios that phase must satisfy, and the
   skill call `/speckit-implement <phase, task ids>`. One phase per dispatch; run phases one after another
   (no worktrees, no parallel writers).
3. When the implementer returns:
   - read its report; answer its QUESTIONS in a batched round with the user;
   - a decision that changes the spec, plan or a principle goes through change.md before work continues;
   - confirm the phase's tasks are checked in tasks.md, each test first failed on an assertion, and the
     gate passed.
4. A task that needs a tool that is not available: ask the user whether to wait, do it by hand, or move it
   out of scope through change.md. Never tick it without the work done.
5. Repeat until no task is unchecked. The state moves to FINISH.
